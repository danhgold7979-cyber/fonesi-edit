"""Typed lifetime evidence, not a media-codec or arbitrary process-kill test."""
from contextlib import ExitStack
from fractions import Fraction as F
import json
import os
from pathlib import Path
import sys
import time
import pytest
from fonesi_edit.jobs.process import run_owned,ProcessCanceled,ProcessError,_RetirementObservation
from fonesi_edit.media.retirement import ValidationLifecycle
from fonesi_edit.media.validation import ExpectedStream,MediaValidationError
from fonesi_edit.media.probe import ProbeCanceled
from fonesi_edit.jobs.publication import PublicationSession
from fonesi_edit.jobs.repository import JobRepository
from fonesi_edit.jobs.ownership import CoordinatorOwnership
from fonesi_edit.jobs.output_manifest import RequiredOutput,RequiredOutputs
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.artifacts.filesystem import PublicationUnknown,PublicationError


def test_unentered_reused_sealed_other_operation_refused():
    token=object();scope=ValidationLifecycle(token)
    assert not scope.confirmed_for(token)
    with scope.validation_body():pass
    assert scope.confirmed_for(token) and not scope.confirmed_for(object())
    with pytest.raises(RuntimeError):
        with scope.validation_body():pass
    assert not scope.confirmed_for(token) # Invalid reuse permanently revokes.
    with pytest.raises(RuntimeError):scope.run(lambda *a,**k:pytest.fail('must not launch'),[])
    nested=ValidationLifecycle(token)
    with nested.validation_body():
        with pytest.raises(RuntimeError):
            with nested.validation_body():pass
    assert not nested.confirmed_for(token)


def test_prelaunch_cancel_records_no_process_and_observation_not_reused():
    observation=_RetirementObservation()
    with pytest.raises(ProcessCanceled):run_owned([sys.executable,'-c','raise SystemExit(9)'],cancel=lambda:True,_retirement=observation)
    assert observation.mechanism=='NO_PROCESS'
    with pytest.raises(ValueError,match='Fresh'):run_owned([sys.executable,'-c','raise SystemExit(9)'],_retirement=observation)


def test_first_invocation_retired_second_unknown_never_seals_safe():
    token=object();scope=ValidationLifecycle(token)
    def unknown(*args,**kwargs):raise ProcessError('retirement unconfirmed')
    with pytest.raises(ProcessError):
        with scope.validation_body():
            scope.run(run_owned,[sys.executable,'-c','print("done")'],grace_seconds=.01)
            scope.run(unknown,[sys.executable])
    assert scope.mechanisms[0] in {'POSIX_GROUP_RETIRED','WINDOWS_JOB_EMPTY'}
    assert scope.mechanisms[1] is None and not scope.confirmed_for(token)


@pytest.mark.parametrize('failure',['cancel_callback','stdout_observer'])
def test_callback_exception_only_confirms_after_owned_retirement(failure):
    token=object();scope=ValidationLifecycle(token);observed=[]
    def fail():raise RuntimeError('callback failed')
    def stdout(chunk):
        observed.append(chunk)
        if failure=='stdout_observer':fail()
    def cancel():
        if observed and failure=='cancel_callback':fail()
        return False
    with pytest.raises(RuntimeError,match='callback failed'):
        with scope.validation_body():
            scope.run(run_owned,[sys.executable,'-c','import time;print("ready",flush=True);time.sleep(10)'],on_stdout=stdout,cancel=cancel,timeout=3,grace_seconds=.01)
    assert scope.confirmed_for(token)


def test_unobserved_fake_runner_success_cannot_claim_retirement():
    token=object();scope=ValidationLifecycle(token)
    with scope.validation_body():scope.run(lambda *a,**k:None,[sys.executable])
    assert scope.mechanisms==(None,) and not scope.confirmed_for(token)


@pytest.mark.skipif(os.name!='posix',reason='POSIX checked-close failure path')
def test_finally_close_failure_overrides_result_but_retires_other_handles(monkeypatch):
    import fonesi_edit.jobs.process as module
    selector=module.selectors.DefaultSelector;children=[];popen=module.subprocess.Popen
    class BrokenClose:
        def __init__(self):self.inner=selector()
        def __getattr__(self,name):return getattr(self.inner,name)
        def close(self):self.inner.close();raise OSError('injected selector close uncertainty')
    def launch(*a,**k):
        child=popen(*a,**k);children.append(child);return child
    monkeypatch.setattr(module.selectors,'DefaultSelector',BrokenClose)
    monkeypatch.setattr(module.subprocess,'Popen',launch)
    observation=_RetirementObservation()
    with pytest.raises(ProcessError,match='retirement unconfirmed'):
        run_owned([sys.executable,'-c','print("done")'],_retirement=observation,grace_seconds=.01)
    assert observation.mechanism is None
    assert children[0].stdout.closed and children[0].stderr.closed and children[0].returncode==0


@pytest.mark.skipif(os.name!='nt',reason='Actual Windows finalizer observation failure required')
def test_windows_failed_empty_observation_never_confirms(monkeypatch):
    import fonesi_edit.jobs.windows_process as module
    actual=module.await_job_empty
    def unknown(kernel,job):
        actual(kernel,job) # Retire actual child, then inject missing-proof observation.
        raise ProcessError('injected empty-job observation uncertainty')
    monkeypatch.setattr(module,'await_job_empty',unknown)
    observation=_RetirementObservation()
    with pytest.raises(ProcessError,match='observation uncertainty'):
        run_owned([sys.executable,'-c','print("done")'],_retirement=observation)
    assert observation.mechanism is None


@pytest.fixture
def media_session(tmp_path,empty_plan):
    root=tmp_path/'out';root.mkdir();source=tmp_path/'source.bin';source.write_bytes(b'synthetic lifecycle bytes, not video')
    empty_plan['output'].update(width=64,height=48,fps=[25,1],video_codec='h264')
    expected=ExpectedStream(0,'video','h264',F(0),F(1),F(1,25),width=64,height=48,frame_rate=F(25))
    outputs=RequiredOutputs((RequiredOutput('media','media',str(root),'final.mp4',expected_streams=(expected,)),))
    with ExitStack() as stack:
        repo=JobRepository(tmp_path/'jobs.db');stack.callback(repo.close)
        job=repo.submit('lifecycle',CompositionPlan.parse(empty_plan),0,outputs=outputs);job=repo.claim(job);job=repo.worker_transition(job,job.lease_token,'validating')
        owner=stack.enter_context(CoordinatorOwnership(repo));session=stack.enter_context(PublicationSession(repo,owner,job))
        yield session,repo,job,source,root


def install_python_probe(monkeypatch,observations):
    metadata={'streams':[{'index':0,'codec_type':'video','codec_name':'h264','start_time':'0','duration':'1','width':64,'height':48,'avg_frame_rate':'25/1'}]}
    def probe(args,**kwargs):
        observations.append(kwargs['_retirement'])
        return run_owned([sys.executable,'-c',f'print({json.dumps(metadata)!r})'],**kwargs)
    monkeypatch.setattr('fonesi_edit.media.probe.run_owned',probe)


def test_actual_owned_decoder_cancel_then_ack_and_only_own_temp_cleanup(media_session,tmp_path,monkeypatch):
    session,repo,job,source,root=media_session;observations=[];install_python_probe(monkeypatch,observations)
    marker=tmp_path/'descendant';child=f'import pathlib,time;p=pathlib.Path({str(marker)!r});p.write_text("ready");time.sleep(.6);p.write_text("SURVIVED")'
    parent=f'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",{child!r}]);time.sleep(10)'
    def decoder(args,**kwargs):
        observations.append(kwargs['_retirement'])
        return run_owned([sys.executable,'-c',parent],**kwargs)
    monkeypatch.setattr('fonesi_edit.media.validation.run_owned',decoder)
    with pytest.raises(ProbeCanceled):session.stage_media('media',source,sys.executable,sys.executable,cancel=marker.exists,timeout=5)
    assert len(observations)==2 and all(o.mechanism==('WINDOWS_JOB_EMPTY' if os.name=='nt' else 'POSIX_GROUP_RETIRED') for o in observations)
    assert not session._quiescence_unknown and not session._staging
    canceled=repo.request_cancel(repo.get(job.id));repo.worker_transition(canceled,canceled.lease_token,'canceled')
    if os.name=='nt':assert session.cleanup_canceled()==1 and not list(root.glob('.fonesi-stage-*'))
    else:
        with pytest.raises(PublicationError,match='unavailable'):session.cleanup_canceled()
        assert list(root.glob('.fonesi-stage-*'))
    time.sleep(.7)
    assert marker.read_text()=='ready' and source.read_bytes()==b'synthetic lifecycle bytes, not video'
    assert not (root/'final.mp4').exists() and repo.get(job.id).state=='canceled'


def test_sanitized_decoder_failure_keeps_unknown_despite_retired_probe(media_session,monkeypatch):
    session,repo,job,source,root=media_session;observations=[];install_python_probe(monkeypatch,observations)
    def unknown(*a,**k):raise ProcessError('native retirement unconfirmed')
    monkeypatch.setattr('fonesi_edit.media.validation.run_owned',unknown)
    with pytest.raises(MediaValidationError):session.stage_media('media',source,sys.executable,sys.executable)
    assert observations[0].mechanism in {'WINDOWS_JOB_EMPTY','POSIX_GROUP_RETIRED'} and session._quiescence_unknown
    canceled=repo.request_cancel(repo.get(job.id));repo.worker_transition(canceled,canceled.lease_token,'canceled')
    with pytest.raises(PublicationUnknown,match='retirement unconfirmed'):session.cleanup_canceled()
    assert next(root.glob('.fonesi-stage-*/payload')).read_bytes()==source.read_bytes()


def test_parser_failure_after_real_probe_retirement_is_not_unknown(media_session,monkeypatch):
    session,repo,job,source,root=media_session;observations=[]
    def malformed(args,**kwargs):
        observations.append(kwargs['_retirement'])
        return run_owned([sys.executable,'-c','print("not-json")'],**kwargs)
    monkeypatch.setattr('fonesi_edit.media.probe.run_owned',malformed)
    with pytest.raises(MediaValidationError):session.stage_media('media',source,sys.executable,sys.executable)
    assert len(observations)==1 and observations[0].mechanism in {'WINDOWS_JOB_EMPTY','POSIX_GROUP_RETIRED'}
    assert not session._quiescence_unknown
    requested=repo.request_cancel(repo.get(job.id));repo.worker_transition(requested,requested.lease_token,'canceled')
    if os.name=='nt':assert session.cleanup_canceled()==1
    else:
        with pytest.raises(PublicationError,match='unavailable'):session.cleanup_canceled()
    assert not (root/'final.mp4').exists()


def test_validator_success_without_lifecycle_entry_is_rejected(media_session,monkeypatch):
    from types import SimpleNamespace
    session,repo,job,source,root=media_session
    monkeypatch.setattr('fonesi_edit.jobs.publication.validate_media',lambda *a,**k:SimpleNamespace(sha256='fake'))
    with pytest.raises(PublicationUnknown,match='without confirmed'):session.stage_media('media',source,sys.executable,sys.executable)
    assert session._quiescence_unknown and not session._staged
    assert not (root/'final.mp4').exists()


def test_actual_validator_early_failure_seals_no_launch_scope(tmp_path):
    from fonesi_edit.media.validation import validate_media
    token=object();scope=ValidationLifecycle(token)
    with pytest.raises(ValueError):validate_media(tmp_path/'unused',sys.executable,sys.executable,(),_lifecycle=scope)
    assert scope.mechanisms==() and scope.confirmed_for(token)


def test_setup_before_any_job_uses_no_process_not_empty_job_proof(monkeypatch):
    from types import SimpleNamespace
    import fonesi_edit.jobs.windows_process as module
    calls=[]
    def fail_job(*args):calls.append('CreateJobObjectW');return 0
    monkeypatch.setattr(module,'os',SimpleNamespace(name='nt'))
    monkeypatch.setattr(module,'_kernel',lambda:SimpleNamespace(CreateJobObjectW=fail_job))
    monkeypatch.setattr(module.C,'get_last_error',lambda:5,raising=False)
    observation=_RetirementObservation()
    with pytest.raises(ProcessError,match='Handle creation failed'):
        module.run_windows_owned([sys.executable,'-c','raise SystemExit(9)'],_retirement=observation)
    assert calls==['CreateJobObjectW'] and observation.mechanism=='NO_PROCESS'
