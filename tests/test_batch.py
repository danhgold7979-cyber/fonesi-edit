from fractions import Fraction
from pathlib import Path
import shutil
import tempfile
import unittest
from fonesi_edit.batch import scan,render_batch
from fonesi_edit.process import run_bounded

class BatchTests(unittest.TestCase):
    def test_scan_dedup_and_output_exclusion(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);out=root/'output';out.mkdir();(root/'a.mp4').write_bytes(b'a');(out/'old.mp4').write_bytes(b'old')
            result=scan((root,root),out)
            self.assertEqual(result.status,'COMPLETE');self.assertEqual(len(result.items),1)
    def test_limits_are_partial(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'a.mp4').touch();(root/'b.mp4').touch()
            self.assertEqual(scan((root,),root/'output',max_items=1).status,'PARTIAL')
            self.assertEqual(scan((root,),root/'output',max_visited=1).status,'PARTIAL')
    def test_cancel_scan(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.assertEqual(scan((root,),root/'out',cancel=lambda:True).status,'CANCELED')
    def test_reject_output_containing_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);child=root/'input';child.mkdir()
            with self.assertRaises(ValueError):scan((child,),root)
    def test_real_batch_failure_isolated_and_collision(self):
        ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
        if not ffmpeg or not ffprobe:self.skipTest('Media tools unavailable')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'input';out=Path(folder)/'out';root.mkdir();out.mkdir()
            source=root/'clip.mp4'
            self.assertEqual(run_bounded([ffmpeg,'-v','error','-n','-f','lavfi','-i','color=blue:s=64x64:r=24:d=1','-c:v','libx264',str(source)]).status,'OK')
            shutil.copyfile(source,root/'second.mp4');(root/'bad.mp4').write_bytes(b'bad')
            items=scan((root,),out).items
            result=render_batch(items,out,Path(ffmpeg),Path(ffprobe),duration_tolerance=Fraction(1,10))
            self.assertEqual(len(result.artifacts),2);self.assertEqual(len(result.failures),1);self.assertEqual(result.status,'PARTIAL')
            again=render_batch(items,out,Path(ffmpeg),Path(ffprobe),duration_tolerance=Fraction(1,10))
            self.assertEqual(len(again.artifacts),0);self.assertEqual(sum(code=='OUTPUT_EXISTS' for _,code in again.failures),2)
            self.assertEqual((root/'bad.mp4').read_bytes(),b'bad')

    def test_symlink_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source.mp4';source.write_bytes(b'x')
            try:(root/'link.mp4').symlink_to(source)
            except OSError:self.skipTest('Symlink creation unavailable; no symlink acceptance claim')
            result=scan((root,),root/'out')
            self.assertEqual(len(result.items),1);self.assertEqual(result.status,'PARTIAL');self.assertIn('SYMLINK_SKIPPED',result.warnings)
