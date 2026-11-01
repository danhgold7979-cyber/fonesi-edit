import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest
from fonesi_edit.media.probe import fingerprint, inspect_media, ProbeError, ProbeCanceled

@pytest.fixture
def source(tmp_path):
    path = tmp_path/'nguồn 中文.bin'; path.write_bytes(b'untouched')
    return path

def fake(tmp_path, body):
    if os.name == 'nt': pytest.skip('POSIX executable fixture; Windows real tool suite separate')
    path = tmp_path/'probe'; path.write_text(f'#!{sys.executable}\n'+body)
    path.chmod(0o700)
    return path

def test_content_identity_rename_and_cancel(source):
    first = fingerprint(source)
    moved = source.with_name('moved.bin'); source.rename(moved)
    assert fingerprint(moved) == first
    with pytest.raises(ProbeCanceled): fingerprint(moved, lambda: True)

def test_explicit_invalid_no_fallback(source):
    with pytest.raises(ProbeError, match='no fallback'): inspect_media(source, '/nonexistent/ffprobe')

@pytest.mark.parametrize('body,error', [
    ('print("bad")', 'invalid JSON'),
    ('print(\'{"streams":[],"streams":[]}\')', 'invalid JSON'),
    ('print(\'{"streams":[],"x":NaN}\')', 'invalid JSON'),
    ('print("{}")', 'No usable'),
    ('import time; time.sleep(10)', 'timed out'),
    ('print("x"*10000)', 'exceeds limit'),
    ('raise SystemExit(7)', 'code 7'),
    ('print(\'{"streams":[{"index":0,"codec_type":"video","nested":{"duration":1e999}}]}\')', 'invalid JSON'),
    ('print(\'{"streams":[{"index":0,"codec_type":"video","nested":{"duration":-1e999}}]}\')', 'invalid JSON'),
])
def test_bounded_failures(tmp_path, source, body, error):
    executable = fake(tmp_path, body)
    with pytest.raises(ProbeError, match=error): inspect_media(source, executable, timeout=.1, max_output_bytes=1000)
    assert source.read_bytes() == b'untouched'

def test_mid_process_cancel_reaped(tmp_path, source):
    executable = fake(tmp_path, 'import time; time.sleep(10)')
    calls = 0
    def cancel():
        nonlocal calls
        calls += 1
        return calls > 6
    with pytest.raises(ProbeCanceled): inspect_media(source, executable, cancel=cancel)

def test_real_audio_probe_source_unchanged(tmp_path):
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not ffmpeg or not ffprobe: pytest.skip('Developer FFmpeg tools unavailable')
    path = tmp_path/'âm thanh.wav'
    subprocess.run([ffmpeg, '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.1', str(path)], check=True)
    before = path.read_bytes()
    result = inspect_media(path, ffprobe)
    assert result.metadata()['streams'][0]['codec_type'] == 'audio'
    assert result.sha256 == fingerprint(path)
    assert path.read_bytes() == before
    copied = result.metadata(); copied.clear()
    assert result.metadata()['streams']

def test_descriptor_and_named_timestamp_precision_compared_separately(source,monkeypatch):
    import fonesi_edit.media.probe as probe
    from types import SimpleNamespace
    original=os.fstat
    def descriptor(fd):
        value=original(fd)
        return SimpleNamespace(st_dev=value.st_dev,st_ino=value.st_ino,st_size=value.st_size,
                               st_mtime_ns=value.st_mtime_ns-1,st_ctime_ns=value.st_ctime_ns-1)
    monkeypatch.setattr(probe.os,'fstat',descriptor)
    assert len(fingerprint(source))==64

def test_fingerprint_rejects_source_write_during_read(source):
    calls=0
    def mutate():
        nonlocal calls
        calls+=1
        if calls==2:source.write_bytes(b'changed-length')
        return False
    with pytest.raises(ProbeError,match='changed'):fingerprint(source,mutate)


@pytest.mark.parametrize('timeout,budget',[(float('nan'),1000),(float('inf'),1000),(True,1000),(1,True),(1,1.5)])
def test_invalid_bounds_rejected_before_launch(source,timeout,budget):
    with pytest.raises(ValueError):inspect_media(source,'/not-used',timeout=timeout,max_output_bytes=budget)


def test_probe_retires_owned_descendant(tmp_path,source):
    import json,time
    if not Path('/proc').is_dir():pytest.skip('Linux process-state proof; target-native tests separate')
    executable=fake(tmp_path,"""import subprocess,sys,json
child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(json.dumps({'streams':[{'index':0,'codec_type':'video'}],'test_child_pid':child.pid}))
""")
    result=inspect_media(source,executable,timeout=2)
    pid=result.metadata()['test_child_pid']
    deadline=time.monotonic()+2
    while time.monotonic()<deadline:
        status=Path(f'/proc/{pid}/stat')
        try:state=status.read_text().rpartition(') ')[2].split()[0]
        except FileNotFoundError:break
        if state=='Z':break
        time.sleep(.01)
    else:pytest.fail('Probe-owned descendant remained running')
    assert source.read_bytes()==b'untouched'


def test_tool_stderr_secret_not_in_probe_error(tmp_path,source):
    executable=fake(tmp_path,"import sys; sys.stderr.write('SECRET_SENTINEL'); raise SystemExit(7)")
    with pytest.raises(ProbeError) as caught:inspect_media(source,executable)
    assert 'SECRET_SENTINEL' not in str(caught.value) and 'code 7' in str(caught.value)



def test_continuously_growing_source_read_is_bounded(source,monkeypatch):
    original=Path.open;reads=0
    class GrowingReader:
        def __init__(self,stream):self.stream=stream
        def __enter__(self):return self
        def __exit__(self,*args):self.stream.close()
        def fileno(self):return self.stream.fileno()
        def read(self,size):
            nonlocal reads
            reads+=1
            assert reads<=3,'Fingerprint continued following a growing input'
            block=self.stream.read(size)
            with original(source,'ab') as other:other.write(b'x')
            return block
    def opened(path,mode='r',*args,**kwargs):
        stream=original(path,mode,*args,**kwargs)
        return GrowingReader(stream) if path==source and mode=='rb' else stream
    monkeypatch.setattr(Path,'open',opened)
    with pytest.raises(ProbeError,match='changed'):fingerprint(source)
    assert reads==2
