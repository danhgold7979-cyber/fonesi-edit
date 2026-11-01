import os
from pathlib import Path
import sys
import time
import pytest
from fonesi_edit.jobs.process import run_owned, ProcessError, ProcessCanceled
pytestmark=pytest.mark.skipif(os.name!='posix',reason='POSIX owned-group adapter; Windows adapter separate')

def cmd(code):return [sys.executable,'-c',code]

def test_output_and_exit_code():
    result=run_owned(cmd('import sys;print("hi");print("error",file=sys.stderr);sys.exit(7)'))
    assert result.returncode==7 and result.stdout==b'hi\n' and result.stderr==b'error\n'

def test_argv_not_shell():
    with pytest.raises(ValueError):run_owned('echo hello')

@pytest.mark.parametrize('code,kwargs,message',[
    ('import time;time.sleep(10)',{'timeout':.05},'timed out'),
    ('print("x"*100000)',{'max_output_bytes':100},'exceeds limit'),
    ('import os,time;os.close(1);os.close(2);time.sleep(10)',{'timeout':.05},'timed out'),
])
def test_execution_bounds(code,kwargs,message):
    with pytest.raises(ProcessError,match=message):run_owned(cmd(code),grace_seconds=.01,**kwargs)

def test_cancel_removes_owned_grandchild(tmp_path):
    marker=tmp_path/'grandchild-started'
    grandchild=f'import pathlib,time;pathlib.Path({str(marker)!r}).write_text("started");time.sleep(0.5);pathlib.Path({str(marker)!r}).write_text("SURVIVED")'
    parent=f'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",{grandchild!r}]);time.sleep(10)'
    with pytest.raises(ProcessCanceled):
        run_owned(cmd(parent),cancel=marker.exists,grace_seconds=.01)
    time.sleep(.55)
    assert marker.read_text()=='started'

def test_successful_leader_cleans_silent_descendant(tmp_path):
    marker=tmp_path/'must-not-exist'
    grandchild=f'import pathlib,time;time.sleep(.4);pathlib.Path({str(marker)!r}).write_text("SURVIVED")'
    parent=f'import subprocess,sys;subprocess.Popen([sys.executable,"-c",{grandchild!r}],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)'
    assert run_owned(cmd(parent),grace_seconds=.01).returncode==0
    time.sleep(.45)
    assert not marker.exists()
