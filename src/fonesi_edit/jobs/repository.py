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
    def __init__(self, path: Path | str, *, clock=time.time, migration_fault=lambda stage:None, adopt_unmarked=False):
        self.clock = clock
        path = Path(path).resolve()
        self.path=path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = None
        self._file_anchor=None
        try:
            flags=os.O_RDONLY|getattr(os,"O_BINARY",0)|getattr(os,"O_NOFOLLOW",0)
            try:self._file_anchor=os.open(path,flags|os.O_CREAT|os.O_EXCL,0o600)
            except FileExistsError:
                info=path.lstat()
                if not stat.S_ISREG(info.st_mode) or getattr(info,"st_file_attributes",0)&0x400:
                    raise JobConflict("Jobs database must be a regular non-reparse file")
                self._file_anchor=os.open(path,flags)
            info=os.fstat(self._file_anchor)
            self._database_identity=(info.st_dev,info.st_ino)
            self.guard_database()
            self.db, version = open_versioned(path,owned=lambda:owns_database(path,APPLICATION_ID,KNOWN_LINEAGE_HASHES))
            self.guard_database() # SQLite opened while original file anchor stayed live
            self.db.row_factory = sqlite3.Row
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
            self.db.execute('PRAGMA journal_mode=WAL')
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute('PRAGMA foreign_keys=ON')
            self.db.execute('PRAGMA busy_timeout=5000')
            register_database(path,APPLICATION_ID,V2_HASH,legacy_hashes=KNOWN_LINEAGE_HASHES)
        except BaseException:
            self.close()
            raise

    @property
    def database_identity(self):return self._database_identity

    def guard_database(self):
        if self._file_anchor is None:raise JobConflict('Jobs database anchor is closed')
        opened=os.fstat(self._file_anchor);named=self.path.lstat()
        if (not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(named.st_mode) or
            getattr(named,'st_file_attributes',0)&0x400 or
            not opened.st_ino or (opened.st_dev,opened.st_ino)!=self._database_identity or
            (named.st_dev,named.st_ino)!=self._database_identity):
            raise JobConflict('Jobs database physical identity changed')

    def duplicate_database_anchor(self):
        self.guard_database()
        return os.dup(self._file_anchor)

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
            self.db.execute('COMMIT')
            return job
        except BaseException:
            self.db.execute('ROLLBACK')
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
