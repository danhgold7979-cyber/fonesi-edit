import hashlib
from fractions import Fraction
from pathlib import Path
import shutil
import tempfile
import unittest
from fonesi_edit.process import run_bounded
from fonesi_edit.render import render_cpu

class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ffmpeg=shutil.which('ffmpeg');cls.ffprobe=shutil.which('ffprobe')
        if not cls.ffmpeg or not cls.ffprobe:raise unittest.SkipTest('Real FFmpeg tools unavailable')
    def test_real_video_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.mp4';dest=Path(folder)/'result.mp4'
            result=run_bounded([self.ffmpeg,'-v','error','-n','-f','lavfi','-i',
                'color=c=blue:s=64x64:r=24:d=1','-c:v','libx264','-pix_fmt','yuv420p',str(source)])
            self.assertEqual(result.status,'OK')
            before=hashlib.sha256(source.read_bytes()).digest()
            artifact=render_cpu(source,dest,Path(self.ffmpeg),Path(self.ffprobe),duration_tolerance=Fraction(1,10))
            self.assertEqual(artifact.digest,hashlib.sha256(dest.read_bytes()).hexdigest())
            self.assertEqual(before,hashlib.sha256(source.read_bytes()).digest())
            saved=dest.read_bytes()
            with self.assertRaises(FileExistsError):
                render_cpu(source,dest,Path(self.ffmpeg),Path(self.ffprobe),duration_tolerance=Fraction(1,10))
            self.assertEqual(dest.read_bytes(),saved)
            self.assertFalse(list(Path(folder).glob('.fonesi-render-*')))
    def test_bad_source_no_output(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'bad.mp4';dest=Path(folder)/'result.mp4';source.write_bytes(b'bad')
            with self.assertRaises(ValueError):
                render_cpu(source,dest,Path(self.ffmpeg),Path(self.ffprobe),duration_tolerance=Fraction(1,10))
            self.assertFalse(dest.exists());self.assertEqual(source.read_bytes(),b'bad')
