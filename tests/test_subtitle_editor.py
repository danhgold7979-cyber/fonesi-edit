import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from fractions import Fraction as F
from pathlib import Path
import tempfile
import time
import unittest
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from fonesi_edit.subtitle_editor import SubtitleModel,SubtitleEditor
except ImportError:QApplication=None
from fonesi_edit.subtitles import Cue,SubtitleDocument,parse_srt
from fonesi_edit.timing import Interval

@unittest.skipIf(QApplication is None,'Qt unavailable; subtitle UI not verified')
class SubtitleUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):self.doc=SubtitleDocument((Cue('c',Interval(F(0),F(2)),'Xin chào'),))
    def test_edit_undo_redo_and_lock(self):
        model=SubtitleModel(self.doc)
        self.assertTrue(model.setData(model.index(0,3),'中文'))
        self.assertEqual(model.document.cues[0].text,'中文');model.undo();self.assertEqual(model.document,self.doc)
        model.redo();self.assertEqual(model.document.cues[0].text,'中文')
        self.assertTrue(model.setData(model.index(0,4),Qt.Checked,Qt.CheckStateRole));self.assertTrue(model.document.cues[0].locked)
    def test_invalid_edit_keeps_original(self):
        model=SubtitleModel(self.doc)
        self.assertFalse(model.setData(model.index(0,1),'00:00:03,000'))
        self.assertEqual(model.document,self.doc);self.assertFalse(model.undo_stack)
    def test_history_bounded(self):
        model=SubtitleModel(self.doc)
        for i in range(110):model.setData(model.index(0,3),str(i))
        self.assertEqual(len(model.undo_stack),100)
    def test_dialog_file_roundtrip_collision(self):
        window=SubtitleEditor();window.show()
        def wait():
            end=time.monotonic()+10
            while window.worker is not None and time.monotonic()<end:self.app.processEvents();time.sleep(.01)
            self.assertIsNone(window.worker)
        try:
            with tempfile.TemporaryDirectory() as folder:
                source=Path(folder)/'source.srt';output=Path(folder)/'new.srt'
                source.write_text('1\n00:00:00,000 --> 00:00:02,000\nXin chào\n',encoding='utf-8')
                self.assertTrue(window.load_path(source));wait()
                self.assertEqual(window.model.document.cues[0].text,'Xin chào')
                window.model.setData(window.model.index(0,3),'中文')
                self.assertTrue(window.save_path(output));wait();before=output.read_bytes()
                self.assertEqual(parse_srt(before).cues[0].text,'中文')
                window.model.setData(window.model.index(0,3),'different')
                self.assertTrue(window.save_path(output));wait()
                self.assertEqual(output.read_bytes(),before);self.assertIn('FileExistsError',window.status.text())
        finally:
            if window.worker:wait()
            window.close();self.app.processEvents()
