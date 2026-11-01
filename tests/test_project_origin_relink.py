import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import uuid
import pytest
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage import projects as storage
from fonesi_edit.storage.projects import Project,ProjectStore,StorageError,save_project_file
from fonesi_edit.storage.db_ownership import register_database,receipt_path
from fonesi_edit.storage.autosave import prepare_open,CompletedCommand,RelinkRequired
from fonesi_edit.storage.relink import relink,RelinkMismatch
from fonesi_edit.media.probe import ProbeCanceled


def model(plan):return Project(str(uuid.uuid4()),'test',CompositionPlan.parse(plan))


def old_database(path,project):
    with sqlite3.connect(path) as db:
        db.execute(storage.PROJECTS_V1_SQL)
        db.execute('INSERT INTO projects VALUES(?,?,?,?,?)',(project.id,project.name,project.to_json(),1,0))
        db.execute(f'PRAGMA application_id={storage.APPLICATION_ID}')
        db.execute('PRAGMA user_version=1')
    register_database(path,storage.APPLICATION_ID,storage.PROJECT_V1_HASH)


def test_owned_v1_migrates_with_validated_old_backup_and_unknown_origin(tmp_path,empty_plan):
    path=tmp_path/'db';p=model(empty_plan);old_database(path,p)
    receipt=receipt_path(path).read_bytes()
    with ProjectStore(path) as store:
        assert store.db.execute('PRAGMA user_version').fetchone()==(2,)
        assert store.load(p.id).origin_base is None
        assert store.load(p.id).project==p
    assert receipt_path(path).read_bytes()==receipt
    backups=list(tmp_path.glob('db.backup-*'));assert len(backups)==1
    with sqlite3.connect(backups[0]) as db:
        assert db.execute('PRAGMA quick_check').fetchone()==('ok',)
        assert db.execute('PRAGMA user_version').fetchone()==(1,)
        assert db.execute('SELECT document FROM projects').fetchone()==(p.to_json(),)
    with ProjectStore(path) as store:assert store.load(p.id).origin_base is None


def test_owned_migration_fault_rolls_back_and_keeps_original(tmp_path,empty_plan):
    path=tmp_path/'db';p=model(empty_plan);old_database(path,p)
    def fault(point):
        if point=='after_schema_creation':raise OSError('migration interrupted')
    with pytest.raises(OSError):ProjectStore(path,fault=fault)
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()==(1,)
        assert len(db.execute('PRAGMA table_info(projects)').fetchall())==5
        assert db.execute('SELECT document FROM projects').fetchone()==(p.to_json(),)
    with ProjectStore(path) as store:assert store.load(p.id).project==p


def test_foreign_receipt_prevents_backup_or_migration(tmp_path,empty_plan):
    path=tmp_path/'db';old_database(path,model(empty_plan));receipt_path(path).write_bytes(b'foreign')
    before=path.read_bytes()
    with pytest.raises(StorageError):ProjectStore(path)
    assert path.read_bytes()==before and not list(tmp_path.glob('db.backup-*'))


def test_relative_origin_survives_moved_project_recovery(tmp_path,multi_plan):
    original=tmp_path/'original';original.mkdir();moved=tmp_path/'moved';moved.mkdir()
    p=model(multi_plan);path=original/'p.json';save_project_file(path,p)
    with ProjectStore(tmp_path/'db') as store:
        session=prepare_open(store,path).choose(store,'file')
        plan=p.plan.to_dict();plan['revision']+=1
        changed=Project(p.id,'edited',CompositionPlan.parse(plan))
        session.commit(CompletedCommand(changed,0))
        assert store.load(p.id).origin_base==str(original)
        shutil.copyfile(path,moved/'p.json')
        recovered=prepare_open(store,moved/'p.json').choose(store,'recovery')
        for key in ('assets','fonts'):
            for before,after in zip(changed.plan.to_dict()[key],recovered.project.plan.to_dict()[key]):
                assert after['path_ref']['path']==str(original/before['path_ref']['path'])
                assert after['path_ref']['base']=='absolute'
        assert 'origin_base' not in json.loads(changed.to_json())
        assert recovered.project.plan.render_content_digest('a'*64)==changed.plan.render_content_digest('a'*64)


def test_same_document_different_known_base_requires_choice(tmp_path,multi_plan):
    p=model(multi_plan);first=tmp_path/'first';second=tmp_path/'second';first.mkdir();second.mkdir()
    save_project_file(second/'p.json',p)
    with ProjectStore(tmp_path/'db') as store:
        store.save(p,origin_base=first)
        assert prepare_open(store,second/'p.json').differs


def test_legacy_relative_origin_remains_unknown(tmp_path,multi_plan):
    p=model(multi_plan);path=tmp_path/'p.json';save_project_file(path,p)
    old_database(tmp_path/'db',p)
    with ProjectStore(tmp_path/'db') as store:
        with pytest.raises(RelinkRequired):prepare_open(store,path).choose(store,'recovery')


@pytest.mark.parametrize('collection',['assets','fonts'])
def test_same_content_relink_preserves_render_and_source(tmp_path,multi_plan,collection):
    candidate=tmp_path/'media';candidate.write_bytes(b'exact fixture bytes')
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    item=multi_plan[collection][0];item['sha256']=item['path_ref']['asset_hash']=digest
    p=model(multi_plan);before=p.to_json()
    command=relink(p,collection,item['id'],candidate)
    assert command.expected_revision==0 and command.project.plan.to_dict()['revision']==1
    assert command.project.plan.to_dict()[collection][0]['path_ref']['path']==str(candidate)
    assert p.to_json()==before and candidate.read_bytes()==b'exact fixture bytes'
    assert p.plan.render_content_digest('a'*64)==command.project.plan.render_content_digest('a'*64)


def test_mismatch_cancel_and_unknown_id_leave_model_unchanged(tmp_path,multi_plan):
    candidate=tmp_path/'media';candidate.write_bytes(b'different bytes');p=model(multi_plan);before=p.to_json()
    with pytest.raises(RelinkMismatch):relink(p,'assets',multi_plan['assets'][0]['id'],candidate)
    with pytest.raises(ProbeCanceled):relink(p,'assets',multi_plan['assets'][0]['id'],candidate,cancel=lambda:True)
    with pytest.raises(StorageError):relink(p,'assets',str(uuid.uuid4()),candidate)
    assert p.to_json()==before and candidate.read_bytes()==b'different bytes'


def test_origin_validation_and_atomic_storage(tmp_path,empty_plan):
    p=model(empty_plan)
    with ProjectStore(tmp_path/'db') as store:
        with pytest.raises(StorageError):store.save(p,origin_base='relative')
        with pytest.raises(KeyError):store.load(p.id)
        store.save(p,origin_base=tmp_path)
    with ProjectStore(tmp_path/'db') as store:assert store.load(p.id).origin_base==str(tmp_path)


def test_verified_relink_commits_through_session_and_explicit_file_save(tmp_path,multi_plan):
    from fonesi_edit.storage.projects import load_project_file
    candidate=tmp_path/'relocated';candidate.write_bytes(b'owned synthetic source')
    item=multi_plan['assets'][0]
    item['sha256']=item['path_ref']['asset_hash']=hashlib.sha256(candidate.read_bytes()).hexdigest()
    p=model(multi_plan);path=tmp_path/'p.json';save_project_file(path,p)
    with ProjectStore(tmp_path/'db') as store:
        session=prepare_open(store,path).choose(store,'file')
        command=relink(session.project,'assets',item['id'],candidate)
        session.commit(command)
        assert store.load(p.id).project==command.project
        assert load_project_file(path)[0]==p # Autosave is not implicit file overwrite.
        session.save()
        assert load_project_file(path)[0]==command.project
        assert candidate.read_bytes()==b'owned synthetic source'


@pytest.mark.parametrize('bad',['/foreign/media','C:\\foreign\\media','C:relative','\\rooted','bad\x00name'])
def test_ambiguous_project_reference_cannot_discard_origin(tmp_path,multi_plan,bad):
    multi_plan['assets'][0]['path_ref']['path']=bad
    p=model(multi_plan);path=tmp_path/'p.json';save_project_file(path,p)
    with ProjectStore(tmp_path/'db') as store:
        store.save(p,origin_base=tmp_path)
        with pytest.raises(RelinkRequired,match='ambiguous'):
            prepare_open(store,path).choose(store,'recovery')
        assert store.load(p.id).project==p
