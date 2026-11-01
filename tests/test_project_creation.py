from fractions import Fraction
import pytest
from fonesi_edit.storage.project_creation import (NewProjectIntent,empty_project,create_project_file,
    CreationCanceled,CreationUnknown)
from fonesi_edit.storage.projects import Project,ProjectStore,ConflictError,load_project_file
from fonesi_edit.storage.autosave import prepare_open,CompletedCommand
from fonesi_edit.domain.composition import CompositionPlan


def intent():return NewProjectIntent('Dự án trắng',1920,1080,Fraction(30000,1001),Fraction(10))


def test_empty_project_real_roundtrip_existing_session_save(tmp_path):
    project=empty_project(intent());other=empty_project(intent());assert project.id!=other.id
    plan=project.plan.to_dict();assert plan['provenance']['project_id']==project.id
    assert plan['assets']==plan['clips']==plan['layers']==plan['fonts']==plan['audio']['clips']==[]
    assert plan['output']['fps']==[30000,1001]
    created=create_project_file(tmp_path/'Công việc.json',project)
    with ProjectStore(tmp_path/'projects.db') as store:
        session=prepare_open(store,created.path).choose(store,'file')
        assert session.project==project and session.revision==0
        plan['revision']=1;plan['provenance']['project_revision']=1
        edited=Project(project.id,'Tên mới',CompositionPlan.parse(plan))
        session.commit(CompletedCommand(edited,0));session.save()
        assert load_project_file(created.path)[0]==edited


def test_existing_target_never_overwritten_and_cancel_before_writer(tmp_path):
    project=empty_project(intent());path=tmp_path/'foreign.json';path.write_bytes(b'FOREIGN')
    with pytest.raises(ConflictError):create_project_file(path,project)
    assert path.read_bytes()==b'FOREIGN'
    fresh=tmp_path/'new.json'
    with pytest.raises(CreationCanceled):create_project_file(fresh,project,cancel=lambda:True)
    assert not fresh.exists() and not (tmp_path/'new.json.lock').exists()


def test_cancel_after_publish_preserves_confirmed_file_and_unknown_never_replays(tmp_path):
    project=empty_project(intent());canceled=[False];path=tmp_path/'created.json'
    def cancel_after(stage):
        if stage=='after_publish':canceled[0]=True
    result=create_project_file(path,project,cancel=lambda:canceled[0],fault=cancel_after)
    assert canceled[0] and result.project==load_project_file(path)[0]
    second=tmp_path/'unknown.json'
    def fail(stage):
        if stage=='after_publish':raise PermissionError('uncertain after effect')
    with pytest.raises(CreationUnknown):create_project_file(second,project,fault=fail)
    assert load_project_file(second)[0]==project
    with pytest.raises(ConflictError):create_project_file(second,project)


@pytest.mark.parametrize('change',[{'name':''},{'width':1919},{'height':0},{'fps':0},{'duration':Fraction(-1)}])
def test_invalid_initial_intent_has_no_files(tmp_path,change):
    values=dict(name='Project',width=1920,height=1080,fps=Fraction(30),duration=Fraction(10));values.update(change)
    with pytest.raises(ValueError):NewProjectIntent(**values)
    assert not list(tmp_path.iterdir())


def test_nul_destination_refused_before_writer(tmp_path,monkeypatch):
    import fonesi_edit.storage.project_creation as module
    monkeypatch.setattr(module,'save_project_file',lambda *a,**kw:pytest.fail('Writer reached invalid NUL path'))
    with pytest.raises(ValueError):create_project_file(str(tmp_path/'invalid')+'\0.json',empty_project(intent()))
    assert not list(tmp_path.iterdir())
