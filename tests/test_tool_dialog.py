import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import threading
import time
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from fonesi_edit.app import MainWindow
from fonesi_edit.media import MediaInfo
from fonesi_edit.media_tools import MediaTools
from fonesi_edit.tool_dialog import ToolDialog


class ToolDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def tools(self):
        return MediaTools(
            Path("/trusted/ffmpeg"), Path("/trusted/ffprobe"), "7.1", "7.1"
        )

    def wait(self, window):
        deadline = time.monotonic() + 5
        while window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        self.assertIsNone(window.worker)

    def test_draft_invalidation_and_fresh_busy_apply_guard(self):
        applied = []
        busy = [False]
        window = ToolDialog(
            "/one", "/two", lambda info: applied.append(info) or True, lambda: busy[0]
        )
        try:
            draft = window.draft()
            window.checked(draft, self.tools(), window.revision)
            self.assertTrue(window.apply_button.isEnabled())
            window.fields[0].setText("/changed")
            self.assertIsNone(window.verified)
            window.checked(draft, self.tools(), window.revision)
            self.assertIsNone(window.verified)
            window.checked(window.draft(), self.tools(), window.revision)
            busy[0] = True
            self.assertFalse(window.apply_selection())
            self.assertFalse(applied)
            busy[0] = False
            self.assertTrue(window.apply_selection())
            self.assertEqual(len(applied), 1)
        finally:
            window.close()

    def test_edited_then_restored_draft_rejects_old_generation(self):
        window = ToolDialog("/one", "/two", lambda info: True, lambda: False)
        try:
            old, revision = window.draft(), window.revision
            window.fields[0].setText("/changed")
            window.fields[0].setText("/one")
            self.assertEqual(window.draft(), old)
            window.checked(old, self.tools(), revision)
            self.assertIsNone(window.verified)
            self.assertFalse(window.apply_button.isEnabled())
        finally:
            window.close()

    def test_cancel_close_never_retains_late_result(self):
        window = ToolDialog("/one", "/two", lambda info: True, lambda: False)
        entered = threading.Event()

        def slow(*args, cancel=None):
            entered.set()
            cancel.wait(3)
            return self.tools()

        try:
            window.show()
            with patch("fonesi_edit.tool_dialog.inspect_tools", slow):
                self.assertTrue(window.check_tools())
                self.assertTrue(entered.wait(2))
                self.assertFalse(window.check_tools())
                window.reject()
                self.assertTrue(window.closing)
                self.wait(window)
            self.assertFalse(window.isVisible())
            self.assertIsNone(window.verified)
        finally:
            window.cancel_work()
            if window.worker:
                self.wait(window)
            window.close()

    def test_parent_paths_and_inspection_invalidation(self):
        parent = MainWindow()
        try:
            source = Path("/source.mp4")
            parent.loaded(
                (source, MediaInfo(Fraction(2), ("video",)), b""), source_sha="a" * 64
            )
            parent.open_batch()
            original_refs = dict(parent.source_refs)
            self.assertTrue(parent.apply_media_tools(self.tools()))
            self.assertFalse(parent.source_hashes)
            self.assertIsNone(parent.media[0][1])
            self.assertEqual(parent.source_refs, original_refs)
            self.assertFalse(parent.export.isEnabled())
            self.assertEqual(parent.batch_window.ffmpeg, str(self.tools().ffmpeg))
            sentinel = object()
            parent.worker = sentinel
            self.assertFalse(parent.apply_media_tools(self.tools()))
            parent.worker = None
        finally:
            parent.worker = None
            parent.close()

    def test_parent_close_resumes_after_tool_check_stops(self):
        parent = MainWindow()
        entered = threading.Event()

        def slow(*args, cancel=None):
            entered.set()
            cancel.wait(3)
            return self.tools()

        try:
            parent.show()
            self.assertTrue(parent.open_tools())
            dialog = parent.tool_window
            with patch("fonesi_edit.tool_dialog.inspect_tools", slow):
                self.assertTrue(dialog.check_tools())
                self.assertTrue(entered.wait(2))
                parent.close()
                self.assertTrue(parent.isVisible())
                self.wait(dialog)
                self.app.processEvents()
            self.assertFalse(parent.isVisible())
            self.assertFalse(dialog.isVisible())
            self.assertFalse(parent.closing)
        finally:
            if parent.tool_window and parent.tool_window.worker:
                parent.tool_window.cancel_work()
                self.wait(parent.tool_window)
            parent.close()
