"""Cancelable background waveform cache. The image represents the entire source."""
from pathlib import Path
import hashlib
import json
import subprocess
import time
from .prototypes.tools import locate_tool
from .render import audio_duration


def waveform(path,directory,cancel=None):
    path=Path(path).resolve();stat=path.stat();duration=audio_duration(path)
    key=hashlib.sha256(json.dumps([str(path),stat.st_size,stat.st_mtime_ns]).encode()).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);target=directory/(key+'.png')
    if target.is_file():return {'path':str(target),'duration':duration}
    temporary=directory/(key+'.part.png');temporary.unlink(missing_ok=True)
    command=[locate_tool('ffmpeg'),'-v','error','-nostdin','-y','-i',str(path),'-filter_complex','aformat=channel_layouts=mono,showwavespic=s=2048x64:colors=0x81d5be','-frames:v','1','-threads','1',str(temporary)]
    process=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);start=time.monotonic()
    try:
        while process.poll() is None:
            if cancel and cancel.is_set():raise RuntimeError('Waveform canceled')
            if time.monotonic()-start>120:raise TimeoutError('Waveform time budget exceeded')
            time.sleep(.05)
        if process.returncode or not temporary.is_file():raise ValueError('Không tạo được waveform cho nguồn này')
        temporary.replace(target);return {'path':str(target),'duration':duration}
    finally:
        if process.poll() is None:process.terminate();process.wait(timeout=5)
        temporary.unlink(missing_ok=True)
