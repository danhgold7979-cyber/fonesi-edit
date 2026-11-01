from pathlib import Path
import struct,shutil
from fractions import Fraction as F
from fonesi_edit.jobs.process import run_owned
from fonesi_edit.media.probe import inspect_media
from fonesi_edit.media.validation import validate_media,ExpectedStream,MediaValidationError
root=Path('runtime/media-decode-negative');root.mkdir(exist_ok=True)
path=root/'generated.mp4'
assert not path.exists(),'Do not overwrite evidence'
ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
r=run_owned([ffmpeg,'-nostdin','-v','error','-f','lavfi','-i','color=c=red:s=64x48:r=25:d=1','-c:v','libx264','-pix_fmt','yuv420p',str(path)],timeout=30)
assert r.returncode==0
raw=bytearray(path.read_bytes());at=0
while at+8<=len(raw):
    size=struct.unpack('>I',raw[at:at+4])[0];kind=raw[at+4:at+8]
    if size<8:raise ValueError('Unsupported fixture box')
    if kind==b'mdat':
        raw[at+8:at+size]=b'\0'*(size-8);break
    at+=size
else:raise AssertionError('No mdat')
damaged=root/'damaged-payload.mp4';damaged.write_bytes(raw)
metadata=inspect_media(damaged,ffprobe).metadata()
assert metadata['streams'][0]['codec_name']=='h264'
expected=(ExpectedStream(0,'video','h264',F(0),F(1),F(1,25),width=64,height=48,frame_rate=F(25)),)
try:validate_media(damaged,ffprobe,ffmpeg,expected,timeout=30)
except MediaValidationError as exc:
    print(str(exc));assert str(exc)=='Output failed full decode'
else:raise AssertionError('Corrupt payload accepted')
assert damaged.read_bytes()==raw
print('Actual readable-metadata/corrupt-payload negative PASS; source unmodified')
