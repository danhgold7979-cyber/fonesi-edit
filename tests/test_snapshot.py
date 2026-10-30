import unittest
from dataclasses import FrozenInstanceError

from fonesi_edit.snapshot import RenderIntent


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.value = RenderIntent(
            "12345678-1234-5678-1234-567812345678",
            "C:\\Nguồn\\clip.mp4",
            "D:\\Kết quả",
            7,
        )

    def test_roundtrip(self):
        self.assertEqual(RenderIntent.parse(self.value.canonical()), self.value)

    def test_digest_is_stable(self):
        self.assertEqual(
            RenderIntent.parse(self.value.canonical()).digest, self.value.digest
        )
        self.assertEqual(len(self.value.digest), 64)

    def test_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            self.value.seed = 8

    def test_unknown_secrets_rejected(self):
        with self.assertRaises(ValueError):
            RenderIntent.parse(self.value.canonical()[:-1] + ',"token":"secret"}')

    def test_duplicate_key_rejected(self):
        with self.assertRaises(ValueError):
            RenderIntent.parse(self.value.canonical()[:-1] + ',"seed":8}')

    def test_version_rejected(self):
        with self.assertRaises(ValueError):
            RenderIntent.parse(
                self.value.canonical().replace(
                    '"schema_version":1', '"schema_version":2'
                )
            )

    def test_bad_paths(self):
        for path in ["relative.mp4", "https://example.test/x", "C:relative", "/x\x00x"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                RenderIntent(self.value.project_id, path, "/output", 1)

    def test_seed_bool_rejected(self):
        with self.assertRaises(ValueError):
            RenderIntent(self.value.project_id, "/source", "/output", True)

    def test_array_rejected(self):
        with self.assertRaises(ValueError):
            RenderIntent.parse("[]")

    def test_oversize_rejected(self):
        with self.assertRaises(ValueError):
            RenderIntent.parse(" " * 65537)
