"""Unresolved source-library facts, separate from render-ready composition assets."""
from dataclasses import dataclass,fields,replace
from fractions import Fraction
from pathlib import PurePosixPath,PureWindowsPath
import re,uuid
from fonesi_edit.media.observations import MediaObservation,StreamObservation

MAX_ITEMS=10000
MAX_STREAMS=256
MAX_PATH_CHARS=32768

class MediaLibraryError(ValueError):pass
class MediaLibraryConflict(MediaLibraryError):pass


def _require(condition,message):
    if not condition:raise MediaLibraryError(message)

def _hash(value):
    _require(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'Exact SHA256 required')

def _integer(value,low,high,*,nullable=False):
    if value is None and nullable:return
    _require(type(value) is int and low<=value<=high,'Bounded exact integer required')

def _fraction(value,*,nullable=True,low=None):
    if value is None and nullable:return
    _require(type(value) is Fraction,'Exact rational required')
    _require(value.numerator.bit_length()<=256 and value.denominator.bit_length()<=256,'Rational exceeds256-bit bound')
    if low is not None:_require(value>=low,'Rational below valid bound')

def _read_fraction(value):
    if value is None:return None
    _require(type(value) is dict and set(value)=={'num','den'},'Exact rational fields required')
    n,d=value['num'],value['den']
    _require(type(n) is int and type(d) is int and d>0 and n.bit_length()<=256 and d.bit_length()<=256,'Bounded rational components required')
    result=Fraction(n,d)
    _require((result.numerator,result.denominator)==(n,d),'Canonical reduced rational required')
    return result

STREAM_DIAGNOSTICS=frozenset(('NON_TIMELINE_OR_UNKNOWN_TRACK','CODEC_UNKNOWN','TIME_BASE_UNKNOWN',
    'START_TIME_SUMMARY_CONFLICT','DURATION_SUMMARY_CONFLICT','START_TIME_UNKNOWN','DURATION_UNKNOWN',
    'AMBIGUOUS_DISPLAY_MATRIX','ROTATION_SUMMARY_UNKNOWN','DISPLAY_MATRIX_INVALID',
    'ATTACHED_PICTURE_NOT_TIMELINE_VIDEO','GEOMETRY_UNKNOWN','SAR_UNKNOWN','ORIENTATION_NOT_OBSERVED',
    'FRAME_PTS_NOT_OBSERVED','AUDIO_LAYOUT_OR_RATE_UNKNOWN','COMPOSITION_LAYOUT_UNRESOLVED'))
GLOBAL_DIAGNOSTICS=frozenset(('CONTAINER_DURATION_UNKNOWN','NO_AUDIO_TRACK'))
RATIONAL_FIELDS=('time_base','start','duration','sar','rotation_degrees')


def _diagnostics(value,allowed):
    _require(type(value) is tuple and len(value)<=len(allowed),'Bounded diagnostic tuple required')
    _require(all(type(x) is str and x in allowed for x in value) and len(set(value))==len(value),'Unknown/duplicate diagnostic code')


def validate_observation(value):
    _require(type(value) is MediaObservation,'Typed media observation required')
    _hash(value.sha256);_require(value.render_ready is False,'Library observations are NEVER render readiness')
    _fraction(value.container_duration,low=0)
    _require(type(value.streams) is tuple and 1<=len(value.streams)<=MAX_STREAMS,'Bounded stream tuple required')
    _diagnostics(value.diagnostics,GLOBAL_DIAGNOSTICS);seen=set()
    for stream in value.streams:
        _require(type(stream) is StreamObservation,'Typed stream observation required')
        _integer(stream.index,0,2**31-1);_require(stream.index not in seen,'Duplicate container-global stream index');seen.add(stream.index)
        _require(type(stream.kind) is str and stream.kind in ('video','audio','subtitle','data','attachment','unknown'),'Unknown stream kind')
        for text in (stream.codec,stream.channel_layout):
            _require(text is None or (type(text) is str and 0<len(text)<=128 and re.fullmatch(r'[A-Za-z0-9_.() +\-]+',text) is not None),'Bounded sanitized stream label required')
        for name in RATIONAL_FIELDS:_fraction(getattr(stream,name))
        for name in ('time_base','sar'):
            item=getattr(stream,name);_require(item is None or item>0,'Positive stream scale required')
        _require(stream.duration is None or stream.duration>=0,'Nonnegative stream duration required')
        _integer(stream.start_pts,-2**63,2**63-1,nullable=True);_integer(stream.duration_ts,0,2**63-1,nullable=True)
        for name in ('width','height','sample_rate','channels'):_integer(getattr(stream,name),1,2**31-1,nullable=True)
        _require(stream.attached_picture is None or type(stream.attached_picture) is bool,'Exact attached-picture flag required')
        if stream.display_matrix is not None:
            _require(type(stream.display_matrix) is tuple and len(stream.display_matrix)==9,'Exact raw display matrix required')
            for number in stream.display_matrix:_integer(number,-2**31,2**31-1)
        for time,ticks,basis in ((stream.start,stream.start_pts,stream.start_basis),(stream.duration,stream.duration_ts,stream.duration_basis)):
            _require(type(basis) is str and basis in ('UNKNOWN','STREAM_TICKS','DECIMAL_SUMMARY','RATIONAL_SUMMARY'),'Exact timing provenance required')
            if ticks is not None and stream.time_base is not None:
                _require(basis=='STREAM_TICKS' and time==ticks*stream.time_base,'Tick-derived timestamp mismatch')
            elif basis=='UNKNOWN':_require(time is None,'Unknown timing cannot contain value')
            else:_require(basis!='STREAM_TICKS' and time is not None,'Summary timing/value mismatch')
        _require(type(stream.rotation_basis) is str and stream.rotation_basis in ('UNKNOWN','DISPLAY_MATRIX_SUMMARY','LEGACY_ROTATE_TAG'),'Exact rotation provenance required')
        _require((stream.rotation_basis=='UNKNOWN')==(stream.rotation_degrees is None),'Rotation summary provenance mismatch')
        if stream.rotation_basis=='LEGACY_ROTATE_TAG':_require(stream.display_matrix is None,'Legacy rotate cannot replace raw matrix')
        _diagnostics(stream.diagnostics,STREAM_DIAGNOSTICS)
        required=set()
        for missing,code in ((stream.codec is None,'CODEC_UNKNOWN'),(stream.time_base is None,'TIME_BASE_UNKNOWN'),
            (stream.start is None,'START_TIME_UNKNOWN'),(stream.duration is None,'DURATION_UNKNOWN'),
            (stream.kind not in ('video','audio','subtitle'),'NON_TIMELINE_OR_UNKNOWN_TRACK'),
            (stream.attached_picture is True,'ATTACHED_PICTURE_NOT_TIMELINE_VIDEO')):
            if missing:required.add(code)
        if stream.kind=='video':
            required.add('FRAME_PTS_NOT_OBSERVED')
            if stream.width is None or stream.height is None:required.add('GEOMETRY_UNKNOWN')
            if stream.sar is None:required.add('SAR_UNKNOWN')
            if stream.rotation_basis=='UNKNOWN' and stream.display_matrix is None:required.add('ORIENTATION_NOT_OBSERVED')
        if stream.kind=='audio':
            if stream.sample_rate is None or stream.channels is None or stream.channel_layout is None:required.add('AUDIO_LAYOUT_OR_RATE_UNKNOWN')
            if stream.channel_layout not in ('mono','stereo'):required.add('COMPOSITION_LAYOUT_UNRESOLVED')
        _require(required<=set(stream.diagnostics),'Unresolved stream facts need explicit diagnostic reasons')
    expected=set()
    if value.container_duration is None:expected.add('CONTAINER_DURATION_UNKNOWN')
    if not any(s.kind=='audio' for s in value.streams):expected.add('NO_AUDIO_TRACK')
    _require(set(value.diagnostics)==expected,'Global observation diagnostics mismatch')
    return value


def observation_from_dict(raw):
    _require(type(raw) is dict and set(raw)=={f.name for f in fields(MediaObservation)},'Exact observation fields required')
    _require(type(raw['streams']) is list and 1<=len(raw['streams'])<=MAX_STREAMS,'Bounded stream list required')
    streams=[]
    for entry in raw['streams']:
        _require(type(entry) is dict and set(entry)=={f.name for f in fields(StreamObservation)},'Exact stream fields required')
        obj=dict(entry)
        for name in RATIONAL_FIELDS:obj[name]=_read_fraction(obj[name])
        for name in ('diagnostics','display_matrix'):
            if obj[name] is not None:
                _require(type(obj[name]) is list and len(obj[name])<=(9 if name=='display_matrix' else len(STREAM_DIAGNOSTICS)),'Bounded exact observation array required');obj[name]=tuple(obj[name])
        streams.append(StreamObservation(**obj))
    _require(type(raw['diagnostics']) is list and len(raw['diagnostics'])<=len(GLOBAL_DIAGNOSTICS),'Bounded diagnostic list required')
    return validate_observation(MediaObservation(raw['sha256'],_read_fraction(raw['container_duration']),tuple(streams),tuple(raw['diagnostics']),raw['render_ready']))


@dataclass(frozen=True)
class MediaPath:
    base:str
    path:str
    asset_hash:str
    def __post_init__(self):
        _hash(self.asset_hash)
        _require(type(self.base) is str and self.base in ('absolute','project'),'Explicit path base required')
        _require(type(self.path) is str and 0<len(self.path)<=MAX_PATH_CHARS and '\0' not in self.path,'Bounded non-NUL path required')
        _require(len(self.path.encode('utf-8'))<=4*MAX_PATH_CHARS,'Bounded UTF-8 path required')
        windows=PureWindowsPath(self.path);posix=PurePosixPath(self.path)
        if self.base=='project':_require(not posix.is_absolute() and not windows.drive and not windows.root,'Ambiguous project-relative path')
        else:_require(posix.is_absolute() or windows.is_absolute(),'Explicit absolute path required')
    def to_dict(self):return {'base':self.base,'path':self.path,'asset_hash':self.asset_hash}
    @classmethod
    def from_dict(cls,raw):
        _require(type(raw) is dict and set(raw)=={'base','path','asset_hash'},'Exact path-reference fields required')
        return cls(**raw)


@dataclass(frozen=True)
class MediaRecord:
    id:str
    sha256:str
    size_bytes:int
    path_ref:MediaPath
    observation_state:str
    observation:MediaObservation|None
    def __post_init__(self):
        try:valid=type(self.id) is str and str(uuid.UUID(self.id))==self.id
        except (ValueError,TypeError,AttributeError):valid=False
        _require(valid,'Canonical independent media UUID required');_hash(self.sha256)
        _integer(self.size_bytes,0,2**63-1)
        _require(type(self.path_ref) is MediaPath and self.path_ref.asset_hash==self.sha256,'Media/path content hash mismatch')
        self.path_ref.__post_init__()
        _require(type(self.observation_state) is str and self.observation_state in ('NOT_PROBED','PROBE_UNAVAILABLE','OBSERVED'),'Explicit observation state required')
        if self.observation_state=='OBSERVED':
            validate_observation(self.observation);_require(self.observation.sha256==self.sha256,'Media/observation hash mismatch')
        else:_require(self.observation is None,'Unobserved record cannot carry fabricated metadata')
    def to_dict(self):
        self.__post_init__()
        return {'id':self.id,'sha256':self.sha256,'size_bytes':self.size_bytes,'path_ref':self.path_ref.to_dict(),
                'observation_state':self.observation_state,'observation':None if self.observation is None else self.observation.to_dict()}
    @classmethod
    def from_dict(cls,raw):
        _require(type(raw) is dict and set(raw)=={f.name for f in fields(cls)},'Exact library record fields required')
        return cls(raw['id'],raw['sha256'],raw['size_bytes'],MediaPath.from_dict(raw['path_ref']),raw['observation_state'],
                   None if raw['observation'] is None else observation_from_dict(raw['observation']))


@dataclass(frozen=True)
class MediaLibrary:
    items:tuple[MediaRecord,...]=()
    def __post_init__(self):
        _require(type(self.items) is tuple and len(self.items)<=MAX_ITEMS,'Bounded immutable source library required')
        ids=set();hashes=set()
        for item in self.items:
            _require(type(item) is MediaRecord,'Typed media record required');item.__post_init__()
            _require(item.id not in ids and item.sha256 not in hashes,'Duplicate library ID/content identity')
            ids.add(item.id);hashes.add(item.sha256)
    def add(self,item):
        _require(type(item) is MediaRecord,'Typed media addition required');item.__post_init__()
        if any(current.id==item.id and current.sha256!=item.sha256 for current in self.items):
            raise MediaLibraryConflict('Media identity cannot change content')
        for current in self.items:
            if current.sha256==item.sha256:
                if replace(item,id=current.id)==current:return self,current.id,False
                raise MediaLibraryConflict('Existing content differs in path/size/observation; explicit relink/refresh required')
        return MediaLibrary((*self.items,item)),item.id,True
    def to_dict(self):
        self.__post_init__();return {'schema_version':1,'items':[x.to_dict() for x in self.items]}
    @classmethod
    def from_dict(cls,raw):
        _require(type(raw) is dict and set(raw)=={'schema_version','items'} and type(raw['schema_version']) is int and raw['schema_version']==1,'Supported source-library schema required')
        _require(type(raw['items']) is list and len(raw['items'])<=MAX_ITEMS,'Bounded source-library array required')
        return cls(tuple(MediaRecord.from_dict(x) for x in raw['items']))
