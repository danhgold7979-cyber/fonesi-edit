"""Bounded, source-time thumbnail cache for the editor timeline.

These are source thumbnails, not the exported composition's reference frames.
The source media is never modified. Cache files are created in a caller-owned
workspace and published only after decoding succeeds.
"""
from pathlib import Path
import hashlib
import json
import math
import os
import subprocess
import time
from uuid import uuid4

from PySide6.QtGui import QImageReader

from .prototypes.media import probe
from .prototypes.tools import locate_tool


def thumbnail_identity(clip, count=3):
    if not 1 <= count <= 4:
        raise ValueError('Thumbnail count must be between 1 and 4')
    path=Path(clip.path).resolve(strict=True)
    info=path.stat()
    spec=[str(path),info.st_size,info.st_mtime_ns,clip.start,clip.end,
          clip.source_duration,clip.speed,count,160,90]
    return hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()


def thumbnail_times(clip, source_duration, count=3):
    if not 1 <= count <= 4 or not math.isfinite(source_duration) or source_duration<=0:
        raise ValueError('Invalid thumbnail count or media duration')
    start=float(clip.start)
    end=min(float(clip.end if clip.end is not None else source_duration),source_duration)
    if not math.isfinite(start) or not math.isfinite(end) or end<=start:
        raise ValueError('Clip has no playable interval')
    span=end-start
    # Sample inside, not at the exact end where FFmpeg may find no frame.
    return [min(source_duration-.001,start+(i+.5)/count*span)
            for i in range(count)]


def thumbnail_strip(clip, directory, cancel=None, count=3):
    """Generate a few small verified PNGs using FFmpeg, with cancellation."""
    source=Path(clip.path).resolve(strict=True)
    identity=thumbnail_identity(clip,count)
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    targets=[directory/f'{identity}-{i}.png' for i in range(count)]
    if not all(_valid_png(path) for path in targets):
        duration=clip.source_duration
        if duration is None:
            duration=probe(source).duration
        times=thumbnail_times(clip,duration,count)
        ffmpeg=locate_tool('ffmpeg')
        if not ffmpeg:
            raise FileNotFoundError('FFmpeg required for timeline thumbnails')
        for index,(second,target) in enumerate(zip(times,targets,strict=True)):
            if cancel is not None and cancel.is_set():
                raise RuntimeError('Thumbnail generation canceled')
            if _valid_png(target):
                continue
            temporary=directory/f'.fonesi-thumbnail-{uuid4().hex}.png'
            try:
                command=[ffmpeg,'-v','error','-nostdin','-n','-ss',f'{second:.6f}',
                         '-i',str(source),'-frames:v','1','-threads','1',
                         '-vf','scale=160:90:force_original_aspect_ratio=decrease',
                         str(temporary)]
                process=subprocess.Popen(command,stdin=subprocess.DEVNULL,
                                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                start=time.monotonic()
                try:
                    while process.poll() is None:
                        if cancel is not None and cancel.is_set():
                            raise RuntimeError('Thumbnail generation canceled')
                        if time.monotonic()-start>20:
                            raise TimeoutError('Thumbnail extraction time budget exceeded')
                        time.sleep(.05)
                    if process.returncode:
                        raise RuntimeError('FFmpeg could not decode timeline frame')
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            process.kill();process.wait(timeout=3)
                if not _valid_png(temporary):
                    raise RuntimeError('Thumbnail frame not readable')
                os.replace(temporary,target)
            finally:
                temporary.unlink(missing_ok=True)
    if not all(_valid_png(path) for path in targets):
        raise RuntimeError('Thumbnail cache incomplete')
    return {'key':identity,'frames':[str(path) for path in targets]}


def _valid_png(path):
    if not path.is_file() or path.stat().st_size<64:
        return False
    reader=QImageReader(str(path))
    if not reader.canRead():
        return False
    image=reader.read()
    return not image.isNull() and image.width()<=160 and image.height()<=90
