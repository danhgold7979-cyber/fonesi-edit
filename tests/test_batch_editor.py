import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from fonesi_edit.batch import BatchInput, ScanResult
from fonesi_edit.batch_editor import BatchEditor
from fonesi_edit.process import run_bounded


class BatchUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = BatchEditor()
        self.window.show()
        self.app.processEvents()

    def wait_worker(self):
        deadline = time.monotonic() + 15
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertIsNone(self.window.worker)

    def tearDown(self):
        self.window.cancel_work()
        self.wait_worker()
        self.window.close()
        self.app.processEvents()

    def test_empty_partial_and_changed_destination(self):
        self.assertFalse(self.window.run_button.isEnabled())
        item = BatchInput(Path("/source/a.mp4"), Path("a.mp4"), "0" * 16)
        self.window.scanned(ScanResult((item,), "PARTIAL", ("VISIT_LIMIT",), 1))
        self.assertFalse(self.window.run_button.isEnabled())
        self.window.scanned(ScanResult((item,), "COMPLETE", (), 1))
        self.assertEqual(self.window.selected_items(), (item,))
        self.window.items.item(0).setCheckState(Qt.Unchecked)
        self.assertFalse(self.window.run_button.isEnabled())
        self.window.set_folder(Path("/new"), output=True)
        self.assertEqual(self.window.items.count(), 0)
        self.assertIsNone(self.window.scan_result)
        self.assertFalse(self.window.run_selected())

    def test_double_start_and_close(self):
        def operation(cancel):
            cancel.wait(5)
            raise ValueError("CANCELED")

        self.assertTrue(self.window.start(operation, lambda result: None))
        self.assertFalse(self.window.start(operation, lambda result: None))
        self.assertFalse(self.window.set_folder(Path("/new"), output=True))
        self.window.close()
        self.assertTrue(self.window.closing)
        self.wait_worker()
        self.assertFalse(self.window.isVisible())
        self.assertFalse(self.window.closing)

    def test_real_scan_export_and_collision(self):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg or not shutil.which("ffprobe"):
            self.skipTest("Media tools unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "source", Path(tmp) / "output"
            source.mkdir()
            output.mkdir()
            video = source / "clip.mp4"
            result = run_bounded(
                [
                    ffmpeg,
                    "-v",
                    "error",
                    "-n",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=s=160x90:r=24:d=1",
                    "-c:v",
                    "libx264",
                    str(video),
                ]
            )
            self.assertEqual(result.status, "OK")
            original = video.read_bytes()
            self.window.set_folder(source, output=False)
            self.window.set_folder(output, output=True)
            self.assertTrue(self.window.scan_sources())
            self.wait_worker()
            self.assertEqual(self.window.items.count(), 1)
            self.assertTrue(self.window.run_selected())
            self.wait_worker()
            self.assertIn("Lô COMPLETE: 1", self.window.status.text())
            self.assertEqual(len(list(output.rglob("*.mp4"))), 1)
            self.assertTrue(self.window.run_selected())
            self.wait_worker()
            self.assertIn("OUTPUT_EXISTS", self.window.status.text())
            self.assertEqual(video.read_bytes(), original)

    def test_parent_close_keeps_worker_alive_until_canceled(self):
        from fonesi_edit.app import MainWindow

        main = MainWindow()
        main.batch_window = self.window

        def operation(cancel):
            cancel.wait(5)
            raise ValueError("CANCELED")

        self.window.start(operation, lambda value: None)
        main.show()
        main.close()
        self.assertTrue(main.isVisible())
        self.assertIsNotNone(self.window.worker)
        self.wait_worker()
        main.close()
        self.assertFalse(main.isVisible())

    def test_selection_is_captured_before_worker_runs(self):
        import threading
        from unittest.mock import patch

        from fonesi_edit.batch import BatchResult

        item = BatchInput(Path("/source/a.mp4"), Path("a.mp4"), "0" * 16)
        self.window.set_folder(Path("/source"), output=False)
        self.window.set_folder(Path("/output"), output=True)
        self.window.ffmpeg = "/tool/ffmpeg"
        self.window.ffprobe = "/tool/ffprobe"
        self.window.scanned(ScanResult((item,), "COMPLETE", (), 1))
        entered, proceed = threading.Event(), threading.Event()
        received = []

        def fake(items, *args, **kwargs):
            entered.set()
            proceed.wait(5)
            received.append(items)
            return BatchResult((), (), "COMPLETE")

        with patch("fonesi_edit.batch_editor.render_batch", fake):
            self.assertTrue(self.window.run_selected())
            self.assertTrue(entered.wait(2))
            self.window.items.item(0).setCheckState(Qt.Unchecked)
            self.assertFalse(self.window.run_selected())
            proceed.set()
            self.wait_worker()
        self.assertEqual(received, [(item,)])

    def test_escape_reject_cancels_and_waits(self):
        def operation(cancel):
            cancel.wait(5)
            raise ValueError("CANCELED")

        self.window.start(operation, lambda result: None)
        self.window.reject()
        self.assertTrue(self.window.closing)
        self.assertIsNotNone(self.window.worker)
        self.wait_worker()
        self.assertFalse(self.window.isVisible())
