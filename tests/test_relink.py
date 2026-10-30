import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from fonesi_edit.app import MainWindow
from fonesi_edit.media import MediaInfo
from fonesi_edit.project import Project, ProjectMedia, load_project, save_new
from fonesi_edit.timing import ClipMap, Interval


class RelinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.project = Project(
            "12345678-1234-5678-1234-567812345678",
            "Test",
            (
                ProjectMedia(
                    "22345678-1234-5678-1234-567812345678",
                    "Z:\\missing\\source.mp4",
                    ClipMap(Interval(F(1, 3), F(7, 3)), F(3, 2)),
                ),
            ),
        )
        self.window.project_loaded(self.project)
        self.path = str(Path(tempfile.gettempdir()).absolute() / "replacement.mp4")

    def tearDown(self):
        self.window.close()
        self.app.processEvents()

    def relink(self, path=None, **kwargs):
        return self.window.relink_media(
            0,
            path or self.path,
            expected_id=kwargs.get("id", self.project.media[0].id),
            expected_reference=kwargs.get("reference", self.project.media[0].source),
        )

    def test_identity_exact_edit_and_proof_invalidation(self):
        self.window.source_hashes[0] = "a" * 64
        self.assertTrue(self.relink())
        current = self.window.current_project()
        self.assertEqual(current.id, self.project.id)
        self.assertEqual(current.media[0].id, self.project.media[0].id)
        self.assertEqual(current.media[0].edit, self.project.media[0].edit)
        self.assertEqual(current.media[0].source, self.path)
        self.assertIsNone(self.window.media[0][1])
        self.assertFalse(self.window.source_hashes)
        self.assertFalse(self.window.export.isEnabled())
        self.assertEqual(self.window.list.item(0).text(), "replacement.mp4")

    def test_undo_restores_foreign_reference_but_not_old_proof(self):
        self.assertTrue(self.relink())
        self.window.source_hashes[0] = "b" * 64
        self.assertTrue(self.window.undo_relink())
        self.assertEqual(self.window.current_project(), self.project)
        self.assertFalse(self.window.source_hashes)
        self.assertFalse(self.window.undo_relink())

    def test_stale_invalid_busy_and_noop(self):
        for kwargs in ({"id": "wrong"}, {"reference": "wrong"}):
            self.assertFalse(self.relink(**kwargs))
        for path in (
            "relative.mp4",
            "https://example.com/x",
            "/bad\x00name",
            "/" + "a" * 4096,
        ):
            self.assertFalse(self.relink(path))
        self.window.closing = True
        self.assertFalse(self.relink())
        self.window.closing = False
        self.window.worker = object()
        self.assertFalse(self.relink())
        self.window.worker = None
        self.assertEqual(self.window.current_project(), self.project)
        self.assertTrue(self.relink())
        self.assertFalse(self.relink(reference=self.path))
        self.assertEqual(len(self.window.relink_history), 1)

    def test_chooser_cancel_and_stale_selection(self):
        with patch(
            "fonesi_edit.app.QFileDialog.getOpenFileName", return_value=("", "")
        ):
            self.assertFalse(self.window.choose_relink())
        self.assertFalse(self.window.relink_history)

        def change(*args):
            self.window.source_refs[0] = "/changed.mp4"
            return self.path, ""

        with patch("fonesi_edit.app.QFileDialog.getOpenFileName", side_effect=change):
            self.assertFalse(self.window.choose_relink())
        self.assertEqual(self.window.source_refs[0], "/changed.mp4")

    def test_save_reopen_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mp4"
            source.write_bytes(b"owned test marker, not a media verification")
            self.assertTrue(self.relink(str(source)))
            destination = Path(folder) / "project.fonesi"
            save_new(self.window.current_project(), destination)
            project = load_project(destination)
            self.window.project_loaded(project)
            self.assertEqual(project.media[0].source, str(source))
            self.assertFalse(self.window.relink_history)
            self.assertIsNone(self.window.selected)
            self.assertEqual(
                source.read_bytes(), b"owned test marker, not a media verification"
            )

    def test_reinspection_keeps_invalid_trim_and_blocks_export(self):
        self.assertTrue(self.relink())
        self.window.loaded(
            (Path(self.path), MediaInfo(F(1), ("video",)), b""), 0, source_sha="c" * 64
        )
        self.assertEqual(
            self.window.current_project().media[0].edit, self.project.media[0].edit
        )
        self.assertFalse(self.window.export.isEnabled())
        self.assertEqual(self.window.source_refs[0], self.path)
