"""Production required-set integration: native cases only count on Windows."""
import os
import pytest
from fonesi_edit.artifacts.filesystem import Destination,PublicationError,PublicationUnknown,_OwnedFD
from fonesi_edit.artifacts.completed_cleanup import cleanup_completed_stage
from fonesi_edit.jobs.repository import JobConflict
from fonesi_edit.jobs.publication import PublicationSession
from test_publication_session import prepared,RAW

windows=pytest.mark.skipif(os.name!='nt',reason='Actual Windows completed-cleanup integration required')


def completed(prepared):
    repo,owner,job,root,clock,outputs=prepared
    session=PublicationSession(repo,owner,job)
    for item in outputs.items:session.stage_subtitle(item.role,RAW)
    session.prepare();session.claim()
    for item in outputs.items:session.publish_member(item.role)
    session.finish()
    return session


def test_owned_fd_transfer_closes_once_even_recycled_number(tmp_path):
    first=os.open(tmp_path/'first',os.O_CREAT|os.O_RDWR,0o600);owner=_OwnedFD(first)
    owner.close()
    second=os.open(tmp_path/'second',os.O_CREAT|os.O_RDWR,0o600)
    try:
        owner.close();assert os.fstat(second).st_size==0 and owner.fd is None
    finally:os.close(second)


def test_unsupported_retains_stage_and_completed_history(prepared):
    if os.name=='nt':pytest.skip('Unsupported-platform branch')
    repo,owner,job,root,clock,outputs=prepared
    session=completed(prepared)
    with pytest.raises(PublicationError,match='unavailable'):session.cleanup_completed()
    assert session._closed and len(list(root.glob('.fonesi-stage-*')))==2
    assert all((root/item.final_name).read_bytes()==RAW for item in outputs.items)
    assert repo.get(job.id).state=='succeeded' and repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==1


@windows
def test_cleanup_completed_exact_set_preserves_all_finals_history(prepared):
    repo,owner,job,root,clock,outputs=prepared
    session=completed(prepared)
    identities={item.final_name:(root/item.final_name).stat().st_ino for item in outputs.items}
    cleaned=session.cleanup_completed()
    assert len(cleaned)==2 and not list(root.glob('.fonesi-stage-*')) and session._closed
    for item in outputs.items:
        assert (root/item.final_name).read_bytes()==RAW and (root/item.final_name).stat().st_ino==identities[item.final_name]
    assert repo.get(job.id).state=='succeeded' and repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==1
    with pytest.raises(JobConflict):session.cleanup_completed()


@windows
@pytest.mark.parametrize('failure',['history','epoch','not_finished'])
def test_cleanup_rejects_missing_live_completion_authority(prepared,failure):
    repo,owner,job,root,clock,outputs=prepared
    if failure=='not_finished':session=PublicationSession(repo,owner,job)
    else:session=completed(prepared)
    if failure=='history':repo.db.execute('DELETE FROM completion_history')
    if failure=='epoch':repo.db.execute("INSERT INTO coordinator_epochs(owner_uuid) VALUES('lost-during-cleanup')")
    before={p.name:p.read_bytes() for p in root.glob('*.srt')}
    with pytest.raises((JobConflict,PublicationError)):session.cleanup_completed()
    assert session._closed and {p.name:p.read_bytes() for p in root.glob('*.srt')}==before


@windows
def test_foreign_child_retained_after_owned_payload_cleanup(prepared):
    repo,owner,job,root,clock,outputs=prepared
    session=completed(prepared)
    receipt,_=session._staged[outputs.items[0].role]
    foreign=root/receipt.directory/'foreign';foreign.write_bytes(b'FOREIGN')
    with pytest.raises(PublicationUnknown):session.cleanup_completed()
    assert foreign.read_bytes()==b'FOREIGN' and session._closed
    assert all((root/item.final_name).read_bytes()==RAW for item in outputs.items)
    assert repo.get(job.id).state=='succeeded'


@windows
def test_cleanup_authority_loss_after_readback_never_marks(prepared,monkeypatch):
    import fonesi_edit.artifacts.completed_cleanup as module
    repo,owner,job,root,clock,outputs=prepared
    session=completed(prepared);original=module._content
    def lose(fd,receipt):
        original(fd,receipt);repo.db.execute("INSERT INTO coordinator_epochs(owner_uuid) VALUES('lost-during-cleanup')")
    monkeypatch.setattr(module,'_content',lose)
    with pytest.raises((JobConflict,PublicationError)):session.cleanup_completed()
    assert session._closed and len(list(root.glob('.fonesi-stage-*/payload')))==2
    assert all((root/item.final_name).read_bytes()==RAW for item in outputs.items)


@windows
def test_partial_cleanup_failure_never_replays_or_undoes_completed_job(prepared,monkeypatch):
    import fonesi_edit.artifacts.completed_cleanup as module
    repo,owner,job,root,clock,outputs=prepared
    session=completed(prepared);native=module.NativeObject
    def refuse_strong_pin(path,**kwargs):
        if path.name.endswith('.srt') and kwargs.get('share')==module.SHARE_READ:
            raise OSError('injected after payload disposition, before directory')
        return native(path,**kwargs)
    monkeypatch.setattr(module,'NativeObject',refuse_strong_pin)
    with pytest.raises(PublicationUnknown):session.cleanup_completed()
    assert session._closed and repo.get(job.id).state=='succeeded'
    assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==1
    assert all((root/item.final_name).read_bytes()==RAW for item in outputs.items)
    with pytest.raises(JobConflict):session.cleanup_completed()


@windows
def test_corrupt_final_hash_refuses_destructive_effect(prepared):
    repo,owner,job,root,clock,outputs=prepared
    session=completed(prepared)
    (root/outputs.items[0].final_name).write_bytes(b'CORRUPT')
    with pytest.raises(PublicationUnknown):session.cleanup_completed()
    assert session._closed and len(list(root.glob('.fonesi-stage-*/payload')))==2
    assert (root/outputs.items[0].final_name).read_bytes()==b'CORRUPT'
    assert repo.get(job.id).state=='succeeded'


def test_uncertain_close_is_unknown_and_session_stays_retired(prepared,monkeypatch):
    repo,owner,job,root,clock,outputs=prepared
    session=PublicationSession(repo,owner,job);close=session._stack.close
    def fail_close():
        close();raise OSError('injected close observation uncertainty')
    monkeypatch.setattr(session._stack,'close',fail_close)
    with pytest.raises(PublicationUnknown,match='retirement uncertain'):session.cleanup_completed()
    assert session._closed and not list(root.glob('*.srt'))


@windows
def test_authority_refusal_after_first_member_is_unknown_not_preflight(prepared,monkeypatch):
    import fonesi_edit.artifacts.completed_cleanup as module
    repo,owner,job,root,clock,outputs=prepared
    session=completed(prepared);cleanup=module.cleanup_completed_stage;effects=[]
    def first_then_lose(destination,receipt,name,**kwargs):
        if effects:raise JobConflict('injected completion-history guard loss after first member')
        result=cleanup(destination,receipt,name,**kwargs)
        assert not (destination.root/receipt.directory).exists()
        effects.append(name)
        return result
    monkeypatch.setattr(module,'cleanup_completed_stage',first_then_lose)
    with pytest.raises(PublicationUnknown,match='partially attempted') as raised:session.cleanup_completed()
    assert isinstance(raised.value.__cause__,JobConflict) and len(effects)==1
    assert session._closed and repo.get(job.id).state=='succeeded'
    assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==1
    assert all((root/item.final_name).read_bytes()==RAW for item in outputs.items)


def test_entered_maintenance_guard_failure_classified_unknown(prepared,monkeypatch):
    from types import SimpleNamespace
    import fonesi_edit.jobs.publication as publication
    import fonesi_edit.artifacts.completed_cleanup as cleanup
    repo,owner,job,root,clock,outputs=prepared
    session=completed(prepared);calls=[]
    def entered(destination,receipt,name,**kwargs):
        calls.append(name)
        raise JobConflict('injected guard failure after entering maintenance')
    monkeypatch.setattr(publication,'os',SimpleNamespace(name='nt'))
    monkeypatch.setattr(cleanup,'cleanup_completed_stage',entered)
    with pytest.raises(PublicationUnknown,match='partially attempted') as raised:session.cleanup_completed()
    assert calls and isinstance(raised.value.__cause__,JobConflict) and session._closed
    assert repo.get(job.id).state=='succeeded' and repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==1
