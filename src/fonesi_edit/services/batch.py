from dataclasses import replace
from pathlib import Path
import copy
import os
from ..core.model import Project,Clip,US,uid,apply_auto,digest
from ..core.paths import safe_name,contained
from .media import inspect_asset
from .subtitles import map_cues

VIDEO_EXT={'.mp4','.mkv','.mov','.avi','.webm','.m4v','.ts','.mts'}
EXCLUDED={'.git','.venv','.local','cache','output','outputs','artifacts','profiles','videos edit'}


def scan_folders(roots:list[Path],exclude=(),cancel=lambda:False) -> list[Path]:
    found=[];seen=set();excluded=[Path(p).resolve() for p in exclude]
    for root in roots:
        root=Path(root).resolve()
        if any(contained(root,e) for e in excluded):continue
        for directory,dirs,files in os.walk(root,followlinks=False):
            if cancel():return found
            dirs[:]=sorted(d for d in dirs if d.casefold() not in EXCLUDED and not d.casefold().endswith(' edit') and not d.startswith('.fonesi-') and not (Path(directory)/d).is_symlink() and not any(contained(Path(directory)/d,e) for e in excluded))
            for filename in sorted(files):
                p=Path(directory)/filename
                if p.suffix.lower() in VIDEO_EXT and not p.is_symlink() and p.resolve() not in seen and not any(contained(p,e) for e in excluded):found.append(p);seen.add(p.resolve())
    return found


def fit_duration(clip:Clip,target:int,policy='error',min_speed=.5,max_speed=2,fps='25') -> list[Clip]:
    if target<=0:raise ValueError('Target duration must be positive')
    natural=clip.time_map.duration
    if target==natural:return [replace(clip)]
    if policy=='speed':
        from fractions import Fraction
        speed=Fraction(clip.source_out-clip.source_in,target)
        if not min_speed<=float(speed)<=max_speed:raise ValueError('Duration cannot fit configured speed limits')
        return [replace(clip,speed=str(speed))]
    if target<natural:
        if policy not in {'cut','loop','freeze'}:raise ValueError('Target shorter than source; select cut or speed explicitly')
        from fractions import Fraction
        return [replace(clip,source_out=clip.source_in+round(target*Fraction(clip.speed)))]
    if policy=='loop':
        result=[];offset=clip.offset;remaining=target
        while remaining:
            segment=replace(clip,id=uid(),offset=offset)
            length=min(natural,remaining)
            if length<natural:
                from fractions import Fraction
                segment.source_out=segment.source_in+round(length*Fraction(segment.speed))
            result.append(segment);remaining-=length;offset+=length
        return result
    if policy=='freeze':
        from fractions import Fraction
        frame=min(clip.source_out-clip.source_in,max(1,round(US/Fraction(fps))));tail=target-natural
        return [replace(clip),replace(clip,id=uid(),source_in=max(clip.source_in,clip.source_out-frame),offset=clip.offset+natural,speed=str(Fraction(frame,tail)),volume=0)]
    raise ValueError('Video is too short; choose speed, loop or freeze. Another clip will not be added automatically.')


def make_batch(paths:list[Path],template:Project,output:Path,overrides:dict|None=None,cancel=lambda:False) -> list[dict]:
    plans=[]
    for path in paths:
        if cancel():break
        try:
            asset=inspect_asset(path);project=Project.from_dict(template.to_dict());project.id=uid();project.name=path.stem
            project.assets=[asset];project.clips=[Clip(asset.id,0,asset.duration)];project.cues=[]
            from .subtitles import match_subtitle,read_subtitles
            sidecar=match_subtitle(path,[p for p in path.parent.iterdir() if p.suffix.lower() in {'.srt','.vtt','.ass'}])
            if sidecar:project.cues=read_subtitles(sidecar)[0]
            for layer in project.layers:layer.end=min(layer.end,asset.duration)
            project.layers=[l for l in project.layers if l.start<l.end]
            if overrides and str(path) in overrides:project.settings.update(copy.deepcopy(overrides[str(path)]))
            project.validate()
            target=output/safe_name(path.parent.name)/(safe_name(path.stem,100)+' edit.mp4')
            plans.append({'source':str(path),'output':str(target),'project':project.to_dict(),'status':'ready','estimated_bytes':round(asset.duration/US*2_000_000/8)})
        except Exception as exc:plans.append({'source':str(path),'status':'invalid','error':str(exc)})
    return plans


def enqueue_batch(store,plans):
    return [store.enqueue('render',{'project':p['project'],'output':p['output']},dedupe_key=digest({'source':p['source'],'project':p['project'],'output':p['output']})) for p in plans if p['status']=='ready']


def allocate_durations(source_durations:list[int],target:int,mode='equal',weights=None,manual=None,overlap=0):
    n=len(source_durations)
    if not n or target<=0 or overlap<0:raise ValueError('Invalid scene duration request')
    total=target+overlap*(n-1)
    if mode=='manual':
        if not manual or len(manual)!=n or sum(manual)!=total:raise ValueError('Manual durations do not match target including transitions')
        result=list(manual)
    else:
        values=[1]*n if mode=='equal' else source_durations if mode=='proportional' else weights if mode=='weighted' else None
        if not values or len(values)!=n or any(v<=0 for v in values):raise ValueError('Invalid allocation weights')
        result=[round(total*v/sum(values)) for v in values];result[-1]+=total-sum(result)
    if any(t<=overlap for t in result):raise ValueError('A scene is shorter than its transition overlap')
    return result
