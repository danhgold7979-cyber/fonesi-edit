"""Narrow CPU proof renderer; no timeline, subtitle or platform support implied."""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import os
import tempfile
from fonesi_edit.media import probe
from fonesi_edit.process import run_bounded

@dataclass(frozen=True)
class Artifact:
    path: Path
    digest: str
    duration: Fraction
    size: int


def render_cpu(source: Path, destination: Path, ffmpeg: Path, ffprobe: Path,
               *, duration_tolerance: Fraction) -> Artifact:
    if not isinstance(duration_tolerance,Fraction) or not 0<=duration_tolerance<=1:
        raise ValueError('EXPLICIT_DURATION_POLICY_REQUIRED')
    source=source.resolve(strict=True)
    destination=destination.absolute()
    if destination.suffix.lower()!='.mp4' or not destination.parent.is_dir():
        raise ValueError('INVALID_DESTINATION')
    if destination.exists() or destination.is_symlink(): raise FileExistsError('OUTPUT_EXISTS')
    original=probe(source,ffprobe)
    if 'video' not in original.stream_types: raise ValueError('VIDEO_REQUIRED')
    with tempfile.TemporaryDirectory(prefix='.fonesi-render-',dir=destination.parent) as folder:
        staged=Path(folder)/'validated.mp4'
        result=run_bounded([str(ffmpeg),'-nostdin','-v','error','-n',
            '-protocol_whitelist','file,pipe','-i',str(source),
            '-map','0:v:0','-map','0:a:0?','-c:v','libx264','-pix_fmt','yuv420p',
            '-c:a','aac','-movflags','+faststart',str(staged)],timeout=60)
        if result.status!='OK': raise ValueError('ENCODE_'+result.status)
        output=probe(staged,ffprobe)
        if 'video' not in output.stream_types or abs(output.duration-original.duration)>duration_tolerance:
            raise ValueError('OUTPUT_DURATION_OR_STREAM_MISMATCH')
        if 'audio' in original.stream_types and 'audio' not in output.stream_types:
            raise ValueError('OUTPUT_AUDIO_MISSING')
        decoded=run_bounded([str(ffmpeg),'-nostdin','-v','error','-protocol_whitelist','file,pipe',
            '-i',str(staged),'-map','0:v:0','-map','0:a:0?','-f','null','-'],timeout=60)
        if decoded.status!='OK': raise ValueError('DECODE_'+decoded.status)
        digest=sha256()
        with staged.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''): digest.update(chunk)
            os.fsync(stream.fileno())
        size=staged.stat().st_size
        if size<=0: raise ValueError('EMPTY_OUTPUT')
        # Never replace an existing name. Unsupported filesystems fail here.
        os.link(staged,destination)
        return Artifact(destination,digest.hexdigest(),output.duration,size)
