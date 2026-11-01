"""SQLite job admission and lease CAS; no output-success shortcut exists."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import sqlite3
import json
import os
import stat
import time
import uuid
from fonesi_edit.domain.composition import CompositionPlan, canonical
from fonesi_edit.storage.sqlite_open import open_versioned
from fonesi_edit.storage.db_ownership import owns_database,register_database,receipt_path

from .output_manifest import RequiredOutputs
from fonesi_edit.artifacts.filesystem import PublicationError
from .schema import JOBS_SQL, APPLICATION_ID, VERSION, V2_HASH, KNOWN_LINEAGE_HASHES, matches, migrate


class JobConflict(RuntimeError):
    pass

@dataclass(frozen=True)
class Job:
    id: str
    request_key: str
    snapshot_json: str
    snapshot_hash: str
    state: str
    version: int
    attempt: int
    lease_token: str | None
    lease_deadline: float | None
    cancel_requested: bool

class JobRepository:
    def __init__(self, path: Path | str, *, clock=time.time, migration_fault=lambda stage:None, adopt_unmarked=False, existing_only=False):
        if type(existing_only) is not bool or type(adopt_unmarked) is not bool or (existing_only and adopt_unmarked):raise JobConflict('Invalid existing-store open policy')
        self._existing_only=existing_only
        self.clock = clock
        path = Path(path).absolute()
        self.path=path
        if not existing_only:path.parent.mkdir(parents=True, exist_ok=True)
        self.db = None
        self._file_anchor=None;self._database_revoked=False
        created=False
        try:
            flags=os.O_RDONLY|getattr(os,"O_BINARY",0)|getattr(os,"O_NOFOLLOW",0)
            try:
                if existing_only:raise FileExistsError
                self._file_anchor=os.open(path,flags|os.O_CREAT|os.O_EXCL,0o600);created=True
            except FileExistsError:
                info=path.lstat()
                if not stat.S_ISREG(info.st_mode) or getattr(info,"st_file_attributes",0)&0x400:
                    raise JobConflict("Jobs database must be a regular non-reparse file")
                self._file_anchor=os.open(path,flags)
            info=os.fstat(self._file_anchor)
            self._database_identity=(info.st_dev,info.st_ino)
            self.guard_database()
            marker=receipt_path(path)
            if ((not created and not adopt_unmarked) or marker.exists() or marker.is_symlink()) and not owns_database(path,APPLICATION_ID,KNOWN_LINEAGE_HASHES):
                raise JobConflict('Unmarked/foreign existing jobs schema; explicit adoption required before SQLite')
            options={'connect':self._connect_existing}
            self.db, version = open_versioned(path,**options,owned=lambda:owns_database(path,APPLICATION_ID,KNOWN_LINEAGE_HASHES))
            self.guard_database() # SQLite opened while original file anchor stayed live
            self.db.row_factory = sqlite3.Row
            if existing_only and version!=VERSION:raise JobConflict('Queue commands require existing current schema; no migration')
            application_id = self.db.execute('PRAGMA application_id').fetchone()[0]
            if version not in (0,1,VERSION):
                raise JobConflict('Unsupported jobs schema; left untouched')
            if (version and application_id != APPLICATION_ID) or (version==0 and application_id not in (0,APPLICATION_ID)):
                raise JobConflict('Database is not a Fonesi jobs store; left untouched')
            if not matches(self.db,version):
                raise JobConflict('Corrupt or unexpected jobs schema; left unchanged')
            marker=receipt_path(path)
            if marker.exists() or marker.is_symlink():
                if not owns_database(path,APPLICATION_ID,KNOWN_LINEAGE_HASHES):
                    raise JobConflict('Foreign/invalid existing ownership receipt; database left untouched')
            elif version and adopt_unmarked is not True:
                raise JobConflict('Unmarked existing jobs database; explicit adoption required before mutation')
            self.db.execute('PRAGMA foreign_keys=ON')
            self.db.execute('PRAGMA busy_timeout=5000')
            if version<VERSION:
                migrate(self.db,path,version,fault=migration_fault)
            if not matches(self.db,VERSION):
                raise JobConflict('Jobs migration schema verification failed')
            self.guard_database()
            if existing_only:
                if self.db.execute('PRAGMA journal_mode').fetchone()[0]!='wal':raise JobConflict('Existing queue WAL mode required')
            else:self.db.execute('PRAGMA journal_mode=WAL')
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute('PRAGMA foreign_keys=ON')
            self.db.execute('PRAGMA busy_timeout=5000')
            self.guard_database()
            if existing_only:
                if not owns_database(path,APPLICATION_ID,KNOWN_LINEAGE_HASHES):raise JobConflict('Existing queue ownership changed')
            else:register_database(path,APPLICATION_ID,V2_HASH,legacy_hashes=KNOWN_LINEAGE_HASHES)
        except BaseException:
            self.close()
            raise

    @staticmethod
    def _connect_existing(path,**kwargs):
        return sqlite3.connect(Path(path).as_uri()+'?mode=rw',uri=True,**kwargs)

    @property
    def database_identity(self):return self._database_identity

    def guard_database(self):
        if self._file_anchor is None or self._database_revoked:
            raise JobConflict('Jobs database anchor closed or continuity revoked')
        try:
            opened=os.fstat(self._file_anchor);named=self.path.lstat()
            if (not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(named.st_mode) or
                getattr(named,'st_file_attributes',0)&0x400 or
                not opened.st_ino or (opened.st_dev,opened.st_ino)!=self._database_identity or
                (named.st_dev,named.st_ino)!=self._database_identity):
                raise JobConflict('Jobs database physical identity changed')
        except BaseException:
            self._database_revoked=True
            raise

    def duplicate_database_anchor(self):
        self.guard_database()
        return os.dup(self._file_anchor)

    def _prepare_coordinator_connection(self, *, windows=None):
        """Read-only preflight before epoch BEGIN; never replay a transaction.

        A peer's Windows exit can invalidate the WAL shared-memory view of an
        already-open idle connection. Exact1546 alone permits closing/reopening
        that owned connection through the existing bounded startup-read helper.
        """
        self.guard_database()
        if self.db is None or self.db.in_transaction:
            raise JobConflict('Coordinator setup requires an idle database connection')
        windows=os.name=='nt' if windows is None else windows
        try:
            self.db.execute('SELECT epoch FROM coordinator_epochs ORDER BY epoch DESC LIMIT 1').fetchall()
            return
        except sqlite3.OperationalError as exc:
            if (not windows or getattr(exc,'sqlite_errorcode',None)!=1546 or self.db.in_transaction or
                not owns_database(self.path,APPLICATION_ID,KNOWN_LINEAGE_HASHES)):
                raise
        # No BEGIN/INSERT/COMMIT has run in this setup attempt. Keep original DB
        # incarnation pinned while retiring only this failed idle SQLite handle.
        self.guard_database()
        self.db.close();self.db=None
        connection=None
        def owned():
            self.guard_database()
            return owns_database(self.path,APPLICATION_ID,KNOWN_LINEAGE_HASHES)
        try:
            options={'connect':self._connect_existing}
            connection,version=open_versioned(self.path,windows=windows,owned=owned,**options)
            self.guard_database()
            if (version!=VERSION or connection.execute('PRAGMA application_id').fetchone()[0]!=APPLICATION_ID or
                not matches(connection,VERSION) or connection.execute('PRAGMA journal_mode').fetchone()[0]!='wal'):
                raise JobConflict('Reopened coordinator database identity/schema/mode changed')
            connection.row_factory=sqlite3.Row
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA synchronous=FULL')
            connection.execute('PRAGMA busy_timeout=5000')
            connection.execute('SELECT epoch FROM coordinator_epochs ORDER BY epoch DESC LIMIT 1').fetchall()
            self.guard_database()
            self.db=connection
        except BaseException:
            if connection is not None:connection.close()
            raise

    def close(self):
        try:
            if self.db is not None:self.db.close()
        finally:
            self.db=None
            if self._file_anchor is not None:os.close(self._file_anchor)
            self._file_anchor=None

    def _job(self, row):
        if row is None:
            raise KeyError('Job not found')
        data = dict(row)
        data['cancel_requested'] = bool(data['cancel_requested'])
        return Job(**data)

    def get(self, job_id):
        self.guard_database()
        return self._job(self.db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone())

    def submit(self, request_key: str, plan: CompositionPlan, seed: int, *, outputs: RequiredOutputs | None = None) -> Job:
        self.guard_database()
        if not isinstance(request_key, str) or not 1 <= len(request_key) <= 200:
            raise ValueError('Bounded nonempty request key required')
        if type(seed) is not int or not 0 <= seed < 2**64:
            raise ValueError('Unsigned 64-bit seed required')
        # Deliberately closed schema: no arbitrary config/credential dictionaries.
        if outputs is not None and type(outputs) is not RequiredOutputs:
            raise ValueError('Closed required-output manifest required')
        payload={'version': 1, 'composition': plan.to_dict(), 'seed': seed}
        if outputs is not None:
            outputs.validate_composition(plan.to_dict())
            payload.update(version=2,outputs=outputs.to_dict())
        snapshot = canonical(payload)
        digest = sha256(snapshot.encode()).hexdigest()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row = self.db.execute('SELECT * FROM jobs WHERE request_key=?', (request_key,)).fetchone()
            if row is not None:
                job = self._job(row)
                if job.snapshot_hash != digest:
                    raise JobConflict('Request key reused with different snapshot')
            else:
                job_id = str(uuid.uuid4())
                self.db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,1,0,NULL,NULL,0)',
                                (job_id, request_key, snapshot, digest, 'pending'))
                job = self.get(job_id)
            self.guard_database()
            self.db.execute('COMMIT')
            return job
        except BaseException:
            if self.db.in_transaction:self.db.execute('ROLLBACK')
            raise

    def publication_manifest(self, job: Job) -> RequiredOutputs:
        """Read immutable intent; legacy/incomplete jobs never acquire publish roles."""
        if self.get(job.id)!=job:raise JobConflict('Stale or modified job record')
        try:
            if len(job.snapshot_json.encode())>32*1024*1024 or sha256(job.snapshot_json.encode()).hexdigest()!=job.snapshot_hash:
                raise ValueError('Snapshot hash/size invalid')
            data=json.loads(job.snapshot_json)
            if (type(data) is not dict or set(data)!={'version','composition','seed','outputs'} or
                type(data['version']) is not int or data['version']!=2 or canonical(data)!=job.snapshot_json):
                raise ValueError('Snapshot lacks canonical required-output intent')
            result=RequiredOutputs.from_dict(data['outputs'])
            result.validate_composition(data['composition'])
            if not all(item.publication_ready for item in result.items):raise ValueError('Incomplete output validation policy')
            return result
        except (ValueError,TypeError,KeyError,PublicationError) as exc:
            raise JobConflict('Publication requires intact complete immutable output policy') from exc

    def _update(self, job: Job, state: str, *, lease=None, deadline=None, attempt=None, cancel=False):
        if self.get(job.id) != job:
            raise JobConflict('Stale or modified job record')
        cursor = self.db.execute('''UPDATE jobs SET state=?, version=version+1,
            lease_token=?, lease_deadline=?, attempt=?, cancel_requested=?
            WHERE id=? AND version=? AND state=? AND lease_token IS ?''',
            (state, lease, deadline, job.attempt if attempt is None else attempt,
             int(cancel), job.id, job.version, job.state, job.lease_token))
        if cursor.rowcount != 1:
            raise JobConflict('Stale job version/state')
        return self.get(job.id)

    def claim(self, job: Job, *, lease_seconds=30):
        if job.state != 'pending' or job.cancel_requested:
            raise JobConflict('Only pending noncanceled jobs can be claimed')
        if not 0 < lease_seconds <= 300:
            raise ValueError('Lease must be in (0,300] seconds')
        return self._update(job, 'running', lease=str(uuid.uuid4()),
                            deadline=self.clock()+lease_seconds, attempt=job.attempt+1)

    def pause(self, job: Job):
        if job.state != 'pending':
            raise JobConflict('Only pending jobs can be held')
        return self._update(job, 'paused')

    def resume(self, job: Job):
        if job.state not in {'paused', 'retry_wait', 'blocked_configuration'}:
            raise JobConflict('Job is not resumable')
        # Caller must perform configuration preflight before resuming blocked jobs.
        return self._update(job, 'pending')

    def request_cancel(self, job: Job):
        if job.state in {'running', 'validating'}:
            return self._update(job, job.state, lease=job.lease_token,
                                deadline=job.lease_deadline, cancel=True)
        if job.state in {'pending', 'paused', 'retry_wait', 'blocked_configuration'}:
            return self._update(job, 'canceled', cancel=True)
        raise JobConflict('Cancellation unavailable after publication claim or terminal state')

    def worker_transition(self, job: Job, token: str, target: str):
        if token != job.lease_token or job.lease_deadline is None or self.clock() >= job.lease_deadline:
            raise JobConflict('Stale or expired worker lease')
        edges = {'running': {'validating', 'retry_wait', 'blocked_configuration', 'failed', 'canceled'},
                 'validating': {'failed', 'canceled'}}
        if target not in edges.get(job.state, set()):
            raise JobConflict('Illegal worker transition; success/publication requires artifact protocol')
        if job.cancel_requested and target != 'canceled':
            raise JobConflict('Cancellation already requested')
        if target == 'canceled' and not job.cancel_requested:
            raise JobConflict('Cancellation must be requested first')
        active = target == 'validating'
        return self._update(job, target, lease=token if active else None,
                            deadline=job.lease_deadline if active else None, cancel=job.cancel_requested)

    def heartbeat(self, job: Job, token: str, *, lease_seconds=30):
        if (job.state not in {'running', 'validating'} or token != job.lease_token or
                job.lease_deadline is None or self.clock() >= job.lease_deadline):
            raise JobConflict('Heartbeat from stale lease')
        if not 0 < lease_seconds <= 300:
            raise ValueError('Invalid lease duration')
        return self._update(job, job.state, lease=token, deadline=self.clock()+lease_seconds,
                            cancel=job.cancel_requested)

    def expired(self):
        self.guard_database()
        # Discovery only. Recovery must inspect owned process/publication before action.
        return tuple(self._job(row) for row in self.db.execute(
            "SELECT * FROM jobs WHERE state IN ('running','validating') AND lease_deadline<=?",
            (self.clock(),)))
