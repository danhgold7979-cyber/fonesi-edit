"""Actual probe plus full decode observations; not publication/job authority."""
from dataclasses import dataclass
from fractions import Fraction
import math
import os
import re
from pathlib import Path
from typing import Callable
from .probe import inspect_media, fingerprint, ProbeError, ProbeCanceled
from fonesi_edit.jobs.process import run_owned, ProcessError, ProcessCanceled


class MediaValidationError(ProbeError):pass


@dataclass(frozen=True)
class ExpectedStream:
    index:int
    kind:str
    codec:str
    start:Fraction
    duration:Fraction
    tolerance:Fraction
    width:int|None=None
    height:int|None=None
    frame_rate:Fraction|None=None
    sample_rate:int|None=None
    channels:int|None=None

    def __post_init__(self):
        if type(self.index) is not int or self.index<0 or self.kind not in {'video','audio'}:
            raise ValueError('Explicit video/audio stream index required')
        if not isinstance(self.codec,str) or not 1<=len(self.codec)<=64 or not self.codec.isascii() or not self.codec.replace('_','').isalnum():
            raise ValueError('Explicit codec name required')
        if any(type(v) is not Fraction for v in (self.start,self.duration,self.tolerance)):
            raise ValueError('Exact rational timing required')
        if not (self.start>=0 and 0<self.duration<=86400 and 0<=self.tolerance<=min(self.duration/2,Fraction(1,2))):
            raise ValueError('Invalid timing/tolerance bounds')
        if self.kind=='video':
            if any(type(v) is not int or not 1<=v<=16384 for v in (self.width,self.height)) or type(self.frame_rate) is not Fraction or not 0<self.frame_rate<=1000:
                raise ValueError('Video geometry/frame rate required')
            if self.sample_rate is not None or self.channels is not None:raise ValueError('Audio fields on video stream')
        else:
            if type(self.sample_rate) is not int or not 1<=self.sample_rate<=768000 or type(self.channels) is not int or not 1<=self.channels<=64:
                raise ValueError('Audio sample rate/channel count required')
            if any(v is not None for v in (self.width,self.height,self.frame_rate)):raise ValueError('Video fields on audio stream')


@dataclass(frozen=True)
class MediaValidation:
    sha256:str
    streams:tuple[ExpectedStream,...]
    policy:str='probe-and-full-decode-v1'


def _number(value):
    # Never accept binary-float approximations, NaN, booleans or unbounded integers.
    if (type(value) not in (str,int) or len(str(value))>80 or
        re.fullmatch(r'[+-]?[0-9]+(?:\.[0-9]+|/[0-9]+)?',str(value)) is None):
        raise MediaValidationError('Missing/invalid bounded rational metadata')
    try:return Fraction(value)
    except (ValueError,ZeroDivisionError):raise MediaValidationError('Missing/invalid rational metadata') from None


def validate_media(path:Path|str,ffprobe:Path|str,ffmpeg:Path|str,expected:tuple[ExpectedStream,...],*,
                   cancel:Callable[[],bool]=lambda:False,timeout:float=300)->MediaValidation:
    if type(expected) is not tuple or not 1<=len(expected)<=32 or any(type(v) is not ExpectedStream for v in expected) or len({s.index for s in expected})!=len(expected):
        raise ValueError('Nonempty bounded unique expected stream tuple required')
    if type(timeout) not in (int,float) or not math.isfinite(timeout) or timeout<=0:raise ValueError('Finite positive timeout required')
    path=Path(path).absolute();decoder=Path(ffmpeg).absolute()
    if not decoder.is_file() or not os.access(decoder,os.X_OK):raise MediaValidationError('Explicit decoder executable unavailable')
    if cancel():raise ProbeCanceled('Media validation canceled')
    try:
        probe=inspect_media(path,ffprobe,cancel=cancel,timeout=timeout)
        streams=probe.metadata()['streams']
        if len(streams)!=len(expected) or {s['index'] for s in streams}!={s.index for s in expected}:
            raise MediaValidationError('Output track set mismatch')
        actual={s['index']:s for s in streams}
        for item in expected:
            stream=actual[item.index]
            if stream.get('codec_type')!=item.kind or stream.get('codec_name')!=item.codec:
                raise MediaValidationError('Output track type/codec mismatch')
            for field,wanted in [('start_time',item.start),('duration',item.duration)]:
                if abs(_number(stream.get(field))-wanted)>item.tolerance:
                    raise MediaValidationError('Output start/duration mismatch')
            if item.kind=='video':
                if type(stream.get('width')) is not int or type(stream.get('height')) is not int or stream.get('width')!=item.width or stream.get('height')!=item.height or _number(stream.get('avg_frame_rate'))!=item.frame_rate:
                    raise MediaValidationError('Output video geometry/frame rate mismatch')
            elif type(stream.get('channels')) is not int or _number(stream.get('sample_rate'))!=item.sample_rate or stream.get('channels')!=item.channels:
                raise MediaValidationError('Output audio layout/rate mismatch')
        args=[str(decoder),'-nostdin','-hide_banner','-v','error','-xerror',
              '-abort_on','empty_output+empty_output_stream','-max_error_rate','0',
              '-protocol_whitelist','file,pipe','-i',str(path)]
        for item in expected:args+=['-map',f'0:{item.index}']
        args+=['-f','null','-']
        result=run_owned(args,cancel=cancel,timeout=timeout,max_output_bytes=256*1024)
        if result.returncode!=0:raise MediaValidationError('Output failed full decode')
        if fingerprint(path,cancel)!=probe.sha256:raise MediaValidationError('Output changed during decode')
        if cancel():raise ProbeCanceled('Media validation canceled')
        return MediaValidation(probe.sha256,expected)
    except (ProcessCanceled,ProbeCanceled):
        raise ProbeCanceled('Media validation canceled; no successful observation returned') from None
    except MediaValidationError:raise
    except (ProcessError,ProbeError,OSError):
        raise MediaValidationError('Media validation failed; output not accepted') from None
