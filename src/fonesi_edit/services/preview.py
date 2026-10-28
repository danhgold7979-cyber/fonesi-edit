"""Background proxy, thumbnails and bounded waveform generation."""
from array import array
from pathlib import Path
import math
import tempfile
from ..core.model import Project,US,digest
from ..core.paths import publish_no_clobber
from ..core.process import run
from .media import tool,probe,validate_media
from .render import normalized_base,mix_audio


def proxy_key(project:Project):
    # Layer/text changes do not invalidate normalized source playback.
    return digest({'width':project.width,'height':project.height,'fps':project.fps,'assets':[a.__dict__ for a in project.assets],
                   'clips':[c.__dict__ for c in project.clips],'audio':[a.__dict__ for a in project.audio],
                   'settings':{k:project.settings.get(k) for k in ['mute_original','original_gain','normalize_audio']},'version':1})


def build_proxy(project:Project,target:Path,cancel=lambda:False):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.fonesi-proxy-',dir=target.parent) as d:
        directory=Path(d);base=normalized_base(project,directory,cancel)
        video=directory/'video.mp4'
        run([tool('ffmpeg'),'-v','error','-i',str(base),'-an','-c:v','libx264','-preset','ultrafast','-crf','25','-pix_fmt','yuv420p','-threads','2',str(video)],cancel=cancel,timeout=max(120,project.duration/US*15))
        out=directory/'proxy.mp4';mix_audio(base,video,project,out,cancel)
        validate_media(out,duration=project.duration,audio=True,cancel=cancel)
        if target.exists():return target
        return publish_no_clobber(out,target)


def waveform(path:Path,buckets=1000,cancel=lambda:False):
    if not 1<=buckets<=10000:raise ValueError('Waveform bucket count must be 1..10000')
    data=probe(path);duration=float(data.get('format',{}).get('duration',0))
    if not any(s['codec_type']=='audio' for s in data.get('streams',[])):return []
    with tempfile.TemporaryDirectory(prefix='fonesi-wave-') as d:
        raw=Path(d)/'mono.f32'
        run([tool('ffmpeg'),'-v','error','-i',str(path),'-vn','-ac','1','-ar','8000','-f','f32le',str(raw)],cancel=cancel,timeout=max(60,duration*3))
        total=raw.stat().st_size//4;stride=max(1,math.ceil(total/buckets));result=[]
        with raw.open('rb') as f:
            while block:=f.read(stride*4):
                samples=array('f');samples.frombytes(block)
                result.append({'min':min(samples,default=0),'max':max(samples,default=0),'rms':math.sqrt(sum(x*x for x in samples)/max(1,len(samples)))})
        return result
