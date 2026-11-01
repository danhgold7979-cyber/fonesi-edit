from pathlib import Path
from hashlib import sha256
import time
import uuid
import pytest
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.projects import Project,ProjectStore,save_project_file,load_project_file,StorageError
from fonesi_edit.storage.relink import relink_root,RelinkMismatch
from fonesi_edit.media.probe import ProbeCanceled
from fonesi_edit.ui.shell import MainWindow


@pytest.fixture
def relocated(tmp_path,multi_plan):
    old=tmp_path/'old';old.mkdir();new=tmp_path/'new';new.mkdir()
    for collection in ('assets','fonts'):
        for i,item in enumerate(multi_plan[collection]):
            data=f'{collection}-{i}-same-content'.encode()
            item['sha256']=item['path_ref']['asset_hash']=sha256(data).hexdigest()
            candidate=new/item['path_ref']['path'];candidate.parent.mkdir(parents=True,exist_ok=True);candidate.write_bytes(data)
    project=Project(str(uuid.uuid4()),'relocate',CompositionPlan.parse(multi_plan))
    path=old/'p.json';save_project_file(path,project)
    return project,path,old,new


def wait(app,predicate):
    deadline=time.monotonic()+5
    while predicate() and time.monotonic()<deadline:app.processEvents();time.sleep(.005)
    assert not predicate()
    app.processEvents()


def test_complete_root_mapping_preserves_semantics_and_reports_actual_count(relocated):
    p,path,old,new=relocated;observations=[]
    command=relink_root(p,old,new,project_base=old,progress=lambda *x:observations.append(x))
    assert observations==[(0,2),(1,2),(2,2)]
    assert command.expected_revision==0 and command.project.plan.to_dict()['revision']==1
    assert command.project.plan.render_content_digest('a'*64)==p.plan.render_content_digest('a'*64)
    for group in ('assets','fonts'):
        assert command.project.plan.to_dict()[group][0]['path_ref']['path'].startswith(str(new))
    assert load_project_file(path)[0]==p


def test_root_mapping_is_all_or_nothing_on_late_mismatch_and_cancel(relocated):
    p,path,old,new=relocated;before=p.to_json()
    font=new/p.plan.to_dict()['fonts'][0]['path_ref']['path'];font.write_bytes(b'different')
    with pytest.raises(RelinkMismatch):relink_root(p,old,new,project_base=old)
    with pytest.raises(ProbeCanceled):relink_root(p,old,new,project_base=old,cancel=lambda:True)
    assert p.to_json()==before and load_project_file(path)[0]==p and font.read_bytes()==b'different'


def test_original_media_subroot_is_not_project_relative_base(relocated):
    p,path,old,new=relocated
    command=relink_root(p,old/'fixtures',new/'fixtures',project_base=old)
    assert command.project.plan.to_dict()['assets'][0]['path_ref']['path']==str(new/'fixtures'/'multi-stream.mkv')
    with pytest.raises(RelinkMismatch):relink_root(p,old/'unrelated',new,project_base=old)


def test_actual_window_root_relink_autosaves_then_explicit_save(qt_app,tmp_path,relocated):
    p,path,old,new=relocated
    with ProjectStore(tmp_path/'db') as store:
        window=MainWindow(store);window.open_project(path)
        window.relink_panel.start(str(old),str(new))
        assert not window.open_button.isEnabled() and not window.save_button.isEnabled()
        wait(qt_app,lambda:window.background_busy)
        assert window.project.plan.to_dict()['revision']==1
        assert store.load(p.id).project==window.project
        assert load_project_file(path)[0]==p
        window.save_button.click();assert load_project_file(path)[0]==window.project
        window.close()


@pytest.mark.parametrize('closing',[False,True])
def test_cancel_or_close_during_hash_never_commits_late_result(qt_app,tmp_path,relocated,monkeypatch,closing):
    import threading
    import fonesi_edit.ui.project_relink as ui
    p,path,old,new=relocated
    command=relink_root(p,old,new,project_base=old);entered=threading.Event()
    def delayed(*args,**kwargs):
        entered.set()
        while not kwargs['cancel']():time.sleep(.005)
        return command # Simulate already-completed verification racing cancellation.
    monkeypatch.setattr(ui,'relink_root',delayed)
    with ProjectStore(tmp_path/'db') as store:
        window=MainWindow(store);window.open_project(path);window.show()
        window.relink_panel.start(str(old),str(new));assert entered.wait(3)
        if closing:window.close()
        else:window.relink_panel.cancel()
        wait(qt_app,lambda:window.background_busy)
        assert window.project==p and load_project_file(path)[0]==p
        with pytest.raises(KeyError):store.load(p.id)
        window.close()


def test_stale_session_completion_never_retargets(qt_app,tmp_path,relocated,monkeypatch):
    import threading
    import fonesi_edit.ui.project_relink as ui
    from fonesi_edit.storage.autosave import prepare_open
    p,path,old,new=relocated
    command=relink_root(p,old,new,project_base=old);entered=threading.Event();release=threading.Event()
    def delayed(*args,**kwargs):entered.set();assert release.wait(3);return command
    monkeypatch.setattr(ui,'relink_root',delayed)
    with ProjectStore(tmp_path/'db') as store:
        window=MainWindow(store);window.open_project(path)
        window.relink_panel.start(str(old),str(new));assert entered.wait(3)
        with pytest.raises(StorageError):window.open_project(path)
        window.session=prepare_open(store,path).choose(store,'file') # An external owner changes session.
        release.set();wait(qt_app,lambda:window.background_busy)
        assert window.project==p
        with pytest.raises(KeyError):store.load(p.id)
        window.close()
