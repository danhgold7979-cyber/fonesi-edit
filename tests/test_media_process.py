import hashlib
import json
from fractions import Fraction
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import wave
from fonesi_edit.media import parse_probe, probe
from fonesi_edit.process import run_bounded

class MediaTests(unittest.TestCase):
    def test_exact_duration(self):
        self.assertEqual(parse_probe(b'{"format":{"duration":"1.001"},"streams":[{"codec_type":"audio"}]}').duration,Fraction(1001,1000))
    def test_bad_payloads(self):
        for data in [b'{}',b'[]',b'garbage',b'x'*65537,b'{"format":{"duration":"NaN"},"streams":[]}']:
            with self.subTest(data=data[:40]),self.assertRaises(ValueError): parse_probe(data)
    def test_nonmedia_stream(self):
        with self.assertRaises(ValueError): parse_probe(b'{"format":{"duration":"1"},"streams":[{"codec_type":"subtitle"}]}')
    def test_real_wave(self):
        ffprobe=shutil.which('ffprobe')
        if not ffprobe: self.skipTest('ffprobe unavailable; real media not verified')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'source.wav'
            with wave.open(str(path),'wb') as w:
                w.setparams((1,2,8000,0,'NONE','not compressed'));w.writeframes(b'\0\0'*8000)
            before=hashlib.sha256(path.read_bytes()).digest()
            self.assertEqual(probe(path,Path(ffprobe)).duration,Fraction(1))
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(),before)

class ProcessTests(unittest.TestCase):
    def test_success(self):
        result=run_bounded([sys.executable,'-c','print("ok")'])
        self.assertEqual(result.status,'OK');self.assertEqual(result.stdout.strip(),b'ok')
    def test_failure_does_not_return_private_output(self):
        result=run_bounded([sys.executable,'-c','print("private");raise SystemExit(2)'])
        self.assertEqual(result.status,'NONZERO_EXIT');self.assertEqual(result.stdout,b'')
    def test_timeout(self):
        result=run_bounded([sys.executable,'-c','import time;time.sleep(5)'],timeout=.05)
        self.assertEqual(result.status,'TIMEOUT')
    def test_output_cap(self):
        result=run_bounded([sys.executable,'-c','print("a"*100000)'],limit=1000)
        self.assertEqual(result.status,'OUTPUT_LIMIT');self.assertEqual(result.stdout,b'')
    def test_explicit_executable(self):
        with self.assertRaises(ValueError):run_bounded(['python','-V'])
