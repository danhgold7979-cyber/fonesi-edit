import json
import unittest
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction as F

from fonesi_edit.cpu_snapshot import CpuExportSnapshot
from fonesi_edit.snapshot import RenderIntent
from fonesi_edit.timing import ClipMap, Interval


class CpuSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.value = CpuExportSnapshot(
            "12345678-1234-5678-1234-567812345678",
            "/Nguồn/🎬.mp4",
            "/Kết quả/video.mp4",
            "a" * 64,
            "/tools/ffmpeg",
            "b" * 64,
            "/tools/ffprobe",
            "c" * 64,
            ClipMap(Interval(F(1, 3), F(7, 3)), F(3, 2)),
            F(1, 10),
            7,
        )

    def test_unicode_rational_roundtrip(self):
        self.assertEqual(CpuExportSnapshot.parse(self.value.canonical()), self.value)
        self.assertIn("🎬", self.value.canonical())
        self.assertEqual(
            json.loads(self.value.canonical())["clip_map"]["start"], [1, 3]
        )
        self.assertEqual(len(self.value.digest), 64)
        reversed_fields = dict(
            reversed(list(json.loads(self.value.canonical()).items()))
        )
        self.assertEqual(
            CpuExportSnapshot.parse(json.dumps(reversed_fields)).digest,
            self.value.digest,
        )

    def test_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            self.value.seed = 8

    def test_execution_changes_alter_digest(self):
        changes = [
            {"destination": "/other.mp4"},
            {"ffmpeg_sha256": "d" * 64},
            {"source_sha256": "e" * 64},
            {"clip_map": None},
            {"seed": 8},
            {"duration_tolerance": F(1, 20)},
        ]
        for values in changes:
            with self.subTest(values=values):
                self.assertNotEqual(
                    replace(self.value, **values).digest, self.value.digest
                )

    def test_old_snapshot_not_automatically_executable(self):
        old = RenderIntent(self.value.project_id, "/source.mp4", "/output", 7)
        self.assertEqual(RenderIntent.parse(old.canonical()), old)
        with self.assertRaises(ValueError):
            CpuExportSnapshot.parse(old.canonical())
        with self.assertRaises(ValueError):
            RenderIntent.parse(self.value.canonical())

    def test_unknown_duplicate_nested_and_version_rejected(self):
        raw = self.value.canonical()
        variants = [
            raw[:-1] + ',"token":"secret"}',
            raw[:-1] + ',"seed":7}',
            raw.replace('"start":[1,3]', '"start":[1,3],"start":[1,3]'),
            raw.replace('"version":1', '"version":2'),
            "[]",
        ]
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                CpuExportSnapshot.parse(value)

    def test_invalid_contract_fields(self):
        for change in [
            {"seed": True},
            {"version": True},
            {"source": "relative.mp4"},
            {"destination": self.value.source},
            {"destination": "/x.mkv"},
            {"ffmpeg_sha256": "A" * 64},
            {"source_sha256": "x" * 64},
            {"duration_tolerance": F(-1)},
            {"duration_tolerance": F(2)},
            {"clip_map": ClipMap(Interval(F(0), F(1)), F(3))},
            {"clip_map": ClipMap(Interval(F(0), F(1)), F(1), F(1))},
            {"source": "/" + "x" * 4096},
            {"project_id": "not-uuid"},
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(self.value, **change)

    def test_raw_rational_limits(self):
        for fraction in [[True, 1], [1, 0], [1, -1], [2**100, 2**100], [1.0, 2]]:
            data = json.loads(self.value.canonical())
            data["duration_tolerance"] = fraction
            with self.subTest(fraction=fraction), self.assertRaises(ValueError):
                CpuExportSnapshot.parse(json.dumps(data))

    def test_null_map_and_oversize(self):
        value = replace(self.value, clip_map=None)
        self.assertEqual(CpuExportSnapshot.parse(value.canonical()), value)
        with self.assertRaises(ValueError):
            CpuExportSnapshot.parse(" " * 65537)

    def test_version_one_golden_digest(self):
        # Fixed Unicode/rational wire contract, not recalculated expected output.
        self.assertEqual(
            self.value.digest,
            "60a2e9ebb256877badce931eec0e86f0d1624382d5eb3ae2c272474d0942f4c3",
        )
