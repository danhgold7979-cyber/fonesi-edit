from copy import deepcopy
from pathlib import Path
import hashlib
import math
import re
import random

from .domain import Clip,Composition,Layer,canonical,identifier
from .prototypes.media import probe
from .render import audio_duration

VIDEO_EXTENSIONS={'.mp4','.mkv','.mov','.webm','.avi','.m4v','.flv','.ts'}
AUDIO_EXTENSIONS={'.mp3','.m4a','.wav','.flac','.aac','.ogg','.opus','.wma','.mp4','.mov','.mkv'}


def natural_key(value):return [int(p) if p.isdigit() else p.casefold() for p in re.split(r'(\d+)',str(value))]


def configured_clip(path,info,composition,clip_id):
    settings=composition.adjustments.get('batch_video',{})
    if not 0<=float(settings.get('random_flip',0))<=1:raise ValueError('Xác suất lật phải từ 0 tới 1')
    rng=random.Random(f'{composition.seed}:{clip_id}')
    flip=bool(settings.get('flip',False))
    if rng.random()<float(settings.get('random_flip',0)):flip=not flip
    rotation=float(settings.get('rotation',0))
    if settings.get('random_rotate'):
        lower,upper=float(settings.get('rotation_min',-5)),float(settings.get('rotation_max',5))
        if not -360<=lower<=upper<=360:raise ValueError('Khoảng random rotation không hợp lệ')
        rotation+=rng.uniform(lower,upper)
    clip=Clip(str(Path(path).resolve()),id=clip_id,start=float(settings.get('trim_head',0)),end=info.duration-float(settings.get('trim_tail',0)),source_duration=info.duration,speed=float(settings.get('speed',1)),flip=flip,rotation=rotation,volume=float(settings.get('volume',1)))
    clip.validate();return clip


def source_subtitle(path, languages=('vi','zh','en'), channel=None):
    path=Path(path);channel=Path(channel) if channel else path.parent.parent if path.parent.name.casefold()=='videos' else path.parent
    candidates=[path.with_suffix(ext) for ext in ('.srt','.vtt','.ass') if path.with_suffix(ext).is_file()]
    media_id=path.stem.rsplit('__',1)[-1]
    for folder in [path.parent,channel/'subtitles']:
        if folder.is_dir():candidates.extend(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {'.srt','.vtt','.ass'} and (p.stem==path.stem or p.stem.startswith(path.stem+'.') or p.stem==media_id or p.stem.startswith(media_id+'.')))
    candidates=list(dict.fromkeys(candidates))
    def rank(item):
        lang=item.stem.split('.')[-1]
        return next((i for i,value in enumerate(languages) if lang==value or lang.startswith(value+'-')),len(languages)),{'.srt':0,'.vtt':1,'.ass':2}[item.suffix.lower()]
    candidates.sort(key=rank)
    if len(candidates)==1 or len(candidates)>1 and rank(candidates[0])<rank(candidates[1]):return str(candidates[0]),[]
    return None,['Nhiều file sub cùng tên; cần chọn' if candidates else 'Không có sub phù hợp']


def bind_source_subtitles(composition, channel=None):
    """Reuse subtitle layout, never the previous video's cue file."""
    templates=[layer for layer in composition.layers if layer.kind=='subtitle']
    if not templates and composition.adjustments.get('bilingual_subtitles'):
        size=float(composition.subtitle_style.get('font_size',32))
        for role,y,size in [('source',.67,max(8,size*.75)),('target',.82,size)]:
            templates.append(Layer(kind='subtitle',id='builtin-subtitle-'+role,name='Sub '+role,x=.1,y=y,width=.8,height=.14,style={**composition.subtitle_style,'font_size':size,'subtitle_role':role}))
    composition.layers=[layer for layer in composition.layers if layer.kind!='subtitle'];warnings=[]
    for clip in composition.clips:
        clip.subtitles=None
        for template in templates or [None]:
            role=template.style.get('subtitle_role','target') if template else 'target'
            languages=template.style.get('subtitle_languages') if template else None
            if not languages:languages=composition.adjustments.get('source_subtitle_languages',['zh','en']) if role=='source' else composition.adjustments.get('subtitle_languages',['vi','zh','en'])
            source,notes=source_subtitle(clip.path,languages,channel)
            warnings.extend(f'{Path(clip.path).name} ({role}): {note}' for note in notes)
            if source and template:
                layer=deepcopy(template);layer.id=hashlib.sha256(f'{template.id}:{clip.id}:{source}'.encode()).hexdigest()[:32];layer.path=source;layer.text='';layer.clip_ids=[clip.id]
                composition.layers.append(layer)
            elif source:clip.subtitles=source
        source_paths={layer.path for layer in composition.layers if clip.id in layer.clip_ids and layer.style.get('subtitle_role')=='source'}
        if any(layer.path in source_paths for layer in composition.layers if clip.id in layer.clip_ids and layer.style.get('subtitle_role')=='target'):warnings.append(f'{Path(clip.path).name}: chưa có bản dịch riêng; chờ auto dịch hoặc chỉ chèn track gốc')
    return warnings


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
    if policy not in {'speed','trim','loop','freeze'}:
        raise ValueError('Unsupported duration policy')
    if allocation not in {'proportional','equal','weights'}:
        raise ValueError('Unsupported duration allocation')
    if allocation=='weights' and weights is None:
        raise ValueError('Manual duration weights must be provided')
    c=deepcopy(composition)
    if not c.clips:raise ValueError('No clips')
    if policy in {'loop','freeze'} and len(c.clips)!=1:
        raise ValueError('Loop/freeze duration policy supports exactly one clip')
    for clip in c.clips:
        if clip.end is None:clip.end=probe(Path(clip.path)).duration
        clip.offset=None
    overlap=c.transition*(len(c.clips)-1);desired=target+overlap
    natural=[(clip.end-clip.start)/clip.speed for clip in c.clips]
    if policy in {'loop','freeze'} and target<natural[0]-.001:
        raise ValueError('Loop/freeze only extends duration; choose trim or speed to shorten')
    if len(c.clips)==1 and policy=='loop' and natural[0]<target:
        original=deepcopy(c.clips[0]);c.clips=[];remaining=target
        while remaining>1/c.fps:
            clip=deepcopy(original);clip.id=hashlib.sha256(f'{original.id}:{len(c.clips)}'.encode()).hexdigest()[:32]
            if remaining<natural[0]:clip.end=clip.start+remaining*clip.speed
            c.clips.append(clip);remaining-=min(remaining,natural[0])
        for layer in c.layers:
            if original.id in layer.clip_ids:layer.clip_ids=[cid for cid in layer.clip_ids if cid!=original.id]+[clip.id for clip in c.clips]
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



def batch_audio_assignments(groups, mode='shared', audio_path=None, audio_folder=None, seed=0):
    """Pick audio for every selected video without modifying source media.

    Return {resolved video path: (resolved audio path, validated duration)}.
    Ordering follows selected source order within natural-sorted channels;
    random is stable for the same source path and project seed.
    """
    if mode not in {'shared','by_name','ordered','random'}:
        raise ValueError('Unknown audio assignment mode')
    sources=[str(Path(source).resolve()) for channel,paths in sorted(
        groups.items(),key=lambda pair:natural_key(pair[0])) for source in paths]
    if mode=='shared':
        if not audio_path:
            return {}
        sound=Path(audio_path).resolve()
        if not sound.is_file():
            raise FileNotFoundError('Âm thanh chung không tồn tại: '+sound.name)
        length=audio_duration(sound)
        return {source:(str(sound),length) for source in sources}
    if not audio_folder:
        raise ValueError('Chọn thư mục audio khi dùng ghép theo tên/danh sách/random')
    directory=Path(audio_folder).resolve()
    if not directory.is_dir():
        raise NotADirectoryError('Thư mục audio không tồn tại: '+str(directory))
    paths=sorted((p for p in directory.iterdir()
        if p.is_file() and not p.is_symlink() and p.suffix.casefold() in AUDIO_EXTENSIONS),
        key=lambda p:natural_key(p.name))
    if not paths:
        raise ValueError('Thư mục audio không có tệp phù hợp')
    # Validate real audio tracks before generating *any* batch plan.
    durations={}
    for sound in paths:
        try:
            length=audio_duration(sound)
        except (OSError,ValueError,RuntimeError) as exc:
            raise ValueError('Tệp audio không có track hợp lệ: '+sound.name) from exc
        if not math.isfinite(length) or length<=0:
            raise ValueError('Thời lượng audio không hợp lệ: '+sound.name)
        durations[str(sound.resolve())]=length
    selection={}
    if mode=='by_name':
        matched={}
        for sound in paths:
            matched.setdefault(sound.stem.casefold(),[]).append(sound)
        for source in sources:
            found=matched.get(Path(source).stem.casefold(),[])
            if len(found)!=1:
                raise ValueError('Ghép theo tên cần đúng một audio: '+Path(source).name)
            sound=found[0].resolve()
            selection[source]=(str(sound),durations[str(sound)])
    elif mode=='ordered':
        if len(paths)!=len(sources):
            raise ValueError('Ghép theo danh sách cần số audio bằng số video được chọn')
        for source,sound in zip(sources,paths,strict=True):
            sound=sound.resolve()
            selection[source]=(str(sound),durations[str(sound)])
    else:
        for source in sources:
            number=int(hashlib.sha256(f'{seed}:{source}'.encode()).hexdigest()[:16],16)
            sound=paths[number%len(paths)].resolve()
            selection[source]=(str(sound),durations[str(sound)])
    return selection


def batch_plan(groups,preset:Composition,audio_path=None,policy='speed',minimum=.5,maximum=2,audio_mode='shared',audio_folder=None):
    assignments=batch_audio_assignments(groups,audio_mode,audio_path,audio_folder,preset.seed)
    plans=[]
    for channel,paths in sorted(groups.items(),key=lambda p:natural_key(p[0])):
        channel=Path(channel);output_root=channel.with_name(channel.name+' edit')/'videos'
        for source in paths:
            path=Path(source);info=probe(path);c=deepcopy(preset)
            for layer in c.layers:layer.clip_ids=[]
            clip_id=hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:32]
            c.clips=[configured_clip(path,info,c,clip_id)]
            audio_binding=assignments.get(str(path.resolve()))
            if audio_binding:
                sound,length=audio_binding
                c.audio=[{'path':sound,'mode':'main','volume':1}]+[a for a in c.audio if a.get('mode')!='main']
                c=fit_duration(c,length,policy,minimum,maximum)
            elif c.duration_target:c=fit_duration(c,c.duration_target,policy,minimum,maximum)
            warnings=bind_source_subtitles(c,channel)
            key=hashlib.sha256(canonical(c.to_dict()).encode()).hexdigest()[:10]
            output=output_root/(path.stem[:120]+'_'+key+'.mp4')
            plans.append({'source':str(path),'audio_source':audio_binding[0] if audio_binding else None,'output':str(output),'composition':c.to_dict(),'warnings':warnings})
    return plans


def enqueue_batch(store,plans):return [store.submit('render',{'composition':p['composition'],'output':p['output'],'warnings':p.get('warnings',[])}) for p in plans]
