import json
import shutil
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from fonesi_edit.media import LOCAL_MEDIA_INPUT_OPTIONS, probe
from fonesi_edit.process import run_bounded
from fonesi_edit.render import render_cpu


class MediaBoundaryTests(unittest.TestCase):
    def test_owned_valid_playlist_is_not_supported_media_input(self):
        ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            self.skipTest("Media tools unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            segment, playlist, output = (
                root / "owned.ts",
                root / "owned.m3u8",
                root / "output.mp4",
            )
            generated = run_bounded(
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
                    "-f",
                    "mpegts",
                    str(segment),
                ]
            )
            self.assertEqual(generated.status, "OK")
            playlist.write_text(
                "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:1\n#EXTINF:1.0,\n"
                + segment.name
                + "\n#EXT-X-ENDLIST\n"
            )
            baseline = run_bounded(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-protocol_whitelist",
                    "file,pipe",
                    "-show_entries",
                    "format=format_name:stream=codec_type",
                    "-of",
                    "json",
                    str(playlist),
                ]
            )
            self.assertEqual(baseline.status, "OK")
            self.assertEqual(
                json.loads(baseline.stdout)["format"]["format_name"], "hls"
            )
            original_playlist, original_segment = (
                playlist.read_bytes(),
                segment.read_bytes(),
            )
            with self.assertRaises(ValueError):
                probe(playlist, Path(ffprobe))
            with self.assertRaises(ValueError):
                render_cpu(
                    playlist,
                    output,
                    Path(ffmpeg),
                    Path(ffprobe),
                    duration_tolerance=Fraction(1, 10),
                )
            self.assertFalse(output.exists())
            self.assertEqual(playlist.read_bytes(), original_playlist)
            self.assertEqual(segment.read_bytes(), original_segment)

    def test_allowed_container_controls(self):
        ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            self.skipTest("Media tools unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            for suffix in ("mp4", "mov", "mkv", "avi"):
                with self.subTest(suffix=suffix):
                    source = Path(tmp) / ("owned." + suffix)
                    generated = run_bounded(
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
                            str(source),
                        ]
                    )
                    self.assertEqual(generated.status, "OK")
                    self.assertIn("video", probe(source, Path(ffprobe)).stream_types)

    def test_allowlist_is_explicit_and_excludes_playlist_demuxers(self):
        self.assertEqual(
            LOCAL_MEDIA_INPUT_OPTIONS[:2], ("-protocol_whitelist", "file,pipe")
        )
        formats = set(LOCAL_MEDIA_INPUT_OPTIONS[3].split(","))
        self.assertTrue({"mov", "matroska", "avi", "wav", "mp3"} <= formats)
        self.assertFalse({"hls", "concat", "dash", "image2"} & formats)
