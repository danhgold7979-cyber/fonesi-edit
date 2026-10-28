"""Probe/validate actual media rather than trusting extensions or exit status."""
from __future__ import annotations
from fractions import Fraction
from pathlib import Path
from PIL import Image
import json
import shutil
import os
import sys
from ..core.model import Asset, US
from ..core.paths import content_hash
from ..core.process import run


def tool(name: str) -> str:
    explicit=os.environ.get('FONESI_'+name.upper()+'_PATH')
    bundled=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'media/bin'/(name+('.exe' if os.name=='nt' else ''))
    p=explicit or (str(bundled) if bundled.is_file() else shutil.which(name))
    if explicit and not Path(explicit).is_file():raise FileNotFoundError('Selected tool path invalid; no silent fallback: '+explicit)
    if not p: raise FileNotFoundError(f'Thiếu {name}: mở Cài đặt → Công cụ')
    return p


def probe(path: Path, ffprobe=None) -> dict:
    return json.loads(run([ffprobe or tool('ffprobe'),'-v','error','-show_format','-show_streams','-of','json',str(path)],timeout=30))


def inspect_asset(path: Path, ffprobe=None) -> Asset:
    path=Path(path).resolve(); data=probe(path,ffprobe)
    streams=data.get('streams',[]); video=next((s for s in streams if s['codec_type']=='video'),{})
    audio=any(s['codec_type']=='audio' for s in streams)
    if not video and not audio: raise ValueError('No playable audio/video stream')
    duration=float(data.get('format',{}).get('duration',video.get('duration',0)))
    if duration<=0: raise ValueError('Missing/invalid media duration')
    fps=video.get('avg_frame_rate','25')
    if fps in {'0/0','0','N/A'}: fps='25'
    rotation=next((s.get('rotation',0) for s in video.get('side_data_list',[]) if 'rotation' in s),0)
    w,h=video.get('width',0),video.get('height',0)
    if abs(rotation)%180==90: w,h=h,w
    return Asset(str(path),fingerprint=content_hash(path),duration=round(duration*US),width=w,height=h,
                 fps=str(Fraction(fps)),has_audio=audio)


def validate_media(path: Path, *, duration: int | None = None, video=True, audio: bool | None = None,
                   tolerance=.15, decode=True, cancel=lambda:False) -> dict:
    data=probe(path); streams=data.get('streams',[])
    has_video=any(s['codec_type']=='video' for s in streams); has_audio=any(s['codec_type']=='audio' for s in streams)
    actual=float(data.get('format',{}).get('duration',0))
    if (video and not has_video) or (audio is True and not has_audio): raise ValueError('Required media track missing')
    if actual<=0: raise ValueError('Empty or invalid media')
    if duration is not None and abs(actual-duration/US)>tolerance: raise ValueError(f'Duration mismatch: {actual}s != {duration/US}s')
    if decode: run([tool('ffmpeg'),'-v','error','-xerror','-i',str(path),'-f','null','-'],cancel=cancel,timeout=max(60,actual*4))
    return {'validated':True,'duration':round(actual*US),'has_video':has_video,'has_audio':has_audio,'sha256':content_hash(path),'size':Path(path).stat().st_size}


def validate_image(path: Path) -> dict:
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:
        im.load(); width,height=im.size
        if width<=0 or height<=0: raise ValueError('Empty image')
    return {'validated':True,'width':width,'height':height,'sha256':content_hash(path),'size':Path(path).stat().st_size}


def thumbnail(path: Path, target: Path, time_us=0, width=640, cancel=lambda:False) -> Path:
    run([tool('ffmpeg'),'-v','error','-ss',str(time_us/US),'-i',str(path),'-frames:v','1','-vf',f'scale={width}:-2','-y',str(target)],cancel=cancel)
    return target
