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
