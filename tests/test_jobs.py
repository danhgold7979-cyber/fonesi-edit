import sqlite3
import tempfile
import unittest
from pathlib import Path

from fonesi_edit.jobs import Conflict, JobStore
from fonesi_edit.snapshot import RenderIntent


class JobsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "jobs.db"
        self.store = JobStore(self.path)
        self.intent = RenderIntent(
            "12345678-1234-5678-1234-567812345678", "/source", "/output", 1
        )
        self.store.enqueue("job", self.intent)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_idempotence(self):
        self.assertFalse(self.store.enqueue("job", self.intent))

    def test_conflicting_intent(self):
        other = RenderIntent(self.intent.project_id, "/different", "/output", 1)
        with self.assertRaises(Conflict):
            self.store.enqueue("job", other)

    def test_two_connections_one_claim(self):
        other = JobStore(self.path)
        try:
            self.store.claim("job", now=100)
            with self.assertRaises(Conflict):
                other.claim("job", now=100)
        finally:
            other.close()

    def test_stale_token(self):
        token = self.store.claim("job", now=100)
        with self.assertRaises(Conflict):
            self.store.transition("job", "wrong", "validating", now=101)
        self.store.transition("job", token, "failed", now=101)
        self.store.retry("job")
        self.store.claim("job", now=101)
        with self.assertRaises(Conflict):
            self.store.transition("job", token, "validating", now=101)

    def test_no_blind_recovery(self):
        self.store.claim("job", now=100, lease_seconds=10)
        self.assertEqual(self.store.reconcile_expired(now=109), 0)
        self.assertEqual(self.store.reconcile_expired(now=110), 1)
        self.assertEqual(self.store.get("job")["state"], "interrupted")
        with self.assertRaises(Conflict):
            self.store.retry("job")

    def test_success_is_not_generic_transition(self):
        token = self.store.claim("job", now=100)
        self.store.transition("job", token, "validating", now=101)
        with self.assertRaises(Conflict):
            self.store.transition("job", token, "succeeded", now=101)

    def test_reopen_keeps_snapshot(self):
        self.store.close()
        self.store = JobStore(self.path)
        self.assertEqual(self.store.get("job")["intent"], self.intent.canonical())

    def test_bad_lease(self):
        for value in [float("nan"), float("inf"), -1, True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.store.claim("job", now=value)

    def test_expired_token_cannot_mutate_before_reconciler(self):
        token = self.store.claim("job", now=100, lease_seconds=1)
        with self.assertRaises(Conflict):
            self.store.transition("job", token, "validating", now=101)
        self.assertEqual(self.store.get("job")["state"], "running")

    def test_online_backup_preserves_lease_without_replay(self):
        token = self.store.claim("job", now=100, lease_seconds=10)
        destination = Path(self.temp.name) / "backup.db"
        self.assertEqual(self.store.backup_new(destination), destination)
        restored = JobStore(destination)
        try:
            self.assertEqual(restored.get("job"), self.store.get("job"))
            self.assertEqual(restored.get("job")["token"], token)
            self.assertEqual(restored.reconcile_expired(now=110), 1)
            self.assertEqual(restored.get("job")["state"], "interrupted")
            self.assertEqual(self.store.get("job")["state"], "running")
            with self.assertRaises(Conflict):
                restored.retry("job")
        finally:
            restored.close()

    def test_backup_no_overwrite_and_cancellation(self):
        import threading

        destination = Path(self.temp.name) / "backup.db"
        destination.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            self.store.backup_new(destination)
        self.assertEqual(destination.read_bytes(), b"keep")
        canceled = threading.Event()
        canceled.set()
        new = Path(self.temp.name) / "canceled.db"
        with self.assertRaisesRegex(ValueError, "BACKUP_CANCELED"):
            self.store.backup_new(new, cancel=canceled)
        self.assertFalse(new.exists())
        self.assertFalse(list(Path(self.temp.name).glob(".fonesi-backup-*")))

    def test_backup_rejects_active_transaction_and_bad_bounds(self):
        destination = Path(self.temp.name) / "backup.db"
        with self.store.transaction(), self.assertRaises(Conflict):
            self.store.backup_new(destination)
        for timeout in (True, 0, -1, float("inf"), float("nan"), 61):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                self.store.backup_new(destination, timeout=timeout)
        self.assertFalse(destination.exists())

    def test_backup_timeout_leaves_no_output(self):
        from unittest.mock import patch

        destination = Path(self.temp.name) / "backup.db"
        with (
            patch("fonesi_edit.jobs.time.monotonic", side_effect=[0, 31]),
            self.assertRaises(TimeoutError),
        ):
            self.store.backup_new(destination, timeout=30)
        self.assertFalse(destination.exists())

    def test_backup_failure_cleans_owned_staging(self):
        from unittest.mock import patch

        class FailedSource:
            in_transaction = False

            def backup(self, *args, **kwargs):
                raise sqlite3.OperationalError("Injected backup failure")

        destination = Path(self.temp.name) / "failed.db"
        with (
            patch.object(self.store, "db", FailedSource()),
            self.assertRaises(sqlite3.OperationalError),
        ):
            self.store.backup_new(destination)
        self.assertFalse(destination.exists())
        self.assertFalse(list(Path(self.temp.name).glob(".fonesi-backup-*")))
        self.assertEqual(self.store.get("job")["intent"], self.intent.canonical())


class SchemaTests(unittest.TestCase):
    def test_reject_foreign_schema_without_mutation(self):
        scenarios = [
            (
                0,
                "CREATE TABLE unrelated(value TEXT)",
                "INSERT INTO unrelated VALUES('keep')",
            ),
            (
                1,
                "CREATE TABLE unrelated(value TEXT)",
                "INSERT INTO unrelated VALUES('keep')",
            ),
            (1, None, None),
            (2, None, None),
        ]
        for version, ddl, insert in scenarios:
            with (
                self.subTest(version=version, ddl=ddl),
                tempfile.TemporaryDirectory() as tmp,
            ):
                path = Path(tmp) / "foreign.db"
                db = sqlite3.connect(path)
                if ddl:
                    db.execute(ddl)
                    db.execute(insert)
                db.execute(f"PRAGMA user_version={version}")
                db.commit()
                before = list(db.iterdump())
                with self.assertRaises(ValueError):
                    JobStore(path)
                self.assertEqual(
                    db.execute("PRAGMA user_version").fetchone()[0], version
                )
                self.assertEqual(list(db.iterdump()), before)
                db.close()

    def test_reject_schema_drift_without_mutation(self):
        changes = [
            "ALTER TABLE jobs ADD COLUMN surprise TEXT",
            "CREATE TRIGGER side_effect AFTER INSERT ON jobs BEGIN DELETE FROM jobs; END",
            "CREATE INDEX extra ON jobs(state)",
            "CREATE TABLE sqlitex_hidden(value TEXT)",
        ]
        for ddl in changes:
            with self.subTest(ddl=ddl), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "jobs.db"
                store = JobStore(path)
                store.close()
                db = sqlite3.connect(path)
                db.execute(ddl)
                db.commit()
                before = list(db.iterdump())
                with self.assertRaises(ValueError):
                    JobStore(path)
                self.assertEqual(list(db.iterdump()), before)
                db.close()

    def test_reopen_original_foundation_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.db"
            db = sqlite3.connect(path)
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, intent TEXT NOT NULL, digest TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('pending','running','validating',
                'succeeded','failed','canceled','blocked_configuration','interrupted')),
                token TEXT, lease_until REAL, attempt INTEGER NOT NULL DEFAULT 0,
                created REAL NOT NULL, validated_artifact TEXT)""")
            db.execute("PRAGMA user_version=1")
            db.commit()
            db.close()
            store = JobStore(path)
            store.close()

    def test_reject_changed_constraint_and_default(self):
        from fonesi_edit.jobs import _SCHEMA

        variants = [
            _SCHEMA.replace("'pending','running'", "'unexpected','running'"),
            _SCHEMA.replace("DEFAULT 0", "DEFAULT 7"),
        ]
        for ddl in variants:
            with self.subTest(ddl=ddl), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "changed.db"
                db = sqlite3.connect(path)
                db.execute(ddl)
                db.execute("PRAGMA user_version=1")
                db.commit()
                before = list(db.iterdump())
                with self.assertRaises(ValueError):
                    JobStore(path)
                self.assertEqual(list(db.iterdump()), before)
                db.close()
