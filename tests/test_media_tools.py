import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from fonesi_edit.media_tools import inspect_tools
from fonesi_edit.process import ProcessResult


class MediaToolsTests(unittest.TestCase):
    def test_real_installed_tools(self):
        ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            self.skipTest("Trusted media tools unavailable")
        result = inspect_tools(Path(ffmpeg), Path(ffprobe))
        self.assertEqual(result.ffmpeg, Path(ffmpeg).resolve())
        self.assertTrue(result.ffmpeg_version)
        with self.assertRaisesRegex(ValueError, "ROLE_OR_VERSION"):
            inspect_tools(Path(ffprobe), Path(ffmpeg))

    def test_missing_or_same_path_and_pre_cancel(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tool"
            path.write_bytes(b"fixture not executed")
            with self.assertRaises(ValueError):
                inspect_tools(path, path)
            with self.assertRaises(ValueError):
                inspect_tools(Path("relative"), path)
            canceled = threading.Event()
            canceled.set()
            with (
                patch("fonesi_edit.media_tools.run_bounded") as run,
                self.assertRaisesRegex(ValueError, "CANCELED"),
            ):
                inspect_tools(path, path, cancel=canceled)
            run.assert_not_called()

    def test_declared_encoders_required_and_errors_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "one", Path(tmp) / "two"
            first.write_bytes(b"fixture")
            second.write_bytes(b"fixture")
            version = [
                ProcessResult("OK", 0, b"ffmpeg version 7.1 test\n"),
                ProcessResult("OK", 0, b"ffprobe version 7.1 test\n"),
            ]
            for output in (
                b"",
                b" V....D libx264 description\n",
                b" A....D aac description\n",
            ):
                with (
                    self.subTest(output=output),
                    patch(
                        "fonesi_edit.media_tools.run_bounded",
                        side_effect=version + [ProcessResult("OK", 0, output)],
                    ),
                    self.assertRaisesRegex(ValueError, "ENCODERS_MISSING"),
                ):
                    inspect_tools(first, second)
            with (
                patch(
                    "fonesi_edit.media_tools.run_bounded",
                    return_value=ProcessResult("OUTPUT_LIMIT", None, b""),
                ),
                self.assertRaisesRegex(ValueError, "OUTPUT_LIMIT"),
            ):
                inspect_tools(first, second)
            with patch(
                "fonesi_edit.media_tools.run_bounded",
                side_effect=version
                + [ProcessResult("OK", 0, b" V....D libx264 x\n A....D aac x\n")],
            ):
                self.assertEqual(inspect_tools(first, second).ffprobe_version, "7.1")
