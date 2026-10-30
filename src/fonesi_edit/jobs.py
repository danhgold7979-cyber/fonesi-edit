"""Durable intent ledger. Workers require an exact claim token; no auto replay."""

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from fonesi_edit.snapshot import RenderIntent


class Conflict(ValueError):
    pass


class JobStore:
    def __init__(self, path: Path):
        self.db = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.db.close()
            raise ValueError("Unsupported database schema")
        with self.transaction():
            self.db.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, intent TEXT NOT NULL, digest TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('pending','running','validating',
                'succeeded','failed','canceled','blocked_configuration','interrupted')),
                token TEXT, lease_until REAL, attempt INTEGER NOT NULL DEFAULT 0,
                created REAL NOT NULL, validated_artifact TEXT)""")
            self.db.execute("PRAGMA user_version=1")

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def close(self):
        self.db.close()

    def enqueue(self, job_id: str, intent: RenderIntent):
        if not isinstance(job_id, str) or not job_id or len(job_id) > 128:
            raise ValueError("Invalid job identity")
        with self.transaction():
            old = self.db.execute(
                "SELECT digest FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
            if old:
                if old["digest"] != intent.digest:
                    raise Conflict("Job identity already has different intent")
                return False
            self.db.execute(
                "INSERT INTO jobs(id,intent,digest,state,created) VALUES(?,?,?,?,?)",
                (job_id, intent.canonical(), intent.digest, "pending", time.time()),
            )
            return True

    def get(self, job_id):
        row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return dict(row)

    def claim(self, job_id: str, *, now: float, lease_seconds: float = 30):
        import math

        if (
            not all(
                type(x) in (int, float) and math.isfinite(x)
                for x in (now, lease_seconds)
            )
            or now < 0
            or not 0 < lease_seconds <= 3600
            or not math.isfinite(now + lease_seconds)
        ):
            raise ValueError("Invalid lease")
        token = uuid4().hex
        with self.transaction():
            changed = self.db.execute(
                """UPDATE jobs SET state='running',token=?,lease_until=?,
                attempt=attempt+1 WHERE id=? AND state='pending' """,
                (token, now + lease_seconds, job_id),
            ).rowcount
            if changed != 1:
                raise Conflict("Job not claimable")
        return token

    def transition(self, job_id, token, target, *, now):
        import math

        if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
            raise ValueError("Invalid clock")
        allowed = {
            "running": {"validating", "failed", "canceled", "blocked_configuration"},
            "validating": {"failed", "canceled"},
        }
        with self.transaction():
            row = self.get(job_id)
            if (
                not isinstance(token, str)
                or not token
                or row["token"] != token
                or row["lease_until"] is None
                or row["lease_until"] <= now
                or target not in allowed.get(row["state"], set())
            ):
                raise Conflict("Invalid worker transition")
            terminal = target != "validating"
            self.db.execute(
                "UPDATE jobs SET state=?,token=?,lease_until=? WHERE id=?",
                (
                    target,
                    None if terminal else token,
                    None if terminal else row["lease_until"],
                    job_id,
                ),
            )

    def reconcile_expired(self, *, now):
        import math

        if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
            raise ValueError("Invalid clock")
        with self.transaction():
            return self.db.execute(
                """UPDATE jobs SET state='interrupted',token=NULL,lease_until=NULL
                WHERE state IN ('running','validating') AND lease_until<=?""",
                (now,),
            ).rowcount

    def retry(self, job_id):
        with self.transaction():
            changed = self.db.execute(
                """UPDATE jobs SET state='pending',token=NULL,lease_until=NULL
                WHERE id=? AND state IN ('failed','canceled','blocked_configuration')""",
                (job_id,),
            ).rowcount
            if changed != 1:
                raise Conflict(
                    "Retry requires resolved terminal failure, never uncertain execution"
                )
