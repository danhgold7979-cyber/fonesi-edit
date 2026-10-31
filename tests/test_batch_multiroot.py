import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from fonesi_edit.batch import ScanResult
from fonesi_edit.batch_editor import BatchEditor
from fonesi_edit.process import run_bounded


class MultiRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = BatchEditor()

    def wait(self):
        deadline = time.monotonic() + 15
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertIsNone(self.window.worker)

    def tearDown(self):
        self.window.cancel_work()
        self.wait()
        self.window.close()
        self.app.processEvents()

    def test_add_duplicate_remove_invalidation_and_limits(self):
        root = Path(tempfile.gettempdir())
        self.assertTrue(self.window.add_source(root / "a"))
        self.assertTrue(self.window.add_source(root / "b"))
        before = ScanResult((), "COMPLETE", (), 0)
        self.window.scanned(before)
        self.assertFalse(self.window.add_source(root / "a"))
        self.assertIs(self.window.scan_result, before)
        self.window.source_roots.setCurrentRow(0)
        self.assertTrue(self.window.remove_source())
        self.assertEqual(self.window.sources, [root / "b"])
        self.assertIsNone(self.window.scan_result)
        self.window.source_roots.setCurrentRow(0)
        self.assertTrue(self.window.remove_source())
        self.assertFalse(self.window.scan_button.isEnabled())
        for i in range(100):
            self.assertTrue(self.window.add_source(root / str(i)))
        self.assertFalse(self.window.add_source(root / "overflow"))
        self.assertEqual(len(self.window.sources), 100)

    def test_root_tuple_snapshot_and_busy_close_admission(self):
        root = Path(tempfile.gettempdir())
        self.window.add_source(root / "a")
        self.window.add_source(root / "b")
        self.window.set_folder(root / "out", output=True)
        entered, release = threading.Event(), threading.Event()
        observed = []

        def fake(roots, *args, **kwargs):
            entered.set()
            release.wait(3)
            observed.append(roots)
            return ScanResult((), "COMPLETE", (), 0)

        try:
            with patch("fonesi_edit.batch_editor.scan", fake):
                self.assertTrue(self.window.scan_sources())
                self.assertTrue(entered.wait(2))
                self.assertFalse(self.window.add_source(root / "c"))
                self.assertFalse(self.window.remove_source())
                # Simulate direct outside mutation; dispatched tuple still cannot change.
                self.window.sources.append(root / "not-in-snapshot")
                release.set()
                self.wait()
            self.assertEqual(observed, [(root / "a", root / "b")])
            self.window.closing = True
            self.assertFalse(self.window.add_source(root / "closing"))
            self.assertFalse(
                self.window.start(lambda cancel: None, lambda result: None)
            )
            self.window.close()
            self.window.show()
            self.app.processEvents()
            self.assertFalse(self.window.closing)
            self.assertTrue(self.window.source_button.isEnabled())
        finally:
            release.set()

    def test_real_same_named_sources_produce_distinct_outputs(self):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg or not shutil.which("ffprobe"):
            self.skipTest("Media tools unavailable")
        with tempfile.TemporaryDirectory() as folder:
            a, b, out = [Path(folder) / name for name in ("first", "second", "out")]
            for p in (a, b, out):
                p.mkdir()
            self.assertEqual(
                run_bounded(
                    [
                        ffmpeg,
                        "-v",
                        "error",
                        "-f",
                        "lavfi",
                        "-i",
                        "color=blue:s=64x64:r=24:d=1",
                        "-c:v",
                        "libx264",
                        str(a / "clip.mp4"),
                    ]
                ).status,
                "OK",
            )
            shutil.copyfile(a / "clip.mp4", b / "clip.mp4")
            before = (a / "clip.mp4").read_bytes()
            self.window.add_source(a)
            self.window.add_source(b)
            self.window.set_folder(out, output=True)
            self.assertTrue(self.window.scan_sources())
            self.wait()
            self.assertEqual(self.window.items.count(), 2)
            self.assertEqual(
                len({item.root_id for item in self.window.scan_result.items}), 2
            )
            displayed = [self.window.items.item(i).text() for i in range(2)]
            expected_sources = {(a / "clip.mp4").resolve(), (b / "clip.mp4").resolve()}
            self.assertEqual(
                {item.source for item in self.window.scan_result.items},
                expected_sources,
            )
            for expected in expected_sources:
                self.assertTrue(
                    any(text.startswith(str(expected) + " → ") for text in displayed),
                    f"Canonical source {expected!s}; displayed={displayed!r}",
                )
            self.assertTrue(self.window.run_selected())
            self.wait()
            self.assertEqual(len(list(out.rglob("clip-mp4-edit.mp4"))), 2)
            self.assertEqual(self.window.batch_progress.validated, 2)
            self.assertEqual((a / "clip.mp4").read_bytes(), before)
            self.assertEqual((b / "clip.mp4").read_bytes(), before)
