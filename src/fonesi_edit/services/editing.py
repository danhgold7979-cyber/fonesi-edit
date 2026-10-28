"""Undo-ready timeline operations on the same project model used for render."""
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
import copy
from ..core.model import Project,Clip,TimeMap,US,uid,canonical
from .subtitles import map_cues


def split_clip(project:Project,playhead:int):
    for index,clip in enumerate(project.clips):
        if clip.offset<playhead<clip.offset+clip.time_map.duration:
            source=clip.source_in+round(Fraction(playhead-clip.offset)*Fraction(clip.speed))
            left=replace(clip,source_out=source);right=replace(clip,id=uid(),source_in=source,offset=playhead)
            project.clips[index:index+1]=[left,right];return left.id,right.id
    raise ValueError('Playhead must be inside a clip')


def delete_clip(project:Project,clip_id:str,ripple=False):
    clip=next(c for c in project.clips if c.id==clip_id)
    if clip.locked:raise ValueError('Clip is locked')
    duration=clip.time_map.duration;start=clip.offset;end=start+duration;total=project.duration
    project.clips.remove(clip)
    if not ripple:return
    for item in project.clips:
        if item.offset>=end:item.offset-=duration
        elif item.offset>=start:raise ValueError('Overlapping clip prevents safe ripple deletion')
    maps=[]
    if start:maps.append(TimeMap(0,start))
    if end<total:maps.append(TimeMap(end,total,offset=start))
    project.cues=map_cues(project.cues,maps)
    layers=[]
    for layer in project.layers:
        if layer.end<=start:layers.append(layer)
        elif layer.start>=end:layer.start-=duration;layer.end-=duration;layers.append(layer)
        elif layer.start<start or layer.end>end:
            layer.start=min(layer.start,start);layer.end=max(start,layer.end-duration)
            if layer.start<layer.end:layers.append(layer)
    project.layers=layers;project.markers=[m if m<start else m-duration for m in project.markers if not start<=m<end]


def relink(project:Project,new_root:Path):
    from ..core.paths import content_hash
    by_hash={};missing=[];changed=[]
    for asset in project.assets:
        if Path(asset.path).is_file():continue
        missing.append(asset)
    needed={a.fingerprint for a in missing if a.fingerprint}
    for path in Path(new_root).rglob('*'):
        if not path.is_file() or path.is_symlink():continue
        fingerprint=content_hash(path)
        if fingerprint in needed:by_hash.setdefault(fingerprint,[]).append(path)
    for asset in missing:
        matches=by_hash.get(asset.fingerprint,[])
        if len(matches)==1:asset.path=str(matches[0]);changed.append(asset.id)
        elif len(matches)>1:raise ValueError('Relink is ambiguous; select the intended file')
    return {'relinked':changed,'missing':[a.id for a in missing if a.id not in changed]}


def export_preset(project:Project):
    # No source identity/media refs, browser profile or credential fields are exported.
    return {'schema_version':1,'name':project.name,'canvas':{'width':project.width,'height':project.height,'fps':project.fps},
            'layers':copy.deepcopy(project.to_dict()['layers']),'audio':copy.deepcopy(project.to_dict()['audio']),
            'settings':copy.deepcopy(project.settings),'seed':project.seed}


def import_preset(project:Project,preset:dict,groups=('canvas','layers','audio','settings')):
    canonical(preset)
    if preset.get('schema_version')!=1:raise ValueError('Unsupported preset version')
    missing=[]
    if 'canvas' in groups:
        for key in ['width','height','fps']:setattr(project,key,preset['canvas'][key])
    merged=project.to_dict()
    for group in ['layers','audio','settings']:
        if group in groups and group in preset:merged[group]=copy.deepcopy(preset[group])
    restored=Project.from_dict(merged)
    for layer in restored.layers:
        if layer.asset_path and not Path(layer.asset_path).is_file():missing.append(layer.asset_path)
        font=layer.style.get('font_path')
        if font and not Path(font).is_file():missing.append(font)
    for audio in restored.audio:
        if not Path(audio.path).is_file():missing.append(audio.path)
    project.__dict__.update(restored.__dict__)
    return {'missing_assets':missing}
