"""Bounded FFmpeg observations, never job completion or publication authority."""
from dataclasses import dataclass
import math
import re
from .process import ProcessError


@dataclass(frozen=True)
class Progress:
    frame: int | None
    out_time_us: int | None
    total_size: int | None
    ended: bool


class ProgressProtocolError(ProcessError):
    pass


class FFmpegProgress:
    """Feed stdout chunks on the runner thread; emit only complete records.

    Unknown keys are discarded. No stderr, paths, free text, percent or ETA is
    exposed. A failed parser/callback is permanently retired. Caller must use
    run_owned's total-output/deadline bounds in addition to these framing bounds.
    """
    def __init__(self, emit):
        if not callable(emit):raise ValueError('Progress callback required')
        self.emit=emit; self.pending=bytearray(); self.fields={}
        self.lines=0; self.ended=False; self.failed=False

    def feed(self, chunk: bytes):
        if self.failed:raise ProgressProtocolError('Progress parser retired')
        try:
            if not isinstance(chunk,bytes) or len(chunk)>65536:
                raise ProgressProtocolError('Invalid progress chunk')
            for part in chunk.splitlines(keepends=True):
                self.pending.extend(part)
                if len(self.pending)>4096:raise ProgressProtocolError('Progress line exceeds bound')
                if not self.pending.endswith(b'\n'):continue
                line=bytes(self.pending).rstrip(b'\r\n');self.pending.clear()
                self._line(line)
        except BaseException:
            self.failed=True
            raise

    def _line(self,line):
        if self.ended:raise ProgressProtocolError('Data after progress end')
        self.lines+=1
        if self.lines>128:raise ProgressProtocolError('Progress record exceeds bound')
        key,sep,value=line.partition(b'=')
        if not sep:raise ProgressProtocolError('Invalid progress framing')
        if key==b'progress':
            if value not in (b'continue',b'end'):raise ProgressProtocolError('Invalid progress boundary')
            self.ended=value==b'end'
            event=Progress(*(self.fields.get(k) for k in (b'frame',b'out_time_us',b'total_size')),self.ended)
            self.fields.clear();self.lines=0
            self.emit(event)
        elif key in (b'frame',b'out_time_us',b'total_size'):
            if key in self.fields:raise ProgressProtocolError('Duplicate progress field')
            if value==b'N/A':self.fields[key]=None
            elif re.fullmatch(rb'-?[0-9]{1,19}',value):
                number=int(value)
                if abs(number)>2**63-1 or (number<0 and key!=b'out_time_us'):
                    raise ProgressProtocolError('Progress number outside bounds')
                self.fields[key]=number
            else:raise ProgressProtocolError('Invalid progress number')

    def finish(self):
        if self.failed or self.pending or self.lines or not self.ended:
            self.failed=True
            raise ProgressProtocolError('Incomplete progress stream')


@dataclass(frozen=True)
class JobProgress:
    job_id: str
    snapshot_hash: str
    attempt: int
    observation: Progress


class JobProgressObserver:
    """Ephemeral observations bound to one live attempt; no DB writes.

    guard is the coordinator's current ownership guard. emit must be bounded and
    nonblocking (e.g. queue a Qt signal), never directly mutate widgets here.
    Rejected/stale observations are ignored and permanently retire this observer.
    Delivery is observational, NOT a lease or permission for any later effect.
    """
    def __init__(self, repository, job, *, guard, emit):
        if not callable(guard) or not callable(emit):raise ValueError('Callbacks required')
        if job.state!='running' or not job.lease_token:raise ValueError('Running leased job required')
        self.repository=repository;self.job=job;self.guard=guard;self.emit=emit;self.retired=False

    def __call__(self, observation: Progress):
        if self.retired:return
        try:
            self.guard()
            current=self.repository.get(self.job.id)
            now=self.repository.clock()
            if (not math.isfinite(now) or current.state!='running' or current.cancel_requested
                or current.snapshot_hash!=self.job.snapshot_hash or current.attempt!=self.job.attempt
                or current.lease_token!=self.job.lease_token or current.lease_deadline is None
                or not math.isfinite(current.lease_deadline) or current.lease_deadline<=now):
                self.retired=True;return
            self.emit(JobProgress(current.id,current.snapshot_hash,current.attempt,observation))
        except BaseException:
            self.retired=True
            raise
