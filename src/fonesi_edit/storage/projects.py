"""Versioned SQLite projects and recoverable explicit project-file saves."""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
import json,os,sqlite3,time,uuid,stat
from pathlib import Path
from typing import Callable
from ..fileio import read_bounded
from ..domain.composition import CompositionPlan,canonical,PlanError

SCHEMA_VERSION=1
APPLICATION_ID=1178946130
PROJECTS_SQL='CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, document TEXT NOT NULL, version INTEGER NOT NULL CHECK(version>0), updated_at REAL NOT NULL)'
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

    def __post_init__(self):
        try:uuid.UUID(self.id)
        except (ValueError,TypeError,AttributeError) as exc:raise StorageError('Invalid project UUID') from exc
        if not isinstance(self.name,str) or not self.name.strip() or len(self.name)>200:
            raise StorageError('Project name must contain1..200characters')
        if not isinstance(self.plan,CompositionPlan):raise StorageError('Validated CompositionPlan required')

    def to_json(self):
        return canonical({'format':'fonesi-edit-project','schema_version':1,'project_id':self.id,'name':self.name,'composition':self.plan.to_dict()})

    @classmethod
    def parse(cls,text):
        def pairs(values):
            out={}
            for k,v in values:
                if k in out:raise StorageError('Duplicate project JSON key')
                out[k]=v
            return out
        try:
            if len(text.encode() if isinstance(text,str) else text)>33*1024*1024:raise StorageError('Project file too large')
            raw=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(StorageError('Nonfinite JSON')))
            if not isinstance(raw,dict) or set(raw)!={'format','schema_version','project_id','name','composition'}:raise StorageError('Invalid/unknown project envelope fields')
            if type(raw['schema_version']) is not int:raise StorageError('Invalid project schema version')
            if raw['schema_version']>1:raise NewerSchemaError('Newer project schema: original left unchanged')
            if raw['schema_version']!=1 or raw['format']!='fonesi-edit-project':raise StorageError('Unsupported project format/version')
            return cls(raw['project_id'],raw['name'],CompositionPlan.parse(raw['composition']))
        except (ValueError,TypeError,UnicodeError) as exc:
            if isinstance(exc,StorageError):raise
            raise StorageError(str(exc)) from exc

@dataclass(frozen=True)
class StoredProject:
    project: Project
    version: int # repository CAS token; distinct from composition revision

class ProjectStore:
    def __init__(self,path:Path|str,*,fault:Callable[[str],None]|None=None):
        self.path=Path(path).resolve();self.path.parent.mkdir(parents=True,exist_ok=True)
        existed=self.path.exists();self._fault=fault or (lambda _:None);self._closed=False
        self.db=sqlite3.connect(self.path,timeout=5,isolation_level=None)
        try:
            version=self.db.execute('PRAGMA user_version').fetchone()[0]
            if version>SCHEMA_VERSION:raise NewerSchemaError(f'Database schema{version} newer than{SCHEMA_VERSION}; no write performed')
            application_id=self.db.execute('PRAGMA application_id').fetchone()[0]
            if version==SCHEMA_VERSION and application_id!=APPLICATION_ID:raise StorageError('Foreign database identity; left unchanged')
            tables=self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            if version==0 and tables:raise StorageError('Unrecognized unversioned database; refusing to migrate unrelated tables')
            if version==SCHEMA_VERSION:
                actual=self.db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
                normalize=lambda value:''.join(value.lower().split())
                if len(actual)!=1 or actual[0][0]!='projects' or normalize(actual[0][1])!=normalize(PROJECTS_SQL):
                    raise StorageError('Corrupt or unexpected project schema; left unchanged')
            self.db.execute('PRAGMA foreign_keys=ON');self.db.execute('PRAGMA busy_timeout=5000')
            if version<SCHEMA_VERSION:
                if existed:self._backup()
                self._fault('before_migration')
                with self.transaction():
                    self.db.execute(PROJECTS_SQL)
                    self._fault('after_schema_creation')
                    self.db.execute(f'PRAGMA application_id={APPLICATION_ID}')
                    self.db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
            self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA synchronous=FULL')
        except Exception:
            self.db.close();self._closed=True;raise

    def _backup(self):
        target=self.path.with_name(self.path.name+'.backup-'+uuid.uuid4().hex)
        # SQLite backup API makes a consistent snapshot, not a live WAL-file copy.
        dest=sqlite3.connect(target)
        try:
            self.db.backup(dest)
            if dest.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise StorageError('Migration backup validation failed')
        finally:dest.close()
        with target.open('rb') as f:os.fsync(f.fileno())
        self._fault('after_backup')
        return target

    @contextmanager
    def transaction(self):
        if self._closed:raise StorageError('Store is closed')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK');raise

    def save(self,project:Project,*,expected_version:int|None=None)->StoredProject:
        # Revalidate at persistence boundary even when caller supplied typed object.
        document=Project.parse(project.to_json()).to_json()
        if expected_version is not None and (type(expected_version) is not int or expected_version<1):raise StorageError('Invalid expected version')
        with self.transaction():
            current=self.db.execute('SELECT version FROM projects WHERE id=?',(project.id,)).fetchone()
            if current is None:
                if expected_version is not None:raise ConflictError('Project was removed or never existed')
                version=1
                self.db.execute('INSERT INTO projects VALUES (?,?,?,?,?)',(project.id,project.name,document,version,time.time()))
            else:
                if current[0]!=expected_version:raise ConflictError('Project changed; reload before saving')
                version=current[0]+1
                self.db.execute('UPDATE projects SET name=?,document=?,version=?,updated_at=? WHERE id=? AND version=?',(project.name,document,version,time.time(),project.id,expected_version))
            self._fault('before_project_commit')
        return StoredProject(project,version)

    def load(self,project_id:str)->StoredProject:
        if self._closed:raise StorageError('Store is closed')
        row=self.db.execute('SELECT document,version FROM projects WHERE id=?',(project_id,)).fetchone()
        if row is None:raise KeyError(project_id)
        return StoredProject(Project.parse(row[0]),row[1])

    def list_projects(self)->tuple[StoredProject,...]:
        if self._closed:raise StorageError('Store is closed')
        return tuple(StoredProject(Project.parse(row[0]),row[1]) for row in self.db.execute('SELECT document,version FROM projects ORDER BY updated_at DESC,id'))

    def close(self):
        if not self._closed:self.db.close();self._closed=True
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
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    except (BlockingIOError,PermissionError) as exc:
        raise ConflictError('Project save is already active or permission denied') from exc
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
            if Project.parse(previous).id!=project.id:raise ConflictError('Target belongs to another project')
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
