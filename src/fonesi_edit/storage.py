"""Transactional local state. Connections are never shared across worker processes."""
from contextlib import closing, contextmanager
from pathlib import Path
import json
import os
import sqlite3
import tempfile
import time

from .domain import canonical, checked_payload, identifier

TERMINAL = {"succeeded", "failed", "canceled"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,name TEXT NOT NULL,data TEXT NOT NULL,updated REAL NOT NULL);
CREATE TABLE IF NOT EXISTS presets(id TEXT PRIMARY KEY,name TEXT NOT NULL,data TEXT NOT NULL,updated REAL NOT NULL);
CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,kind TEXT NOT NULL,state TEXT NOT NULL,payload TEXT NOT NULL,
 result TEXT,error TEXT,progress REAL NOT NULL DEFAULT 0,priority INTEGER NOT NULL DEFAULT 0,
 attempts INTEGER NOT NULL DEFAULT 0,cancel_requested INTEGER NOT NULL DEFAULT 0,
 created REAL NOT NULL,updated REAL NOT NULL,heartbeat REAL,depends_on TEXT NOT NULL DEFAULT '[]');
CREATE INDEX IF NOT EXISTS jobs_pending ON jobs(state,priority,created);
CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY,label TEXT NOT NULL,path TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS bindings(id TEXT PRIMARY KEY,profile_id TEXT NOT NULL,platform TEXT NOT NULL,
 identity TEXT,status TEXT NOT NULL DEFAULT 'unverified',checked REAL,UNIQUE(profile_id,platform));
CREATE TABLE IF NOT EXISTS secrets(key TEXT PRIMARY KEY,value BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS matrix_history(scope TEXT NOT NULL,combination TEXT NOT NULL,state TEXT NOT NULL,
 job_id TEXT,created REAL NOT NULL,PRIMARY KEY(scope,combination));
CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY,data TEXT NOT NULL,updated REAL NOT NULL);
CREATE TABLE IF NOT EXISTS tool_versions(name TEXT NOT NULL,version TEXT NOT NULL,path TEXT NOT NULL,
 hash TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(name,version));
CREATE TABLE IF NOT EXISTS schedules(id TEXT PRIMARY KEY,data TEXT NOT NULL,next_run REAL NOT NULL,last_run REAL);
"""


def _backup_connection(source: sqlite3.Connection, destination: Path) -> Path:
    """Create, validate, then atomically publish a backup without overwriting a file."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".fonesi-backup-", suffix=".tmp", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with closing(sqlite3.connect(temporary)) as target:
            source.backup(target)
            target.commit()

        with closing(sqlite3.connect(temporary)) as check:
            row = check.execute("PRAGMA integrity_check").fetchone()
            if not row or row[0] != "ok":
                detail = row[0] if row else "no result"
                raise sqlite3.DatabaseError(f"Backup integrity_check failed: {detail}")

        with temporary.open("rb+") as stream:
            stream.flush()
            os.fsync(stream.fileno())

        try:
            # Source and destination share a directory/filesystem. Hard-link
            # publication is atomic and fails if the destination appeared meanwhile.
            os.link(temporary, destination)
        except FileExistsError:
            raise
        except OSError as exc:
            raise RuntimeError(
                "Atomic backup publication requires hard-link support on the destination "
                "filesystem; backup was not published"
            ) from exc
        return destination
    finally:
        temporary.unlink(missing_ok=True)


class Store:
    def __init__(self, path: Path):
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version > 2:
                raise ValueError("Database is newer than this application")
            if version==1:
                backup=self.path.with_name(self.path.stem+'.before-v2-'+identifier()[:8]+'.db')
                _backup_connection(conn, backup)
            conn.executescript(SCHEMA)
            columns={r[1] for r in conn.execute('PRAGMA table_info(jobs)')}
            if 'started' not in columns:conn.execute('ALTER TABLE jobs ADD COLUMN started REAL')
            conn.execute("PRAGMA user_version=2")

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=15000")
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def backup(self, destination: Path):
        with self.connect() as source:
            return _backup_connection(source, destination)

    def setting(self, key, default=None):
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_setting(self, key, value):
        data = canonical(checked_payload(value))
        with self.connect() as conn:
            conn.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, data))

    def save_named(self, table, name, data, item_id=None):
        if table not in {"projects", "presets"}:
            raise ValueError("Invalid table")
        item_id = item_id or identifier()
        data = canonical(checked_payload(data))
        with self.connect() as conn:
            conn.execute(f"INSERT INTO {table} VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,data=excluded.data,updated=excluded.updated",
                         (item_id, name, data, time.time()))
        return item_id

    def list_named(self, table):
        if table not in {"projects", "presets"}:
            raise ValueError("Invalid table")
        with self.connect() as conn:
            return [{**dict(row), "data": json.loads(row["data"])} for row in conn.execute(f"SELECT * FROM {table} ORDER BY updated DESC")]

    def submit(self, kind, payload, priority=0, depends_on=()):
        if kind not in {'render','scan','download','translate'}:raise ValueError('Unknown job kind')
        payload={**payload,'_tools':self.setting('tool_paths',{})}
        data = canonical(checked_payload(payload))
        job_id, now = identifier(), time.time()
        with self.connect() as conn:
            for dependency in depends_on:
                if not conn.execute("SELECT 1 FROM jobs WHERE id=?", (dependency,)).fetchone():
                    raise ValueError("Unknown dependency")
            conn.execute("INSERT INTO jobs(id,kind,state,payload,priority,created,updated,depends_on) VALUES(?,?,'pending',?,?,?,?,?)",
                         (job_id, kind, data, int(priority), now, now, canonical(list(depends_on))))
        return job_id

    def job(self, job_id):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise KeyError(job_id)
        return self._job(row)

    def jobs(self, limit=500):
        with self.connect() as conn:
            return [self._job(row) for row in conn.execute("SELECT * FROM jobs ORDER BY created DESC LIMIT ?", (limit,))]

    def download_jobs_for_urls(self, urls):
        """Find all matching download jobs without truncating older history.

        URLs are bound SQL parameters, not statements. One UI batch is capped
        at 500 distinct URLs; unrelated job payloads are not returned.
        """
        if not isinstance(urls, (list, tuple, set)):
            raise ValueError("Danh sách URL đồng bộ không hợp lệ")
        urls = list(dict.fromkeys(urls))
        if len(urls) > 500 or any(type(u) is not str or not u for u in urls):
            raise ValueError("Chỉ kiểm tra tối đa 500 URL hợp lệ trong một lần đồng bộ")
        if not urls:
            return []
        placeholders = ",".join("?" for _ in urls)
        statement = (
            "SELECT * FROM jobs WHERE kind='download' "
            "AND json_extract(payload, '$.url') IN (" + placeholders + ") "
            "ORDER BY created DESC, id"
        )
        with self.connect() as conn:
            rows = conn.execute(statement, urls).fetchall()
        return [self._job(row) for row in rows]

    @staticmethod
    def _job(row):
        item = dict(row)
        for key in ("payload", "result", "depends_on"):
            item[key] = json.loads(item[key]) if item[key] else None
        return item

    def claim(self,allowed=None):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            for blocked in conn.execute("SELECT id,depends_on FROM jobs WHERE state='blocked' AND error LIKE 'Dependency%'").fetchall():
                deps=json.loads(blocked['depends_on'])
                if deps and all(conn.execute('SELECT state FROM jobs WHERE id=?',(key,)).fetchone()[0]=='succeeded' for key in deps):
                    conn.execute("UPDATE jobs SET state='pending',error=NULL WHERE id=?",(blocked['id'],))
            rows = conn.execute("SELECT * FROM jobs WHERE state='pending' AND cancel_requested=0 ORDER BY priority DESC,created").fetchall()
            for row in rows:
                if allowed is not None and row['kind'] not in allowed:continue
                deps = json.loads(row["depends_on"])
                states = [conn.execute("SELECT state FROM jobs WHERE id=?", (d,)).fetchone()[0] for d in deps]
                if any(s in {"failed", "canceled"} for s in states):
                    conn.execute("UPDATE jobs SET state='blocked',error='Dependency did not succeed',updated=? WHERE id=?", (time.time(), row["id"]))
                    continue
                if any(s=='blocked' for s in states):
                    conn.execute("UPDATE jobs SET state='blocked',error='Dependency waiting for configuration' WHERE id=?",(row['id'],));continue
                if any(s != "succeeded" for s in states):
                    continue
                conn.execute("UPDATE jobs SET state='running',attempts=attempts+1,heartbeat=?,updated=?,started=? WHERE id=?",
                             (time.time(), time.time(),time.time(), row["id"]))
                return self._job(row)
        return None

    def progress(self, job_id, value):
        with self.connect() as conn:
            conn.execute("UPDATE jobs SET progress=?,heartbeat=?,updated=? WHERE id=? AND state='running'",
                         (max(0, min(0.99, value)), time.time(), time.time(), job_id))

    def heartbeat(self,job_id):
        with self.connect() as conn:conn.execute("UPDATE jobs SET heartbeat=? WHERE id=? AND state='running'",(time.time(),job_id))

    def finish(self, job_id, result):
        data = canonical(checked_payload(result))
        with self.connect() as conn:
            canceled=conn.execute('SELECT cancel_requested FROM jobs WHERE id=?',(job_id,)).fetchone()
            if canceled and canceled[0]:
                result={**result,'warnings':[*result.get('warnings',[]),'Cancellation arrived after validated output; preserved artifact']};data=canonical(checked_payload(result))
            conn.execute("UPDATE jobs SET state='succeeded',result=?,progress=1,error=NULL,updated=? WHERE id=?", (data, time.time(), job_id))
            conn.execute("UPDATE matrix_history SET state='succeeded' WHERE job_id=?",(job_id,))

    def fail(self, job_id, message, blocked=False):
        # Every caller, including schedulers and recovery paths, passes through
        # this persistence boundary. Never trust callers to redact first.
        from .worker import sanitize_error_message
        safe_error = sanitize_error_message(message, limit=3000)
        with self.connect() as conn:
            row = conn.execute("SELECT cancel_requested FROM jobs WHERE id=?", (job_id,)).fetchone()
            state = "canceled" if row and row[0] else "blocked" if blocked else "failed"
            conn.execute("UPDATE jobs SET state=?,error=?,updated=? WHERE id=?", (state, safe_error, time.time(), job_id))
            conn.execute("UPDATE matrix_history SET state='failed' WHERE job_id=?",(job_id,))

    def cancel(self, job_id):
        with self.connect() as conn:
            conn.execute("UPDATE jobs SET cancel_requested=1,state=CASE WHEN state IN ('pending','blocked') THEN 'canceled' ELSE state END,updated=? WHERE id=? AND state NOT IN ('succeeded','failed','canceled')", (time.time(), job_id))
            row=conn.execute('SELECT state FROM jobs WHERE id=?',(job_id,)).fetchone()
            if row and row[0]=='canceled':conn.execute("UPDATE matrix_history SET state='failed' WHERE job_id=?",(job_id,))

    def retry(self, job_id):
        with self.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row=conn.execute('SELECT payload,state FROM jobs WHERE id=?',(job_id,)).fetchone()
            if not row or row['state'] not in {'failed','blocked','canceled'}:return
            data=json.loads(row['payload'])
            if data.get('matrix_scope'):
                reservation=conn.execute('SELECT state,job_id FROM matrix_history WHERE scope=? AND combination=?',(data['matrix_scope'],data['matrix_combination'])).fetchone()
                if reservation and reservation['job_id']!=job_id and reservation['state'] in {'reserved','succeeded'}:raise ValueError('Combination already reserved by a different job')
                conn.execute("UPDATE matrix_history SET state='reserved',job_id=? WHERE scope=? AND combination=?",(job_id,data['matrix_scope'],data['matrix_combination']))
            conn.execute("UPDATE jobs SET state='pending',error=NULL,cancel_requested=0,progress=0,updated=? WHERE id=? AND state IN ('failed','blocked','canceled')", (time.time(), job_id))

    def recover(self, stale_seconds=60,exclude=()):
        with self.connect() as conn:
            exclude=list(exclude);suffix=' AND id NOT IN ('+','.join('?' for _ in exclude)+')' if exclude else ''
            count=conn.execute("UPDATE jobs SET state=CASE WHEN cancel_requested=1 THEN 'canceled' ELSE 'pending' END,error='Recovered orphaned worker; output will be reconciled',updated=? WHERE state='running' AND COALESCE(heartbeat,0)<?"+suffix, (time.time(), time.time() - stale_seconds,*exclude)).rowcount
            conn.execute("UPDATE matrix_history SET state='failed' WHERE job_id IN (SELECT id FROM jobs WHERE state='canceled')")
            return count

    def cached(self, key):
        with self.connect() as conn:
            row = conn.execute("SELECT data FROM cache WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def cache(self, key, value):
        with self.connect() as conn:
            conn.execute("INSERT INTO cache VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET data=excluded.data,updated=excluded.updated", (key, canonical(checked_payload(value)), time.time()))
