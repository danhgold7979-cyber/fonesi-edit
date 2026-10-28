"""No shell, bounded diagnostics, cancellation of owned process groups."""
from __future__ import annotations
from collections import deque
from pathlib import Path
import os
import queue
import re
import signal
import subprocess
import threading
import time


class Cancelled(Exception):
    pass


class ProcessFailure(RuntimeError):
    def __init__(self, code, diagnostics):
        self.code = code
        super().__init__(f'Process exited {code}: {redact(diagnostics)[-8000:]}')


def redact(text: str) -> str:
    text = re.sub(r'(?i)(authorization|cookie|api[_-]?key|access_token|password)(\s*[:=]\s*)[^\s,;]+', r'\1\2[REDACTED]', text)
    text = re.sub(r'(?i)Bearer\s+\S+', 'Bearer [REDACTED]', text)
    return re.sub(r'(https?://[^\s?]+)\?[^\s]+', r'\1?[REDACTED]', text)


def stop_process(proc: subprocess.Popen):
    if proc.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'], capture_output=True, timeout=10)
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    proc.wait(timeout=10)


def run(args: list[str], *, cancel=lambda: False, timeout=120, line=None, cwd=None) -> str:
    flags = {'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
    proc = subprocess.Popen([str(x) for x in args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf8', errors='replace', stdin=subprocess.DEVNULL, **flags)
    q = queue.Queue(); tail = deque(maxlen=4000)
    def read():
        try:
            for row in proc.stdout:
                q.put(row)
        finally:
            q.put(None)
    reader = threading.Thread(target=read, daemon=True); reader.start()
    started=time.monotonic(); finished=False
    try:
        while not finished:
            if cancel():
                raise Cancelled('Operation cancelled; render restart may be required')
            if timeout is not None and time.monotonic()-started > timeout:
                raise TimeoutError(f'Process exceeded {timeout}s')
            try:
                row=q.get(timeout=.05)
            except queue.Empty:
                continue
            if row is None:
                finished=True
            else:
                tail.append(row)
                if line: line(row.rstrip())
        code=proc.wait(timeout=10)
        output=''.join(tail)
        if code:
            raise ProcessFailure(code, output)
        return output
    finally:
        stop_process(proc)
        proc.stdout.close()
        reader.join(timeout=1)
