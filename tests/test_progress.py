from dataclasses import replace
from types import SimpleNamespace
import sys
import time
import pytest
from fonesi_edit.jobs.process import run_owned,ProcessCanceled
from fonesi_edit.jobs.progress import FFmpegProgress,Progress,ProgressProtocolError,JobProgressObserver
from fonesi_edit.jobs.repository import Job


def test_fragmented_records_unknowns_and_negative_media_time():
    events=[];parser=FFmpegProgress(events.append)
    data=b'frame=3\nout_time_us=-20\nsecret=DO NOT EMIT\ntotal_size=N/A\nprogress=continue\nframe=4\nout_time_us=1000\nprogress=end\n'
    for byte in data:parser.feed(bytes([byte]))
    parser.finish()
    assert events==[Progress(3,-20,None,False),Progress(4,1000,None,True)]
    assert 'SECRET' not in repr(events).upper()


@pytest.mark.parametrize('data',[
    b'frame=1e999\n',b'frame=-1\n',b'frame=9223372036854775808\n',
    b'frame=1\nframe=2\n',b'progress=success\n',b'bad framing\n',
    b'x'*4097,b'x=1\n'*129,b'progress=end\nframe=3\n',
])
def test_invalid_stream_permanently_retires(data):
    parser=FFmpegProgress(lambda event:None)
    with pytest.raises(ProgressProtocolError):parser.feed(data)
    with pytest.raises(ProgressProtocolError,match='retired'):parser.feed(b'progress=end\n')


@pytest.mark.parametrize('data',[b'',b'frame=1\n',b'progress=end',b'progress=continue\n'])
def test_truncated_or_no_end_not_complete(data):
    parser=FFmpegProgress(lambda event:None);parser.feed(data)
    with pytest.raises(ProgressProtocolError):parser.finish()


def job():return Job('id','request','{}','hash','running',2,1,'lease',100,False)


@pytest.mark.parametrize('change',[
    {'state':'canceled'},{'state':'validating'},{'cancel_requested':True},
    {'snapshot_hash':'other'},{'attempt':2},{'lease_token':'new'},
    {'lease_deadline':10},{'lease_deadline':float('nan')},
])
def test_stale_observation_never_revives(change):
    original=job();repo=SimpleNamespace(get=lambda _:replace(original,**change),clock=lambda:10)
    events=[];observer=JobProgressObserver(repo,original,guard=lambda:None,emit=events.append)
    observer(Progress(1,100,None,False));repo.get=lambda _:original
    observer(Progress(2,200,None,True));assert events==[] and observer.retired


def test_end_is_only_observation_no_repository_mutation():
    original=job();repo=SimpleNamespace(get=lambda _:original,clock=lambda:10)
    events=[];guards=[]
    observer=JobProgressObserver(repo,original,guard=lambda:guards.append(1),emit=events.append)
    observer(Progress(4,1000,None,True))
    assert len(events)==1 and len(guards)==1 and original.state=='running'
    assert events[0].job_id=='id' and events[0].attempt==1


def test_live_stdout_before_exit_and_no_stderr_forwarding():
    chunks=[]
    code='import sys,time;print("PRIVATE",file=sys.stderr,flush=True);print("progress=continue",flush=True);time.sleep(10)'
    with pytest.raises(ProcessCanceled):
        run_owned([sys.executable,'-c',code],on_stdout=chunks.append,cancel=lambda:bool(chunks),timeout=3,grace_seconds=.01)
    assert b'progress=continue' in b''.join(chunks) and b'PRIVATE' not in b''.join(chunks)


def test_observer_exception_retires_owned_descendant(tmp_path):
    marker=tmp_path/'survived';ready=tmp_path/'ready'
    child=f'import pathlib,time;pathlib.Path({str(ready)!r}).touch();time.sleep(.7);pathlib.Path({str(marker)!r}).touch()'
    parent=f'import subprocess,sys,pathlib,time;subprocess.Popen([sys.executable,"-c",{child!r}]);\nwhile not pathlib.Path({str(ready)!r}).exists():time.sleep(.01)\nprint("ready",flush=True);time.sleep(10)'
    def fail(chunk):raise RuntimeError('observer failed')
    with pytest.raises(RuntimeError,match='observer failed'):
        run_owned([sys.executable,'-c',parent],on_stdout=fail,timeout=3,grace_seconds=.01)
    time.sleep(.8)
    assert ready.exists() and not marker.exists()


def test_invalid_observer_before_launch(tmp_path):
    marker=tmp_path/'not-created'
    with pytest.raises(ValueError,match='observer'):
        run_owned([sys.executable,'-c',f'open({str(marker)!r},"w").close()'],on_stdout=42)
    assert not marker.exists()


def test_real_repository_on_runner_thread_end_and_cancel_filter(tmp_path,empty_plan):
    from fonesi_edit.jobs.repository import JobRepository
    from fonesi_edit.domain.composition import CompositionPlan
    from contextlib import closing
    with closing(JobRepository(tmp_path/'progress.db',clock=lambda:100)) as repository:
        current=repository.claim(repository.submit('progress',CompositionPlan.parse(empty_plan),42))
        events=[];guards=[]
        observer=JobProgressObserver(repository,current,guard=lambda:guards.append(1),emit=events.append)
        parser=FFmpegProgress(observer)
        result=run_owned([sys.executable,'-c','print("frame=25\\nout_time_us=1000000\\nprogress=end")'],on_stdout=parser.feed)
        parser.finish()
        assert result.returncode==0 and len(events)==1 and guards==[1]
        assert repository.get(current.id)==current # progress=end never mutates job/version
        canceled=repository.request_cancel(current)
        observer(Progress(30,2000000,None,False))
        assert len(events)==1 and observer.retired and repository.get(current.id)==canceled
