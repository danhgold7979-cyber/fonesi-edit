import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import time
import unittest
from fractions import Fraction as F
from pathlib import Path

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from fonesi_edit.subtitle_editor import SubtitleEditor, SubtitleModel
except ImportError:
    QApplication = None
from fonesi_edit.subtitles import Cue, SubtitleDocument, parse_srt
from fonesi_edit.timing import Interval


@unittest.skipIf(QApplication is None, "Qt unavailable; subtitle UI not verified")
class SubtitleUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.doc = SubtitleDocument((Cue("c", Interval(F(0), F(2)), "Xin chào"),))

    def test_edit_undo_redo_and_lock(self):
        model = SubtitleModel(self.doc)
        self.assertTrue(model.setData(model.index(0, 3), "中文"))
        self.assertEqual(model.document.cues[0].text, "中文")
        model.undo()
        self.assertEqual(model.document, self.doc)
        model.redo()
        self.assertEqual(model.document.cues[0].text, "中文")
        self.assertTrue(model.setData(model.index(0, 4), Qt.Checked, Qt.CheckStateRole))
        self.assertTrue(model.document.cues[0].locked)

    def test_invalid_edit_keeps_original(self):
        model = SubtitleModel(self.doc)
        self.assertFalse(model.setData(model.index(0, 1), "00:00:03,000"))
        self.assertEqual(model.document, self.doc)
        self.assertFalse(model.undo_stack)

    def test_history_bounded(self):
        model = SubtitleModel(self.doc)
        for i in range(110):
            model.setData(model.index(0, 3), str(i))
        self.assertEqual(len(model.undo_stack), 100)

    def test_dialog_file_roundtrip_collision(self):
        window = SubtitleEditor()
        window.show()

        def wait():
            end = time.monotonic() + 10
            while window.worker is not None and time.monotonic() < end:
                self.app.processEvents()
                time.sleep(0.01)
            self.assertIsNone(window.worker)

        try:
            with tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / "source.srt"
                output = Path(folder) / "new.srt"
                source.write_text(
                    "1\n00:00:00,000 --> 00:00:02,000\nXin chào\n", encoding="utf-8"
                )
                self.assertTrue(window.load_path(source))
                wait()
                self.assertEqual(window.model.document.cues[0].text, "Xin chào")
                window.model.setData(window.model.index(0, 3), "中文")
                self.assertTrue(window.save_path(output))
                wait()
                before = output.read_bytes()
                self.assertEqual(parse_srt(before).cues[0].text, "中文")
                window.model.setData(window.model.index(0, 3), "different")
                self.assertTrue(window.save_path(output))
                wait()
                self.assertEqual(output.read_bytes(), before)
                self.assertIn("FileExistsError", window.status.text())
        finally:
            if window.worker:
                wait()
            window.close()
            self.app.processEvents()

    def test_invalid_check_state_does_not_unlock(self):
        model = SubtitleModel(
            SubtitleDocument((Cue("c", Interval(F(0), F(2)), "x", True),))
        )
        self.assertFalse(model.setData(model.index(0, 4), 99, Qt.CheckStateRole))
        self.assertTrue(model.document.cues[0].locked)

    def test_find_wrap_replace_lock_and_single_undo(self):
        window = SubtitleEditor()
        doc = SubtitleDocument(
            (
                Cue("a", Interval(F(0), F(1)), "Xin chào"),
                Cue("b", Interval(F(1), F(2)), "Khác"),
                Cue("c", Interval(F(2), F(3)), "Xin chào", True),
            )
        )
        try:
            window.model.replace(doc, remember=False)
            window.search_text.setText("Xin")
            for expected in (0, 2, 0):
                self.assertTrue(window.find_next())
                self.assertEqual(window.table.currentIndex().row(), expected)
            window.replacement_text.setText("Chào")
            self.assertTrue(window.replace_all())
            self.assertEqual(window.model.document.cues[0].text, "Chào chào")
            self.assertEqual(window.model.document.cues[2].text, "Xin chào")
            self.assertEqual(len(window.model.undo_stack), 1)
            window.model.undo()
            self.assertEqual(window.model.document, doc)
            window.search_text.setText("not present")
            self.assertFalse(window.replace_all())
            self.assertFalse(window.model.undo_stack)
        finally:
            window.close()

    def test_escape_waits_and_reopen_does_not_autoclose(self):
        import threading

        window = SubtitleEditor()
        release = threading.Event()

        def wait():
            deadline = time.monotonic() + 5
            while window.worker is not None and time.monotonic() < deadline:
                self.app.processEvents()
                time.sleep(0.01)
            self.assertIsNone(window.worker)

        try:
            window.show()
            self.assertTrue(window.start(lambda: release.wait(3), lambda result: None))
            window.reject()
            self.assertTrue(window.closing)
            self.assertTrue(window.isVisible())
            release.set()
            wait()
            self.assertFalse(window.isVisible())
            self.assertFalse(window.closing)
            window.show()
            self.assertTrue(window.start(lambda: True, lambda result: None))
            wait()
            self.assertTrue(window.isVisible())
        finally:
            release.set()
            if window.worker:
                wait()
            window.close()
