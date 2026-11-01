"""Typed, unresolved-capable ffprobe observations; never render-ready assets."""
from dataclasses import dataclass,asdict
from fractions import Fraction
import json,re
from .probe import ProbeResult,_json_pairs,_finite_float,_reject_constant,ProbeError
from .validation import _number,MediaValidationError


@dataclass(frozen=True)
class StreamObservation:
    index:int
    kind:str
    codec:str|None
    time_base:Fraction|None
    start_pts:int|None
    duration_ts:int|None
    start:Fraction|None
    duration:Fraction|None
    start_basis:str
    duration_basis:str
    width:int|None
    height:int|None
    sar:Fraction|None
    display_matrix:tuple[int,...]|None
    rotation_degrees:Fraction|None
    rotation_basis:str
    sample_rate:int|None
    channels:int|None
    channel_layout:str|None
    attached_picture:bool|None
    diagnostics:tuple[str,...]


@dataclass(frozen=True)
class MediaObservation:
    sha256:str
    container_duration:Fraction|None
    streams:tuple[StreamObservation,...]
    diagnostics:tuple[str,...]
    render_ready:bool=False
    def to_dict(self):
        def encode(value):
            if isinstance(value,Fraction):return {'num':value.numerator,'den':value.denominator}
            if isinstance(value,dict):return {k:encode(v) for k,v in value.items()}
            if isinstance(value,(tuple,list)):return [encode(v) for v in value]
            return value
        return encode(asdict(self))


def _integer(value,*,minimum=-(2**63),maximum=2**63-1):
    if type(value) is int:number=value
    elif isinstance(value,str) and len(value)<=20 and re.fullmatch(r'-?[0-9]+',value):number=int(value)
    else:return None
    return number if minimum<=number<=maximum else None


def _rational(value,*,positive=False,nonnegative=False,colon=False):
    if colon and isinstance(value,str):value=value.replace(':','/')
    try:number=_number(value)
    except MediaValidationError:return None
    if number.numerator.bit_length()>128 or number.denominator.bit_length()>128:return None
    if positive and number<=0 or nonnegative and number<0:return None
    return number


def _label(value,limit=128):
    return value if isinstance(value,str) and 0<len(value)<=limit and re.fullmatch(r'[A-Za-z0-9_.() +\-]+',value) else None


def _matrix(value):
    if not isinstance(value,str) or len(value)>512:return None
    lines=[line for line in value.splitlines() if line.strip()]
    if len(lines)!=3:return None
    result=[]
    for index,line in enumerate(lines):
        m=re.fullmatch(r'\s*([0-9a-fA-F]{8}):\s+(-?[0-9]+)\s+(-?[0-9]+)\s+(-?[0-9]+)\s*',line)
        if not m or int(m[1],16)!=index:return None
        values=[_integer(x,minimum=-(2**31),maximum=2**31-1) for x in m.groups()[1:]]
        if None in values:return None
        result.extend(values)
    return tuple(result)


def _timing(raw,ticks,base,field,issues):
    decimal=_rational(raw.get(field),nonnegative=field=='duration')
    if ticks is not None and base is not None:
        exact=ticks*base
        # ffprobe decimal summaries are rounded; record only discrepancies larger
        # than half their displayed decimal unit, never replace exact tick timing.
        text=raw.get(field)
        if decimal is not None:
            precision=len(text.partition('.')[2]) if isinstance(text,str) and '.' in text else 0
            resolution=Fraction(0) if isinstance(text,str) and '/' in text else Fraction(1,2*10**precision)
            if abs(decimal-exact)>resolution:issues.append(field.upper()+'_SUMMARY_CONFLICT')
        return exact,'STREAM_TICKS'
    if decimal is not None:return decimal,'RATIONAL_SUMMARY' if isinstance(raw.get(field),str) and '/' in raw[field] else 'DECIMAL_SUMMARY'
    issues.append(field.upper()+'_UNKNOWN');return None,'UNKNOWN'


def normalize_probe(result:ProbeResult)->MediaObservation:
    if type(result) is not ProbeResult or not isinstance(result.sha256,str) or not re.fullmatch(r'[a-f0-9]{64}',result.sha256):
        raise ProbeError('Typed content-bound probe observation required')
    if not isinstance(result.metadata_json,str) or len(result.metadata_json)>16*1024*1024:
        raise ProbeError('Bounded probe metadata required')
    try:
        if len(result.metadata_json.encode())>16*1024*1024:raise ProbeError('Bounded probe metadata required')
    except UnicodeError:raise ProbeError('Invalid UTF-8 probe metadata') from None
    try:raw=json.loads(result.metadata_json,object_pairs_hook=_json_pairs,parse_float=_finite_float,parse_constant=_reject_constant)
    except (ValueError,RecursionError):raise ProbeError('Malformed probe observation') from None
    if not isinstance(raw,dict) or not isinstance(raw.get('streams'),list) or not 1<=len(raw['streams'])<=256:
        raise ProbeError('Nonempty bounded stream observations required')
    streams=[];seen=set();global_issues=[]
    for stream in raw['streams']:
        if not isinstance(stream,dict):raise ProbeError('Invalid stream record')
        index=_integer(stream.get('index'),minimum=0,maximum=2**31-1)
        if index is None or index in seen:raise ProbeError('Unique container-global stream index required')
        seen.add(index);issues=[];kind=stream.get('codec_type')
        if kind not in ('video','audio','subtitle','data','attachment'):kind='unknown'
        if kind not in ('video','audio','subtitle'):issues.append('NON_TIMELINE_OR_UNKNOWN_TRACK')
        codec=_label(stream.get('codec_name'));base=_rational(stream.get('time_base'),positive=True)
        if codec is None:issues.append('CODEC_UNKNOWN')
        if base is None:issues.append('TIME_BASE_UNKNOWN')
        start_pts=_integer(stream.get('start_pts'));duration_ts=_integer(stream.get('duration_ts'),minimum=0)
        start,start_basis=_timing(stream,start_pts,base,'start_time',issues)
        duration,duration_basis=_timing(stream,duration_ts,base,'duration',issues)
        width=_integer(stream.get('width'),minimum=1,maximum=2**31-1)
        height=_integer(stream.get('height'),minimum=1,maximum=2**31-1)
        sar=_rational(stream.get('sample_aspect_ratio'),positive=True,colon=True)
        matrix=None;rotation=None;rotation_basis='UNKNOWN';side=stream.get('side_data_list',[])
        if not isinstance(side,list) or len(side)>256:raise ProbeError('Bounded side-data records required')
        display=[x for x in side if isinstance(x,dict) and x.get('side_data_type')=='Display Matrix']
        if len(display)>1:issues.append('AMBIGUOUS_DISPLAY_MATRIX')
        elif display:
            matrix=_matrix(display[0].get('displaymatrix'));rotation=_rational(display[0].get('rotation'))
            if rotation is not None:rotation_basis='DISPLAY_MATRIX_SUMMARY'
            else:issues.append('ROTATION_SUMMARY_UNKNOWN')
            if matrix is None:issues.append('DISPLAY_MATRIX_INVALID')
        elif not display:
            tags=stream.get('tags')
            rotation=_rational(tags.get('rotate')) if isinstance(tags,dict) else None
            if rotation is not None:rotation_basis='LEGACY_ROTATE_TAG'
        sample=_integer(stream.get('sample_rate'),minimum=1,maximum=2**31-1)
        channels=_integer(stream.get('channels'),minimum=1,maximum=2**31-1)
        layout=_label(stream.get('channel_layout'))
        disposition=stream.get('disposition');attached=None
        if isinstance(disposition,dict) and type(disposition.get('attached_pic')) is int and disposition['attached_pic'] in (0,1):attached=bool(disposition['attached_pic'])
        if attached:issues.append('ATTACHED_PICTURE_NOT_TIMELINE_VIDEO')
        if kind=='video':
            if width is None or height is None:issues.append('GEOMETRY_UNKNOWN')
            if sar is None:issues.append('SAR_UNKNOWN')
            if rotation_basis=='UNKNOWN' and matrix is None:issues.append('ORIENTATION_NOT_OBSERVED')
            issues.append('FRAME_PTS_NOT_OBSERVED')
        if kind=='audio' and (sample is None or channels is None or layout is None):issues.append('AUDIO_LAYOUT_OR_RATE_UNKNOWN')
        if kind=='audio' and layout not in ('mono','stereo'):issues.append('COMPOSITION_LAYOUT_UNRESOLVED')
        streams.append(StreamObservation(index,kind,codec,base,start_pts,duration_ts,start,duration,start_basis,duration_basis,
                       width,height,sar,matrix,rotation,rotation_basis,sample,channels,layout,attached,tuple(issues)))
    format_=raw.get('format');duration=_rational(format_.get('duration'),nonnegative=True) if isinstance(format_,dict) else None
    if duration is None:global_issues.append('CONTAINER_DURATION_UNKNOWN')
    if not any(s.kind=='audio' for s in streams):global_issues.append('NO_AUDIO_TRACK')
    return MediaObservation(result.sha256,duration,tuple(streams),tuple(global_issues))
