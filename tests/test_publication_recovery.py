import json
import os
import sqlite3
from pathlib import Path
import subprocess
import sys
import time
import pytest

from fonesi_edit.jobs.ownership import CoordinatorOwnership
from fonesi_edit.jobs.repository import JobRepository,JobConflict
from fonesi_edit.jobs.recovery import quarantine_abandoned
from test_publication_session import prepared,claimed_session,RAW,FaultConnection
from test_coordinator_ownership import _post_exit_owner


def test_new_owner_quarantines_without_requeue_or_file_changes(prepared):
    repo,owner,job,root,_,_=prepared
    with claimed_session(prepared) as session:
        session.publish_member('original');set_id=session._set_id
    owner.close()
    before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    with CoordinatorOwnership(repo) as newer:
        hold=quarantine_abandoned(repo,newer,set_id)
        assert hold.code=='OWNERSHIP_UNKNOWN' and hold.roles==('original','translated')
        versions=list(repo.db.execute('SELECT role,version FROM publications ORDER BY role'))
        assert quarantine_abandoned(repo,newer,set_id)==hold
        assert [tuple(x) for x in versions]==[tuple(x) for x in repo.db.execute('SELECT role,version FROM publications ORDER BY role')]
        assert {r[0] for r in repo.db.execute('SELECT state FROM publications')}=={'committed','unknown'}
        assert repo.get(job.id).state=='publishing'
        with pytest.raises(JobConflict):repo.resume(repo.get(job.id))
        with pytest.raises(JobConflict):repo.claim(repo.get(job.id))
        assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==0
    assert before=={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_current_owner_cannot_quarantine_its_live_session(prepared):
    repo,owner,job,root,_,_=prepared
    with claimed_session(prepared) as session:
        with pytest.raises(JobConflict):quarantine_abandoned(repo,owner,session._set_id)
        assert {r[0] for r in repo.db.execute('SELECT state FROM publications')}=={'claimed'}


def test_successful_set_not_reclassified(prepared):
    repo,owner,job,root,_,_=prepared
    with claimed_session(prepared) as session:
        session.publish_member('original');session.publish_member('translated');session.finish();set_id=session._set_id
    owner.close()
    with CoordinatorOwnership(repo) as newer:
        with pytest.raises(JobConflict):quarantine_abandoned(repo,newer,set_id)
        assert repo.get(job.id).state=='succeeded'
        assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==1


CHILD=r'''
import json,sys,time
from pathlib import Path
from hashlib import sha256
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.jobs.repository import JobRepository
from fonesi_edit.jobs.ownership import CoordinatorOwnership
from fonesi_edit.jobs.output_manifest import RequiredOutput,RequiredOutputs
from fonesi_edit.jobs.publication import PublicationSession
base=Path(sys.argv[1]);boundary=sys.argv[2];root=base/'outputs'
raw=b'1\n00:00:00,000 --> 00:00:01,000\nHello'
outputs=RequiredOutputs(tuple(RequiredOutput(role,'subtitle',str(root),role+'.srt',subtitle_format='srt',subtitle_encoding='utf-8',subtitle_sha256=sha256(raw).hexdigest()) for role in ('original','translated')))
repo=JobRepository(base/'jobs.db')
job=repo.submit('kill-boundary',CompositionPlan.parse(json.loads((base/'plan.json').read_text())),42,outputs=outputs)
job=repo.claim(job);job=repo.worker_transition(job,job.lease_token,'validating')
with CoordinatorOwnership(repo) as owner,PublicationSession(repo,owner,job) as session:
 session.stage_subtitle('original',raw);session.stage_subtitle('translated',raw);set_id=session.prepare()
 if boundary!='prepared':session.claim()
 if boundary in ('one_member','all_members'):session.publish_member('original')
 if boundary=='all_members':session.publish_member('translated')
 (base/'ready.tmp').write_text(json.dumps({'job':job.id,'set':set_id}))
 (base/'ready.tmp').replace(base/'ready.json')
 while True:time.sleep(1)
'''


@pytest.mark.parametrize('boundary',['prepared','claimed','one_member','all_members'])
def test_actual_process_kill_never_adopts_or_completes_old_outputs(tmp_path,empty_plan,boundary):
    root=tmp_path/'outputs';root.mkdir();(tmp_path/'plan.json').write_text(json.dumps(empty_plan))
    env=dict(os.environ);env['PYTHONPATH']=str(Path(__file__).resolve().parents[1]/'src')
    child=subprocess.Popen([sys.executable,'-c',CHILD,str(tmp_path),boundary],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        deadline=time.monotonic()+10
        while not (tmp_path/'ready.json').exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.01)
        assert (tmp_path/'ready.json').exists(), 'child did not reach publication boundary'
        ids=json.loads((tmp_path/'ready.json').read_text());child.kill();child.wait(timeout=5)
        # Foreign identical final created after crash-before-link must remain foreign.
        foreign=root/'translated.srt'
        if boundary in {'prepared','claimed','one_member'}:foreign.write_bytes(RAW)
        before={str(p.relative_to(root)):(p.stat().st_ino,p.read_bytes()) for p in root.rglob('*') if p.is_file()}
        repo=JobRepository(tmp_path/'jobs.db')
        try:
            with _post_exit_owner(repo,child) as owner:
                hold=quarantine_abandoned(repo,owner,ids['set'])
                assert hold.code=='OWNERSHIP_UNKNOWN'
                assert repo.get(ids['job']).state==('validating' if boundary=='prepared' else 'publishing')
                assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==0
                assert repo.db.execute('SELECT count(*) FROM artifacts').fetchone()[0]=={'prepared':0,'claimed':0,'one_member':1,'all_members':2}[boundary]
                with pytest.raises(JobConflict):repo.claim(repo.get(ids['job']))
        finally:repo.close()
        assert before=={str(p.relative_to(root)):(p.stat().st_ino,p.read_bytes()) for p in root.rglob('*') if p.is_file()}
    finally:
        if child.poll() is None:child.kill();child.wait(timeout=5)
        child.stderr.close()


def test_quarantine_transaction_failure_rolls_back_all_classifications(prepared):
    repo,owner,job,root,_,_=prepared
    with claimed_session(prepared) as session:set_id=session._set_id
    owner.close()
    with CoordinatorOwnership(repo) as newer:
        db=repo.db;repo.db=FaultConnection(db,'COMMIT')
        try:
            with pytest.raises(sqlite3.OperationalError):quarantine_abandoned(repo,newer,set_id)
        finally:repo.db=db
        assert {r[0] for r in repo.db.execute('SELECT state FROM publications')}=={'claimed'}
        assert repo.get(job.id).state=='publishing'


def test_mismatched_snapshot_never_reclassified(prepared):
    repo,owner,job,root,_,_=prepared
    with claimed_session(prepared) as session:set_id=session._set_id
    owner.close()
    repo.db.execute("UPDATE artifact_sets SET snapshot_hash='foreign'")
    with CoordinatorOwnership(repo) as newer:
        with pytest.raises(JobConflict):quarantine_abandoned(repo,newer,set_id)
        assert {r[0] for r in repo.db.execute('SELECT state FROM publications')}=={'claimed'}
