import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import shutil
import tempfile
import threading
import time
import unittest
from fractions import Fraction
from pathlib import Path

from PySide6.QtWidgets import QApplication

from fonesi_edit.batch import BatchProgress, render_batch, scan
from fonesi_edit.batch_editor import BatchEditor
from fonesi_edit.process import run_bounded


class BatchProgressTests(unittest.TestCase):
    def test_real_mixed_outcome_and_progress_observer_failure(self):
        ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            self.skipTest("Media tools unavailable")
        with tempfile.TemporaryDirectory() as folder:
            root, out = Path(folder) / "in", Path(folder) / "out"
            root.mkdir()
            out.mkdir()
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
                        str(root / "a.mp4"),
                    ]
                ).status,
                "OK",
            )
            (root / "b.mp4").write_bytes(b"bad")
            selected = scan((root,), out).items
            events = []
            result = render_batch(
                selected,
                out,
                Path(ffmpeg),
                Path(ffprobe),
                duration_tolerance=Fraction(1, 10),
                progress=events.append,
            )
            self.assertEqual(result.status, "PARTIAL")
            self.assertEqual(events[-1], BatchProgress(2, 2, 1, 1, None, "PARTIAL"))
            self.assertEqual(
                [x.finished for x in events], sorted(x.finished for x in events)
            )
            self.assertTrue(all(x.finished == x.validated + x.failed for x in events))
            self.assertEqual(
                [x.active_index for x in events if x.active_index is not None], [0, 1]
            )
            second = Path(folder) / "other"
            second.mkdir()

            def broken(update):
                raise RuntimeError("observer failed")

            again = render_batch(
                selected,
                second,
                Path(ffmpeg),
                Path(ffprobe),
                duration_tolerance=Fraction(1, 10),
                progress=broken,
            )
            self.assertTrue(again.progress_failed)
            self.assertEqual(again.status, "PARTIAL")
            self.assertEqual(len(again.artifacts), 1)
            self.assertTrue(again.artifacts[0].path.is_file())

    def test_cancel_before_next_item_does_not_count_unattempted(self):
        with tempfile.TemporaryDirectory() as folder:
            root, out = Path(folder) / "in", Path(folder) / "out"
            root.mkdir()
            out.mkdir()
            for name in ("a.mp4", "b.mp4"):
                (root / name).write_bytes(b"bad")
            items = scan((root,), out).items
            cancel = threading.Event()
            events = []

            def progress(value):
                events.append(value)
                if value.finished == 1:
                    cancel.set()

            # Missing executable fails only the attempted first item, without a launch.
            result = render_batch(
                items,
                out,
                Path(folder) / "missing",
                Path(folder) / "missing",
                duration_tolerance=Fraction(1, 10),
                cancel=cancel,
                progress=progress,
            )
            self.assertEqual(result.status, "CANCELED")
            self.assertEqual(events[-1], BatchProgress(2, 1, 0, 1, None, "CANCELED"))
            self.assertEqual(len(result.failures), 1)
            events.clear()
            result = render_batch(
                items,
                out,
                Path(folder) / "missing",
                Path(folder) / "missing",
                duration_tolerance=Fraction(1, 10),
                cancel=cancel,
                progress=events.append,
            )
            self.assertEqual(events, [BatchProgress(2, 0, 0, 0, None, "CANCELED")])
            self.assertFalse(result.failures)


class BatchProgressUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_queued_main_thread_progress_retained_and_stale_ignored(self):
        window = BatchEditor()
        threads = []
        main_id = threading.get_ident()
        original = window.progress_changed

        def record(worker, update):
            threads.append(threading.get_ident())
            return original(worker, update)

        window.progress_changed = record
        update = BatchProgress(3, 2, 1, 1, None, "CANCELED")
        window.batch_progress = BatchProgress(3, 0, 0, 0, None, "RUNNING")

        def operation(cancel, report):
            report(update)

        try:
            self.assertTrue(
                window.start(operation, lambda result: None, report_progress=True)
            )
            worker = window.worker
            deadline = time.monotonic() + 5
            while window.worker is not None and time.monotonic() < deadline:
                self.app.processEvents()
                time.sleep(0.01)
            self.assertIsNone(window.worker)
            self.assertEqual(threads, [main_id])
            self.assertEqual(window.progress.value(), 2)
            self.assertEqual(window.progress.maximum(), 3)
            self.assertFalse(
                original(worker, BatchProgress(3, 3, 3, 0, None, "COMPLETE"))
            )
            self.assertEqual(window.progress.value(), 2)
            window.set_folder(Path(tempfile.gettempdir()), output=True)
            self.assertIsNone(window.batch_progress)
        finally:
            if window.worker:
                window.cancel_work()
                window.worker.wait(5000)
                self.app.processEvents()
            window.close()
