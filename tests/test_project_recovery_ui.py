"""Real widgets; no renderer, provider or synthetic queue progress."""
import uuid
import pytest
from PySide6.QtWidgets import QMessageBox
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.projects import Project, ProjectStore, save_project_file, load_project_file
from fonesi_edit.storage.autosave import RelinkRequired
from fonesi_edit.ui.shell import MainWindow


def project(plan, name='disk', project_id=None):
    return Project(project_id or str(uuid.uuid4()), name, CompositionPlan.parse(plan))


def test_recovery_cancel_preserves_model_and_file_choice_is_explicit(qt_app,tmp_path,empty_plan,monkeypatch):
    with ProjectStore(tmp_path/'db') as store:
        first=project(empty_plan,'first'); first_path=tmp_path/'first.json';save_project_file(first_path,first)
        disk=project(empty_plan);path=tmp_path/'disk.json';save_project_file(path,disk)
        local=Project(disk.id,'local',disk.plan);store.save(local)
        window=MainWindow(store);window.open_project(first_path);old_session=window.session
        monkeypatch.setattr(window,'_choose_recovery',lambda:'cancel')
        assert window.open_project(path) is None
        assert window.project==first and window.session is old_session
        assert load_project_file(path)[0]==disk and store.load(disk.id).project==local
        monkeypatch.setattr(window,'_choose_recovery',lambda:'file')
        assert window.open_project(path)==disk
        assert window.session is not old_session
        window.close()


def test_recovery_save_updates_file_and_keeps_backup(qt_app,tmp_path,empty_plan,monkeypatch):
    with ProjectStore(tmp_path/'db') as store:
        disk=project(empty_plan);path=tmp_path/'disk.json';save_project_file(path,disk)
        local=Project(disk.id,'recovered',disk.plan);store.save(local)
        window=MainWindow(store)
        monkeypatch.setattr(window,'_choose_recovery',lambda:'recovery')
        assert window.open_project(path)==local
        assert load_project_file(path)[0]==disk
        window.save_button.click()
        assert load_project_file(path)[0]==local
        backups=list(tmp_path.glob('disk.json.backup-*'))
        assert len(backups)==1 and load_project_file(backups[0])[0]==disk
        window.close()


def test_stale_save_preserves_foreign_change_and_current_model(qt_app,tmp_path,empty_plan,monkeypatch):
    with ProjectStore(tmp_path/'db') as store:
        disk=project(empty_plan);path=tmp_path/'disk.json';digest=save_project_file(path,disk)
        window=MainWindow(store);window.open_project(path)
        changed=Project(disk.id,'other writer',disk.plan)
        save_project_file(path,changed,expected_digest=digest)
        notices=[];monkeypatch.setattr(QMessageBox,'warning',lambda *args:notices.append(args))
        window.save_button.click()
        assert notices and window.project==disk and load_project_file(path)[0]==changed
        window.close()


def test_relative_recovery_refusal_preserves_previous_model(qt_app,tmp_path,empty_plan,multi_plan):
    with ProjectStore(tmp_path/'db') as store:
        previous=project(empty_plan);prior=tmp_path/'prior.json';save_project_file(prior,previous)
        disk=project(multi_plan);path=tmp_path/'relative.json';save_project_file(path,disk)
        store.save(Project(disk.id,'local relative',disk.plan))
        window=MainWindow(store);window.open_project(prior)
        with pytest.raises(RelinkRequired):window.open_project(path,recovery_choice='recovery')
        assert window.project==previous
        window.close()


def test_unknown_save_disables_retry_and_preserves_model(qt_app,tmp_path,empty_plan,monkeypatch):
    import fonesi_edit.storage.autosave as autosave
    with ProjectStore(tmp_path/'db') as store:
        disk=project(empty_plan);path=tmp_path/'disk.json';save_project_file(path,disk)
        window=MainWindow(store);window.open_project(path)
        calls=[]
        def fail(*args,**kwargs):calls.append(1);raise OSError('uncertain')
        monkeypatch.setattr(autosave,'save_project_file',fail)
        monkeypatch.setattr(QMessageBox,'warning',lambda *args:None)
        window.save_button.click();window.save_button.click()
        assert calls==[1] and window.project==disk and not window.save_button.isEnabled()
        assert not window.relink_panel.button.isEnabled()
        window.close()
