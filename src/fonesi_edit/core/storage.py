"""SQLite is authoritative for jobs, reservations and scoped caches; projects remain portable."""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import json
import shutil
import sqlite3
import time
from .model import Project, canonical, digest, uid
from .paths import atomic_write

SCHEMA = 1
TERMINAL = {'succeeded','succeeded_with_warnings','failed','canceled','skipped'}


def save_project(project: Project, path: Path, backup=True):
    project.validate()
    if backup and path.exists():
        shutil.copy2(path, path.with_suffix(path.suffix+'.bak'))
    atomic_write(path, canonical(project.to_dict()))


def load_project(path: Path) -> Project:
    return Project.from_dict(json.loads(Path(path).read_text('utf8')))


class Store:
    def __init__(self, path: Path):
        self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    @contextmanager
    def connection(self):
        db=sqlite3.connect(self.path, timeout=20)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback(); raise
        finally:
            db.close()

    def migrate(self):
        with self.connection() as db:
            version=db.execute('PRAGMA user_version').fetchone()[0]
            if version>SCHEMA:
                raise ValueError('Database is newer than this app; no changes made')
            if version == SCHEMA: return
            if self.path.stat().st_size:
                with sqlite3.connect(self.path.with_suffix(f'.v{version}.bak')) as backup:
                    db.backup(backup)
            db.executescript('''
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS jobs(
                id TEXT PRIMARY KEY, kind TEXT NOT NULL, snapshot TEXT NOT NULL, snapshot_hash TEXT NOT NULL,
                dedupe_key TEXT UNIQUE, state TEXT NOT NULL, stage TEXT NOT NULL DEFAULT '', priority INTEGER NOT NULL DEFAULT 0,
                progress REAL, progress_text TEXT NOT NULL DEFAULT '', attempt INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3, owner TEXT, lease_until REAL, cancel_requested INTEGER DEFAULT 0,
                created REAL NOT NULL, updated REAL NOT NULL, error TEXT, result TEXT, available_at REAL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS dependencies(job_id TEXT REFERENCES jobs(id), depends_on TEXT REFERENCES jobs(id),
                allow_failure INTEGER DEFAULT 0, PRIMARY KEY(job_id, depends_on));
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, job_id TEXT, time REAL, state TEXT, detail TEXT);
            CREATE TABLE IF NOT EXISTS objects(namespace TEXT, id TEXT, payload TEXT, PRIMARY KEY(namespace,id));
            CREATE TABLE IF NOT EXISTS cache(scope TEXT, key TEXT, payload TEXT, updated REAL, PRIMARY KEY(scope,key));
            CREATE TABLE IF NOT EXISTS matrix_history(project TEXT, combination TEXT, state TEXT, job_id TEXT, artifact TEXT,
                PRIMARY KEY(project,combination));
            PRAGMA user_version=1;
            COMMIT;
            ''')
            db.execute('PRAGMA journal_mode=WAL')

    def enqueue(self, kind: str, snapshot: dict, *, dedupe_key=None, priority=0, dependencies=()) -> str:
        data=canonical(snapshot); job_id=uid(); now=time.time()
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if dedupe_key:
                old=db.execute('SELECT id FROM jobs WHERE dedupe_key=?',(dedupe_key,)).fetchone()
                if old: return old['id']
            db.execute('INSERT INTO jobs(id,kind,snapshot,snapshot_hash,dedupe_key,state,priority,created,updated) VALUES(?,?,?,?,?,?,?,?,?)',
                       (job_id,kind,data,digest(snapshot),dedupe_key,'pending',priority,now,now))
            for dep, allow in dependencies:
                db.execute('INSERT INTO dependencies VALUES(?,?,?)',(job_id,dep,int(allow)))
        return job_id

    def get(self, job_id):
        with self.connection() as db:
            row=db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
            if not row: raise KeyError(job_id)
            return dict(row)

    def jobs(self):
        with self.connection() as db:
            return [dict(r) for r in db.execute('SELECT * FROM jobs ORDER BY priority DESC,created')]

    def claim(self, owner: str, kinds: list[str] | None = None, lease=30):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            rows=db.execute("SELECT * FROM jobs WHERE state IN ('pending','retry_wait') AND available_at<=? AND cancel_requested=0 ORDER BY priority DESC,created",(time.time(),))
            for row in rows:
                if kinds and row['kind'] not in kinds: continue
                deps=db.execute('SELECT j.state,d.allow_failure FROM dependencies d JOIN jobs j ON j.id=d.depends_on WHERE d.job_id=?',(row['id'],)).fetchall()
                if any(d['state'] not in TERMINAL or (not d['allow_failure'] and d['state'] not in {'succeeded','succeeded_with_warnings'}) for d in deps): continue
                now=time.time()
                db.execute("UPDATE jobs SET state='running',owner=?,lease_until=?,attempt=attempt+1,updated=? WHERE id=?",(owner,now+lease,now,row['id']))
                return dict(db.execute('SELECT * FROM jobs WHERE id=?',(row['id'],)).fetchone())
        return None

    def update_progress(self, job_id, owner, stage, value, message=''):
        if value is not None and not 0<=value<=1: raise ValueError('Progress outside 0..1')
        with self.connection() as db:
            db.execute('UPDATE jobs SET stage=?,progress=?,progress_text=?,updated=? WHERE id=? AND owner=? AND state IN (\'running\',\'validating\')',
                       (stage,value,message,time.time(),job_id,owner))

    def heartbeat(self, job_id, owner, lease=30):
        with self.connection() as db:
            db.execute("UPDATE jobs SET lease_until=? WHERE id=? AND owner=? AND state IN ('running','validating')",(time.time()+lease,job_id,owner))

    def finish(self, job_id, owner, state, *, result=None, error=None):
        if state not in TERMINAL | {'blocked_configuration','uncertain'}: raise ValueError('Invalid finish state')
        if state.startswith('succeeded') and not (result and result.get('validated')):
            raise ValueError('Success requires validation evidence')
        with self.connection() as db:
            cursor=db.execute("UPDATE jobs SET state=?,result=?,error=?,progress=?,updated=?,owner=NULL,lease_until=NULL WHERE id=? AND owner=? AND state IN ('running','validating')",
                (state, canonical(result) if result else None,error,1 if state.startswith('succeeded') else None,time.time(),job_id,owner))
            if cursor.rowcount != 1: raise RuntimeError('Lease lost or invalid job transition')
            db.execute('INSERT INTO events(job_id,time,state,detail) VALUES(?,?,?,?)',(job_id,time.time(),state,error or ''))

    def cancel(self, job_id):
        with self.connection() as db:
            db.execute("UPDATE jobs SET cancel_requested=1,state=CASE WHEN state IN ('pending','retry_wait','blocked_configuration') THEN 'canceled' ELSE state END WHERE id=? AND state NOT IN ('succeeded','succeeded_with_warnings','failed','canceled','skipped')",(job_id,))

    def retry(self, job_id):
        with self.connection() as db:
            row=db.execute('SELECT state,attempt,max_attempts FROM jobs WHERE id=?',(job_id,)).fetchone()
            if not row or row['state'] not in {'failed','canceled','blocked_configuration','interrupted'}: raise ValueError('Job cannot be retried; uncertain provider outcomes need reconciliation')
            if row['attempt']>=row['max_attempts']: raise ValueError('Retry limit reached')
            db.execute("UPDATE jobs SET state='pending',cancel_requested=0,error=NULL,progress=NULL,owner=NULL,lease_until=NULL WHERE id=?",(job_id,))

    def recover(self, now=None):
        with self.connection() as db:
            rows=db.execute("SELECT id FROM jobs WHERE state IN ('running','validating') AND lease_until<?",(now or time.time(),)).fetchall()
            db.execute("UPDATE jobs SET state='interrupted',owner=NULL,lease_until=NULL,error='Worker lease expired; inspect artifacts then retry stage' WHERE state IN ('running','validating') AND lease_until<?",(now or time.time(),))
            return [r['id'] for r in rows]

    def put(self, namespace, object_id, payload):
        with self.connection() as db:
            db.execute('INSERT INTO objects VALUES(?,?,?) ON CONFLICT(namespace,id) DO UPDATE SET payload=excluded.payload',(namespace,object_id,canonical(payload)))

    def objects(self, namespace):
        with self.connection() as db:
            return {r['id']:json.loads(r['payload']) for r in db.execute('SELECT * FROM objects WHERE namespace=?',(namespace,))}

    def cache_get(self, scope, key):
        with self.connection() as db:
            r=db.execute('SELECT payload FROM cache WHERE scope=? AND key=?',(scope,key)).fetchone()
            return json.loads(r[0]) if r else None

    def cache_put(self, scope,key,payload):
        with self.connection() as db:
            db.execute('INSERT INTO cache VALUES(?,?,?,?) ON CONFLICT(scope,key) DO UPDATE SET payload=excluded.payload,updated=excluded.updated',(scope,key,canonical(payload),time.time()))
