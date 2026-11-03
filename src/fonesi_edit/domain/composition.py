"""Strict immutable CompositionPlan, semantic preflight and stable digests.

Pure model validation. Filesystem/tool/GPU/provider capability checks are separate;
accepting this model does not imply that its media or renderer is available.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from importlib.resources import files
import json
from typing import Any, Mapping
import re
from jsonschema import Draft202012Validator, FormatChecker
from .timebase import rational, TimeValueError, TimeSegment, pair

_SCHEMA = json.loads(files(__package__).joinpath('composition-v1.schema.json').read_text())
_VALIDATOR = Draft202012Validator(_SCHEMA, format_checker=FormatChecker())
MAX_PLAN_BYTES = 32 * 1024 * 1024

class PlanError(ValueError):
    def __init__(self, code: str, path: str, message: str):
        self.code, self.path = code, path
        super().__init__(f'{code} at {path or "/"}: {message}')

@dataclass(frozen=True)
class Diagnostic:
    code: str
    path: str
    message: str
    severity: str = 'warning'

def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PlanError('duplicate_key', key, 'Duplicate JSON key')
        result[key] = value
    return result

def _number_constant(value):
    raise PlanError('nonfinite', '', f'JSON constant {value} is forbidden')

def _require(condition, path, message, code='invalid_semantics'):
    if not condition:
        raise PlanError(code, path, message)

def _q(value, path):
    try:
        return rational(value)
    except TimeValueError as exc:
        raise PlanError('invalid_rational', path, str(exc)) from exc

def _rational_walk(value, path=''):
    if isinstance(value, dict):
        for k,v in value.items(): _rational_walk(v, f'{path}/{k}')
    elif isinstance(value, list):
        if len(value)==2 and all(type(x) is int for x in value):
            _q(value,path)
        else:
            for i,v in enumerate(value): _rational_walk(v,f'{path}/{i}')

def _stream(asset, index, kind, path):
    stream = next((s for s in asset['probe']['streams'] if s['index']==index),None)
    _require(stream is not None and stream['type']==kind,path,f'Expected {kind} stream {index}', 'stream_reference')
    return stream

def _positive(value,path,allow_zero=False):
    q=_q(value,path);_require(q>=0 if allow_zero else q>0,path,'Expected nonnegative value' if allow_zero else 'Expected positive value');return q

def _interval(start,end,path,limit=None):
    a,b=_q(start,path+'/start'),_q(end,path+'/end')
    _require(a>=0 and b>a,path,'Expected 0 <= start < end')
    if limit is not None:_require(b<=limit,path,'Interval exceeds output duration')
    return a,b

def _crop(c,path):
    l,t,w,h=(_q(c[k],path+'/'+k) for k in ['left','top','width','height'])
    _require(l>=0 and t>=0 and w>0 and h>0 and l+w<=1 and t+h<=1,path,'Crop outside normalized displayed source')

def _transform(t,path):
    for name in ['width','height','scale_x','scale_y']:_positive(t[name],path+'/'+name)
    _require(0<=_q(t['opacity'],path+'/opacity')<=1,path+'/opacity','Opacity outside[0,1]')

def _validate(data):
    _rational_walk(data)
    warnings=[];duration=_positive(data['output']['duration'],'/output/duration');fps=_positive(data['output']['fps'],'/output/fps')
    frame_count=duration*fps
    frame_total=(frame_count.numerator+frame_count.denominator-1)//frame_count.denominator
    timeline_range=data.get('timeline_range')
    if timeline_range is not None:
        in_frame=timeline_range['in_frame'];out_frame=timeline_range['out_frame']
        _require(type(in_frame) is int or in_frame is None,'/timeline_range/in_frame','In frame must be an integer or null')
        _require(type(out_frame) is int or out_frame is None,'/timeline_range/out_frame','Out frame must be an integer or null')
        _require(in_frame is not None or out_frame is not None,'/timeline_range','Empty timeline range must be omitted')
        _require(out_frame is None or in_frame is not None,'/timeline_range/out_frame','Out marker requires an In marker')
        if in_frame is not None:
            _require(0<=in_frame<frame_total,'/timeline_range/in_frame','In marker must identify an existing output frame')
        if out_frame is not None:
            _require(1<=out_frame<=frame_total,'/timeline_range/out_frame','Out marker must be within the half-open output boundary')
            _require(out_frame>in_frame,'/timeline_range/out_frame','Out marker must be strictly after In')
    if data['output']['pixel_format']=='yuv420p':
        _require(data['output']['width']%2==0 and data['output']['height']%2==0,'/output','yuv420p requires even dimensions')
    ids=set()
    def register(obj,path):
        _require(obj['id'] not in ids,path+'/id','Duplicate object ID','duplicate_id');ids.add(obj['id'])
    marker_frames=set()
    for i,marker in enumerate(data.get('timeline_markers',[])):
        mp=f'/timeline_markers/{i}';register(marker,mp)
        frame=marker['frame'];label=marker['label']
        _require(type(frame) is int and 0<=frame<frame_total,mp+'/frame','Marker frame must identify an existing output frame')
        _require(frame not in marker_frames,mp+'/frame','Only one timeline marker is allowed per output frame')
        marker_frames.add(frame)
        _require(label==label.strip() and bool(label),mp+'/label','Marker label must be non-empty and trimmed')
        _require(not any(ord(ch)<32 or ord(ch)==127 for ch in label),mp+'/label','Marker label cannot contain control characters')
    assets={};fonts={};clips={};audio={}
    content_records={}
    def consistent_content(obj, key, path):
        signature=canonical({k:v for k,v in obj.items() if k not in {'id','path_ref','license_ref','provenance_ref'}})
        previous=content_records.setdefault(key,signature)
        _require(previous==signature,path,'Conflicting metadata for identical content identity','content_identity_conflict')
    for i,a in enumerate(data['assets']):
        p=f'/assets/{i}';register(a,p);assets[a['id']]=a
        consistent_content(a,('asset',a['sha256']),p)
        _require(a['sha256']==a['path_ref']['asset_hash'],p+'/path_ref','Asset/path hash mismatch')
        _positive(a['probe']['duration'],p+'/probe/duration',True);seen=set()
        for j,s in enumerate(a['probe']['streams']):
            sp=f'{p}/probe/streams/{j}';_require(s['index'] not in seen,sp+'/index','Duplicate stream index');seen.add(s['index'])
            _positive(s['time_base'],sp+'/time_base');sd=_positive(s['duration'],sp+'/duration',True)
            if s['type'] in {'video','image'}:_positive(s['sar'],sp+'/sar')
            if s['type']=='video':
                pts=[_q(x,sp+'/frame_pts') for x in s['frame_pts']]
                _require(all(a<b for a,b in zip(pts,pts[1:])),sp+'/frame_pts','Frame PTS must increase')
                _require(all(0<=x<=sd for x in pts),sp+'/frame_pts','Relative frame PTS out of bounds')
            if s['type']=='audio':
                _require(s['channels']=={'mono':1,'stereo':2}[s['channel_layout']],sp,'Channel count/layout mismatch')
    for i,f in enumerate(data['fonts']):
        p=f'/fonts/{i}';register(f,p);fonts[f['id']]=f
        consistent_content(f,('font',f['sha256'],f['face_index']),p)
        _require(f['sha256']==f['path_ref']['asset_hash'],p,'Font/path hash mismatch')
    _require(len(fonts)<=4096,'/fonts','Font graph exceeds 4096 nodes')
    _require(sum(len(f['fallback_ids']) for f in fonts.values())<=65536,'/fonts','Font graph exceeds 65536 edges')
    for font in fonts.values():
        children=font['fallback_ids']
        _require(len(children)==len(set(children)),'/fonts','Duplicate fallback reference')
        _require(all(child in fonts for child in children),'/fonts','Missing fallback font','font_reference')
    # Iterative color DFS visits every node/edge once; shared DAGs never expand recursively.
    colors={}
    for root in fonts:
        if colors.get(root)==2:continue
        stack=[(root,False)]
        while stack:
            fid,leaving=stack.pop()
            if leaving:
                colors[fid]=2
                continue
            color=colors.get(fid,0)
            _require(color!=1,'/fonts','Font fallback cycle')
            if color==2:continue
            colors[fid]=1
            stack.append((fid,True))
            for child in reversed(fonts[fid]['fallback_ids']):
                stack.append((child,False))
    clip_intervals={}
    for i,c in enumerate(data['clips']):
        p=f'/clips/{i}';register(c,p);clips[c['id']]=c
        _require(c['asset_id'] in assets,p+'/asset_id','Missing asset','asset_reference');asset=assets[c['asset_id']]
        a,b=_interval(c['source_in'],c['source_out'],p+'/source');speed=_positive(c['speed'],p+'/speed');start=_positive(c['output_start'],p+'/output_start',True);freeze=_positive(c['freeze_duration'],p+'/freeze_duration',True)
        if asset['kind']=='image':_require(c['video_stream_index'] is None,p,'Image must not select video stream')
        else:
            st=_stream(asset,c['video_stream_index'],'video',p+'/video_stream_index');_require(b<=_q(st['duration'],p),p+'/source_out','Clip exceeds selected video stream')
        end=start+(b-a)/speed+freeze;_require(end<=duration,p,'Clip exceeds output duration');clip_intervals[c['id']]=(start,end)
        _crop(c['crop'],p+'/crop');_transform(c['transform'],p+'/transform');_positive(c['background']['blur_amount'],p+'/background/blur_amount',True)
        color={k:_q(v,p+'/color/'+k) for k,v in c['color'].items()}
        _require(-1<=color['brightness']<=1 and 0<=color['contrast']<=4 and 0<=color['saturation']<=4 and 0<color['gamma']<=10 and -1<=color['temperature']<=1,p+'/color','Color parameter outside declared range')
    transitions={}
    for i,t in enumerate(data['transitions']):
        p=f'/transitions/{i}';register(t,p);left,right=t['left_clip_id'],t['right_clip_id'];_require(left in clips and right in clips and left!=right,p,'Transition clip reference invalid')
        key=frozenset([left,right]);_require(key not in transitions,p,'Duplicate transition');overlap=min(clip_intervals[left][1],clip_intervals[right][1])-max(clip_intervals[left][0],clip_intervals[right][0]);amount=_positive(t['duration'],p+'/duration')
        _require(overlap==amount,p,'Declared overlap differs from clip intervals');transitions[key]=t
    clip_ids=list(clips)
    for n,a in enumerate(clip_ids):
        for b in clip_ids[n+1:]:
            overlap=min(clip_intervals[a][1],clip_intervals[b][1])-max(clip_intervals[a][0],clip_intervals[b][0])
            _require(overlap<=0 or frozenset([a,b]) in transitions,'/clips','Undeclared overlapping clips')
    events=sorted([(start,1) for start,end in clip_intervals.values()]+[(end,-1) for start,end in clip_intervals.values()]);active=0
    for _,change in events:
        active+=change;_require(active<=2,'/clips','Triple overlap is not supported by schema v1')
    for i,c in enumerate(data['audio']['clips']):
        p=f'/audio/clips/{i}';register(c,p);audio[c['id']]=c
        _require(c['asset_id'] in assets,p,'Missing audio asset','asset_reference');st=_stream(assets[c['asset_id']],c['audio_stream_index'],'audio',p+'/audio_stream_index')
        a,b=_interval(c['source_in'],c['source_out'],p+'/source');speed=_positive(c['speed'],p+'/speed');start=_positive(c['output_start'],p+'/output_start',True);length=(b-a)/speed
        _require(b<=_q(st['duration'],p) and start+length<=duration,p,'Audio exceeds selected stream/output')
        _require(-1<=_q(c['pan'],p+'/pan')<=1,p+'/pan','Pan outside[-1,1]')
        fi,fo=(_positive(c[k],p+'/'+k,True) for k in ['fade_in','fade_out']);_require(fi<=length and fo<=length,p,'Fade exceeds audio clip')
    layer_ids={l['id'] for l in data['layers']};cue_ids=set();cue_refs=[];group_counts={}
    for i,l in enumerate(data['layers']):
        p=f'/layers/{i}';register(l,p);_transform(l['transform'],p+'/transform');last=Fraction(0)
        group_id=l.get('group_id')
        if group_id is not None:
            _require(isinstance(group_id,str) and bool(group_id),p+'/group_id','Invalid layer group ID')
            group_counts[group_id]=group_counts.get(group_id,0)+1
        for j,interval in enumerate(l['intervals']):
            a,b=_interval(interval['start'],interval['end'],p+f'/intervals/{j}',duration);_require(a>=last,p+'/intervals','Intervals overlap/out of order');last=b
        style,content=l['style'],l['content']
        if l['type'] in {'text','subtitle'}:
            _require('font_id' in style and style['font_id'] in fonts,p+'/style','Missing/incorrect font style','font_reference')
            size=_positive(style['size_px'],p+'/style/size_px');minimum=_positive(style['min_size_px'],p+'/style/min_size_px');_require(minimum<=size,p+'/style','Minimum font size exceeds selected size')
            for k in ['line_spacing','wrap_width_px']:_positive(style[k],p+'/style/'+k)
            for group,keys in [('outline',['width_px']),('shadow',['blur_px']),('background',['padding_px','radius_px'])]:
                for k in keys:_positive(style[group][k],p+'/style/'+group+'/'+k,True)
            _require(isinstance(content,dict) and ('text' in content if l['type']=='text' else 'cues' in content),p+'/content','Layer content/type mismatch')
        elif l['type']=='logo':
            _require(isinstance(content,dict) and 'asset_id' in content and content['asset_id'] in assets,p+'/content','Missing logo asset')
            _require(assets[content['asset_id']]['kind']=='image' and 'crop' in style,p,'Logo requires image/style');_crop(style['crop'],p+'/style/crop')
            for k in ['outline_width_px','shadow_blur_px']:_positive(style[k],p+'/style/'+k,True)
        else:
            _require(content is None and 'mode' in style,p,'Mask style/content mismatch')
            for k in ['amount','feather_px','radius_px']:_positive(style[k],p+'/style/'+k,True)
        if l['type']=='subtitle':
            _positive(content['gap_px'],p+'/content/gap_px',True)
            _require(content['linked_track_id'] is None or content['linked_track_id'] in layer_ids,p+'/content','Missing linked track')
            for j,c in enumerate(content['cues']):
                cp=p+f'/content/cues/{j}';register(c,cp);cue_ids.add(c['id']);cue_refs.append((c['source_cue_id'],cp))
                a,b=_q(c['start'],cp+'/start'),_q(c['end'],cp+'/end');_require(a<b,cp,'Cue interval empty/reversed')
                if a<0 or b>duration:warnings.append(Diagnostic('cue_range',cp,'Cue extends outside output; mapping/intersection required'))
                if not c['text']:warnings.append(Diagnostic('empty_cue',cp,'Empty cue text'))
                if c['time_basis']=='output':
                    _require(c['asset_id'] is None and c['subtitle_stream_index'] is None and c['source_track_id'] is None and c['sidecar_origin'] is None and not c['segment_ids'],cp,'Output cue has ambiguous source binding')
                else:
                    _require(c['asset_id'] in assets and bool(c['source_track_id']) and bool(c['segment_ids']),cp,'Source cue requires asset/track/segments')
                    if c['subtitle_stream_index'] is None:_require(c['sidecar_origin'] is not None,cp,'Sidecar origin required')
                    else:
                        _stream(assets[c['asset_id']],c['subtitle_stream_index'],'subtitle',cp);_require(c['sidecar_origin'] is None,cp,'Embedded cue cannot also apply sidecar origin')
                    for sid in c['segment_ids']:_require(sid in clips and clips[sid]['asset_id']==c['asset_id'],cp,'Cue segment missing or wrong asset')
        seen=set()
        for j,k in enumerate(l['keyframes']):
            kp=p+f'/keyframes/{j}';t=_q(k['time'],kp+'/time');value=_q(k['value'],kp+'/value');ref=k['reference_clip_id']
            if k['time_mode']=='absolute':_require(ref is None,kp,'Absolute keyframe must not reference clip');effective=t
            else:
                _require(0<=t<=1,kp,'Relative time outside[0,1]');_require(ref is None or ref in clips,kp,'Missing keyframe clip')
                start,end=clip_intervals[ref] if ref else (Fraction(0),duration);effective=start+t*(end-start)
            _require(0<=effective<=duration,kp,'Keyframe time outside output');key=(k['property'],effective);_require(key not in seen,kp,'Duplicate effective keyframe time');seen.add(key)
            if k['property'] in {'width','height','scale_x','scale_y'}:_require(value>0,kp,'Size/scale must be positive')
            if k['property']=='opacity':_require(0<=value<=1,kp,'Opacity outside[0,1]')
    for group_id,count in group_counts.items():
        _require(count>=2,'/layers','A layer group must contain at least two members')
    for ref,path in cue_refs:_require(ref is None or ref in cue_ids,path,'Missing source cue reference')
    for i,d in enumerate(data['audio']['master']['ducking']):
        p=f'/audio/master/ducking/{i}';_interval(d['start'],d['end'],p,duration);targets=set(d['target_audio_clip_ids']);sources=set(d['sidechain_audio_clip_ids'])
        _require(targets<=audio.keys() and sources<=audio.keys() and not targets&sources,p,'Invalid/overlapping duck targets and sidechain')
        _positive(d['attack'],p+'/attack',True);_positive(d['release'],p+'/release',True)
        if d['source_mode']=='signal_envelope':_require(bool(sources) and isinstance(d['envelope_hash'],str) and len(d['envelope_hash'])==64,p,'Signal duck requires sidechain and measured envelope hash')
        else:_require(not sources and d['envelope_hash'] is None,p,'Marked duck cannot imply measured sidechain')
    return tuple(warnings)

@dataclass(frozen=True, init=False)
class CompositionPlan:
    canonical_json: str
    diagnostics: tuple[Diagnostic,...]

    def __init__(self, *args, **kwargs):
        raise TypeError('Use CompositionPlan.parse; direct unchecked construction is forbidden')

    @classmethod
    def parse(cls, source: str | bytes | Mapping[str,Any]) -> 'CompositionPlan':
        try:
            raw=source if isinstance(source,(str,bytes)) else canonical(source)
            if len(raw.encode('utf-8') if isinstance(raw,str) else raw)>MAX_PLAN_BYTES:
                raise PlanError('too_large','','Plan exceeds32MiB')
            data=json.loads(raw,object_pairs_hook=_unique_pairs,parse_constant=_number_constant)
        except (UnicodeError,json.JSONDecodeError,TypeError,ValueError,RecursionError) as exc:
            if isinstance(exc,PlanError):raise
            raise PlanError('invalid_json','',str(exc)) from exc
        stack=[(data,0)]
        while stack:
            value,depth=stack.pop()
            _require(depth<=64,'','JSON nesting exceeds 64 levels','too_deep')
            if isinstance(value,dict):stack.extend((child,depth+1) for child in value.values())
            elif isinstance(value,list):stack.extend((child,depth+1) for child in value)
        error=next(_VALIDATOR.iter_errors(data),None)
        if error is not None:raise PlanError('schema','/'+ '/'.join(map(str,error.absolute_path)),error.message)
        diagnostics=_validate(data)
        result=object.__new__(cls)
        object.__setattr__(result,'canonical_json',canonical(data))
        object.__setattr__(result,'diagnostics',diagnostics)
        return result

    def to_dict(self) -> dict:
        return json.loads(self.canonical_json)

    def execution_digest(self, context: Mapping[str,Any]) -> str:
        """Full execution envelope: paths/context intentionally affect this digest."""
        return sha256(canonical({'composition':self.to_dict(),'execution_context':dict(context)}).encode()).hexdigest()

    def render_content_digest(self, renderer_build_hash: str) -> str:
        _require(isinstance(renderer_build_hash,str) and re.fullmatch('[a-f0-9]{64}',renderer_build_hash) is not None,'renderer_build_hash','Pinned renderer/tool build hash required')
        d=self.to_dict();d.pop('id');d.pop('revision');d.pop('provenance');d.pop('timeline_markers',None)
        # IDs only link records. Canonical tokens preserve actual order/references and z tie order.
        aliases={a['id']:'asset:'+a['sha256'] for a in d['assets']}
        aliases.update({f['id']:'font:'+f['sha256']+':'+str(f['face_index']) for f in d['fonts']})
        aliases.update({c['id']:f'clip:{i}' for i,c in enumerate(d['clips'])})
        aliases.update({a['id']:f'audio:{i}' for i,a in enumerate(d['audio']['clips'])})
        d['layers'].sort(key=lambda x:(x['z'],x['id']))
        aliases.update({l['id']:f'layer:{i}' for i,l in enumerate(d['layers'])})
        for i,l in enumerate(d['layers']):
            if l['type']=='subtitle':
                for j,c in enumerate(l['content']['cues']):aliases[c['id']]=f'cue:{i}:{j}'
        for i,t in enumerate(d['transitions']):aliases[t['id']]=f'transition:{i}'
        reference_fields={'id','asset_id','font_id','linked_track_id','source_cue_id','reference_clip_id','left_clip_id','right_clip_id','fallback_ids','segment_ids','target_audio_clip_ids','sidechain_audio_clip_ids'}
        def project(v,field=None):
            if isinstance(v,dict):return {k:project(val,k) for k,val in v.items() if k not in {'path_ref','locked_fields','manual_lock','license_ref','provenance_ref','source_track_id'}}
            if isinstance(v,list):return [project(x,field) for x in v]
            if isinstance(v,str) and field in reference_fields:return aliases.get(v,v)
            return v
        d=project(d);d['assets'].sort(key=canonical);d['fonts'].sort(key=canonical)
        return sha256(canonical({'projection_version':'render-content-1','render_plan':d,'renderer_build_hash':renderer_build_hash}).encode()).hexdigest()

    def time_segments(self) -> dict[str,TimeSegment]:
        d=self.to_dict();assets={a['id']:a for a in d['assets']};result={}
        for c in d['clips']:
            if assets[c['asset_id']]['kind']=='image':continue
            s=_stream(assets[c['asset_id']],c['video_stream_index'],'video','clip')
            result[c['id']]=TimeSegment(c['id'],c['asset_id'],s['index'],rational(s['start_time']),rational(c['source_in']),rational(c['source_out']),rational(c['output_start']),rational(c['speed']))
        return result
