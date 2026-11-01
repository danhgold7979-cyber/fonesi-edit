import pytest
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.jobs.repository import JobRepository, JobConflict

@pytest.fixture
def repo(tmp_path):
    r=JobRepository(tmp_path/'jobs.sqlite3',clock=lambda:100)
    yield r
    r.close()

def submit(repo, empty_plan, key='one'):
    return repo.submit(key,CompositionPlan.parse(empty_plan),42)

def test_idempotence_snapshot_conflict_and_reopen(tmp_path, empty_plan):
    path=tmp_path/'jobs.db';r=JobRepository(path)
    j=submit(r,empty_plan)
    assert submit(r,empty_plan)==j
    with pytest.raises(JobConflict):r.submit('one',CompositionPlan.parse(empty_plan),43)
    r.close();r=JobRepository(path)
    assert r.get(j.id)==j
    r.close()

def test_competing_claims(tmp_path,empty_plan):
    path=tmp_path/'jobs.db';a=JobRepository(path);b=JobRepository(path)
    j=submit(a,empty_plan);running=a.claim(j)
    with pytest.raises(JobConflict):b.claim(j)
    assert b.get(j.id)==running
    a.close();b.close()

def test_pause_cancel_and_stale_version(repo,empty_plan):
    j=submit(repo,empty_plan);p=repo.pause(j)
    with pytest.raises(JobConflict):repo.claim(j)
    with pytest.raises(JobConflict):repo.claim(p)
    pending=repo.resume(p);canceled=repo.request_cancel(pending)
    assert canceled.state=='canceled'
    with pytest.raises(JobConflict):repo.resume(canceled)

def test_lease_cancel_ack_and_late_events(repo,empty_plan):
    r=repo.claim(submit(repo,empty_plan));token=r.lease_token
    h=repo.heartbeat(r,token)
    with pytest.raises(JobConflict):repo.worker_transition(r,token,'validating')
    c=repo.request_cancel(h)
    with pytest.raises(JobConflict):repo.worker_transition(c,token,'validating')
    done=repo.worker_transition(c,token,'canceled')
    with pytest.raises(JobConflict):repo.heartbeat(c,token)
    assert done.state=='canceled'

def test_no_success_or_publish_without_artifacts(repo,empty_plan):
    r=repo.claim(submit(repo,empty_plan))
    for target in ['succeeded','succeeded_with_warnings','publishing','skipped','canceled']:
        with pytest.raises(JobConflict):repo.worker_transition(r,r.lease_token,target)
    v=repo.worker_transition(r,r.lease_token,'validating')
    with pytest.raises(JobConflict):repo.worker_transition(v,v.lease_token,'publishing')

def test_expiry_discovery_not_retry(repo,empty_plan):
    r=repo.claim(submit(repo,empty_plan));repo.clock=lambda:131
    assert repo.expired()==(r,)
    with pytest.raises(JobConflict):repo.heartbeat(r,r.lease_token)
    with pytest.raises(JobConflict):repo.worker_transition(r,r.lease_token,'failed')
    assert repo.get(r.id).state=='running'


def test_forged_lease_record_rejected(repo,empty_plan):
    from dataclasses import replace
    r=repo.claim(submit(repo,empty_plan))
    forged=replace(r,lease_token='wrong',lease_deadline=999)
    with pytest.raises(JobConflict):repo.worker_transition(forged,'wrong','validating')
    assert repo.get(r.id)==r

def test_foreign_version_one_untouched(tmp_path):
    import sqlite3
    path=tmp_path/'foreign.db';db=sqlite3.connect(path)
    db.executescript('CREATE TABLE foreign_data(x);PRAGMA user_version=1;');db.close()
    before=path.read_bytes()
    with pytest.raises(JobConflict):JobRepository(path)
    assert path.read_bytes()==before

def test_matching_identity_malformed_schema_unchanged(tmp_path):
    import sqlite3
    path=tmp_path/'corrupt.db';db=sqlite3.connect(path)
    db.executescript('CREATE TABLE jobs(id TEXT);PRAGMA user_version=1;PRAGMA application_id=1178946122;');db.close()
    before=path.read_bytes()
    with pytest.raises(JobConflict,match='schema'):JobRepository(path)
    assert path.read_bytes()==before
