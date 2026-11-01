"""Canceled stage ownership and native deletion; no fake native acceptance."""
from contextlib import ExitStack
from fractions import Fraction as F
import os
import pytest
from fonesi_edit.artifacts.filesystem import Destination,PublicationCanceled,PublicationError,PublicationUnknown
from fonesi_edit.artifacts.subtitle_stage import SubtitleStageCanceled
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.jobs.repository import JobRepository,JobConflict
from fonesi_edit.jobs.ownership import CoordinatorOwnership
from fonesi_edit.jobs.output_manifest import RequiredOutput,RequiredOutputs
from fonesi_edit.jobs.publication import PublicationSession
from fonesi_edit.media.validation import ExpectedStream
from test_publication_session import prepared,RAW

windows=pytest.mark.skipif(os.name!='nt',reason='Actual Windows canceled cleanup required')


def acknowledge(repo,job):
    requested=repo.request_cancel(repo.get(job.id))
    return repo.worker_transition(requested,requested.lease_token,'canceled')


def test_failed_producer_keeps_original_unvalidated_anchor_not_receipt(tmp_path):
    def failing():
        yield b'partial'
        raise PublicationCanceled('producer canceled')
    with Destination(tmp_path) as dest:
        with pytest.raises(PublicationCanceled):dest._create_stage_chunks(failing())
        assert len(dest._created)==1 and dest._attempted_directories==set(dest._created)
        owned=next(iter(dest._created.values()));anchor=dest._anchors[owned.directory]
        assert os.fstat(anchor.fd).st_ino==owned.file_identity[1]
        assert (tmp_path/owned.directory/'payload').read_bytes()==b'partial'
        with pytest.raises(PublicationError):dest.publish(owned,'not-validated.bin')
    assert (tmp_path/owned.directory/'payload').read_bytes()==b'partial'


def test_active_operation_blocks_cleanup_without_retiring_writer_session(prepared):
    repo,owner,job,root,clock,outputs=prepared
    with PublicationSession(repo,owner,job) as session:
        with session._staging_operation():
            with pytest.raises(JobConflict,match='retirement'):session.cleanup_canceled()
            with pytest.raises(JobConflict,match='retirement'):session.cleanup_completed()
            assert session._staging and not session._closed
        assert not session._staging


def test_subtitle_postwrite_cancel_keeps_ownership_and_exits_operation(prepared):
    repo,owner,job,root,clock,outputs=prepared;calls=[]
    with PublicationSession(repo,owner,job) as session:
        def cancel():calls.append(1);return len(calls)==3
        with pytest.raises(SubtitleStageCanceled):session.stage_subtitle('original',RAW,cancel=cancel)
        assert not session._staging and not session._staged
        dest=session._destinations[str(root)];assert len(dest._created)==1
        assert next(root.glob('.fonesi-stage-*/payload')).read_bytes()==RAW


@pytest.mark.parametrize('state',['validating','expired','claimed'])
def test_nonacknowledged_or_publishing_cleanup_refused(prepared,state):
    repo,owner,job,root,clock,outputs=prepared
    session=PublicationSession(repo,owner,job);session.stage_subtitle('original',RAW)
    if state=='expired':clock[0]=1000
    if state=='claimed':
        session.stage_subtitle('translated',RAW);session.prepare();session.claim()
    with pytest.raises(JobConflict):session.cleanup_canceled()
    assert session._closed and next(root.glob('.fonesi-stage-*/payload')).read_bytes()==RAW
    assert not list(root.glob('*.srt'))


def test_nonwindows_cancel_cleanup_retains_without_path_delete(prepared):
    if os.name=='nt':pytest.skip('Non-Windows unsupported branch')
    repo,owner,job,root,clock,outputs=prepared
    session=PublicationSession(repo,owner,job);session.stage_subtitle('original',RAW);acknowledge(repo,job)
    with pytest.raises(PublicationError,match='unavailable'):session.cleanup_canceled()
    assert session._closed and next(root.glob('.fonesi-stage-*/payload')).read_bytes()==RAW
    assert repo.get(job.id).state=='canceled'


@windows
@pytest.mark.parametrize('prepared_set',[False,True])
def test_canceled_exact_stages_removed_sources_foreign_final_preserved(prepared,prepared_set):
    repo,owner,job,root,clock,outputs=prepared
    source=root.parent/'source.srt';source.write_bytes(RAW);foreign=root/'foreign.srt';foreign.write_bytes(b'FOREIGN')
    session=PublicationSession(repo,owner,job)
    for item in outputs.items:session.stage_subtitle(item.role,RAW)
    if prepared_set:session.prepare()
    acknowledge(repo,job)
    assert session.cleanup_canceled()==2
    assert session._closed and not list(root.glob('.fonesi-stage-*'))
    assert source.read_bytes()==RAW and foreign.read_bytes()==b'FOREIGN'
    assert repo.get(job.id).state=='canceled' and repo.db.execute('SELECT count(*) FROM artifacts').fetchone()[0]==0
    assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==0
    with pytest.raises(JobConflict):session.cleanup_canceled()


@windows
def test_postwrite_cancellation_cleans_unvalidated_owned_stage(prepared):
    repo,owner,job,root,clock,outputs=prepared;session=PublicationSession(repo,owner,job);calls=[]
    def cancel():calls.append(1);return len(calls)==3
    with pytest.raises(SubtitleStageCanceled):session.stage_subtitle('original',RAW,cancel=cancel)
    acknowledge(repo,job)
    assert session.cleanup_canceled()==1 and not list(root.glob('.fonesi-stage-*'))
    assert not list(root.glob('*.srt'))


@windows
def test_foreign_child_survives_partial_canceled_cleanup(prepared):
    repo,owner,job,root,clock,outputs=prepared
    session=PublicationSession(repo,owner,job);session.stage_subtitle('original',RAW)
    stage=next(root.glob('.fonesi-stage-*'));foreign=stage/'foreign';foreign.write_bytes(b'FOREIGN')
    acknowledge(repo,job)
    with pytest.raises(PublicationUnknown):session.cleanup_canceled()
    assert foreign.read_bytes()==b'FOREIGN' and session._closed and repo.get(job.id).state=='canceled'


@windows
def test_epoch_loss_at_native_effect_preserves_payload(prepared,monkeypatch):
    import fonesi_edit.artifacts.canceled_cleanup as module
    repo,owner,job,root,clock,outputs=prepared
    session=PublicationSession(repo,owner,job);session.stage_subtitle('original',RAW);acknowledge(repo,job)
    capability=module.DeleteCapability
    class LoseEpoch(capability):
        def mark(self,**kwargs):
            repo.db.execute("INSERT INTO coordinator_epochs(owner_uuid) VALUES('cancel-lost')")
            return super().mark(**kwargs)
    monkeypatch.setattr(module,'DeleteCapability',LoseEpoch)
    with pytest.raises(PublicationUnknown):session.cleanup_canceled()
    assert next(root.glob('.fonesi-stage-*/payload')).read_bytes()==RAW and session._closed


@pytest.mark.parametrize('native',[False,True])
def test_interrupted_media_copy_keeps_source_and_original_partial(tmp_path,empty_plan,native,monkeypatch):
    if native and os.name!='nt':pytest.skip('Actual Windows canceled-copy cleanup required')
    root=tmp_path/'out';root.mkdir();source=tmp_path/'source.bin';source.write_bytes(b'x'*(2*1024*1024));calls=[]
    empty_plan['output'].update(width=64,height=48,fps=[25,1],video_codec='h264')
    stream=ExpectedStream(0,'video','h264',F(0),F(1),F(1,25),width=64,height=48,frame_rate=F(25))
    outputs=RequiredOutputs((RequiredOutput('media','media',str(root),'final.mp4',expected_streams=(stream,)),))
    with ExitStack() as stack:
        repo=JobRepository(tmp_path/'jobs.db');stack.callback(repo.close)
        job=repo.submit('copy',CompositionPlan.parse(empty_plan),0,outputs=outputs);job=repo.claim(job);job=repo.worker_transition(job,job.lease_token,'validating')
        owner=stack.enter_context(CoordinatorOwnership(repo));session=stack.enter_context(PublicationSession(repo,owner,job))
        def cancel():calls.append(1);return len(calls)==3
        def unexpected(*a,**k):pytest.fail('Canceled copy must never launch validation')
        monkeypatch.setattr('fonesi_edit.jobs.publication.validate_media',unexpected)
        with pytest.raises(PublicationCanceled):session.stage_media('media',source,'not-launched','not-launched',cancel=cancel)
        dest=session._destinations[str(root)];record=next(iter(dest._created.values()))
        assert os.fstat(dest._anchors[record.directory].fd).st_ino==record.file_identity[1]
        assert (root/record.directory/'payload').stat().st_size==1024*1024
        assert not session._staging and not session._staged and source.read_bytes()==b'x'*(2*1024*1024)
        if native:
            acknowledge(repo,job);assert session.cleanup_canceled()==1
            assert not list(root.glob('.fonesi-stage-*'))
    assert source.read_bytes()==b'x'*(2*1024*1024) and not (root/'final.mp4').exists()


def test_cancel_before_any_creation_needs_no_destructive_capability(prepared):
    repo,owner,job,root,clock,outputs=prepared
    session=PublicationSession(repo,owner,job);acknowledge(repo,job)
    assert session.cleanup_canceled()==0 and session._closed and not list(root.iterdir())


def test_creation_anchor_failure_is_unknown_never_silently_clean(prepared,monkeypatch):
    repo,owner,job,root,clock,outputs=prepared
    session=PublicationSession(repo,owner,job)
    def fail_dup(fd):raise OSError('injected anchor allocation failure')
    with monkeypatch.context() as patch:
        patch.setattr(os,'dup',fail_dup)
        with pytest.raises(OSError):session.stage_subtitle('original',RAW)
    acknowledge(repo,job)
    with pytest.raises(PublicationUnknown,match='Incomplete creation ownership'):session.cleanup_canceled()
    assert session._closed and len(list(root.glob('.fonesi-stage-*')))==1


def test_reconstructed_record_never_grants_cleanup_authority(tmp_path,monkeypatch):
    from dataclasses import replace
    from types import SimpleNamespace
    import fonesi_edit.artifacts.canceled_cleanup as module
    with Destination(tmp_path) as dest:
        receipt=dest.create_stage(b'owned');record=dest._created[receipt.directory]
        monkeypatch.setattr(module,'os',SimpleNamespace(name='nt')) # Refusal before any native API.
        with pytest.raises(PublicationUnknown,match='original live creation'):
            module.cleanup_canceled_stage(dest,replace(record),before_effect=lambda:None)
        assert (tmp_path/receipt.directory/'payload').read_bytes()==b'owned'


@windows
def test_canceled_handoff_swap_preserves_foreign_payload(prepared,monkeypatch):
    import fonesi_edit.artifacts.canceled_cleanup as module
    repo,owner,job,root,clock,outputs=prepared
    session=PublicationSession(repo,owner,job);session.stage_subtitle('original',RAW);acknowledge(repo,job)
    stage=next(root.glob('.fonesi-stage-*'));capability=module.DeleteCapability
    class ReplaceDuringTransfer(capability):
        def __init__(self,path,fd,release,**kwargs):
            def swap():
                release();path.rename(path.with_name('original'));path.write_bytes(b'FOREIGN')
            super().__init__(path,fd,swap,**kwargs)
    monkeypatch.setattr(module,'DeleteCapability',ReplaceDuringTransfer)
    with pytest.raises(PublicationUnknown):session.cleanup_canceled()
    assert (stage/'payload').read_bytes()==b'FOREIGN' and (stage/'original').read_bytes()==RAW
    assert session._closed and repo.get(job.id).state=='canceled'


def test_unknown_validator_retirement_stays_blocked_after_cancel_ack(tmp_path,empty_plan,monkeypatch):
    from fonesi_edit.jobs.process import ProcessError
    import fonesi_edit.artifacts.canceled_cleanup as cleanup
    root=tmp_path/'out';root.mkdir();source=tmp_path/'source.bin';source.write_bytes(b'copied source')
    empty_plan['output'].update(width=64,height=48,fps=[25,1],video_codec='h264')
    stream=ExpectedStream(0,'video','h264',F(0),F(1),F(1,25),width=64,height=48,frame_rate=F(25))
    outputs=RequiredOutputs((RequiredOutput('media','media',str(root),'final.mp4',expected_streams=(stream,)),))
    with ExitStack() as stack:
        repo=JobRepository(tmp_path/'jobs.db');stack.callback(repo.close)
        job=repo.submit('uncertain',CompositionPlan.parse(empty_plan),0,outputs=outputs);job=repo.claim(job);job=repo.worker_transition(job,job.lease_token,'validating')
        owner=stack.enter_context(CoordinatorOwnership(repo));session=stack.enter_context(PublicationSession(repo,owner,job))
        def uncertain(*a,**k):raise ProcessError('Process retirement unconfirmed')
        def forbidden(*a,**k):pytest.fail('Unknown retirement must not enter native cleanup')
        monkeypatch.setattr('fonesi_edit.jobs.publication.validate_media',uncertain)
        monkeypatch.setattr(cleanup,'cleanup_canceled_stage',forbidden)
        with pytest.raises(ProcessError):session.stage_media('media',source,'not-launched','not-launched')
        assert not session._staging and session._quiescence_unknown
        acknowledge(repo,job)
        for action in (session.cleanup_canceled,session.cleanup_completed,session._guard_worker):
            with pytest.raises(PublicationUnknown,match='retirement unconfirmed'):action()
        assert next(root.glob('.fonesi-stage-*/payload')).read_bytes()==source.read_bytes()
        assert not list(root.glob('*.mp4'))
        assert repo.get(job.id).state=='canceled'
