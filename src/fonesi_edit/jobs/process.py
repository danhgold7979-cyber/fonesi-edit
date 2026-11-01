"""Owned process execution: POSIX groups or native Windows Job Object adapter."""
from dataclasses import dataclass
import os
import selectors
import signal
import subprocess
import time
from typing import Callable, Sequence

class ProcessError(RuntimeError):
    pass

class ProcessCanceled(ProcessError):
    pass

class _RetirementObservation:
    """Internal, single-invocation receipt; no serialization or caller booleans."""
    __slots__=('_token','_mechanism')
    def __init__(self):self._token=None;self._mechanism=None
    @property
    def mechanism(self):return self._mechanism


def _begin_retirement(observation):
    if observation is None:return None
    if type(observation) is not _RetirementObservation or observation._token is not None:
        raise ValueError('Fresh internal retirement observation required')
    observation._token=object()
    return observation._token


def _confirm_retirement(observation,token,mechanism):
    if observation is None:return
    if (token is None or observation._token is not token or observation._mechanism is not None
        or mechanism not in {'NO_PROCESS','POSIX_GROUP_RETIRED','WINDOWS_JOB_EMPTY'}):
        raise ProcessError('Invalid retirement observation provenance')
    observation._mechanism=mechanism


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def run_owned(argv: Sequence[str], *, cancel: Callable[[], bool] = lambda: False,
              timeout: float = 300, max_output_bytes: int = 4*1024*1024,
              grace_seconds: float = .2, on_stdout: Callable[[bytes], None] | None = None,
              _retirement: _RetirementObservation | None = None) -> ProcessResult:
    if on_stdout is not None and not callable(on_stdout):
        raise ValueError("stdout observer must be callable")
    if os.name == 'nt':
        from .windows_process import run_windows_owned
        return run_windows_owned(argv,cancel=cancel,timeout=timeout,
                                 max_output_bytes=max_output_bytes,grace_seconds=grace_seconds,on_stdout=on_stdout,_retirement=_retirement)
    if os.name != 'posix' or not hasattr(os, 'WNOWAIT'):
        raise ProcessError('Windows Job Object adapter unavailable; no unsafe parent-only fallback')
    if isinstance(argv, (str, bytes)) or not argv or any(not isinstance(v,str) or '\0' in v for v in argv):
        raise ValueError('Nonempty argv sequence without NUL required')
    if timeout<=0 or max_output_bytes<1 or grace_seconds<0:
        raise ValueError('Invalid execution bounds')
    retirement_token=_begin_retirement(_retirement)
    if cancel():
        _confirm_retirement(_retirement,retirement_token,'NO_PROCESS')
        raise ProcessCanceled('Canceled before launch')
    child = subprocess.Popen(list(argv), stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             shell=False, start_new_session=True)
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    selector = selectors.DefaultSelector()
    started = time.monotonic()
    stopped = False
    group_retired = False
    def exited():
        return os.waitid(os.P_PID,child.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is not None
    def stop_group():
        nonlocal stopped,group_retired
        if stopped:return
        stopped=True
        # WNOWAIT retains the leader until group cleanup, preventing PID/PGID reuse.
        # start_new_session gave this invocation sole ownership of its new pgid.
        for sig,delay in [(signal.SIGTERM,grace_seconds),(signal.SIGKILL,0)]:
            try:
                os.killpg(child.pid,sig)
            except ProcessLookupError:
                break
            if delay:
                time.sleep(delay)
        child.wait()
        group_retired=True
    try:
        for name,pipe in [('stdout',child.stdout),('stderr',child.stderr)]:
            os.set_blocking(pipe.fileno(),False)
            selector.register(pipe,selectors.EVENT_READ,name)
        while selector.get_map():
            if cancel():
                raise ProcessCanceled('Canceled during execution')
            if time.monotonic()-started>timeout:
                raise ProcessError('Owned process timed out')
            for key,_ in selector.select(.02):
                chunk=os.read(key.fd,65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffers[key.data].extend(chunk)
                if sum(map(len,buffers.values()))>max_output_bytes:
                    raise ProcessError('Owned process output exceeds limit')
                if key.data == 'stdout' and on_stdout is not None:
                    on_stdout(chunk)
        # A child may close streams and continue running. Keep ownership until exit.
        while not exited():
            if cancel():raise ProcessCanceled('Canceled during execution')
            if time.monotonic()-started>timeout:raise ProcessError('Owned process timed out')
            time.sleep(.01)
        stop_group()
        return ProcessResult(child.returncode,bytes(buffers['stdout']),bytes(buffers['stderr']))
    except BaseException:
        stop_group()
        raise
    finally:
        retirement_errors=[]
        # Attempt every owned resource's retirement even if a prior close failed.
        for retire in (selector.close,child.stdout.close,child.stderr.close,stop_group):
            try:retire()
            except BaseException as exc:retirement_errors.append(exc)
        if retirement_errors:
            if not isinstance(retirement_errors[0],Exception):raise retirement_errors[0]
            raise ProcessError('Owned process retirement unconfirmed') from retirement_errors[0]
        if group_retired:_confirm_retirement(_retirement,retirement_token,'POSIX_GROUP_RETIRED')
