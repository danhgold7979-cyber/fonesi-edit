import threading,time
from pathlib import Path
from PySide6.QtCore import QTimer
from fonesi_edit.ui import project_restore as ui
from fonesi_edit.ui.shell import MainWindow
from fonesi_edit.storage.projects import ProjectStore
from fonesi_edit.storage.restore import RestoreResult,RestoreError
from test_project_backup_restore import migration_backup


def spin(app,predicate,seconds=5):
    end=time.monotonic()+seconds
    while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.005)
    assert predicate()
    app.processEvents()


def test_real_restore_worker_keeps_gui_and_active_store_unchanged(qt_app,migration_backup,tmp_path):
    original,backup,projects=migration_backup;before=(original.read_bytes(),backup.read_bytes())
    folder=tmp_path/'new';folder.mkdir();target=folder/'projects.sqlite3'
    with ProjectStore(original) as store:
        window=MainWindow(store);window.show();panel=window.restore_panel
        owner=threading.get_ident();pulses=[];timer=QTimer();timer.timeout.connect(lambda:pulses.append(threading.get_ident()));timer.start(1)
        panel.start(backup,target);worker=panel.worker
        assert panel.busy and not panel.button.isEnabled()
        spin(qt_app,lambda:not panel.busy);timer.stop()
        assert worker.outcome=='CONFIRMED' and '2 dự án' in panel.message.text()
        assert pulses and all(x==owner for x in pulses)
        assert window.store is store and window.session is None
        assert store.load(projects[0].id).project.name=='Newer active state'
        window.close()
    assert (original.read_bytes(),backup.read_bytes())==before
    with ProjectStore(target) as restored:assert restored.load(projects[0].id).version==3


def test_cancel_close_waits_worker_and_retains_unknown_notice(qt_app,tmp_path,monkeypatch):
    entered=threading.Event();released=threading.Event();calls=[]
    def restore(source,destination,*,cancel,progress):
        calls.append(1);entered.set()
        while not cancel():time.sleep(.005)
        released.wait(3)
        raise RestoreError('PRIVATE',destination_created=True,ownership_unknown=True)
    monkeypatch.setattr(ui,'restore_project_backup',restore)
    with ProjectStore(tmp_path/'active.db') as store:
        window=MainWindow(store);window.show();panel=window.restore_panel
        panel.start(tmp_path/'backup',tmp_path/'new.db');spin(qt_app,entered.is_set)
        window.close();assert window.background_busy and not panel.button.isEnabled()
        qt_app.processEvents();assert panel.worker is not None
        released.set();spin(qt_app,lambda:not window.background_busy)
        assert len(calls)==1 and 'không tự thử lại hoặc xóa' in panel.message.text()
        assert 'PRIVATE' not in panel.message.text()
        window.close()


def test_late_cancel_cannot_erase_confirmed_new_store(qt_app,tmp_path,monkeypatch):
    entered=threading.Event();release=threading.Event()
    def restore(source,destination,**kwargs):
        entered.set();release.wait(3)
        return RestoreResult(Path(destination),1,2,'a'*64,100)
    monkeypatch.setattr(ui,'restore_project_backup',restore)
    panel=ui.RestorePanel();panel.start(tmp_path/'a',tmp_path/'b');spin(qt_app,entered.is_set)
    panel.cancel();release.set();spin(qt_app,lambda:not panel.busy)
    assert 'Đã xác nhận kho mới' in panel.message.text()
    panel.close()


def test_old_worker_progress_and_completion_cannot_retarget(qt_app,tmp_path):
    panel=ui.RestorePanel();old=ui.RestoreWorker(tmp_path/'a',tmp_path/'b',panel)
    panel.message.setText('current');panel._copied(old,(100,100));panel._finished(old)
    assert panel.message.text()=='current' and panel.worker is None
    old.deleteLater();panel.close()
