import ctypes as C
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest
from fonesi_edit.jobs.windows_process import (STARTUPINFOW, STARTUPINFOEXW,
    PROCESS_INFORMATION, EXTENDED_LIMIT, run_windows_owned)
from fonesi_edit.jobs.process import ProcessError, ProcessCanceled


def test_win64_structure_layouts():
    if C.sizeof(C.c_void_p)!=8:pytest.skip('64-bit structure contract')
    assert C.sizeof(STARTUPINFOW)==104
    assert C.sizeof(STARTUPINFOEXW)==112
    assert C.sizeof(PROCESS_INFORMATION)==24
    assert C.sizeof(EXTENDED_LIMIT)==144

windows=pytest.mark.skipif(os.name!='nt',reason='Real Windows Job Object test; not simulated')

def cmd(code):return [sys.executable,'-c',code]

def started(path):
    try:return path.read_text()=='started'
    except OSError:return False

@windows
def test_real_output_unicode_argument_and_exit():
    # Explicit UTF-8 child output avoids platform code-page ambiguity.
    result=run_windows_owned(cmd('import sys;sys.stdout.buffer.write(sys.argv[1].encode("utf8"));sys.exit(7)')+['xin chào 中文 "quoted" \\ end'])
    assert result.returncode==7 and result.stdout.decode('utf8')=='xin chào 中文 "quoted" \\ end'

@windows
@pytest.mark.parametrize('code,kwargs,message',[
    ('import time;time.sleep(10)',{'timeout':.05},'timed out'),
    ('print("x"*100000)',{'max_output_bytes':100},'exceeds limit'),
])
def test_real_limits(code,kwargs,message):
    with pytest.raises(ProcessError,match=message):run_windows_owned(cmd(code),**kwargs)

@windows
def test_cancel_owned_grandchild(tmp_path):
    marker=tmp_path/'grandchild.txt'
    grandchild=f'import pathlib,time;pathlib.Path({str(marker)!r}).write_text("started");time.sleep(.6);pathlib.Path({str(marker)!r}).write_text("SURVIVED")'
    parent=f'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",{grandchild!r}]);time.sleep(10)'
    with pytest.raises(ProcessCanceled):run_windows_owned(cmd(parent),cancel=lambda:started(marker))
    time.sleep(.7)
    assert marker.read_text()=='started'

@windows
def test_supervisor_crash_kills_job(tmp_path):
    marker=tmp_path/'child.txt'
    child=f'import pathlib,time;pathlib.Path({str(marker)!r}).write_text("started");time.sleep(1);pathlib.Path({str(marker)!r}).write_text("SURVIVED")'
    supervisor='from fonesi_edit.jobs.windows_process import run_windows_owned;import sys;run_windows_owned([sys.executable,"-c",'+repr(child)+'])'
    process=subprocess.Popen(cmd(supervisor))
    try:
        deadline=time.monotonic()+10
        while not started(marker) and time.monotonic()<deadline:time.sleep(.01)
        assert started(marker)
        process.kill();process.wait(timeout=5)
        time.sleep(1.2)
        assert marker.read_text()=='started'
    finally:
        if process.poll() is None:process.kill();process.wait()

@windows
def test_unlisted_inheritable_handle_not_leaked(tmp_path):
    import msvcrt
    sentinel=tmp_path/'private-inherited-sentinel.txt';sentinel.write_text('private')
    fd=os.open(sentinel,os.O_RDONLY)
    handle=msvcrt.get_osfhandle(fd)
    os.set_handle_inheritable(handle,True)
    try:
        child='''import ctypes as c,sys
k=c.WinDLL('kernel32',use_last_error=True)
f=k.GetFinalPathNameByHandleW
f.argtypes=[c.c_void_p,c.c_wchar_p,c.c_uint32,c.c_uint32];f.restype=c.c_uint32
b=c.create_unicode_buffer(4096)
n=f(c.c_void_p(int(sys.argv[1])),b,4096,0)
print('LEAK' if n and 'private-inherited-sentinel.txt' in b.value else 'CLOSED')
'''
        result=run_windows_owned(cmd(child)+[str(handle)])
        assert result.returncode==0 and result.stdout.strip()==b'CLOSED'
    finally:
        os.set_handle_inheritable(handle,False);os.close(fd)

@windows
def test_dispatch_uses_windows_job():
    from fonesi_edit.jobs.process import run_owned
    assert run_owned(cmd('print("dispatched")')).stdout.strip()==b'dispatched'

@windows
def test_native_handles_retired_across_success_and_failure():
    import json
    script='''import ctypes as c,json,sys
from fonesi_edit.jobs.windows_process import run_windows_owned
from fonesi_edit.jobs.process import ProcessError
k=c.WinDLL('kernel32',use_last_error=True)
k.GetCurrentProcess.restype=c.c_void_p
k.GetProcessHandleCount.argtypes=[c.c_void_p,c.POINTER(c.c_uint32)]
def count():
 n=c.c_uint32()
 assert k.GetProcessHandleCount(k.GetCurrentProcess(),c.byref(n))
 return n.value
def cycle():
 assert run_windows_owned([sys.executable,'-c','print("ok")']).returncode==0
 try:run_windows_owned([sys.executable,'-c','import time;time.sleep(10)'],timeout=.02)
 except ProcessError:pass
 else:raise AssertionError('timeout absent')
cold=count()
cycle() # initialize Win32/Python lazy runtime handles before measuring per-call leakage
before=count()
counts=[]
for i in range(10):
 cycle()
 counts.append(count())
print(json.dumps({'cold':cold,'warm':before,'counts':counts}))
'''
    result=run_windows_owned(cmd(script),timeout=30)
    assert result.returncode==0, result.stderr
    measurement=json.loads(result.stdout)
    assert max(measurement['counts'])<=measurement['warm']+1, measurement
    assert measurement['counts'][-1]<=measurement['counts'][0], measurement

@windows
def test_cancel_never_terminates_separate_sibling(tmp_path):
    ready=tmp_path/'owned-ready.txt';sentinel=tmp_path/'separate-survived.txt'
    outsider=subprocess.Popen(cmd(f'import pathlib,time;time.sleep(.4);pathlib.Path({str(sentinel)!r}).write_text("survived")'))
    try:
        owned=f'import pathlib,time;pathlib.Path({str(ready)!r}).write_text("started");time.sleep(10)'
        with pytest.raises(ProcessCanceled):run_windows_owned(cmd(owned),cancel=lambda:started(ready))
        assert outsider.wait(timeout=5)==0
        assert sentinel.read_text()=='survived'
    finally:
        if outsider.poll() is None:outsider.kill();outsider.wait()

@windows
def test_native_quiescence_observed_before_return(monkeypatch):
    import fonesi_edit.jobs.windows_process as native
    real=native.await_job_empty;observed=[]
    def record(kernel,job,**kwargs):
        real(kernel,job,**kwargs)
        observed.append('ACTIVE_PROCESS_ZERO')
    monkeypatch.setattr(native,'await_job_empty',record)
    result=native.run_windows_owned(cmd('print("completed")'))
    assert result.returncode==0 and observed==['ACTIVE_PROCESS_ZERO']
