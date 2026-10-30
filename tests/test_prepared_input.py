import hashlib
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from fonesi_edit.prepared_input import stage_verified_input


class PreparedInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.mp4"
        self.data = b"synthetic bytes" * 1000
        self.source.write_bytes(self.data)
        self.digest = hashlib.sha256(self.data).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def prepare(self, **kwargs):
        return stage_verified_input(
            self.source, self.digest, self.root, max_bytes=100000, **kwargs
        )

    def test_copy_matches_hash_and_outlives_source_change(self):
        with self.prepare() as result:
            self.assertEqual(result.path.read_bytes(), self.data)
            self.assertEqual(result.sha256, self.digest)
            self.assertEqual(result.size, len(self.data))
            self.source.write_bytes(b"changed after completed preparation")
            self.assertEqual(result.path.read_bytes(), self.data)
            path = result.path
        self.assertFalse(path.exists())
        self.assertEqual(
            self.source.read_bytes(), b"changed after completed preparation"
        )

    def test_consumer_failure_cleans_only_owned_input(self):
        unrelated = self.root / "keep.txt"
        unrelated.write_bytes(b"keep")
        with self.assertRaisesRegex(RuntimeError, "consumer"), self.prepare() as result:
            path = result.path
            raise RuntimeError("consumer")
        self.assertFalse(path.exists())
        self.assertEqual(unrelated.read_bytes(), b"keep")
        self.assertEqual(self.source.read_bytes(), self.data)

    def test_stale_digest_and_size_budget(self):
        self.source.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "DIGEST_MISMATCH"), self.prepare():
            self.fail("Unexpected prepared input")
        self.assertFalse(list(self.root.glob(".fonesi-input-*")))
        with (
            self.assertRaisesRegex(ValueError, "BYTE_BUDGET"),
            stage_verified_input(self.source, self.digest, self.root, max_bytes=1),
        ):
            self.fail("Unexpected prepared input")

    def test_cancel_and_timeout_publish_nothing(self):
        event = threading.Event()
        event.set()
        with self.assertRaisesRegex(ValueError, "CANCELED"), self.prepare(cancel=event):
            self.fail("Unexpected prepared input")
        with (
            patch("fonesi_edit.prepared_input.time.monotonic", side_effect=[0, 31]),
            self.assertRaises(TimeoutError),
            self.prepare(timeout=30),
        ):
            self.fail("Unexpected prepared input")
        self.assertFalse(list(self.root.glob(".fonesi-input-*")))
        self.assertEqual(self.source.read_bytes(), self.data)

    def test_bad_bounds_and_directory(self):
        for value in [0, -1, True, 2**63]:
            with (
                self.subTest(value=value),
                self.assertRaises(ValueError),
                stage_verified_input(
                    self.source, self.digest, self.root, max_bytes=value
                ),
            ):
                self.fail("Unexpected prepared input")
        for timeout in [0, -1, True, float("nan"), float("inf"), 61]:
            with (
                self.subTest(timeout=timeout),
                self.assertRaises(ValueError),
                self.prepare(timeout=timeout),
            ):
                self.fail("Unexpected prepared input")
        with (
            self.assertRaisesRegex(ValueError, "REGULAR_SOURCE"),
            stage_verified_input(self.root, self.digest, self.root, max_bytes=100000),
        ):
            self.fail("Unexpected prepared input")

    def test_final_symlink_rejected(self):
        link = self.root / "link.mp4"
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink permission unavailable; no symlink coverage claimed")
        with (
            self.assertRaisesRegex(ValueError, "REGULAR_SOURCE"),
            stage_verified_input(link, self.digest, self.root, max_bytes=100000),
        ):
            self.fail("Unexpected prepared input")

    def test_copy_fsync_failure_cleans_staging(self):
        with (
            patch(
                "fonesi_edit.prepared_input.os.fsync", side_effect=OSError("injected")
            ),
            self.assertRaises(OSError),
            self.prepare(),
        ):
            self.fail("Unexpected prepared input")
        self.assertFalse(list(self.root.glob(".fonesi-input-*")))
        self.assertEqual(self.source.read_bytes(), self.data)

    def test_concurrent_source_change_before_yield_rejects(self):
        import os

        real_fsync = os.fsync

        def mutate_after_flush(descriptor):
            real_fsync(descriptor)
            # Simulated external writer while preparation still owns its read handle.
            self.source.write_bytes(b"external replacement contents")

        with (
            patch(
                "fonesi_edit.prepared_input.os.fsync", side_effect=mutate_after_flush
            ),
            self.assertRaisesRegex(ValueError, "INPUT_CHANGED"),
            self.prepare(),
        ):
            self.fail("Unexpected prepared input")
        self.assertFalse(list(self.root.glob(".fonesi-input-*")))
        self.assertEqual(self.source.read_bytes(), b"external replacement contents")

    def test_cross_api_creation_time_is_not_change_time(self):
        from types import SimpleNamespace

        from fonesi_edit.prepared_input import _cross_api_identity, _identity

        fields = {
            "st_dev": 1,
            "st_ino": 2,
            "st_size": 3,
            "st_mtime_ns": 4,
            "st_birthtime_ns": 5,
            "st_ctime_ns": 5,
        }
        path_stat = SimpleNamespace(**fields)
        handle_stat = SimpleNamespace(**(fields | {"st_ctime_ns": 99}))
        self.assertEqual(
            _cross_api_identity(path_stat), _cross_api_identity(handle_stat)
        )
        self.assertNotEqual(_identity(path_stat), _identity(handle_stat))
        for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_birthtime_ns"):
            altered = SimpleNamespace(**(fields | {key: 999}))
            self.assertNotEqual(
                _cross_api_identity(path_stat), _cross_api_identity(altered)
            )
        changed_handle = SimpleNamespace(**(fields | {"st_ctime_ns": 100}))
        self.assertNotEqual(_identity(handle_stat), _identity(changed_handle))

    def test_windows_style_stat_semantics_full_copy(self):
        import os
        from types import SimpleNamespace

        real_lstat, real_fstat = Path.lstat, os.fstat
        source = self.source

        def fields(info, change):
            return SimpleNamespace(
                st_dev=info.st_dev,
                st_ino=info.st_ino,
                st_size=info.st_size,
                st_mtime_ns=info.st_mtime_ns,
                st_ctime_ns=change,
                st_birthtime_ns=5,
                st_mode=info.st_mode,
            )

        def path_stat(path, *args, **kwargs):
            info = real_lstat(path, *args, **kwargs)
            return fields(info, 5) if path == source else info

        def handle_stat(fd):
            return fields(real_fstat(fd), 99)

        with (
            patch.object(Path, "lstat", path_stat),
            patch("fonesi_edit.prepared_input.os.fstat", handle_stat),
            self.prepare() as result,
        ):
            self.assertEqual(result.path.read_bytes(), self.data)
        self.assertFalse(list(self.root.glob(".fonesi-input-*")))
