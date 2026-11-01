"""Closed immutable required-output intent, not filesystem or validation authority."""
from dataclasses import dataclass, fields
from fractions import Fraction
from pathlib import PurePosixPath, PureWindowsPath
import re
from fonesi_edit.artifacts.filesystem import safe_name
from fonesi_edit.media.validation import ExpectedStream
from fonesi_edit.subtitles.adapter import ENCODINGS

MAX_RATIONAL_BITS=128


@dataclass(frozen=True)
class RequiredOutput:
    role:str
    kind:str
    destination_root:str
    final_name:str
    expected_streams:tuple[ExpectedStream,...]=()
    subtitle_format:str|None=None
    subtitle_encoding:str|None=None
    subtitle_sha256:str|None=None

    def __post_init__(self):
        if type(self.role) is not str or re.fullmatch(r'[a-z][a-z0-9_]{0,63}',self.role) is None:
            raise ValueError('Bounded ASCII artifact role required')
        if self.kind not in ('media','subtitle') or type(self.kind) is not str:
            raise ValueError('Explicit supported output kind required')
        root=self.destination_root
        if type(root) is not str or not 1<=len(root)<=4096 or '\0' in root:
            raise ValueError('Bounded explicit output root required')
        windows=PureWindowsPath(root);posix=PurePosixPath(root)
        if root.startswith(('\\\\','//')):
            raise ValueError('Network output requires separate capability admission')
        if not ((windows.is_absolute() and re.fullmatch(r'[A-Za-z]:',windows.drive)) or posix.is_absolute()):
            raise ValueError('Absolute output root required')
        if '..' in windows.parts or '..' in posix.parts:
            raise ValueError('Parent traversal in output root')
        safe_name(self.final_name)
        if type(self.expected_streams) is not tuple or len(self.expected_streams)>32 or any(type(v) is not ExpectedStream for v in self.expected_streams):
            raise ValueError('Closed bounded stream expectation tuple required')
        if len({v.index for v in self.expected_streams})!=len(self.expected_streams):raise ValueError('Duplicate expected stream')
        for stream in self.expected_streams:
            for field in fields(stream):
                value=getattr(stream,field.name)
                if type(value) is Fraction and (value.numerator.bit_length()>MAX_RATIONAL_BITS or value.denominator.bit_length()>MAX_RATIONAL_BITS):
                    raise ValueError('Bounded rational policy required')
        subtitle=(self.subtitle_format,self.subtitle_encoding,self.subtitle_sha256)
        if self.kind=='media':
            if any(v is not None for v in subtitle):raise ValueError('Subtitle policy on media output')
        elif self.expected_streams:raise ValueError('Media policy on subtitle output')
        elif any(v is not None for v in subtitle):
            if (type(self.subtitle_format) is not str or self.subtitle_format not in {'srt','vtt','ass','ssa'} or
                type(self.subtitle_encoding) is not str or self.subtitle_encoding not in ENCODINGS or
                type(self.subtitle_sha256) is not str or re.fullmatch('[0-9a-f]{64}',self.subtitle_sha256) is None):
                raise ValueError('Complete explicit subtitle validation policy required')

    def to_dict(self):
        data={'role':self.role,'kind':self.kind,'destination_root':self.destination_root,'final_name':self.final_name}
        if self.expected_streams:
            data['validation']={'policy':'media-probe-decode-v1','streams':[
                {field.name:([value.numerator,value.denominator] if type(value) is Fraction else value)
                 for field in fields(item) for value in [getattr(item,field.name)]}
                for item in sorted(self.expected_streams,key=lambda value:value.index)]}
        elif self.subtitle_sha256 is not None:
            data['validation']={'policy':'subtitle-bytes-parse-v1','format':self.subtitle_format,
                                'encoding':self.subtitle_encoding,'sha256':self.subtitle_sha256}
        return data

    @property
    def publication_ready(self):return bool(self.expected_streams) if self.kind=='media' else self.subtitle_sha256 is not None

    @classmethod
    def from_dict(cls,data):
        basic={'role','kind','destination_root','final_name'}
        if type(data) is not dict or set(data) not in (basic,basic|{'validation'}):raise ValueError('Unknown output definition keys')
        kwargs={key:data[key] for key in basic}
        if 'validation' in data:
            v=data['validation']
            if type(v) is not dict:raise ValueError('Closed validation policy required')
            if v.get('policy')=='media-probe-decode-v1' and set(v)=={'policy','streams'}:
                if type(v['streams']) is not list or not 1<=len(v['streams'])<=32:raise ValueError('Bounded expected stream list required')
                streams=[]
                for raw in v['streams']:
                    if type(raw) is not dict or set(raw)!={field.name for field in fields(ExpectedStream)}:raise ValueError('Closed stream record required')
                    values=dict(raw)
                    for key in ('start','duration','tolerance','frame_rate'):
                        value=values[key]
                        if value is None and key=='frame_rate':continue
                        if (type(value) is not list or len(value)!=2 or any(type(n) is not int or n.bit_length()>MAX_RATIONAL_BITS for n in value) or value[1]<=0):
                            raise ValueError('Bounded rational policy required')
                        number=Fraction(*value)
                        if [number.numerator,number.denominator]!=value:raise ValueError('Canonical rational policy required')
                        values[key]=number
                    streams.append(ExpectedStream(**values))
                kwargs['expected_streams']=tuple(streams)
            elif v.get('policy')=='subtitle-bytes-parse-v1' and set(v)=={'policy','format','encoding','sha256'}:
                kwargs.update(subtitle_format=v['format'],subtitle_encoding=v['encoding'],subtitle_sha256=v['sha256'])
            else:raise ValueError('Unsupported validation policy')
        return cls(**kwargs)


@dataclass(frozen=True)
class RequiredOutputs:
    items:tuple[RequiredOutput,...]

    def __post_init__(self):
        if type(self.items) is not tuple or not 1<=len(self.items)<=32 or any(type(item) is not RequiredOutput for item in self.items):
            raise ValueError('Nonempty bounded immutable output tuple required')
        if len({item.role for item in self.items})!=len(self.items):raise ValueError('Duplicate required artifact role')
        # Exact duplicates only. Native aliases/case semantics require pinned admission.
        if len({(item.destination_root,item.final_name) for item in self.items})!=len(self.items):
            raise ValueError('Duplicate output destination')

    def to_dict(self):
        return {'version':2 if any(item.publication_ready for item in self.items) else 1,
                'required': [item.to_dict() for item in sorted(self.items,key=lambda item:item.role)]}

    @classmethod
    def from_dict(cls,data):
        if (type(data) is not dict or set(data)!={'version','required'} or type(data['version']) is not int or
            data['version'] not in (1,2) or type(data['required']) is not list or not 1<=len(data['required'])<=32):
            raise ValueError('Unsupported required-output manifest')
        result=cls(tuple(RequiredOutput.from_dict(item) for item in data['required']))
        if result.to_dict()!=data:raise ValueError('Noncanonical output manifest')
        return result

    def validate_composition(self, composition):
        output=composition['output']
        for item in self.items:
            for stream in item.expected_streams:
                if stream.start!=0 or stream.duration!=Fraction(*output['duration']):
                    raise ValueError('Expected media timing contradicts composition output')
                if stream.kind=='video':
                    if (stream.codec!=output['video_codec'] or stream.width!=output['width'] or stream.height!=output['height'] or stream.frame_rate!=Fraction(*output['fps'])):
                        raise ValueError('Expected video contradicts composition output')
                elif (stream.codec!=output['audio_codec'] or stream.sample_rate!=output['sample_rate'] or stream.channels!=({'mono':1,'stereo':2}[output['channel_layout']])):
                    raise ValueError('Expected audio contradicts composition output')
