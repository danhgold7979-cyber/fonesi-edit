import tempfile
import unittest
from fractions import Fraction as F
from pathlib import Path

from fonesi_edit.project import Project, ProjectMedia, load_project, save_new
from fonesi_edit.timing import ClipMap, Interval


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.project = Project(
            "12345678-1234-5678-1234-567812345678",
            "Dự án thử",
            (
                ProjectMedia(
                    "22345678-1234-5678-1234-567812345678",
                    "/missing/source.mp4",
                    ClipMap(Interval(F(1, 3), F(7, 3)), F(3, 2)),
                ),
            ),
        )

    def test_roundtrip_exact(self):
        self.assertEqual(Project.decode(self.project.encode()), self.project)

    def test_missing_media_reference_retained(self):
        self.assertEqual(
            Project.decode(self.project.encode()).media[0].source, "/missing/source.mp4"
        )

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.fonesi"
            save_new(self.project, path)
            before = path.read_bytes()
            self.assertEqual(load_project(path), self.project)
            with self.assertRaises(FileExistsError):
                save_new(self.project, path)
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(list(Path(folder).glob(".fonesi-project-*")))

    def test_duplicate_key(self):
        with self.assertRaises(ValueError):
            Project.decode(self.project.encode()[:-1] + b',"schema":1}')

    def test_secret_unknown_field(self):
        with self.assertRaises(ValueError):
            Project.decode(self.project.encode()[:-1] + b',"api_key":"secret"}')

    def test_future_version(self):
        with self.assertRaises(ValueError):
            Project.decode(self.project.encode().replace(b'"schema":1', b'"schema":2'))

    def test_nested_unknown(self):
        with self.assertRaises(ValueError):
            Project.decode(
                self.project.encode().replace(b'"edit":{', b'"edit":{"token":"secret",')
            )

    def test_duplicate_media_ids(self):
        with self.assertRaises(ValueError):
            Project(self.project.id, "Title", self.project.media * 2)

    def test_size_bound(self):
        with self.assertRaises(ValueError):
            Project.decode(b" " * 4194305)
