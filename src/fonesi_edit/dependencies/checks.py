"""Explicit pinned pair observations; no discovery-to-execution trust shortcut."""
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
import math
import os
import re
import stat
import time
from hashlib import sha256
from contextlib import nullcontext
from fonesi_edit.jobs.process import run_owned,ProcessError,ProcessCanceled
from fonesi_edit.media.probe import fingerprint,ProbeError,ProbeCanceled
from fonesi_edit.media.validation import validate_media,ExpectedStream


class ToolCheckError(RuntimeError):pass
class ToolCheckCanceled(ToolCheckError):pass

@dataclass(frozen=True)
class ToolPin:
    component:str
    path:Path
    sha256:str
    def __post_init__(self):
        if self.component not in ('ffmpeg','ffprobe') or not isinstance(self.path,Path) or not self.path.is_absolute():
            raise ValueError('Explicit component and absolute executable path required')
        if type(self.sha256) is not str or not re.fullmatch('[a-f0-9]{64}',self.sha256):raise ValueError('Expected executable SHA256 required')

@dataclass(frozen=True)
class VersionObservation:
    version:str
    libraries:tuple[tuple[str,str,str],...]
    response_sha256:str

@dataclass(frozen=True)
class PairObservation:
    ffmpeg:ToolPin
    ffprobe:ToolPin
    ffmpeg_version:VersionObservation
    ffprobe_version:VersionObservation
    fixture_sha256:str
    streams:tuple[ExpectedStream,...]
    observed_at:float
    scope:str='known-fixture-probe-full-decode-and-black-rgb16-only'
    raw_frame_sha256:str=sha256(bytes(16*16*3)).hexdigest()


def _check_pin(pin,cancel):
    info=pin.path.lstat()
    if not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400 or not 0<info.st_size<=1024**3:
        raise ToolCheckError('Executable must be a bounded regular non-reparse file')
    if not os.access(pin.path,os.X_OK):raise ToolCheckError('Explicit executable cannot be launched')
    if fingerprint(pin.path,cancel)!=pin.sha256:raise ToolCheckError('Executable differs from approved integrity pin; no fallback')


def _version(pin,cancel,timeout,_lifecycle=None):
    _check_pin(pin,cancel)
    runner=run_owned if _lifecycle is None else lambda argv,**kwargs:_lifecycle.run(run_owned,argv,**kwargs)
    result=runner([str(pin.path),'-version'],cancel=cancel,timeout=timeout,max_output_bytes=256*1024)
    _check_pin(pin,cancel)
    if result.returncode!=0:raise ToolCheckError('Version check failed')
    try:text=result.stdout.decode('utf-8')
    except UnicodeError:raise ToolCheckError('Invalid version response') from None
    match=re.match(r'^'+pin.component+r' version ([A-Za-z0-9._+:~\-]{1,128})(?:\s|$)',text)
    if not match:raise ToolCheckError('Unexpected component version response')
    libraries=[]
    for line in text.splitlines():
        item=re.fullmatch(r'\s*(libavutil|libavcodec|libavformat|libavdevice|libavfilter|libswscale|libswresample)\s+(\d+\.\s*\d+\.\s*\d+)\s*/\s*(\d+\.\s*\d+\.\s*\d+)\s*',line)
        if item:libraries.append((item[1],re.sub(r'\s','',item[2]),re.sub(r'\s','',item[3])))
    names=[item[0] for item in libraries]
    if len(names)!=len(set(names)) or not {'libavutil','libavcodec','libavformat'}<=set(names):
        raise ToolCheckError('Missing/duplicate library compatibility metadata')
    return VersionObservation(match[1],tuple(sorted(libraries)),sha256(result.stdout).hexdigest())


def _check_pair_impl(ffmpeg:ToolPin,ffprobe:ToolPin,fixture:Path,fixture_sha256:str,
               expected:tuple[ExpectedStream,...],*,cancel:Callable[[],bool]=lambda:False,
               timeout:float=15,_retirement=None)->PairObservation:
    """Caller must authorize exact tools/fixture. Timeout is per process, not total OS I/O."""
    if not isinstance(ffmpeg,ToolPin) or not isinstance(ffprobe,ToolPin) or (ffmpeg.component,ffprobe.component)!=('ffmpeg','ffprobe'):
        raise ValueError('Explicit FFmpeg and ffprobe pins required')
    if type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=60:raise ValueError('Invalid process timeout')
    if not isinstance(fixture,Path) or not fixture.is_absolute() or type(fixture_sha256) is not str or not re.fullmatch('[a-f0-9]{64}',fixture_sha256):
        raise ValueError('Explicit absolute known-hash fixture required')
    if type(expected) is not tuple or not 1<=len(expected)<=32 or any(type(x) is not ExpectedStream for x in expected) or len({x.index for x in expected})!=len(expected):raise ValueError('Exact fixture expectations required')
    try:
        if cancel():raise ToolCheckCanceled('Tool check canceled')
        info=fixture.lstat()
        if not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400 or not 0<info.st_size<=32*1024*1024:
            raise ToolCheckError('Fixture must be bounded regular non-reparse media')
        if fingerprint(fixture,cancel)!=fixture_sha256:raise ToolCheckError('Fixture integrity mismatch; no tool launched')
        # Verify BOTH before launching either, so an invalid explicit member never falls back.
        _check_pin(ffmpeg,cancel);_check_pin(ffprobe,cancel)
        with (_retirement.stage('versions') if _retirement is not None else nullcontext()) as scope:
            with (scope.validation_body() if scope is not None else nullcontext()):
                left=_version(ffmpeg,cancel,timeout,scope);right=_version(ffprobe,cancel,timeout,scope)
        if (left.version,left.libraries)!=(right.version,right.libraries):
            raise ToolCheckError('Pair reported versions/libraries differ; compatibility unverified')
        _check_pin(ffmpeg,cancel);_check_pin(ffprobe,cancel)
        with (_retirement.stage('media') if _retirement is not None else nullcontext()) as scope:
            validation=validate_media(fixture,ffprobe.path,ffmpeg.path,expected,cancel=cancel,timeout=timeout,
                **({'_lifecycle':scope} if scope is not None else {}))
        if validation.sha256!=fixture_sha256:raise ToolCheckError('Fixture changed during functional check')
        _check_pin(ffmpeg,cancel);_check_pin(ffprobe,cancel)
        with (_retirement.stage('frame') if _retirement is not None else nullcontext()) as scope:
            with (scope.validation_body() if scope is not None else nullcontext()):
                runner=run_owned if scope is None else lambda argv,**kwargs:scope.run(run_owned,argv,**kwargs)
                frame=runner([str(ffmpeg.path),'-nostdin','-hide_banner','-v','error','-f','lavfi','-i',
                             'color=c=black:s=16x16:r=1:d=1','-frames:v','1','-threads','1','-filter_threads','1',
                             '-pix_fmt','rgb24','-f','rawvideo','pipe:1'],cancel=cancel,timeout=timeout,max_output_bytes=256*1024)
        _check_pin(ffmpeg,cancel);_check_pin(ffprobe,cancel)
        if frame.returncode!=0 or frame.stdout!=bytes(16*16*3):raise ToolCheckError('Bounded raw-frame functional check failed')
        if fingerprint(fixture,cancel)!=fixture_sha256:raise ToolCheckError('Fixture changed after functional check')
        if cancel():raise ToolCheckCanceled('Tool check canceled')
        return PairObservation(ffmpeg,ffprobe,left,right,fixture_sha256,expected,time.time())
    except (ProcessCanceled,ProbeCanceled):raise ToolCheckCanceled('Tool check canceled; no successful observation') from None
    except ToolCheckError:raise
    except (ProcessError,ProbeError,OSError):raise ToolCheckError('Tool check failed; no successful observation or automatic retry') from None


def check_pair(ffmpeg:ToolPin,ffprobe:ToolPin,fixture:Path,fixture_sha256:str,
               expected:tuple[ExpectedStream,...],*,cancel:Callable[[],bool]=lambda:False,
               timeout:float=15,_retirement=None)->PairObservation:
    if _retirement is None:
        return _check_pair_impl(ffmpeg,ffprobe,fixture,fixture_sha256,expected,cancel=cancel,timeout=timeout)
    from .retirement import PairRetirement
    if type(_retirement) is not PairRetirement:raise ValueError('Internal pair receipt required')
    with _retirement.check_body():
        return _check_pair_impl(ffmpeg,ffprobe,fixture,fixture_sha256,expected,cancel=cancel,timeout=timeout,_retirement=_retirement)
