import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import shutil
import tempfile
import time
from pathlib import Path
import unittest
try:
    from PySide6.QtWidgets import QApplication
    from fonesi_edit.app import MainWindow
except ImportError:
    QApplication=None
from fonesi_edit.process import run_bounded

@unittest.skipIf(QApplication is None,'Qt unavailable; UI not verified')
class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):self.window=MainWindow();self.window.show();self.app.processEvents()
    def tearDown(self):
        if self.window.worker:self.window.cancel_work();self.wait_worker()
        self.window.close();self.app.processEvents()
    def wait_worker(self):
        deadline=time.monotonic()+15
        while self.window.worker is not None and time.monotonic()<deadline:
            self.app.processEvents();time.sleep(.01)
        self.assertIsNone(self.window.worker)
    def test_empty_and_nonrunning_cancel(self):
        self.assertFalse(self.window.export.isEnabled());self.assertFalse(self.window.cancel_button.isEnabled())
        self.window.cancel_work();self.assertIsNone(self.window.worker)
    def test_double_start_and_close_cancel(self):
        def operation(cancel):
            while not cancel.wait(.01):pass
            raise ValueError('CANCELED')
        self.assertTrue(self.window.start(operation,lambda r:None))
        self.assertFalse(self.window.start(operation,lambda r:None))
        self.window.close();self.assertTrue(self.window.closing);self.wait_worker()
        self.assertFalse(self.window.isVisible())
    def test_real_import_export(self):
        ffmpeg=shutil.which('ffmpeg')
        if not ffmpeg or not shutil.which('ffprobe'):self.skipTest('Media tools unavailable')
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'synthetic.mp4';output=Path(folder)/'output.mp4'
            self.assertEqual(run_bounded([ffmpeg,'-v','error','-n','-f','lavfi','-i','testsrc2=s=320x180:r=24:d=1','-c:v','libx264',str(source)]).status,'OK')
            self.assertTrue(self.window.load_source(source));self.wait_worker()
            self.assertEqual(self.window.list.count(),1);self.assertTrue(self.window.export.isEnabled())
            self.assertFalse(self.window.preview.pixmap().isNull())
            self.assertTrue(self.window.export_to(output));self.wait_worker()
            self.assertTrue(output.is_file());self.assertIn('Đã kiểm tra',self.window.status.text())
            self.assertTrue(self.window.export_to(output));self.wait_worker()
            self.assertIn('FileExistsError',self.window.status.text())

    def test_invalid_trim_disables_export(self):
        from fractions import Fraction
        from fonesi_edit.media import MediaInfo
        self.window.loaded((Path('/synthetic.mp4'),MediaInfo(Fraction(2),('video',)),b''))
        self.window.start_time.setValue(1.5);self.window.end_time.setValue(1)
        self.assertFalse(self.window.export.isEnabled())
        self.window.end_time.setValue(2)
        self.assertTrue(self.window.export.isEnabled())
        self.assertEqual(self.window.edits[0],(1.5,2.0,1.0))
        self.window.end_time.setValue(3)
        self.assertFalse(self.window.export.isEnabled())
