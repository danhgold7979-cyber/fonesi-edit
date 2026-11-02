"""Real project library command wired to Qt; synthetic probe is NOT codec acceptance."""
import json
import os
import sys
from pathlib import Path
import time
from hashlib import sha256

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from fonesi_edit.domain.media_library import MediaLibrary
from fonesi_edit.jobs.process import run_owned
from fonesi_edit.media.probe import ProbeResult
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore, save_project_file, load_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for
from fractions import Fraction


def _metadata():
    return {'streams':[{'index':0,'codec_type':'video','codec_name':'mpeg4',
        'time_base':'1/1000','start_pts':0,'duration_ts':1000,'width':64,'height':48,
        'sample_aspect_ratio':'1:1','disposition':{'attached_pic':0}}],
        'format':{'duration':'1'}}


def _owned_synthetic_probe(source, executable, *, cancel, _lifecycle):
    # The actual child proves process-owner lifecycle only; metadata is synthetic.
    result=_lifecycle.run(run_owned,[sys.executable,'-c','print("owned")'],
        cancel=cancel,timeout=5)
    assert result.returncode==0
    return ProbeResult(sha256(source.read_bytes()).hexdigest(),
        json.dumps(_metadata()),str(executable),())


def _opened(tmp_path):
    project=empty_project(NewProjectIntent('Import',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json'
    save_project_file(path,project)
    return project,path


def _panel(window,source):
    panel=window.media_import
    panel.source.setText(str(source))
    panel.tool.setText(str(Path(sys.executable).resolve()))
    panel.trust.setChecked(True)
    return panel


def test_real_qt_import_saves_v2_library_once_and_does_not_change_source(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.media_import as ui
    monkeypatch.setattr(ui,'inspect_media',_owned_synthetic_probe)
    source=tmp_path/'media 中文.bin'
    payload=b'local media fixture, synthetic metadata'
    source.write_bytes(payload)
    project,path=_opened(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store)
        window.show()
        try:
            window.open_project(path)
            panel=_panel(window,source)
            assert panel.add_button.isEnabled()
            panel.add_button.click()
            wait_for(qt_app,lambda:not panel.busy and window.session.revision==1)
            assert window.session.project.plan.to_dict()['assets']==[]
            assert window.session.project.library is not None
            assert len(window.session.project.library.items)==1
            entry=window.session.project.library.items[0]
            assert entry.sha256==sha256(payload).hexdigest()
            assert entry.path_ref.path==str(source)
            assert entry.observation_state=='OBSERVED' and not entry.observation.render_ready
            assert panel.table.rowCount()==1
            assert source.read_bytes()==payload
            window.save_current_project()
            saved,digest=load_project_file(path)
            assert saved==window.session.project and saved.library.items[0].id==entry.id
            panel.add_button.click()
            wait_for(qt_app,lambda:not panel.busy)
            assert window.session.revision==1 and len(window.session.project.library.items)==1
            assert 'không tạo bản sao' in panel.message.text()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()


def test_no_project_no_file_or_database_effect(tmp_path,qt_app):
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store)
        panel=_panel(window,tmp_path/'missing.bin')
        assert not panel.add_button.isEnabled()
        assert not panel.busy
        assert not (tmp_path/'jobs.sqlite3').exists()
        window.close()
        window.deleteLater()


def test_source_changes_after_probe_never_commit(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.media_import as ui
    source=tmp_path/'changing.bin';source.write_bytes(b'before')
    project,path=_opened(tmp_path)
    def altered(*args,**kwargs):
        result=_owned_synthetic_probe(*args,**kwargs)
        source.write_bytes(b'after')
        return result
    monkeypatch.setattr(ui,'inspect_media',altered)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store)
        window.show()
        try:
            window.open_project(path)
            panel=_panel(window,source)
            panel.add_button.click()
            wait_for(qt_app,lambda:not panel.busy)
            assert window.session.revision==0 and window.session.project.library is None
            assert not panel.revoked
            assert 'Không xác nhận' in panel.message.text()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()


def test_cancel_during_owned_probe_does_not_mutate_project(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.media_import as ui
    from fonesi_edit.jobs.process import ProcessCanceled
    from fonesi_edit.media.probe import ProbeCanceled
    import threading
    source=tmp_path/'cancel.bin';data=b'unchanged';source.write_bytes(data)
    project,path=_opened(tmp_path)
    started=threading.Event()
    def slow(source,exe,*,cancel,_lifecycle):
        started.set()
        try:_lifecycle.run(run_owned,[sys.executable,'-c','import time; time.sleep(8)'],
                           cancel=cancel,timeout=10)
        except ProcessCanceled as exc:raise ProbeCanceled('Canceled') from exc
        return _owned_synthetic_probe(source,exe,cancel=cancel,_lifecycle=_lifecycle)
    monkeypatch.setattr(ui,'inspect_media',slow)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store)
        window.show()
        try:
            window.open_project(path)
            panel=_panel(window,source)
            panel.add_button.click()
            wait_for(qt_app,lambda:started.is_set())
            panel.cancel_button.click()
            wait_for(qt_app,lambda:not panel.busy,timeout=10)
            assert window.session.revision==0
            assert window.session.project.library is None
            assert source.read_bytes()==data
            assert not panel.revoked
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater()


def test_close_with_import_active_waits_and_does_not_commit(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.media_import as ui
    import threading
    from fonesi_edit.jobs.process import ProcessCanceled
    from fonesi_edit.media.probe import ProbeCanceled
    source=tmp_path/'close.bin';source.write_bytes(b'fixture')
    project,path=_opened(tmp_path)
    started=threading.Event()
    def running(source,exe,*,cancel,_lifecycle):
        started.set()
        try:_lifecycle.run(run_owned,[sys.executable,'-c','import time; time.sleep(8)'],
                           cancel=cancel,timeout=10)
        except ProcessCanceled as exc:raise ProbeCanceled('Canceled') from exc
        return _owned_synthetic_probe(source,exe,cancel=cancel,_lifecycle=_lifecycle)
    monkeypatch.setattr(ui,'inspect_media',running)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store)
        window.show()
        window.open_project(path)
        panel=_panel(window,source)
        panel.add_button.click()
        wait_for(qt_app,lambda:started.is_set())
        window.close()
        wait_for(qt_app,lambda:not window.background_busy and not window.isVisible(),timeout=10)
        assert window.session.revision==0
        assert not panel.busy
        window.deleteLater()
