"""Bounded decoded-frame facts; EOF observation is not media validity/readiness."""
from dataclasses import dataclass,asdict
from fractions import Fraction
import json,math,os
from pathlib import Path
from .probe import fingerprint,ProbeError,ProbeCanceled,_json_pairs,_finite_float,_reject_constant
from .observations import MediaObservation,_integer,_rational
from fonesi_edit.jobs.process import run_owned,ProcessError,ProcessCanceled


@dataclass(frozen=True)
class FrameObservation:
    pts:int|None
    best_effort_timestamp:int|None
    duration:int|None
    packet_duration:int|None
    diagnostics:tuple[str,...]


@dataclass(frozen=True)
class FrameScan:
    source_sha256:str
    tool_sha256:str
    stream_index:int
    time_base:Fraction
    start_pts:int|None
    status:str
    frames:tuple[FrameObservation,...]
    diagnostics:tuple[str,...]
    render_ready:bool=False
    def to_dict(self):
        value=asdict(self);value['time_base']={'num':self.time_base.numerator,'den':self.time_base.denominator}
        return value


def observe_frames(path,executable,observation:MediaObservation,stream_index:int,*,
                   cancel=lambda:False,timeout=300,max_frames=100000,max_output_bytes=32*1024*1024,_lifecycle=None):
    """Caller authorizes a trusted stable executable; hashes only observe drift.

    Process/capture/cancel failures raise: no fabricated parseable partial prefix.
    Valid bounded JSON can retain a prefix marked INCOMPLETE. OBSERVED_EOF means
    command+JSON ended, not proof of no corrupt/skipped frames or a usable map.
    """
    path=Path(path);executable=Path(executable)
    if (not path.is_absolute() or not executable.is_absolute() or type(observation) is not MediaObservation or
        type(stream_index) is not int or type(max_frames) is not int or not 1<=max_frames<=1000000 or
        type(max_output_bytes) is not int or not 1024<=max_output_bytes<=64*1024*1024 or
        type(timeout) not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=3600):
        raise ProbeError('Explicit bounded frame observation inputs required')
    if not path.is_file() or not executable.is_file() or not os.access(executable,os.X_OK):
        raise ProbeError('Regular media and explicit executable required; no fallback')
    selected=[s for s in observation.streams if s.index==stream_index]
    if len(selected)!=1 or selected[0].kind!='video' or selected[0].time_base is None:
        raise ProbeError('Observed video stream with known timebase required')
    selected=selected[0]
    if selected.attached_picture:raise ProbeError('Attached picture is not a timeline video frame map')
    def check():
        if cancel():raise ProbeCanceled('Frame observation canceled; no complete map')
    check();source_hash=fingerprint(path,cancel);tool_hash=fingerprint(executable,cancel)
    if source_hash!=observation.sha256:raise ProbeError('Source differs from stream observation')
    args=[str(executable),'-v','error','-select_streams',str(stream_index),'-show_streams','-show_frames',
          '-show_entries','stream=index,codec_type,time_base,start_pts:frame=stream_index,pts,best_effort_timestamp,duration,pkt_duration',
          '-print_format','json','-protocol_whitelist','file,pipe','-i',str(path)]
    try:
        if _lifecycle is None:result=run_owned(args,cancel=cancel,timeout=timeout,max_output_bytes=max_output_bytes)
        else:result=_lifecycle.run(run_owned,args,cancel=cancel,timeout=timeout,max_output_bytes=max_output_bytes)
    except ProcessCanceled as exc:raise ProbeCanceled('Frame observation canceled; no complete map') from exc
    except (ProcessError,OSError) as exc:raise ProbeError('Frame observation incomplete; process outcome not accepted') from exc
    check()
    if len(result.stdout)>max_output_bytes:raise ProbeError('Frame output exceeds bound')
    try:raw=json.loads(result.stdout.decode('utf-8'),object_pairs_hook=_json_pairs,parse_float=_finite_float,parse_constant=_reject_constant)
    except (ValueError,UnicodeError,RecursionError):raise ProbeError('Frame JSON incomplete or malformed; no frame map') from None
    if not isinstance(raw,dict) or not isinstance(raw.get('streams'),list) or len(raw['streams'])!=1 or not isinstance(raw.get('frames'),list):
        raise ProbeError('Selected stream/frame envelope required')
    stream=raw['streams'][0]
    if (not isinstance(stream,dict) or type(stream.get('index')) is not int or stream['index']!=stream_index or
        stream.get('codec_type')!='video' or _rational(stream.get('time_base'),positive=True)!=selected.time_base or
        _integer(stream.get('start_pts'))!=selected.start_pts):
        raise ProbeError('Frame scan stream identity/timing differs from observation')
    diagnostics=['NOT_MEDIA_VALIDITY_OR_RENDER_READINESS'];status='OBSERVED_EOF'
    if result.returncode!=0:status='INCOMPLETE';diagnostics.append('NONZERO_PROBE_EXIT')
    if result.stderr:status='INCOMPLETE';diagnostics.append('DECODE_ERRORS_REPORTED')
    if len(raw['frames'])>max_frames:status='INCOMPLETE';diagnostics.append('FRAME_COUNT_LIMIT')
    frames=[];previous=None
    for index,frame in enumerate(raw['frames'][:max_frames]):
        if index%128==0:check()
        if not isinstance(frame,dict) or type(frame.get('stream_index')) is not int or frame['stream_index']!=stream_index:
            raise ProbeError('Unexpected frame stream; no trusted frame map')
        pts=_integer(frame.get('pts'));best=_integer(frame.get('best_effort_timestamp'))
        duration=_integer(frame.get('duration'),minimum=0);packet=_integer(frame.get('pkt_duration'),minimum=0)
        issues=[]
        if pts is None:issues.append('PTS_UNKNOWN')
        if best is None:issues.append('BEST_EFFORT_UNKNOWN')
        if duration is None and packet is None:issues.append('DURATION_UNKNOWN')
        if duration is not None and packet is not None and duration!=packet:issues.append('DURATION_FIELDS_DIFFER')
        if pts is not None and previous is not None and pts<=previous:issues.append('NONINCREASING_PTS_PRESERVED')
        if pts is not None:previous=pts
        frames.append(FrameObservation(pts,best,duration,packet,tuple(issues)))
    if not frames:diagnostics.append('NO_DECODED_FRAMES_OBSERVED')
    check()
    if fingerprint(path,cancel)!=source_hash or fingerprint(executable,cancel)!=tool_hash:
        raise ProbeError('Source/tool changed during frame observation')
    return FrameScan(source_hash,tool_hash,stream_index,selected.time_base,selected.start_pts,status,tuple(frames),tuple(diagnostics))
