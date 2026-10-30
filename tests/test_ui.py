import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import shutil
import tempfile
import time
import unittest
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication

    from fonesi_edit.app import MainWindow
except ImportError:
    QApplication = None
from fonesi_edit.process import run_bounded


@unittest.skipIf(QApplication is None, "Qt unavailable; UI not verified")
class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        if self.window.worker:
            self.window.cancel_work()
            self.wait_worker()
        self.window.close()
        self.app.processEvents()

    def wait_worker(self):
        deadline = time.monotonic() + 15
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertIsNone(self.window.worker)

    def test_empty_and_nonrunning_cancel(self):
        self.assertFalse(self.window.export.isEnabled())
        self.assertFalse(self.window.cancel_button.isEnabled())
        self.window.cancel_work()
        self.assertIsNone(self.window.worker)

    def test_double_start_and_close_cancel(self):
        def operation(cancel):
            while not cancel.wait(0.01):
                pass
            raise ValueError("CANCELED")

        self.assertTrue(self.window.start(operation, lambda r: None))
        self.assertFalse(self.window.start(operation, lambda r: None))
        self.window.close()
        self.assertTrue(self.window.closing)
        self.wait_worker()
        self.assertFalse(self.window.isVisible())

    def test_real_import_export(self):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg or not shutil.which("ffprobe"):
            self.skipTest("Media tools unavailable")
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "synthetic.mp4"
            output = Path(folder) / "output.mp4"
            self.assertEqual(
                run_bounded(
                    [
                        ffmpeg,
                        "-v",
                        "error",
                        "-n",
                        "-f",
                        "lavfi",
                        "-i",
                        "testsrc2=s=320x180:r=24:d=1",
                        "-c:v",
                        "libx264",
                        str(source),
                    ]
                ).status,
                "OK",
            )
            self.assertTrue(self.window.load_source(source))
            self.wait_worker()
            self.assertEqual(self.window.list.count(), 1)
            self.assertTrue(self.window.export.isEnabled())
            self.assertFalse(self.window.preview.pixmap().isNull())
            self.assertTrue(self.window.export_to(output))
            self.wait_worker()
            self.assertTrue(output.is_file())
            self.assertIn("Đã kiểm tra", self.window.status.text())
            self.assertTrue(self.window.export_to(output))
            self.wait_worker()
            self.assertIn("FileExistsError", self.window.status.text())

    def test_invalid_trim_disables_export(self):
        from fractions import Fraction

        from fonesi_edit.media import MediaInfo

        self.window.loaded(
            (Path("/synthetic.mp4"), MediaInfo(Fraction(2), ("video",)), b"")
        )
        self.window.start_time.setValue(1.5)
        self.window.end_time.setValue(1)
        self.assertFalse(self.window.export.isEnabled())
        self.window.end_time.setValue(2)
        self.assertTrue(self.window.export.isEnabled())
        self.assertEqual(self.window.edits[0], (1.5, 2.0, 1.0))
        self.window.end_time.setValue(3)
        self.assertFalse(self.window.export.isEnabled())

    def test_project_save_open_retains_unprobed_media(self):
        from fractions import Fraction

        from fonesi_edit.media import MediaInfo

        with tempfile.TemporaryDirectory() as folder:
            self.window.loaded(
                (Path(folder) / "missing.mp4", MediaInfo(Fraction(2), ("video",)), b"")
            )
            self.window.start_time.setValue(0.5)
            project = Path(folder) / "saved.fonesi"
            self.assertTrue(self.window.save_project_to(project))
            self.wait_worker()
            self.assertTrue(project.is_file())
            self.assertFalse(self.window.open_project_path(project))
            self.assertTrue(self.window.open_project_path(project, replace=True))
            self.wait_worker()
            self.assertIsNone(self.window.media[0][1])
            self.assertFalse(self.window.export.isEnabled())
            self.assertEqual(self.window.edits[0], (0.5, 2.0, 1.0))
            self.assertEqual(self.window.list.count(), 1)

    def test_unedited_project_preserves_rational_time(self):
        from fractions import Fraction as F

        from fonesi_edit.project import Project, ProjectMedia
        from fonesi_edit.timing import ClipMap, Interval

        project = Project(
            "12345678-1234-5678-1234-567812345678",
            "Exact",
            (
                ProjectMedia(
                    "22345678-1234-5678-1234-567812345678",
                    "/missing.mp4",
                    ClipMap(Interval(F(1, 3), F(7, 3)), F(3, 2)),
                ),
            ),
        )
        self.window.project_loaded(project)
        self.assertEqual(self.window.current_project(), project)

    def test_untrusted_labels_are_plain_text(self):
        from PySide6.QtCore import Qt

        for label in (self.window.status, self.window.details, self.window.preview):
            self.assertEqual(label.textFormat(), Qt.PlainText)

    def test_foreign_path_preserved_and_not_probed(self):
        import os

        from fonesi_edit.project import Project, ProjectMedia

        foreign = (
            "/foreign/source.mp4" if os.name == "nt" else "C:\\foreign\\source.mp4"
        )
        project = Project(
            "12345678-1234-5678-1234-567812345678",
            "Foreign",
            (ProjectMedia("22345678-1234-5678-1234-567812345678", foreign),),
        )
        self.window.project_loaded(project)
        self.assertEqual(self.window.current_project(), project)
        self.assertFalse(self.window.inspect_selected())
        self.assertIsNone(self.window.worker)

    def test_deselection_clears_implicit_export_target(self):
        from fractions import Fraction

        from fonesi_edit.media import MediaInfo

        self.window.loaded(
            (Path("/source.mp4"), MediaInfo(Fraction(2), ("video",)), b"")
        )
        self.assertTrue(self.window.export.isEnabled())
        self.window.list.setCurrentRow(-1)
        self.assertIsNone(self.window.selected)
        self.assertFalse(self.window.export.isEnabled())
        self.assertFalse(self.window.export_to(Path("/must-not-create.mp4")))
        self.assertEqual(len(self.window.media), 1)
        self.window.list.setCurrentRow(0)
        self.assertTrue(self.window.export.isEnabled())
