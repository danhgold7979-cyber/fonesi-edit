"""Versioned SQLite projects and recoverable explicit project-file saves."""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass,replace
from hashlib import sha256
import json,os,sqlite3,time,uuid,stat
from pathlib import Path
from typing import Callable
from ..fileio import read_bounded
from .sqlite_open import open_versioned
from .db_ownership import owns_database,register_database,receipt_path
from ..domain.composition import CompositionPlan,canonical,PlanError
from ..domain.media_library import MediaLibrary,MediaRecord

SCHEMA_VERSION=2
APPLICATION_ID=1178946130
PROJECTS_V1_SQL='CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, document TEXT NOT NULL, version INTEGER NOT NULL CHECK(version>0), updated_at REAL NOT NULL)'
PROJECTS_SQL=PROJECTS_V1_SQL[:-1]+', origin_base TEXT)'
PROJECT_SCHEMA_HASH=sha256(''.join(PROJECTS_SQL.lower().split()).encode()).hexdigest()
PROJECT_V1_HASH=sha256(''.join(PROJECTS_V1_SQL.lower().split()).encode()).hexdigest()
MAX_PROJECT_BYTES=33*1024*1024

def _read_project(path):
    try:return read_bounded(path,MAX_PROJECT_BYTES)
    except ValueError as exc:raise StorageError(str(exc)) from exc

class StorageError(RuntimeError):pass
class ConflictError(StorageError):pass
class NewerSchemaError(StorageError):pass

@dataclass(frozen=True)
class Project:
    id: str
    name: str
    plan: CompositionPlan
    library: MediaLibrary|None = None

    def __post_init__(self):
        try:uuid.UUID(self.id)
        except (ValueError,TypeError,AttributeError) as exc:raise StorageError('Invalid project UUID') from exc
        if not isinstance(self.name,str) or not self.name.strip() or len(self.name)>200:
            raise StorageError('Project name must contain1..200characters')
        if not isinstance(self.plan,CompositionPlan):raise StorageError('Validated CompositionPlan required')
        if self.library is not None:
            if type(self.library) is not MediaLibrary:raise StorageError('Typed source library required')
            self.library.__post_init__()

    def with_plan(self,plan):
        """Preserve every project-level field when changing composition."""
        return replace(self,plan=plan)

    def to_json(self):
        self.__post_init__()
        payload={'format':'fonesi-edit-project','schema_version':1 if self.library is None else 2,
                 'project_id':self.id,'name':self.name,'composition':self.plan.to_dict()}
        if self.library is not None:payload['media_library']=self.library
        def encode(value):
            # Do not eagerly asdict the entire library before enforcing the
            # whole-envelope budget. At most one bounded record is projected.
            if type(value) is MediaLibrary:return {'schema_version':1,'items':value.items}
            if type(value) is MediaRecord:return value.to_dict()
            raise TypeError('Unsupported project field')
        encoder=json.JSONEncoder(sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False,default=encode)
        chunks=[];size=0
        for chunk in encoder.iterencode(payload):
            if len(chunk)>MAX_PROJECT_BYTES-size:raise StorageError('Project envelope exceeds33MiB')
            size+=len(chunk.encode('utf-8'))
            if size>MAX_PROJECT_BYTES:raise StorageError('Project envelope exceeds33MiB')
            chunks.append(chunk)
        return ''.join(chunks)

    @classmethod
    def parse(cls,text):
        def pairs(values):
            out={}
            for k,v in values:
                if k in out:raise StorageError('Duplicate project JSON key')
                out[k]=v
            return out
        try:
            if type(text) not in (str,bytes) or len(text)>MAX_PROJECT_BYTES:raise StorageError('Project file too large/invalid input')
            if isinstance(text,str) and len(text.encode('utf-8'))>MAX_PROJECT_BYTES:raise StorageError('Project file too large')
            raw=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(StorageError('Nonfinite JSON')))
            if type(raw) is not dict or 'schema_version' not in raw:raise StorageError('Invalid project envelope')
            if type(raw['schema_version']) is not int:raise StorageError('Invalid project schema version')
            if raw['schema_version']>2:raise NewerSchemaError('Newer project schema: original left unchanged')
            expected={'format','schema_version','project_id','name','composition'}
            if raw['schema_version']==2:expected.add('media_library')
            if set(raw)!=expected:raise StorageError('Invalid/unknown project envelope fields')
            if raw['schema_version'] not in (1,2) or raw['format']!='fonesi-edit-project':raise StorageError('Unsupported project format/version')
            library=None if raw['schema_version']==1 else MediaLibrary.from_dict(raw['media_library'])
            return cls(raw['project_id'],raw['name'],CompositionPlan.parse(raw['composition']),library)
        except (ValueError,TypeError,UnicodeError,RecursionError) as exc:
            if isinstance(exc,StorageError):raise
            raise StorageError(str(exc)) from exc

@dataclass(frozen=True)
class StoredProject:
    project: Project
    version: int # repository CAS token; distinct from composition revision
    origin_base: str|None = None # Private execution base; never exported in Project JSON

def _origin(value):
    if value is None:return None
    if not isinstance(value,(str,Path)):raise StorageError('Invalid project origin base')
    text=str(value)
    if not text or len(text)>32767 or '\x00' in text or not Path(text).is_absolute():
        raise StorageError('Project origin base must be a bounded absolute path')
    return text


class ProjectStore:
    def __init__(self,path:Path|str,*,fault:Callable[[str],None]|None=None):
        self.path=Path(path).absolute();self.path.parent.mkdir(parents=True,exist_ok=True)
        self._fault=fault or (lambda _:None);self._closed=False
        self.db=None;self._fd=None;self._revoked=False
        created=False
        try:
            schema_hash=PROJECT_SCHEMA_HASH
            allowed_hashes=(PROJECT_SCHEMA_HASH,PROJECT_V1_HASH)
            flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)
            try:
                self._fd=os.open(self.path,flags|os.O_CREAT|os.O_EXCL,0o600);created=True
            except FileExistsError:
                info=self.path.lstat()
                if not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
                    raise StorageError('Project database must be regular/non-reparse')
                self._fd=os.open(self.path,flags)
            info=os.fstat(self._fd);self._identity=(info.st_dev,info.st_ino);self._guard()
            if not created and not owns_database(self.path,APPLICATION_ID,allowed_hashes):
                os.lseek(self._fd,0,os.SEEK_SET);header=os.read(self._fd,100)
                if len(header)==100 and header[:16]==b'SQLite format 3\x00' and int.from_bytes(header[60:64],'big')>SCHEMA_VERSION:
                    raise NewerSchemaError('Newer database schema; no write performed')
                raise StorageError('Unrecognized/Foreign database or unmarked schema; explicit recovery required')
            marker=receipt_path(self.path)
            if created and (marker.exists() or marker.is_symlink()):
                raise StorageError('Existing project ownership receipt conflicts with new database')
            connect=lambda path,**kwargs:sqlite3.connect(Path(path).as_uri()+'?mode=rw',uri=True,**kwargs)
            self.db,version=open_versioned(self.path,connect=connect,owned=lambda:owns_database(self.path,APPLICATION_ID,allowed_hashes))
            self._guard()
            if version not in (0,1,SCHEMA_VERSION) and version<=SCHEMA_VERSION:raise StorageError('Unsupported project schema version')
            if version>SCHEMA_VERSION:raise NewerSchemaError(f'Database schema{version} newer than{SCHEMA_VERSION}; no write performed')
            application_id=self.db.execute('PRAGMA application_id').fetchone()[0]
            if version in (1,SCHEMA_VERSION) and application_id!=APPLICATION_ID:raise StorageError('Foreign database identity; left unchanged')
            tables=self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            if version==0 and tables:raise StorageError('Unrecognized unversioned database; refusing to migrate unrelated tables')
            if version in (1,SCHEMA_VERSION):
                actual=self.db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
                extra=self.db.execute("SELECT 1 FROM sqlite_master WHERE type!='table' AND name NOT LIKE 'sqlite_%'").fetchone()
                if extra or actual!=[('projects',PROJECTS_V1_SQL if version==1 else PROJECTS_SQL)]:
                    raise StorageError('Corrupt or unexpected project schema; left unchanged')
            self.db.execute('PRAGMA foreign_keys=ON');self.db.execute('PRAGMA busy_timeout=5000')
            if version<SCHEMA_VERSION:
                if version==0 and not created:
                    raise StorageError('Unmarked initialization is not automatically resumed')
                if version==1:
                    self._backup()
                    self._guard()
                    if not owns_database(self.path,APPLICATION_ID,allowed_hashes):
                        raise StorageError('Project ownership changed before migration')
                self._fault('before_migration')
                with self.transaction():
                    expected_tables=[] if version==0 else [('projects',PROJECTS_V1_SQL)]
                    expected_id=0 if version==0 else APPLICATION_ID
                    if (self.db.execute('PRAGMA user_version').fetchone()[0]!=version or
                            self.db.execute('PRAGMA application_id').fetchone()[0]!=expected_id or
                            self.db.execute("SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()!=expected_tables):
                        raise StorageError('Concurrent project migration; not replayed')
                    if version==0:self.db.execute(PROJECTS_SQL)
                    else:self.db.execute('ALTER TABLE projects ADD COLUMN origin_base TEXT')
                    self._fault('after_schema_creation')
                    self.db.execute(f'PRAGMA application_id={APPLICATION_ID}')
                    self.db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
            self._guard()
            self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
            self._guard()
            register_database(self.path,APPLICATION_ID,schema_hash,legacy_hashes=(PROJECT_V1_HASH,))
        except BaseException as exc:
            if isinstance(exc,sqlite3.Error):
                exc.add_note(f'SQLite {sqlite3.sqlite_version}; extended code={getattr(exc, "sqlite_errorcode", None)} name={getattr(exc, "sqlite_errorname", None)}')
            self.close();raise

    def _guard(self):
        if self._closed or self._revoked:raise StorageError('Project store closed or identity revoked')
        try:
            current=self.path.lstat();opened=os.fstat(self._fd)
            if (not opened.st_ino or not current.st_ino or not stat.S_ISREG(current.st_mode) or getattr(current,'st_file_attributes',0)&0x400 or
                    (current.st_dev,current.st_ino)!=self._identity or
                    (opened.st_dev,opened.st_ino)!=self._identity):
                raise StorageError('Project database identity changed')
        except BaseException:
            self._revoked=True
            raise

    def _backup(self):
        target=self.path.with_name(self.path.name+'.backup-'+uuid.uuid4().hex)
        # SQLite backup API makes a consistent snapshot, not a live WAL-file copy.
        dest=sqlite3.connect(target)
        try:
            self.db.backup(dest)
            if dest.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise StorageError('Migration backup validation failed')
        finally:dest.close()
        with target.open('r+b') as f:os.fsync(f.fileno())
        self._fault('after_backup')
        return target

    @contextmanager
    def transaction(self):
        self._guard()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self._guard()
            self.db.execute('COMMIT')
        except BaseException:
            if self.db.in_transaction:self.db.execute('ROLLBACK')
            raise

    def save(self,project:Project,*,expected_version:int|None=None,origin_base:Path|str|None=None)->StoredProject:
        # Revalidate at persistence boundary even when caller supplied typed object.
        document=Project.parse(project.to_json()).to_json()
        origin_base=_origin(origin_base)
        if expected_version is not None and (type(expected_version) is not int or expected_version<1):raise StorageError('Invalid expected version')
        with self.transaction():
            current=self.db.execute('SELECT version FROM projects WHERE id=?',(project.id,)).fetchone()
            if current is None:
                if expected_version is not None:raise ConflictError('Project was removed or never existed')
                version=1
                self.db.execute('INSERT INTO projects VALUES (?,?,?,?,?,?)',(project.id,project.name,document,version,time.time(),origin_base))
            else:
                if current[0]!=expected_version:raise ConflictError('Project changed; reload before saving')
                if project.library is None:
                    prior=self.db.execute('SELECT document FROM projects WHERE id=?',(project.id,)).fetchone()[0]
                    if Project.parse(prior).library is not None:raise ConflictError('Cannot downgrade v2 project library')
                version=current[0]+1
                self.db.execute('UPDATE projects SET name=?,document=?,version=?,updated_at=?,origin_base=? WHERE id=? AND version=?',(project.name,document,version,time.time(),origin_base,project.id,expected_version))
            self._fault('before_project_commit')
        return StoredProject(project,version,origin_base)

    def load(self,project_id:str)->StoredProject:
        self._guard()
        row=self.db.execute('SELECT document,version,origin_base FROM projects WHERE id=?',(project_id,)).fetchone()
        self._guard()
        if row is None:raise KeyError(project_id)
        return StoredProject(Project.parse(row[0]),row[1],_origin(row[2]))

    def list_projects(self)->tuple[StoredProject,...]:
        self._guard()
        result=tuple(StoredProject(Project.parse(row[0]),row[1],_origin(row[2])) for row in self.db.execute('SELECT document,version,origin_base FROM projects ORDER BY updated_at DESC,id'))
        self._guard()
        return result

    def close(self):
        try:
            if not self._closed and self.db is not None:self.db.close()
        finally:
            self._closed=True
            if self._fd is not None:os.close(self._fd);self._fd=None
    def __enter__(self):return self
    def __exit__(self,*exc):self.close()

@contextmanager
def _project_lock(path):
    """Cooperating saves use a marked lock file; never write a preexisting file."""
    lock=path.with_name(path.name+'.fonesi-lock')
    marker=b'FONESI-PROJECT-LOCK-v1\n'
    flags=os.O_RDWR|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)
    created=False
    try:
        fd=os.open(lock,flags|os.O_CREAT|os.O_EXCL,0o600)
        created=True
    except FileExistsError:
        info=lock.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400):
            raise StorageError('Refusing project lock symlink/reparse point')
        if not stat.S_ISREG(info.st_mode):raise StorageError('Project lock must be a regular file')
        fd=os.open(lock,flags)
    try:
        if created:
            os.write(fd,marker);os.fsync(fd)
        opened=os.fstat(fd);named=lock.lstat()
        if (not stat.S_ISREG(opened.st_mode) or stat.S_ISLNK(named.st_mode) or
                getattr(named,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400) or
                (opened.st_dev,opened.st_ino)!=(named.st_dev,named.st_ino)):
            raise StorageError('Project lock identity changed')
        os.lseek(fd,0,os.SEEK_SET)
        if opened.st_size!=len(marker) or os.read(fd,len(marker)+1)!=marker:
            raise StorageError('Existing lock file is foreign or still initializing; left untouched')
        os.lseek(fd,0,os.SEEK_SET)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except (BlockingIOError,PermissionError) as exc:
            # Only acquisition failure proves the writer body never ran.
            raise ConflictError('Project save is already active or permission denied') from exc
        yield
    finally:
        os.close(fd) # OS releases lock; never unlink another opener's lock inode

def _sync_dir(path):
    if os.name=='nt':return # Windows file flush/replace separately target-tested; no POSIX-dir guarantee claimed
    fd=os.open(path,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)

def save_project_file(path:Path|str,project:Project,*,expected_digest:str|None=None,fault:Callable[[str],None]|None=None)->str:
    """New file is no-overwrite. Existing app project requires identity+digest and gets a backup.

    Replacement is atomic for cooperating app writers. External writers that ignore
    advisory locking are not promised compare-and-swap filesystem semantics.
    """
    path=Path(path).absolute();path.parent.mkdir(parents=True,exist_ok=True);fault=fault or (lambda _:None)
    if path.is_symlink():raise StorageError('Refusing project symlink target')
    data=Project.parse(project.to_json()).to_json().encode('utf-8');result=sha256(data).hexdigest()
    with _project_lock(path):
        previous=None
        if path.exists():
            previous=_read_project(path)
            if expected_digest is None or sha256(previous).hexdigest()!=expected_digest:raise ConflictError('Existing project differs or overwrite not explicitly authorized')
            prior=Project.parse(previous)
            if prior.id!=project.id:raise ConflictError('Target belongs to another project')
            if prior.library is not None and project.library is None:raise ConflictError('Cannot downgrade v2 project library')
        elif expected_digest is not None:raise ConflictError('Expected previous project is missing')
        staging=path.with_name('.'+path.name+'.staging-'+uuid.uuid4().hex)
        try:
            with staging.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            Project.parse(_read_project(staging));fault('after_staging')
            if previous is None:
                os.link(staging,path) # atomic no-replace; fail closed on unsupported filesystem
                fault('after_publish')
            else:
                if not path.exists() or path.is_symlink() or sha256(_read_project(path)).hexdigest()!=expected_digest:raise ConflictError('Project changed during save')
                backup=path.with_name(path.name+'.backup-'+uuid.uuid4().hex)
                with backup.open('xb') as f:f.write(previous);f.flush();os.fsync(f.fileno())
                fault('after_backup')
                os.replace(staging,path) # only existing app project explicitly matched above
                fault('after_publish')
            _sync_dir(path.parent)
            if sha256(_read_project(path)).hexdigest()!=result:raise StorageError('Project readback mismatch')
            return result
        finally:
            if staging.exists():staging.unlink() # unique owned staging only

def load_project_file(path:Path|str)->tuple[Project,str]:
    data=_read_project(Path(path))
    return Project.parse(data),sha256(data).hexdigest()
