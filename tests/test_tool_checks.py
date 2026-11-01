from hashlib import sha256
from pathlib import Path
from fractions import Fraction as F
from dataclasses import replace
import pytest
from fonesi_edit.dependencies.checks import ToolPin,check_pair,ToolCheckError,ToolCheckCanceled
from fonesi_edit.media.validation import ExpectedStream,MediaValidation
from fonesi_edit.jobs.process import ProcessResult,ProcessError,ProcessCanceled
import fonesi_edit.dependencies.checks as checks

EXPECTED=(ExpectedStream(0,'video','h264',F(0),F(1),F(1,25),width=64,height=48,frame_rate=F(25)),)

@pytest.fixture
def pair(tmp_path,monkeypatch):
    pins=[]
    for name in ('ffmpeg','ffprobe'):
        path=tmp_path/name;path.write_bytes(name.encode());path.chmod(0o700)
        pins.append(ToolPin(name,path,sha256(path.read_bytes()).hexdigest()))
    fixture=tmp_path/'fixture';fixture.write_bytes(b'known fixture');digest=sha256(fixture.read_bytes()).hexdigest()
    calls=[]
    def run(args,**kwargs):
        calls.append(tuple(args))
        assert kwargs['max_output_bytes']==256*1024 and kwargs['timeout']==15
        if args[-1]=='-version':
            data=(Path(args[0]).name+' version 7.1.5 Copyright\nlibavutil 59. 39.100 / 59. 39.100\nlibavcodec 61. 19.101 / 61. 19.101\nlibavformat 61. 7.100 / 61. 7.100\n').encode()
            return ProcessResult(0,data,b'')
        assert args[-3:]==['-f','rawvideo','pipe:1']
        return ProcessResult(0,bytes(768),b'')
    monkeypatch.setattr(checks,'run_owned',run)
    monkeypatch.setattr(checks,'validate_media',lambda *a,**k:MediaValidation(digest,EXPECTED))
    return pins,fixture,digest,calls


def test_pinned_pair_returns_only_scoped_observation_without_writes(pair):
    pins,fixture,digest,calls=pair;before=fixture.read_bytes()
    result=check_pair(*pins,fixture,digest,EXPECTED)
    assert result.fixture_sha256==digest and result.streams==EXPECTED
    assert result.scope=='known-fixture-probe-full-decode-and-black-rgb16-only'
    assert len(calls)==3 and fixture.read_bytes()==before


@pytest.mark.parametrize('target',['ffmpeg','ffprobe','fixture'])
def test_bad_explicit_pin_refuses_before_any_launch(pair,target):
    pins,fixture,digest,calls=pair
    if target=='fixture':digest='0'*64
    else:
        index=0 if target=='ffmpeg' else 1;pins[index]=replace(pins[index],sha256='0'*64)
    with pytest.raises(ToolCheckError):check_pair(*pins,fixture,digest,EXPECTED)
    assert calls==[]


def test_versions_differ_no_functional_fallback(pair,monkeypatch):
    pins,fixture,digest,calls=pair;real=checks.run_owned
    def run(args,**kwargs):
        result=real(args,**kwargs)
        return replace(result,stdout=result.stdout.replace(b'7.1.5',b'8.0')) if args[0]==str(pins[1].path) else result
    monkeypatch.setattr(checks,'run_owned',run)
    monkeypatch.setattr(checks,'validate_media',lambda *a,**k:pytest.fail('Incompatible pair used'))
    with pytest.raises(ToolCheckError,match='compatibility unverified'):check_pair(*pins,fixture,digest,EXPECTED)
    assert len(calls)==2


def test_executable_drift_during_version_refuses(pair,monkeypatch):
    pins,fixture,digest,calls=pair;real=checks.run_owned
    def run(*a,**k):
        result=real(*a,**k);pins[0].path.write_bytes(b'changed');return result
    monkeypatch.setattr(checks,'run_owned',run)
    with pytest.raises(ToolCheckError,match='integrity pin'):check_pair(*pins,fixture,digest,EXPECTED)
    assert len(calls)==1


@pytest.mark.parametrize('failure',['empty','wrong_frame','nonzero','secret','cancel','malformed'])
def test_bad_outputs_and_errors_never_observe_success(pair,monkeypatch,failure):
    pins,fixture,digest,calls=pair;real=checks.run_owned
    def run(args,**kwargs):
        if failure=='secret':raise ProcessError('SECRET STDERR')
        if failure=='cancel':raise ProcessCanceled('SECRET STDERR')
        result=real(args,**kwargs)
        if failure=='malformed':return replace(result,stdout=b'wrong component')
        if args[-1]!='-version':
            return ProcessResult(1 if failure=='nonzero' else 0,b'' if failure=='empty' else b'x'*768,b'SECRET STDERR')
        return result
    monkeypatch.setattr(checks,'run_owned',run)
    with pytest.raises(ToolCheckError) as caught:check_pair(*pins,fixture,digest,EXPECTED)
    assert 'SECRET' not in str(caught.value)


def test_invalid_policy_and_early_cancel_never_launch(pair):
    pins,fixture,digest,calls=pair
    with pytest.raises(ValueError):check_pair(*pins,fixture,digest,(EXPECTED[0],EXPECTED[0]))
    with pytest.raises(ToolCheckCanceled):check_pair(*pins,fixture,digest,EXPECTED,cancel=lambda:True)
    assert not calls
