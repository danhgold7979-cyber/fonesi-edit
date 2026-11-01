import threading
import time
from PySide6.QtCore import QTimer
from fonesi_edit.ui.shell import MainWindow
from fonesi_edit.ui import project_creation as ui
from fonesi_edit.storage.projects import ProjectStore,load_project_file
from fonesi_edit.storage.project_creation import CreationUnknown


def spin(app,predicate):
    end=time.monotonic()+6
    while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.005)
    assert predicate();app.processEvents()


def test_actual_new_project_worker_activates_existing_save_session(qt_app,tmp_path):
    with ProjectStore(tmp_path/'projects.db') as store:
        window=MainWindow(store);panel=window.new_project_panel;window.new_button.click()
        assert window.new_project_dialog.isVisible()
        panel.path.setText(str(tmp_path/'Mới.json'));panel.name.setText('Dự án của tôi')
        panel.fps_num.setValue(30000);panel.fps_den.setValue(1001);panel.button.click()
        spin(qt_app,lambda:not panel.busy)
        assert window.session is not None and window.project.name=='Dự án của tôi'
        assert window.project.plan.to_dict()['output']['fps']==[30000,1001]
        assert window.project.plan.to_dict()['assets']==[]
        assert load_project_file(tmp_path/'Mới.json')[0]==window.project
        window.save_current_project();assert 'Đã lưu' in window.statusBar().currentMessage()
        window.new_project_dialog.close();window.close()


def test_dialog_close_after_creation_preserves_file_without_activation(qt_app,tmp_path,monkeypatch):
    entered=threading.Event();release=threading.Event();real=ui.create_project_file
    def held(*a,**kw):
        result=real(*a,**kw);entered.set();release.wait(4);return result
    monkeypatch.setattr(ui,'create_project_file',held)
    with ProjectStore(tmp_path/'projects.db') as store:
        window=MainWindow(store);panel=window.new_project_panel;window.new_button.click()
        panel.path.setText(str(tmp_path/'created.json'));panel.start();spin(qt_app,entered.is_set)
        pulses=[];timer=QTimer();timer.timeout.connect(lambda:pulses.append(1));timer.start(2)
        window.new_project_dialog.close();assert panel.busy and panel.worker.isInterruptionRequested()
        release.set();spin(qt_app,lambda:not panel.busy);timer.stop()
        assert window.session is None and (tmp_path/'created.json').exists()
        assert not window.new_project_dialog.isVisible() and pulses
        window.new_button.click();assert window.new_project_dialog.isVisible() and panel.button.isEnabled()
        window.close()


def test_changed_session_preserved_and_unknown_blocks_repeated_create(qt_app,tmp_path,monkeypatch):
    entered=threading.Event();release=threading.Event();real=ui.create_project_file
    def held(*a,**kw):
        result=real(*a,**kw);entered.set();release.wait(4);return result
    monkeypatch.setattr(ui,'create_project_file',held)
    with ProjectStore(tmp_path/'projects.db') as store:
        window=MainWindow(store);panel=window.new_project_panel;panel.path.setText(str(tmp_path/'new.json'))
        panel.start();spin(qt_app,entered.is_set)
        class Other:
            revision=9
        other=Other();window.session=other
        release.set();spin(qt_app,lambda:not panel.busy)
        assert window.session is other and (tmp_path/'new.json').exists()
        window.session=None
        calls=[]
        def unknown(*a,**kw):calls.append(1);raise CreationUnknown('private path secret')
        monkeypatch.setattr(ui,'create_project_file',unknown);panel.path.setText(str(tmp_path/'unknown.json'));panel.start()
        spin(qt_app,lambda:not panel.busy)
        assert panel.uncertain and not panel.button.isEnabled() and 'secret' not in panel.message.text()
        panel.start();assert calls==[1];window.close()


def test_picker_cancel_and_existing_foreign_target_preserved(qt_app,tmp_path,monkeypatch):
    with ProjectStore(tmp_path/'projects.db') as store:
        window=MainWindow(store);panel=window.new_project_panel
        monkeypatch.setattr(ui.QFileDialog,'getSaveFileName',lambda *a,**kw:('',''))
        before=set(tmp_path.iterdir());panel.choose_path();assert set(tmp_path.iterdir())==before and panel.path.text()==''
        foreign=tmp_path/'foreign.json';foreign.write_bytes(b'FOREIGN');panel.path.setText(str(foreign));panel.start()
        spin(qt_app,lambda:not panel.busy)
        assert foreign.read_bytes()==b'FOREIGN' and window.session is None and not panel.uncertain
        window.close()


def test_nul_destination_does_not_start_worker_or_lock_creation(qt_app,tmp_path,monkeypatch):
    monkeypatch.setattr(ui,'CreationWorker',lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Worker reached invalid path')))
    with ProjectStore(tmp_path/'projects.db') as store:
        window=MainWindow(store);panel=window.new_project_panel
        panel.path.setText(str(tmp_path/'bad')+'\0.json');panel.start()
        assert not panel.busy and not panel.uncertain and panel.button.isEnabled()
        assert 'Chưa ghi' in panel.message.text();window.close()
