"""Bounded direct-child execution. Not a descendant-process containment guarantee."""
from dataclasses import dataclass
from pathlib import Path
import subprocess
import threading
import time

@dataclass(frozen=True)
class ProcessResult:
    status: str
    exit_code: int | None
    stdout: bytes


def run_bounded(arguments: list[str], *, timeout: float=10, limit: int=65536) -> ProcessResult:
    if not arguments or not all(isinstance(a,str) and '\x00' not in a for a in arguments):
        raise ValueError('Invalid arguments')
    executable=Path(arguments[0])
    if not executable.is_absolute() or not executable.is_file():
        raise ValueError('Explicit local executable required')
    if type(timeout) not in (int,float) or not 0<timeout<=60 or type(limit) is not int or not 1<=limit<=1048576:
        raise ValueError('Invalid process bounds')
    try:
        child=subprocess.Popen(arguments,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
    except OSError:
        return ProcessResult('START_FAILED',None,b'')
    overflow=threading.Event();failure=threading.Event();buffers=[bytearray(),bytearray()]
    def drain(pipe, destination):
        try:
            while True:
                chunk=pipe.read(4096)
                if not chunk: break
                if len(destination)+len(chunk)>limit:
                    overflow.set(); break
                destination.extend(chunk)
        except (OSError,ValueError): failure.set()
        finally: pipe.close()
    readers=[threading.Thread(target=drain,args=(pipe,buffer),daemon=True)
             for pipe,buffer in zip((child.stdout,child.stderr),buffers)]
    for reader in readers: reader.start()
    deadline=time.monotonic()+timeout;status='EXITED'
    while child.poll() is None:
        if overflow.is_set() or failure.is_set(): status='OUTPUT_LIMIT' if overflow.is_set() else 'READ_FAILED';break
        if time.monotonic()>=deadline: status='TIMEOUT';break
        time.sleep(.005)
    if status!='EXITED':
        try: child.kill()
        except ProcessLookupError: pass
    try: child.wait(timeout=2)
    except subprocess.TimeoutExpired: status='CLEANUP_TIMEOUT'
    for reader in readers: reader.join(timeout=.5)
    if any(reader.is_alive() for reader in readers): status='PIPE_NOT_CLOSED'
    elif overflow.is_set(): status='OUTPUT_LIMIT'
    elif failure.is_set(): status='READ_FAILED'
    if status!='EXITED': return ProcessResult(status,child.poll(),b'')
    return ProcessResult('OK' if child.returncode==0 else 'NONZERO_EXIT',child.returncode,bytes(buffers[0]) if child.returncode==0 else b'')
