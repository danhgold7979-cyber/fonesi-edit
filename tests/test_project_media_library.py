from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
import pytest
from fonesi_edit.domain.media_library import MediaLibrary,MediaRecord,MediaPath
from fonesi_edit.storage.projects import Project,ProjectStore,StorageError,NewerSchemaError,save_project_file,load_project_file
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.media_commands import add_media
from fonesi_edit.storage.autosave import prepare_open,CompletedCommand,RelinkRequired
from fonesi_edit.storage.relink import relink,relink_root,RelinkMismatch
from test_media_library import record


def project():return empty_project(NewProjectIntent('Library',1920,1080,Fraction(30),Fraction(10)))


def test_v1_bytes_stable_v2_empty_not_downgraded_and_future_refused():
    old=project();text=old.to_json();assert Project.parse(text).to_json()==text
    assert json.loads(text)['schema_version']==1 and 'media_library' not in json.loads(text)
    upgraded=replace(old,library=MediaLibrary());raw=json.loads(upgraded.to_json())
    assert raw['schema_version']==2 and raw['media_library']['items']==[]
    assert Project.parse(upgraded.to_json())==upgraded
    raw['schema_version']=3
    with pytest.raises(NewerSchemaError):Project.parse(json.dumps(raw))
    raw=json.loads(text);raw['media_library']={'schema_version':1,'items':[]}
    with pytest.raises(StorageError):Project.parse(json.dumps(raw))


def test_library_command_cas_save_reopen_and_duplicate_noop(tmp_path):
    old=project();path=tmp_path/'project.json';save_project_file(path,old);item=record()
    with ProjectStore(tmp_path/'projects.db') as store:
        session=prepare_open(store,path).choose(store,'file');addition=add_media(old,item)
        assert addition.media_id==item.id and addition.command.expected_revision==0
        session.commit(addition.command);assert session.revision==1
        assert session.project.library.items==(item,)
        session.save();reopened=prepare_open(store,path).choose(store,'file')
        assert reopened.project==session.project
        duplicate=add_media(reopened.project,replace(item,id='12345678-1234-4234-8234-123456789abc'))
        assert duplicate.command is None and duplicate.media_id==item.id
        assert reopened.revision==1
        with pytest.raises(StorageError):session.commit(addition.command)


def test_composition_only_change_preserves_library(tmp_path):
    value=add_media(project(),record()).command.project
    plan=value.plan.to_dict();plan['revision']+=1
    from fonesi_edit.domain.composition import CompositionPlan
    changed=value.with_plan(CompositionPlan.parse(plan))
    assert changed.library==value.library and Project.parse(changed.to_json()).library==value.library


def test_library_only_relative_recovery_uses_original_base_and_saveas_guard(tmp_path):
    original=tmp_path/'original';moved=tmp_path/'moved';original.mkdir();moved.mkdir()
    old=project();file=original/'project.json';save_project_file(file,old)
    with ProjectStore(tmp_path/'projects.db') as store:
        session=prepare_open(store,file).choose(store,'file')
        session.commit(add_media(old,record('media.bin')).command)
        newfile=moved/'project.json';newfile.write_bytes(file.read_bytes())
        offer=prepare_open(store,newfile);assert offer.differs
        recovered=offer.choose(store,'recovery')
        item=recovered.project.library.items[0]
        assert item.path_ref.base=='absolute' and item.path_ref.path==str(original/'media.bin')
        assert recovered.project.plan.to_dict()['assets']==[]
        with pytest.raises(RelinkRequired):session.save(moved/'another.json')
        # Legacy unknown origin must not be guessed from the selected file folder.
        store.db.execute('UPDATE projects SET origin_base=NULL')
        with pytest.raises(RelinkRequired):prepare_open(store,newfile).choose(store,'recovery')


def test_single_and_root_library_relink_preserve_identity_facts_atomicity(tmp_path):
    old=tmp_path/'old';new=tmp_path/'new';old.mkdir();new.mkdir();(new/'media.bin').write_bytes(b'media')
    item=record('media.bin');value=add_media(project(),item).command.project
    result=relink(value,'media',item.id,new/'media.bin')
    assert result.project.library.items[0].id==item.id and result.project.library.items[0].observation==item.observation
    assert result.project.plan.to_dict()['revision']==value.plan.to_dict()['revision']+1
    mapped=relink_root(value,old,new,project_base=old).project
    assert mapped.library.items[0].path_ref.path==str(new/'media.bin')
    assert mapped.library.items[0].id==item.id and value.library.items[0].path_ref.base=='project'
    (new/'media.bin').write_bytes(b'OTHER')
    with pytest.raises(RelinkMismatch):relink_root(value,old,new,project_base=old)
    assert value.library.items==(item,)


def test_whole_envelope_limit_before_writer_and_streaming_v1_compatibility(tmp_path,monkeypatch):
    import fonesi_edit.storage.projects as module
    value=add_media(project(),record()).command.project
    monkeypatch.setattr(module,'MAX_PROJECT_BYTES',100)
    with pytest.raises(StorageError):value.to_json()
    # Validation precedes staging/target effects (the shared writer may mkdir parent).
    target=tmp_path/'limit.json'
    with pytest.raises(StorageError):save_project_file(target,value)
    assert not target.exists()


def test_streaming_limit_does_not_project_entire_large_library(tmp_path,monkeypatch):
    import fonesi_edit.storage.projects as module
    from hashlib import sha256
    import uuid
    items=[]
    for n in range(100):
        digest=sha256(str(n).encode()).hexdigest()
        items.append(MediaRecord(str(uuid.uuid4()),digest,n,MediaPath('project',f'{n}.bin',digest),'NOT_PROBED',None))
    value=replace(project(),library=MediaLibrary(tuple(items)))
    projected=[];original=MediaRecord.to_dict
    def tracked(self):projected.append(self.id);return original(self)
    monkeypatch.setattr(MediaRecord,'to_dict',tracked);monkeypatch.setattr(module,'MAX_PROJECT_BYTES',4000)
    with pytest.raises(StorageError):value.to_json()
    assert 0<len(projected)<len(items)


def test_backup_restore_preserves_v2_library_and_unknown_legacy_origin(tmp_path):
    import sqlite3
    from fonesi_edit.storage.projects import PROJECTS_V1_SQL,PROJECT_V1_HASH,APPLICATION_ID
    from fonesi_edit.storage.db_ownership import register_database
    from fonesi_edit.storage.restore import restore_project_backup
    value=add_media(project(),record()).command.project
    source=tmp_path/'v1.db'
    with sqlite3.connect(source) as db:
        db.execute(PROJECTS_V1_SQL);db.execute(f'PRAGMA application_id={APPLICATION_ID}');db.execute('PRAGMA user_version=1')
        db.execute('INSERT INTO projects VALUES(?,?,?,?,?)',(value.id,value.name,value.to_json(),7,1.0))
    register_database(source,APPLICATION_ID,PROJECT_V1_HASH)
    with ProjectStore(source) as store:assert store.load(value.id).project==value
    backups=list(tmp_path.glob('v1.db.backup-*'));assert len(backups)==1
    destination=tmp_path/'restored.db';restore_project_backup(backups[0],destination)
    with ProjectStore(destination) as restored:
        row=restored.load(value.id);assert row.project==value and row.version==7 and row.origin_base is None


@pytest.mark.parametrize('collection',['assets','fonts'])
def test_legacy_relink_preserves_v2_library(tmp_path,multi_plan,collection):
    from hashlib import sha256
    from fonesi_edit.domain.composition import CompositionPlan
    payload=b'legacy content';candidate=tmp_path/'legacy.bin';candidate.write_bytes(payload)
    entry=multi_plan[collection][0];entry['sha256']=entry['path_ref']['asset_hash']=sha256(payload).hexdigest()
    value=replace(project(),plan=CompositionPlan.parse(multi_plan),library=MediaLibrary((record(),)))
    updated=relink(value,collection,entry['id'],candidate).project
    assert updated.library==value.library and Project.parse(updated.to_json()).library==value.library


def test_mixed_root_relink_preserves_all_ids_and_updates_once(tmp_path,multi_plan):
    from hashlib import sha256
    from fonesi_edit.domain.composition import CompositionPlan
    old=tmp_path/'old';new=tmp_path/'new';old.mkdir();new.mkdir()
    for collection in ('assets','fonts'):
        for index,entry in enumerate(multi_plan[collection]):
            data=f'{collection}-{index}'.encode();name=f'{collection}-{index}.bin';(new/name).write_bytes(data)
            entry['sha256']=entry['path_ref']['asset_hash']=sha256(data).hexdigest()
            entry['path_ref'].update(base='project',path=name)
    (new/'media.bin').write_bytes(b'media');item=record()
    value=replace(project(),plan=CompositionPlan.parse(multi_plan),library=MediaLibrary((item,)))
    updated=relink_root(value,old,new,project_base=old).project
    for collection in ('assets','fonts'):
        before=value.plan.to_dict()[collection];after=updated.plan.to_dict()[collection]
        assert [x['id'] for x in before]==[x['id'] for x in after]
        assert all(x['path_ref']['base']=='absolute' for x in after)
    assert updated.library.items[0].id==item.id and updated.library.items[0].observation==item.observation
    assert updated.plan.to_dict()['revision']==value.plan.to_dict()['revision']+1


def test_v2_downgrade_refused_at_session_database_and_file_boundaries(tmp_path):
    from fonesi_edit.domain.composition import CompositionPlan
    from fonesi_edit.storage.projects import ConflictError
    value=add_media(project(),record()).command.project;path=tmp_path/'p.json';digest=save_project_file(path,value)
    with ProjectStore(tmp_path/'db') as store:
        store.save(value,origin_base=tmp_path)
        session=prepare_open(store,path).choose(store,'file')
        plan=value.plan.to_dict();plan['revision']+=1;plan['provenance']['project_revision']=plan['revision']
        downgraded=Project(value.id,value.name,CompositionPlan.parse(plan))
        before=store.load(value.id)
        with pytest.raises(ConflictError):session.commit(CompletedCommand(downgraded,session.revision))
        assert session.project==value and not session.reconciliation_required and store.load(value.id)==before
        with pytest.raises(ConflictError):store.save(downgraded,expected_version=before.version)
        assert store.load(value.id)==before
        with pytest.raises(ConflictError):save_project_file(path,downgraded,expected_digest=digest)
        assert load_project_file(path)==(value,digest) and not list(tmp_path.glob('p.json.backup-*'))
        # Explicit last-item removal retains the v2 discriminator.
        empty=replace(downgraded,library=MediaLibrary())
        session.commit(CompletedCommand(empty,session.revision));session.save()
        assert Project.parse(path.read_bytes()).library==MediaLibrary()
