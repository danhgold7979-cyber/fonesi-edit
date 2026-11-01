"""SQLite job admission and lease CAS; no output-success shortcut exists."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import sqlite3
import time
import uuid
from fonesi_edit.domain.composition import CompositionPlan, canonical

JOBS_SQL='CREATE TABLE jobs(\n                        id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,\n                        snapshot_json TEXT NOT NULL, snapshot_hash TEXT NOT NULL,\n                        state TEXT NOT NULL, version INTEGER NOT NULL,\n                        attempt INTEGER NOT NULL, lease_token TEXT,\n                        lease_deadline REAL, cancel_requested INTEGER NOT NULL)'

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
    def __init__(self, path: Path | str, *, clock=time.time):
        self.clock = clock
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, isolation_level=None, timeout=5)
        self.db.row_factory = sqlite3.Row
        try:
            version = self.db.execute('PRAGMA user_version').fetchone()[0]
            application_id = self.db.execute('PRAGMA application_id').fetchone()[0]
            if version == 1 and application_id != 1178946122:
                raise JobConflict('Database is not a Fonesi jobs store; left untouched')
            if version not in (0, 1):
                raise JobConflict('Unsupported jobs schema; left untouched')
            if version == 0:
                if self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                    raise JobConflict('Refusing unrelated database')
                self.db.executescript('''BEGIN IMMEDIATE;
                    CREATE TABLE jobs(
                        id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
                        snapshot_json TEXT NOT NULL, snapshot_hash TEXT NOT NULL,
                        state TEXT NOT NULL, version INTEGER NOT NULL,
                        attempt INTEGER NOT NULL, lease_token TEXT,
                        lease_deadline REAL, cancel_requested INTEGER NOT NULL);
                    PRAGMA application_id=1178946122;
                    PRAGMA user_version=1;
                    COMMIT;''')
            actual=self.db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            normalize=lambda value:''.join(value.lower().split())
            if len(actual)!=1 or actual[0]['name']!='jobs' or normalize(actual[0]['sql'])!=normalize(JOBS_SQL):
                raise JobConflict('Corrupt or unexpected jobs schema; left unchanged')
            self.db.execute('PRAGMA journal_mode=WAL')
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute('PRAGMA foreign_keys=ON')
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def _job(self, row):
        if row is None:
            raise KeyError('Job not found')
        data = dict(row)
        data['cancel_requested'] = bool(data['cancel_requested'])
        return Job(**data)

    def get(self, job_id):
        return self._job(self.db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone())

    def submit(self, request_key: str, plan: CompositionPlan, seed: int) -> Job:
        if not isinstance(request_key, str) or not 1 <= len(request_key) <= 200:
            raise ValueError('Bounded nonempty request key required')
        if type(seed) is not int or not 0 <= seed < 2**64:
            raise ValueError('Unsigned 64-bit seed required')
        # Deliberately closed schema: no arbitrary config/credential dictionaries.
        snapshot = canonical({'version': 1, 'composition': plan.to_dict(), 'seed': seed})
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
        # Discovery only. Recovery must inspect owned process/publication before action.
        return tuple(self._job(row) for row in self.db.execute(
            "SELECT * FROM jobs WHERE state IN ('running','validating') AND lease_deadline<=?",
            (self.clock(),)))
