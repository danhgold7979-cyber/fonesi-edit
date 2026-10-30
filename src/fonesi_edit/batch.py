from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import hashlib
import math
import re
import random

from .domain import Clip,Composition,Layer,canonical,identifier
from .prototypes.media import probe,MediaError
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
        dirs[:]=[name for name in dirs if not name.startswith('.') and not name.casefold().endswith(' edit') and name.casefold() not in {'videos edit','quality-upgrades','cache','profiles','browser-profiles','node_modules','dist','build'}]
        for name in sorted(files,key=natural_key):
            path=current/name
            if path.suffix.casefold() not in VIDEO_EXTENSIONS or path.is_symlink():continue
            if current.name.casefold()=='videos':channel=current.parent
            else:
                relative=path.relative_to(root)
                channel=root/relative.parts[0] if len(relative.parts)>1 else root
            groups.setdefault(str(channel),[]).append(str(path))
    return groups



def scan_multiple_folders(roots):
    """Merge channel-aware recursive scans without duplicating overlapping files."""
    roots=list(roots)
    if not roots:
        raise ValueError('Chọn ít nhất một thư mục nguồn để quét')
    combined={}
    seen_roots=set()
    seen_files=set()
    for value in roots:
        root=Path(value).expanduser().resolve()
        if root in seen_roots:
            continue
        seen_roots.add(root)
        for channel,paths in scan_folders(root).items():
            for value in paths:
                path=Path(value).resolve()
                if path in seen_files:
                    continue
                seen_files.add(path)
                combined.setdefault(channel,[]).append(str(path))
    return combined


def probe_batch_metadata(groups, progress=None, cancel=None):
    """Read FFprobe video facts off the UI thread; keep per-file failures explicit.

    Group values are paths returned by the batch scanner. Repeated source paths
    (including overlapping roots) are only probed once. No media is modified.
    """
    sources=list(dict.fromkeys(str(Path(path).expanduser().resolve())
        for paths in groups.values() for path in paths))
    media={}
    errors={}
    for index,source in enumerate(sources):
        if cancel is not None and cancel.is_set():
            return {'media':media,'errors':errors,'cancelled':True}
        try:
            info=probe(Path(source))
            if info.width<=0 or info.height<=0:
                raise ValueError('Invalid video dimensions')
            fps=float(Fraction(info.fps))
            if not math.isfinite(fps) or fps<=0:
                raise ValueError('Invalid video FPS')
            codec=info.video_codec.casefold()
            if not codec:
                raise ValueError('Missing video codec')
            bitrate=info.video_bitrate
            media[source]={
                'duration':info.duration,'width':info.width,'height':info.height,
                'fps':fps,'codec':codec,
                'video_bitrate_kbps':bitrate/1000 if bitrate is not None else None,
            }
        except (OSError,ValueError,KeyError,TypeError,ZeroDivisionError,MediaError) as exc:
            errors[source]=type(exc).__name__
        if progress is not None:
            progress((index+1)/len(sources))
    return {'media':media,'errors':errors,'cancelled':False}


def fit_duration(composition:Composition,target,policy='speed',minimum=.5,maximum=2,allocation='proportional',weights=None,manual_durations=None):
    if not math.isfinite(target) or target<=0 or not .1<=minimum<=maximum<=10:raise ValueError('Invalid target/speed bounds')
    if policy not in {'speed','trim','loop','freeze'}:
        raise ValueError('Unsupported duration policy')
    if allocation not in {'proportional','equal','weights','manual'}:
        raise ValueError('Unsupported duration allocation')
    if allocation=='weights' and weights is None:
        raise ValueError('Manual duration weights must be provided')
    if allocation=='manual' and manual_durations is None:
        raise ValueError('Explicit scene durations must be provided')
    if allocation=='manual' and policy not in {'speed','trim'}:
        raise ValueError('Manual durations only support speed or trim policy')
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
        if allocation=='manual':
            durations=list(manual_durations)
            if (len(durations)!=len(c.clips)
                    or any(type(value) not in (int,float)
                        or not math.isfinite(value) or value<=0 for value in durations)):
                raise ValueError('Scene durations must be positive finite numbers matching scene count')
            if abs(sum(durations)-desired)>.001:
                raise ValueError('Manual scene durations must sum to target including transition overlap')
            if any(value<minimum_duration-.001 or value>maximum_duration+.001
                   for value,minimum_duration,maximum_duration in zip(durations,lower,upper)):
                raise ValueError('Manual scene duration exceeds trim/speed bounds')
        else:
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



class BatchPlanCancelled(Exception):
    """Cooperative preparation cancellation; never publish an incomplete plan."""


def _check_batch_cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise BatchPlanCancelled()


def batch_audio_assignments(groups, mode='shared', audio_path=None, audio_folder=None,
                            seed=0, *, cancel=None, playlist_paths=None):
    """Assign one validated audio source per selected video.

    Playlist entries are explicit absolute paths in caller order. Unlike the
    folder-based ordered mode, they may span directories and share basenames.
    Duplicate playlist paths are intentional and probed only once.
    """
    _check_batch_cancel(cancel)
    if mode not in {'shared','by_name','ordered','random','playlist'}:
        raise ValueError('Unknown audio assignment mode')
    sources=[str(Path(source).resolve()) for channel,paths in sorted(
        groups.items(),key=lambda pair:natural_key(pair[0])) for source in paths]
    _check_batch_cancel(cancel)
    if mode=='shared':
        if not audio_path:
            return {}
        sound=Path(audio_path).resolve()
        if not sound.is_file():
            raise FileNotFoundError('Âm thanh chung không tồn tại: '+sound.name)
        length=audio_duration(sound)
        _check_batch_cancel(cancel)
        return {source:(str(sound),length) for source in sources}
    if mode=='playlist':
        if not isinstance(playlist_paths,(list,tuple)):
            raise ValueError('Playlist audio phải là danh sách đường dẫn riêng biệt')
        if len(playlist_paths)!=len(sources):
            raise ValueError('Playlist audio phải có đúng một mục cho mỗi video được chọn')
        ordered=[]
        for entry in playlist_paths:
            _check_batch_cancel(cancel)
            if not isinstance(entry,str) or not entry.strip():
                raise ValueError('Mỗi dòng playlist phải là một đường dẫn audio không rỗng')
            sound=Path(entry)
            if not sound.is_absolute():
                raise ValueError('Mỗi đường dẫn playlist phải là đường dẫn tuyệt đối')
            if any(part.is_symlink() for part in (sound,*sound.parents)):
                raise ValueError('Playlist audio không chấp nhận symbolic link')
            try:
                sound=sound.resolve(strict=True)
            except OSError as exc:
                raise FileNotFoundError('Playlist audio không tồn tại') from exc
            if not sound.is_file():
                raise ValueError('Mỗi mục playlist phải là một tệp audio, không phải thư mục')
            if sound.suffix.casefold() not in AUDIO_EXTENSIONS:
                raise ValueError('Định dạng audio playlist không được hỗ trợ: '+sound.suffix)
            ordered.append(sound)
        durations={}
        for sound in ordered:
            _check_batch_cancel(cancel)
            key=str(sound)
            if key in durations:
                continue
            try:
                length=audio_duration(sound)
            except (OSError,ValueError,RuntimeError) as exc:
                raise ValueError('Tệp playlist không có audio stream hợp lệ: '+sound.name) from exc
            _check_batch_cancel(cancel)
            if not math.isfinite(length) or length<=0:
                raise ValueError('Thời lượng audio playlist không hợp lệ: '+sound.name)
            durations[key]=length
        selection={source:(str(sound),durations[str(sound)])
                   for source,sound in zip(sources,ordered,strict=True)}
        _check_batch_cancel(cancel)
        return selection
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
    durations={}
    for sound in paths:
        _check_batch_cancel(cancel)
        try:
            length=audio_duration(sound)
        except (OSError,ValueError,RuntimeError) as exc:
            raise ValueError('Tệp audio không có track hợp lệ: '+sound.name) from exc
        _check_batch_cancel(cancel)
        if not math.isfinite(length) or length<=0:
            raise ValueError('Thời lượng audio không hợp lệ: '+sound.name)
        durations[str(sound.resolve())]=length
    selection={}
    if mode=='by_name':
        matched={}
        for sound in paths:
            matched.setdefault(sound.stem.casefold(),[]).append(sound)
        for source in sources:
            _check_batch_cancel(cancel)
            found=matched.get(Path(source).stem.casefold(),[])
            if len(found)!=1:
                raise ValueError('Ghép theo tên cần đúng một audio: '+Path(source).name)
            sound=found[0].resolve()
            selection[source]=(str(sound),durations[str(sound)])
    elif mode=='ordered':
        if len(paths)!=len(sources):
            raise ValueError('Ghép theo danh sách cần số audio bằng số video được chọn')
        for source,sound in zip(sources,paths,strict=True):
            _check_batch_cancel(cancel)
            sound=sound.resolve()
            selection[source]=(str(sound),durations[str(sound)])
    else:
        for source in sources:
            _check_batch_cancel(cancel)
            number=int(hashlib.sha256(f'{seed}:{source}'.encode()).hexdigest()[:16],16)
            sound=paths[number%len(paths)].resolve()
            selection[source]=(str(sound),durations[str(sound)])
    _check_batch_cancel(cancel)
    return selection

def batch_plan(groups,preset:Composition,audio_path=None,policy='speed',minimum=.5,maximum=2,
               audio_mode='shared',audio_folder=None,*,playlist_paths=None,failures=None,progress=None,cancel=None):
    """Build immutable render snapshots; optionally isolate per-video input faults.

    Default callers remain fail-fast. Only callers explicitly supplying a
    failures list can skip invalid sources. Audio assignment is a whole-batch
    preflight: bad mapping is never silently changed or downgraded.
    """
    _check_batch_cancel(cancel)
    assignments=batch_audio_assignments(groups,audio_mode,audio_path,audio_folder,preset.seed,
                                        cancel=cancel,playlist_paths=playlist_paths)
    _check_batch_cancel(cancel)
    total=sum(len(paths) for paths in groups.values())
    processed=0
    plans=[]
    for channel,paths in sorted(groups.items(),key=lambda p:natural_key(p[0])):
        channel=Path(channel);output_root=channel.with_name(channel.name+' edit')/'videos'
        for source in paths:
            _check_batch_cancel(cancel)
            path=Path(source)
            try:
                info=probe(path);c=deepcopy(preset)
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
                planned={'source':str(path),
                         'audio_source':audio_binding[0] if audio_binding else None,
                         'output':str(output),'composition':c.to_dict(),
                         'warnings':warnings}
            except (OSError,ValueError,MediaError) as exc:
                if failures is None:
                    raise
                # Do not show arbitrary third-party error messages, which can
                # include paths, signed URLs or credentials in other adapters.
                reason=('Không đọc được media' if isinstance(exc,MediaError)
                        else 'Không truy cập được tệp' if isinstance(exc,OSError)
                        else 'Cấu hình clip không hợp lệ')
                failures.append({'source':str(path),'reason':reason,
                                 'error_type':type(exc).__name__})
            else:
                plans.append(planned)
            # This check is after the expensive probe/composition work, so a
            # cancel during one FFprobe call cannot publish a partial result.
            _check_batch_cancel(cancel)
            processed+=1
            if progress is not None and total:
                # Reserve 100% for successful completion, including preflight.
                progress(min(.99,processed/total))
            _check_batch_cancel(cancel)
    _check_batch_cancel(cancel)
    if progress is not None:
        progress(1.0)
    return plans


def batch_plan_report(groups,preset:Composition,audio_path=None,policy='speed',minimum=.5,
                      maximum=2,audio_mode='shared',audio_folder=None,*,playlist_paths=None,progress=None,cancel=None):
    """Report per-video errors; cancellation never exposes partial render plans."""
    failures=[]
    try:
        plans=batch_plan(groups,preset,audio_path,policy,minimum,maximum,
                         audio_mode,audio_folder,playlist_paths=playlist_paths,
                         failures=failures,progress=progress,cancel=cancel)
    except BatchPlanCancelled:
        return {'plans':[],'failures':[],'cancelled':True}
    return {'plans':plans,'failures':failures}


def enqueue_batch(store,plans):
    """Publish all validated Batch render requests or none of them."""
    payloads=[]
    seen=set()
    for plan in plans:
        if type(plan) is not dict or type(plan.get('composition')) is not dict:
            raise ValueError('Batch render plan has no composition')
        output=plan.get('output')
        if type(output) is not str or not output.strip():
            raise ValueError('Batch render plan has no output path')
        # Path equality uses platform semantics (Windows case-insensitive).
        # Duplicate targets would collide in the no-overwrite renderer.
        lexical=Path(output).expanduser()
        # Check before resolve: resolving a dangling symlink can hide the
        # existing directory entry that the renderer must never overwrite.
        if lexical.is_symlink() or lexical.exists():
            raise FileExistsError('Batch output already exists')
        target=lexical.resolve()
        if target in seen:
            raise ValueError('Duplicate Batch output path')
        seen.add(target)
        payloads.append({
            'composition':plan['composition'],
            'output':output,
            'warnings':plan.get('warnings',[]),
        })
    return store.submit_many('render',payloads)
