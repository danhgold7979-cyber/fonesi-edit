from copy import deepcopy
from pathlib import Path
import hashlib
import math
import re

from .domain import Clip,Composition,canonical
from .prototypes.media import probe
from .render import audio_duration

VIDEO_EXTENSIONS={'.mp4','.mkv','.mov','.webm','.avi','.m4v','.flv','.ts'}


def natural_key(value):return [int(p) if p.isdigit() else p.casefold() for p in re.split(r'(\d+)',str(value))]


def scan_folders(root:Path):
    root=root.resolve();groups={}
    if not root.is_dir():raise NotADirectoryError(root)
    for current,dirs,files in root.walk(follow_symlinks=False):
        dirs[:]=[name for name in dirs if not name.startswith('.') and not name.casefold().endswith(' edit') and name.casefold() not in {'videos edit','cache','profiles','browser-profiles','node_modules','dist','build'}]
        for name in sorted(files,key=natural_key):
            path=current/name
            if path.suffix.casefold() not in VIDEO_EXTENSIONS or path.is_symlink():continue
            if current.name.casefold()=='videos':channel=current.parent
            else:
                relative=path.relative_to(root)
                channel=root/relative.parts[0] if len(relative.parts)>1 else root
            groups.setdefault(str(channel),[]).append(str(path))
    return groups


def fit_duration(composition:Composition,target,policy='speed',minimum=.5,maximum=2,allocation='proportional',weights=None):
    if not math.isfinite(target) or target<=0 or not .1<=minimum<=maximum<=10:raise ValueError('Invalid target/speed bounds')
    c=deepcopy(composition)
    if not c.clips:raise ValueError('No clips')
    for clip in c.clips:
        if clip.end is None:clip.end=probe(Path(clip.path)).duration
        clip.offset=None
    overlap=c.transition*(len(c.clips)-1);desired=target+overlap
    natural=[(clip.end-clip.start)/clip.speed for clip in c.clips]
    if len(c.clips)==1 and policy=='loop' and natural[0]<target:
        original=deepcopy(c.clips[0]);c.clips=[];remaining=target
        while remaining>1/c.fps:
            clip=deepcopy(original);clip.id=hashlib.sha256(f'{original.id}:{len(c.clips)}'.encode()).hexdigest()[:32]
            if remaining<natural[0]:clip.end=clip.start+remaining*clip.speed
            c.clips.append(clip);remaining-=min(remaining,natural[0])
        c.transition=0
    elif len(c.clips)==1 and policy=='freeze' and natural[0]<target:c.clips[0].freeze=target-natural[0]
    else:
        lower=[(clip.end-clip.start)/maximum for clip in c.clips]
        upper=[(clip.end-clip.start)/minimum for clip in c.clips]
        if policy=='trim':lower=[1/c.fps]*len(c.clips);upper=natural
        if desired<sum(lower)-.001 or desired>sum(upper)+.001:raise ValueError(f'Không khớp được mà giữ đủ cảnh: cần {desired:.2f}s, khoảng hợp lệ {sum(lower):.2f}–{sum(upper):.2f}s')
        weights=list(weights) if weights is not None else [1]*len(natural) if allocation=='equal' else natural
        if len(weights)!=len(c.clips) or any(w<=0 or not math.isfinite(w) for w in weights):raise ValueError('Scene weights must be positive and match scene count')
        lo,hi=0,max(upper)/min(weights)*2
        for _ in range(100):
            mid=(lo+hi)/2;durations=[max(a,min(b,mid*w)) for a,b,w in zip(lower,upper,weights)]
            if sum(durations)<desired:lo=mid
            else:hi=mid
        durations=[max(a,min(b,(lo+hi)/2*w)) for a,b,w in zip(lower,upper,weights)]
        for clip,duration in zip(c.clips,durations):
            if policy=='trim':clip.end=clip.start+duration*clip.speed
            else:clip.speed=(clip.end-clip.start)/duration
    c.duration_target=target;c.validate();return c


def batch_plan(groups,preset:Composition,audio_path=None,policy='speed',minimum=.5,maximum=2):
    plans=[]
    for channel,paths in sorted(groups.items(),key=lambda p:natural_key(p[0])):
        channel=Path(channel);output_root=channel.with_name(channel.name+' edit')/'videos'
        for source in paths:
            path=Path(source);info=probe(path);c=deepcopy(preset)
            for layer in c.layers:layer.clip_ids=[]
            clip_id=hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:32]
            c.clips=[Clip(str(path.resolve()),end=info.duration,source_duration=info.duration,id=clip_id)]
            candidates=[path.with_suffix(ext) for ext in ('.srt','.vtt','.ass') if path.with_suffix(ext).is_file()]
            subfolder=channel/'subtitles'
            if not candidates and subfolder.is_dir():
                media_id=path.stem.rsplit('__',1)[-1]
                candidates=[p for p in subfolder.glob('*') if p.suffix in {'.srt','.vtt','.ass'} and (p.stem==path.stem or p.stem==media_id or p.stem.startswith(media_id+'.'))]
                languages=c.adjustments.get('subtitle_languages',['vi','zh','en'])
                def sub_rank(item):
                    lang=item.stem.split('.')[-1]
                    return next((i for i,value in enumerate(languages) if lang==value or lang.startswith(value+'-')),len(languages)),{'.srt':0,'.vtt':1,'.ass':2}[item.suffix]
                candidates.sort(key=sub_rank)
                if candidates and (len(candidates)==1 or sub_rank(candidates[0])<sub_rank(candidates[1])):candidates=candidates[:1]
            warnings=[]
            if len(candidates)==1:c.clips[0].subtitles=str(candidates[0])
            elif len(candidates)>1:warnings.append('Nhiều file sub cùng tên; cần chọn')
            else:warnings.append('Không có sub phù hợp')
            if audio_path:
                c.audio=[{'path':str(Path(audio_path).resolve()),'mode':'main','volume':1}]+[a for a in c.audio if a.get('mode')!='main']
                c=fit_duration(c,audio_duration(audio_path),policy,minimum,maximum)
            elif c.duration_target:c=fit_duration(c,c.duration_target,policy,minimum,maximum)
            key=hashlib.sha256(canonical(c.to_dict()).encode()).hexdigest()[:10]
            output=output_root/(path.stem[:120]+'_'+key+'.mp4')
            plans.append({'source':str(path),'output':str(output),'composition':c.to_dict(),'warnings':warnings})
    return plans


def enqueue_batch(store,plans):return [store.submit('render',{'composition':p['composition'],'output':p['output'],'warnings':p.get('warnings',[])}) for p in plans]
