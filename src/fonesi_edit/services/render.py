"""Source-safe canonical CPU compositor. Explicit lossless intermediate, one final video encode."""
from __future__ import annotations
from fractions import Fraction
from pathlib import Path
from PIL import Image
import json
import math
import os
import subprocess
import tempfile
import time
from ..core.model import Project,Clip,US,seconds,digest
from ..core.paths import atomic_write,publish_no_clobber
from ..core.process import run,stop_process,Cancelled,ProcessFailure,popen
from .media import tool,validate_media
from .composition import paint_frame,composition_warnings


def atempo(speed:Fraction) -> str:
    parts=[]
    while speed>2:parts.append('atempo=2');speed/=2
    while speed<Fraction(1,2):parts.append('atempo=0.5');speed*=2
    parts.append(f'atempo={float(speed):.9f}')
    return ','.join(parts)


def video_filters(clip:Clip,project:Project) -> str:
    w,h=project.width,project.height;filters=[]
    if clip.rotation not in {0,90,180,270}:raise ValueError('Clip rotation supports 0/90/180/270; free rotation is layer-specific')
    if clip.rotation==90:filters.append('transpose=1')
    if clip.rotation==180:filters.extend(['hflip','vflip'])
    if clip.rotation==270:filters.append('transpose=2')
    if clip.flip:filters.append('hflip')
    filters += [f'setpts=(PTS-STARTPTS)/{float(Fraction(clip.speed)):.12f}',f'fps={project.fps}']
    if clip.fit=='crop':filters += [f'scale={w}:{h}:force_original_aspect_ratio=increase',f'crop={w}:{h}']
    elif clip.fit=='fit':filters += [f'scale={w}:{h}:force_original_aspect_ratio=decrease',f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black']
    elif clip.fit=='blur':
        filters += [f'split[fg][bg];[bg]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20:2[back];[fg]scale={w}:{h}:force_original_aspect_ratio=decrease[front];[back][front]overlay=(W-w)/2:(H-h)/2']
    filters += ['setsar=1',f'eq=brightness={clip.brightness}:contrast={clip.contrast}:saturation={clip.saturation}:gamma={clip.gamma}']
    return ','.join(filters)


def normalized_base(project:Project,directory:Path,cancel=lambda:False,progress=lambda *a:None) -> Path:
    if not project.clips:raise ValueError('No video clips to render')
    assets={a.id:a for a in project.assets};clips=sorted(project.clips,key=lambda c:c.offset);paths=[];end=0
    for i,c in enumerate(clips):
        if c.offset<end:raise ValueError('Overlapping video clips require an explicit transition; none was configured')
        if c.offset>end:
            gap=directory/f'gap{i}.mkv'
            run([tool('ffmpeg'),'-v','error','-f','lavfi','-i',f'color=black:s={project.width}x{project.height}:r={project.fps}',
                 '-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t',seconds(c.offset-end),'-c:v','ffv1','-c:a','pcm_s16le',str(gap)],cancel=cancel)
            paths.append(gap)
        asset=assets[c.asset_id]
        if not Path(asset.path).is_file():raise FileNotFoundError(asset.path)
        out=directory/f'clip{i}.mkv'
        args=[tool('ffmpeg'),'-v','error','-ss',seconds(c.source_in),'-t',seconds(c.source_out-c.source_in),'-i',asset.path]
        if not asset.has_audio:args+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
        vf=video_filters(c,project)
        graph=f'[0:v]{vf}[v];'+(f'[0:a]{atempo(Fraction(c.speed))},volume={c.volume},aresample=48000,apad[a]' if asset.has_audio else '[1:a]anull[a]')
        args+=['-filter_complex',graph,'-map','[v]','-map','[a]','-t',seconds(c.time_map.duration),'-c:v','ffv1','-level','3','-pix_fmt','yuv420p','-c:a','pcm_s16le','-ar','48000','-ac','2','-threads','2',str(out)]
        run(args,cancel=cancel,timeout=max(120,c.time_map.duration/US*20));paths.append(out);end=c.offset+c.time_map.duration
        progress('preparing',.15*(i+1)/len(clips),'Chuẩn hóa nguồn không thay đổi file gốc')
    if len(paths)==1:return paths[0]
    listing=directory/'concat.txt';listing.write_text(''.join(f"file '{p.name}'\n" for p in paths))
    out=directory/'base.mkv';run([tool('ffmpeg'),'-v','error','-f','concat','-safe','1','-i',str(listing),'-c','copy',str(out)],cancel=cancel)
    return out


def _popen(args,**kwargs):
    flags={'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
    return popen(args,**kwargs,**flags)


def render_frames(base:Path,project:Project,target:Path,cancel,progress):
    size=project.width*project.height*3;fps=Fraction(project.fps);total=math.ceil(Fraction(project.duration,US)*fps)
    with tempfile.TemporaryFile() as de, tempfile.TemporaryFile() as ee:
        decoder=_popen([tool('ffmpeg'),'-v','error','-i',str(base),'-an','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE,stderr=de,stdin=subprocess.DEVNULL)
        encoder=_popen([tool('ffmpeg'),'-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{project.width}x{project.height}','-r',project.fps,'-i','-',
                       '-an','-c:v','libx264','-preset','veryfast','-crf',str(project.settings.get('crf',20)),'-pix_fmt','yuv420p','-threads',str(project.settings.get('render_threads',2)),str(target)],stdin=subprocess.PIPE,stderr=ee,stdout=subprocess.DEVNULL)
        count=0
        try:
            while count<total:
                if cancel():raise Cancelled('Render cancelled; source unchanged')
                raw=decoder.stdout.read(size)
                if not raw:break
                if len(raw)!=size:raise ValueError('Incomplete decoded frame')
                frame=Image.frombytes('RGB',(project.width,project.height),raw)
                t=round(Fraction(count*US)/fps)
                encoder.stdin.write(paint_frame(frame,project,t).tobytes());count+=1
                if count%5==0:progress('rendering',.15+.7*count/total,f'{count}/{total} frames')
            encoder.stdin.close();encoder.wait(timeout=60)
            decoder.wait(timeout=60)
            if decoder.returncode or encoder.returncode:
                de.seek(0);ee.seek(0);raise ProcessFailure(encoder.returncode or decoder.returncode,(de.read()+ee.read()).decode(errors='replace'))
            if count<total-1:raise ValueError(f'Decoded only {count}/{total} frames')
        finally:
            stop_process(decoder);stop_process(encoder);decoder.stdout.close()
            if not encoder.stdin.closed:encoder.stdin.close()


def mix_audio(base:Path,video:Path,project:Project,out:Path,cancel):
    tracks=[a for a in project.audio if not a.muted];solo=any(a.solo for a in tracks)
    if solo:tracks=[a for a in tracks if a.solo]
    args=[tool('ffmpeg'),'-v','error','-i',str(video),'-i',str(base)]
    filters=[];labels=[]
    original_gain=0 if solo or project.settings.get('mute_original') else float(project.settings.get('original_gain',1))
    filters.append(f'[1:a]volume={original_gain},atrim=duration={seconds(project.duration)},asetpts=PTS-STARTPTS[a0]');labels.append('[a0]')
    for n,track in enumerate(tracks,2):
        if track.loop:args+=['-stream_loop','-1']
        args+=['-i',track.path]
        chain=f'atrim=start={seconds(track.trim_in)}'
        if track.trim_out:chain+=f':end={seconds(track.trim_out)}'
        chain+=f',asetpts=PTS-STARTPTS,volume={track.gain}'
        if track.fade_in:chain+=f',afade=t=in:st=0:d={seconds(track.fade_in)}'
        if track.fade_out:chain+=f',afade=t=out:st={seconds(max(0,project.duration-track.start-track.fade_out))}:d={seconds(track.fade_out)}'
        chain+=f',adelay={round(track.start/1000)}:all=1,apad,atrim=duration={seconds(project.duration)}'
        label=f'a{n-1}';filters.append(f'[{n}:a]{chain}[{label}]');labels.append(f'[{label}]')
    filters.append(''.join(labels)+f'amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.95:latency=1'+(',loudnorm=I=-16:TP=-1.5:LRA=11' if project.settings.get('normalize_audio') else '')+'[audio]')
    args+=['-filter_complex',';'.join(filters),'-map','0:v','-map','[audio]','-c:v','copy','-c:a','aac','-b:a','192k','-t',seconds(project.duration),'-movflags','+faststart',str(out)]
    run(args,cancel=cancel,timeout=max(120,project.duration/US*10))


def render_project(project:Project,target:Path,*,cancel=lambda:False,progress=lambda *a:None) -> dict:
    project.validate()
    if project.settings.get('hardware','auto')=='gpu':raise ValueError('GPU required but no real tested GPU renderer is available; choose CPU/Auto explicitly')
    warnings=composition_warnings(project)
    if warnings and not project.settings.get('allow_missing_glyphs',False):raise ValueError('; '.join(warnings)+'; choose a suitable font')
    target=Path(target).resolve()
    if target.suffix.lower()!='.mp4':raise ValueError('This renderer currently exports MP4 only')
    if target in [Path(a.path).resolve() for a in project.assets]:raise ValueError('Output must not replace a source')
    target.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='.fonesi-render-',dir=target.parent) as work:
        directory=Path(work);base=normalized_base(project,directory,cancel,progress)
        encoded=directory/'encoded.mp4';render_frames(base,project,encoded,cancel,progress)
        final=directory/'final.mp4';mix_audio(base,encoded,project,final,cancel)
        progress('validating',.9,'Probe + full decode + duration + required tracks')
        result=validate_media(final,duration=project.duration,audio=True,cancel=cancel)
        if cancel():raise Cancelled('Cancelled before artifact publication')
        output=publish_no_clobber(final,target)
    result.update(path=str(output),warnings=warnings,elapsed_seconds=time.monotonic()-started,snapshot_hash=digest(project.to_dict()),
                  renderer='canonical-pillow-cpu-v1',intermediate_reason='Lossless FFV1 normalization for mixed sources before canonical CPU layers; one final H.264 encode',
                  hardware_reason='CPU compositor; Auto selects tested CPU path, not an unverified GPU encoder')
    atomic_write(output.with_suffix('.provenance.json'),json.dumps(result,ensure_ascii=False,indent=2))
    if project.cues:
        from .subtitles import write_subtitles
        write_subtitles(project.cues,output.with_suffix('.srt'),bilingual=bool(project.settings.get('bilingual')))
    progress('complete',1,'Đã kiểm tra đầu ra');return result


def reference_frame(project:Project,time_us:int,target:Path,cancel=lambda:False) -> Path:
    """Expensive canonical reference; call outside UI thread and cache by snapshot+time."""
    with tempfile.TemporaryDirectory(prefix='fonesi-preview-') as d:
        base=normalized_base(project,Path(d),cancel)
        raw=Path(d)/'frame.png'
        run([tool('ffmpeg'),'-v','error','-ss',seconds(min(time_us,max(0,project.duration-1))),'-i',str(base),'-frames:v','1',str(raw)],cancel=cancel)
        with Image.open(raw) as image:paint_frame(image,project,time_us).save(target)
    return target
