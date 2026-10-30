import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import shutil
import struct
import tempfile
import threading
import time
import unittest
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from fonesi_edit.app import MainWindow
from fonesi_edit.process import ProcessResult, run_bounded
from fonesi_edit.source_preview import source_frame


def make_source(path, ffmpeg):
    return run_bounded(
        [
            ffmpeg,
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=red:s=64x64:r=24:d=1",
            "-f",
            "lavfi",
            "-i",
            "color=blue:s=64x64:r=24:d=1",
            "-filter_complex",
            "[0:v][1:v]concat=n=2:v=1:a=0[out]",
            "-map",
            "[out]",
            "-c:v",
            "libx264",
            str(path),
        ]
    )


class SourceFrameTests(unittest.TestCase):
    def test_invalid_bounds_and_canceled_never_launch(self):
        cancel = threading.Event()
        cancel.set()
        with patch("fonesi_edit.source_preview.run_bounded") as run:
            for value in (-F(1), F(31536001), F(1, 3), 1, True):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    source_frame(Path("unused"), Path("unused"), value)
            with self.assertRaises(ValueError):
                source_frame(Path("unused"), Path("unused"), F(0), cancel=cancel)
            run.assert_not_called()

    def test_empty_corrupt_and_oversize_image_reject(self):
        for payload in (
            b"",
            b"not png",
            b"\x89PNG\r\n\x1a\n",
            b"\x89PNG\r\n\x1a\n"
            + struct.pack(">I", 13)
            + b"IHDR"
            + struct.pack(">II", 640, 1000000),
        ):
            with (
                patch(
                    "fonesi_edit.source_preview.run_bounded",
                    return_value=ProcessResult("OK", 0, payload),
                ),
                self.assertRaises(ValueError),
            ):
                source_frame(Path("unused"), Path("unused"), F(0))

    def test_real_distinct_requested_frames(self):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            self.skipTest("FFmpeg unavailable")
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "colors.mp4"
            self.assertEqual(make_source(source, ffmpeg).status, "OK")
            before = source.read_bytes()
            colors = []
            for at in (F(1, 4), F(5, 4)):
                image = QImage.fromData(source_frame(source, Path(ffmpeg), at))
                self.assertFalse(image.isNull())
                self.assertLessEqual(image.width(), 640)
                self.assertLessEqual(image.height(), 480)
                colors.append(image.pixelColor(image.width() // 2, image.height() // 2))
            self.assertGreater(colors[0].red(), 200)
            self.assertLess(colors[0].blue(), 30)
            self.assertGreater(colors[1].blue(), 200)
            self.assertLess(colors[1].red(), 30)
            self.assertEqual(source.read_bytes(), before)
            with self.assertRaises(ValueError):
                source_frame(source, Path(ffmpeg), F(3))


class SourceFrameUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_real_seek_edit_retention_and_changed_source_rejection(self):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg or not shutil.which("ffprobe"):
            self.skipTest("Media tools unavailable")
        window = MainWindow()

        def wait():
            end = time.monotonic() + 15
            while window.worker is not None and time.monotonic() < end:
                self.app.processEvents()
                time.sleep(0.01)
            self.assertIsNone(window.worker)

        try:
            self.assertFalse(window.preview_source_frame())
            with tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / "colors.mp4"
                self.assertEqual(make_source(source, ffmpeg).status, "OK")
                self.assertTrue(window.load_source(source))
                wait()
                window.start_time.setValue(0.25)
                before = window.current_project()
                window.source_time.setValue(1.25)
                self.assertTrue(window.preview_source_frame())
                self.assertFalse(window.preview_source_frame())
                wait()
                self.assertEqual(window.current_project(), before)
                image = window.preview.pixmap().toImage()
                self.assertGreater(
                    image.pixelColor(image.width() // 2, image.height() // 2).blue(),
                    200,
                )
                previous = window.preview.pixmap().cacheKey()
                window.source_time.setValue(2)
                self.assertFalse(window.preview_source_frame())
                source.write_bytes(b"changed owned fixture")
                window.source_time.setValue(0.25)
                self.assertTrue(window.preview_source_frame())
                wait()
                self.assertEqual(window.preview.pixmap().cacheKey(), previous)
                self.assertIn("không hoàn tất", window.status.text())
        finally:
            if window.worker:
                window.cancel_work()
                wait()
            window.close()
