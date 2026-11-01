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

@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def run_owned(argv: Sequence[str], *, cancel: Callable[[], bool] = lambda: False,
              timeout: float = 300, max_output_bytes: int = 4*1024*1024,
              grace_seconds: float = .2) -> ProcessResult:
    if os.name == 'nt':
        from .windows_process import run_windows_owned
        return run_windows_owned(argv,cancel=cancel,timeout=timeout,
                                 max_output_bytes=max_output_bytes,grace_seconds=grace_seconds)
    if os.name != 'posix' or not hasattr(os, 'WNOWAIT'):
        raise ProcessError('Windows Job Object adapter unavailable; no unsafe parent-only fallback')
    if isinstance(argv, (str, bytes)) or not argv or any(not isinstance(v,str) or '\0' in v for v in argv):
        raise ValueError('Nonempty argv sequence without NUL required')
    if timeout<=0 or max_output_bytes<1 or grace_seconds<0:
        raise ValueError('Invalid execution bounds')
    if cancel():
        raise ProcessCanceled('Canceled before launch')
    child = subprocess.Popen(list(argv), stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             shell=False, start_new_session=True)
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    selector = selectors.DefaultSelector()
    started = time.monotonic()
    stopped = False
    def exited():
        return os.waitid(os.P_PID,child.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is not None
    def stop_group():
        nonlocal stopped
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
        selector.close()
        child.stdout.close()
        child.stderr.close()
        # Completed leader can leave silent descendants. The session group remains ours.
        stop_group()
