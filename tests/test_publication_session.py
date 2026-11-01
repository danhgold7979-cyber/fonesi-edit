from dataclasses import replace
from hashlib import sha256
import json
import sqlite3
import pytest
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.jobs.repository import JobRepository,JobConflict
from fonesi_edit.jobs.ownership import CoordinatorOwnership
from fonesi_edit.jobs.output_manifest import RequiredOutput,RequiredOutputs
from fonesi_edit.jobs.publication import PublicationSession
from fonesi_edit.artifacts.filesystem import PublicationConflict,PublicationUnknown

RAW=b'1\n00:00:00,000 --> 00:00:01,000\nHello'


def definition(root,role):
    return RequiredOutput(role,'subtitle',str(root),role+'.srt',subtitle_format='srt',
                          subtitle_encoding='utf-8',subtitle_sha256=sha256(RAW).hexdigest())


@pytest.fixture
def prepared(tmp_path,empty_plan):
    root=tmp_path/'outputs';root.mkdir();clock=[100]
    repo=JobRepository(tmp_path/'jobs.db',clock=lambda:clock[0])
    outputs=RequiredOutputs((definition(root,'original'),definition(root,'translated')))
    job=repo.submit('one',CompositionPlan.parse(empty_plan),42,outputs=outputs)
    job=repo.claim(job);job=repo.worker_transition(job,job.lease_token,'validating')
    with CoordinatorOwnership(repo) as owner:
        yield repo,owner,job,root,clock,outputs
    repo.close()


def test_all_roles_prepare_then_atomic_claim_no_final_or_success(prepared):
    repo,owner,job,root,clock,outputs=prepared
    with PublicationSession(repo,owner,job) as session:
        session.stage_subtitle('original',RAW)
        with pytest.raises(JobConflict,match='incomplete'):session.prepare()
        assert repo.db.execute('SELECT count(*) FROM artifact_sets').fetchone()[0]==0
        session.stage_subtitle('translated',RAW)
        set_id=session.prepare()
        assert repo.get(job.id).state=='validating'
        assert repo.db.execute('SELECT count(*) FROM publications WHERE set_id=?',(set_id,)).fetchone()[0]==2
        claimed=session.claim()
        assert claimed.state=='publishing'
        assert {r[0] for r in repo.db.execute('SELECT state FROM publications')}=={'claimed'}
        assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==0
        with pytest.raises(JobConflict):repo.request_cancel(claimed)
    assert not any((root/item.final_name).exists() for item in outputs.items)


@pytest.mark.parametrize('failure',['wrong_bytes','wrong_role','duplicate'])
def test_caller_cannot_substitute_staged_validation(prepared,failure):
    repo,owner,job,root,_,_=prepared
    with PublicationSession(repo,owner,job) as session:
        if failure=='duplicate':session.stage_subtitle('original',RAW)
        with pytest.raises(JobConflict):
            session.stage_subtitle('wrong' if failure=='wrong_role' else 'original',b'evil' if failure=='wrong_bytes' else RAW)
        assert repo.db.execute('SELECT count(*) FROM artifact_sets').fetchone()[0]==0


@pytest.mark.parametrize('failure',['cancel','expired','corrupt'])
def test_prepared_set_never_claims_after_cancel_expiry_or_corruption(prepared,failure):
    repo,owner,job,root,clock,_=prepared
    with PublicationSession(repo,owner,job) as session:
        session.stage_subtitle('original',RAW);session.stage_subtitle('translated',RAW);session.prepare()
        if failure=='cancel':repo.request_cancel(repo.get(job.id))
        elif failure=='expired':clock[0]=1000
        else:
            receipt,_=session._staged['original'];(root/receipt.directory/'payload').write_bytes(b'corrupt')
        with pytest.raises(PublicationUnknown if failure=='corrupt' else JobConflict):session.claim()
        assert repo.get(job.id).state=='validating'
        assert {r[0] for r in repo.db.execute('SELECT state FROM publications')}=={'prepared'}
        assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==0


def test_existing_foreign_identical_output_not_adopted(prepared):
    repo,owner,job,root,_,_=prepared
    foreign=root/'original.srt';foreign.write_bytes(RAW);identity=foreign.stat().st_ino
    with pytest.raises(PublicationConflict):PublicationSession(repo,owner,job)
    assert foreign.read_bytes()==RAW and foreign.stat().st_ino==identity
    assert repo.get(job.id).state=='validating'


def test_database_member_insert_failure_rolls_back_entire_prepare(prepared,empty_plan):
    repo,owner,job,root,_,outputs=prepared
    second=repo.submit('two',CompositionPlan.parse(empty_plan),43,outputs=outputs)
    second=repo.claim(second);second=repo.worker_transition(second,second.lease_token,'validating')
    with PublicationSession(repo,owner,job) as first,PublicationSession(repo,owner,second) as other:
        for session in (first,other):
            session.stage_subtitle('original',RAW);session.stage_subtitle('translated',RAW)
        first.prepare()
        with pytest.raises(sqlite3.IntegrityError):other.prepare()
        assert repo.db.execute('SELECT count(*) FROM artifact_sets').fetchone()[0]==1
        assert repo.db.execute('SELECT count(*) FROM publications').fetchone()[0]==2
        assert repo.get(second.id).state=='validating'


def test_legacy_or_intent_only_snapshot_cannot_invent_publication_roles(tmp_path,empty_plan):
    repo=JobRepository(tmp_path/'jobs.db');plan=CompositionPlan.parse(empty_plan)
    try:
        legacy=repo.submit('legacy',plan,42)
        incomplete=repo.submit('intent',plan,42,outputs=RequiredOutputs((RequiredOutput('video','media',str(tmp_path),'video.mp4'),)))
        for job in (legacy,incomplete):
            with pytest.raises(JobConflict):repo.publication_manifest(job)
    finally:repo.close()


def test_policy_roundtrip_drift_and_invalid_serialization(prepared,empty_plan):
    repo,owner,job,root,_,outputs=prepared
    assert repo.publication_manifest(job)==outputs
    assert outputs.to_dict()['version']==2
    changed=RequiredOutputs((replace(outputs.items[0],subtitle_sha256='0'*64),outputs.items[1]))
    with pytest.raises(JobConflict):repo.submit('one',CompositionPlan.parse(empty_plan),42,outputs=changed)
    invalid=outputs.to_dict();invalid['required'][0]['validation']['validated']=True
    with pytest.raises(ValueError):RequiredOutputs.from_dict(invalid)
    repo.db.execute('UPDATE jobs SET snapshot_hash=? WHERE id=?',('0'*64,job.id))
    with pytest.raises(JobConflict):repo.publication_manifest(repo.get(job.id))


@pytest.mark.parametrize('column,value',[('final_name','foreign.srt'),('validation_json','{}'),('version',2)])
def test_prepared_member_mutation_never_claimed(prepared,column,value):
    repo,owner,job,root,_,_=prepared
    with PublicationSession(repo,owner,job) as session:
        session.stage_subtitle('original',RAW);session.stage_subtitle('translated',RAW);session.prepare()
        repo.db.execute(f'UPDATE publications SET {column}=? WHERE role=?',(value,'original'))
        with pytest.raises(JobConflict):session.claim()
        assert repo.get(job.id).state=='validating'


def test_actual_media_and_subtitle_required_set_integration(tmp_path,empty_plan):
    import shutil
    from fractions import Fraction as F
    from fonesi_edit.media.validation import ExpectedStream
    from fonesi_edit.jobs.process import run_owned
    ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:pytest.skip('Actual target FFmpeg unavailable')
    source=tmp_path/'rendered.mp4';root=tmp_path/'outputs';root.mkdir()
    result=run_owned([ffmpeg,'-nostdin','-v','error','-f','lavfi','-i','color=c=black:s=64x48:r=25:d=1',
                      '-c:v','libx264','-pix_fmt','yuv420p',str(source)],timeout=30)
    assert result.returncode==0
    original=source.read_bytes()
    empty_plan['output'].update(width=64,height=48,fps=[25,1])
    expected=(ExpectedStream(0,'video','h264',F(0),F(1),F(1,25),width=64,height=48,frame_rate=F(25)),)
    outputs=RequiredOutputs((RequiredOutput('video','media',str(root),'video.mp4',expected_streams=expected),definition(root,'subtitle')))
    assert RequiredOutputs.from_dict(outputs.to_dict()).to_dict()==outputs.to_dict()
    repo=JobRepository(tmp_path/'jobs.db')
    try:
        job=repo.submit('render',CompositionPlan.parse(empty_plan),42,outputs=outputs)
        job=repo.claim(job);job=repo.worker_transition(job,job.lease_token,'validating')
        with CoordinatorOwnership(repo) as owner,PublicationSession(repo,owner,job) as session:
            session.stage_media('video',source,ffprobe,ffmpeg,timeout=30)
            with pytest.raises(JobConflict,match='incomplete'):session.prepare()
            session.stage_subtitle('subtitle',RAW);session.prepare();claimed=session.claim()
            assert claimed.state=='publishing'
            assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==0
        assert source.read_bytes()==original
        assert not (root/'video.mp4').exists() and not (root/'subtitle.srt').exists()
        mismatched=RequiredOutputs((replace(outputs.items[0],expected_streams=(replace(expected[0],width=128),)),outputs.items[1]))
        with pytest.raises(ValueError,match='contradicts'):repo.submit('wrong',CompositionPlan.parse(empty_plan),42,outputs=mismatched)
    finally:repo.close()


def test_claim_member_update_failure_rolls_back_job_set_and_members(prepared):
    repo,owner,job,root,_,_=prepared
    with PublicationSession(repo,owner,job) as session:
        session.stage_subtitle('original',RAW);session.stage_subtitle('translated',RAW);session.prepare()
        def deny_member_update(action,table,*args):
            return sqlite3.SQLITE_DENY if action==sqlite3.SQLITE_UPDATE and table=='publications' else sqlite3.SQLITE_OK
        repo.db.set_authorizer(deny_member_update)
        try:
            with pytest.raises(sqlite3.DatabaseError):session.claim()
        finally:repo.db.set_authorizer(None)
        assert repo.get(job.id).state=='validating'
        assert session.job==job
        assert {r[0] for r in repo.db.execute('SELECT state FROM artifact_sets')}=={'prepared'}
        assert {r[0] for r in repo.db.execute('SELECT state FROM publications')}=={'prepared'}
        assert repo.db.execute('SELECT count(*) FROM completion_history').fetchone()[0]==0


def test_cancel_before_prepare_has_no_journal_rows(prepared):
    repo,owner,job,root,_,_=prepared
    with PublicationSession(repo,owner,job) as session:
        session.stage_subtitle('original',RAW);session.stage_subtitle('translated',RAW)
        repo.request_cancel(repo.get(job.id))
        with pytest.raises(JobConflict):session.prepare()
        assert repo.db.execute('SELECT count(*) FROM artifact_sets').fetchone()[0]==0


def test_unknown_policy_and_noninteger_manifest_version_rejected(prepared):
    _,_,_,_,_,outputs=prepared
    bad=outputs.to_dict();bad['version']=True
    with pytest.raises(ValueError):RequiredOutputs.from_dict(bad)
    bad=outputs.to_dict();bad['required'][0]['validation']['policy']='caller_validated'
    with pytest.raises(ValueError):RequiredOutputs.from_dict(bad)


def test_oversized_subtitle_refused_before_hash_or_stage(prepared,monkeypatch):
    import fonesi_edit.jobs.publication as publication
    repo,owner,job,root,_,_=prepared
    with PublicationSession(repo,owner,job) as session:
        monkeypatch.setattr(publication,'sha256',lambda *a:pytest.fail('Oversized bytes reached digest'))
        with pytest.raises(JobConflict):session.stage_subtitle('original',b'x'*(publication.MAX_BYTES+1))
        assert not list(root.iterdir())


def test_typed_rational_policy_bounds_before_job_insert_and_exact_roundtrip(tmp_path,empty_plan):
    from fractions import Fraction as F
    from fonesi_edit.media.validation import ExpectedStream
    plan=CompositionPlan.parse(empty_plan);repo=JobRepository(tmp_path/'jobs.db')
    stream=ExpectedStream(0,'video','h264',F(0),F(1),F(1,2**127),width=1920,height=1080,frame_rate=F(30))
    try:
        with pytest.raises(ValueError,match='Bounded rational'):
            repo.submit('unreadable',plan,42,outputs=RequiredOutputs((RequiredOutput(
                'video','media',str(tmp_path),'video.mp4',expected_streams=(replace(stream,tolerance=F(1,2**129)),)),)))
        assert repo.db.execute('SELECT count(*) FROM jobs').fetchone()[0]==0
        outputs=RequiredOutputs((RequiredOutput('video','media',str(tmp_path),'video.mp4',expected_streams=(stream,)),))
        job=repo.submit('bounded',plan,42,outputs=outputs)
        assert repo.publication_manifest(job).to_dict()==outputs.to_dict()
    finally:repo.close()
