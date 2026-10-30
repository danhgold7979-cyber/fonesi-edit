"""On-demand local playback proxies. Never substitute for compositor exports."""
from pathlib import Path
import hashlib
import json
import math
import os
import subprocess
import time
from uuid import uuid4

from .prototypes.media import probe
from .prototypes.tools import locate_tool

# Maximum proxy side in pixels, FFmpeg CRF. The original media stays untouched.
PROXY_LEVELS={'fast':(640,28),'balanced':(1280,25),'high':(1920,22)}


def proxy_identity(source,quality):
    if quality not in PROXY_LEVELS:
        raise ValueError('Unknown proxy quality')
    source=Path(source).resolve(strict=True)
    stat=source.stat()
    identity=[str(source),stat.st_size,stat.st_mtime_ns,
              quality,*PROXY_LEVELS[quality],2]
    return hashlib.sha256(json.dumps(identity).encode()).hexdigest()


def playback_proxy(source,directory,quality='fast',cancel=None):
    """Create a validated, atomically published MP4 proxy in a cache folder."""
    source=Path(source).resolve(strict=True)
    key=proxy_identity(source,quality)
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    target=directory/f'{key}.mp4'
    original=probe(source)
    if target.is_file():
        if _valid_proxy(target,original.duration):
            return {'key':key,'path':str(target),'quality':quality}
        target.unlink()
    if cancel and cancel.is_set():
        raise RuntimeError('Proxy canceled')
    maximum,crf=PROXY_LEVELS[quality]
    maximum=min(maximum,max(original.width,original.height))  # never upscale a source
    ffmpeg=locate_tool('ffmpeg')
    if not ffmpeg:
        raise FileNotFoundError('FFmpeg required to make local proxy')
    temporary=directory/f'.fonesi-proxy-{uuid4().hex}.mp4'
    cmd=[ffmpeg,'-v','error','-nostdin','-n','-i',str(source),
         '-map','0:v:0','-map','0:a:0?',
         '-vf',f'scale={maximum}:{maximum}:force_original_aspect_ratio=decrease:force_divisible_by=2',
         '-c:v','libx264','-threads','2','-preset','veryfast',
         '-crf',str(crf),'-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','128k','-movflags','+faststart',str(temporary)]
    process=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    started=time.monotonic()
    try:
        try:
            while process.poll() is None:
                if cancel and cancel.is_set():
                    raise RuntimeError('Proxy canceled')
                if time.monotonic()-started>240:
                    raise TimeoutError('Proxy encoding exceeded time budget')
                time.sleep(.1)
            if process.returncode!=0:
                raise RuntimeError('FFmpeg proxy encode failed')
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill();process.wait(timeout=3)
        if not _valid_proxy(temporary,original.duration,maximum):
            raise RuntimeError('Proxy validation failed; source file preserved')
        os.replace(temporary,target)
        return {'key':key,'path':str(target),'quality':quality}
    finally:
        temporary.unlink(missing_ok=True)


def _valid_proxy(path,duration,maximum=None):
    if not path.is_file() or path.stat().st_size<512:
        return False
    try:
        actual=probe(path)
    except (OSError,ValueError,RuntimeError):
        return False
    if maximum is not None and max(actual.width,actual.height)>maximum:
        return False
    return (math.isfinite(actual.duration) and
            abs(actual.duration-duration)<=max(.15,duration*.03))
