"""Actual Qt/read-only sentinel discovery; no executable is launched."""
import os
import threading
import time
from PySide6.QtCore import QTimer
from fonesi_edit.ui import tool_inventory as ui
from fonesi_edit.ui.shell import MainWindow
from fonesi_edit.storage.projects import ProjectStore


def spin(app,predicate,seconds=6):
    end=time.monotonic()+seconds
    while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.005)
    assert predicate();app.processEvents()


def text(panel,row,column):return panel.table.item(row,column).text()


def test_settings_opens_without_tools_then_first_open_scans_once_missing_not_ready(qt_app,tmp_path,monkeypatch):
    calls=[];real=ui.discover_tools
    def scan(**kwargs):calls.append(threading.get_ident());return real(**kwargs)
    monkeypatch.setattr(ui,'discover_tools',scan);monkeypatch.setattr(ui,'system_search_dirs',lambda:())
    with ProjectStore(tmp_path/'active.db') as store:
        window=MainWindow(store);panel=window.tool_inventory
        assert calls==[] and not panel.busy # constructing app is not blocked by tools/preferences
        window.navigation.setCurrentRow(7)
        assert window.pages.currentIndex()==7 and panel.first_open_attempted
        spin(qt_app,lambda:bool(calls) and not panel.busy)
        assert len(calls)==1 and calls[0]!=threading.get_ident()
        assert all('Chưa thấy' in text(panel,r,6) for r in range(5))
        assert all(text(panel,r,4)=='Chưa biết' for r in range(5))
        window.navigation.setCurrentRow(0);window.navigation.setCurrentRow(7);qt_app.processEvents()
        assert len(calls)==1 and not (tmp_path/'tool-preferences.sqlite3').exists()
        assert 'COMPLETE' in panel.message.text() and window.store is store
        window.close()


def test_actual_unicode_candidate_and_invalid_explicit_no_fallback_read_only(qt_app,tmp_path):
    root=tmp_path/'Công cụ';root.mkdir()
    candidate=root/('ffmpeg.exe' if os.name=='nt' else 'ffmpeg');candidate.write_bytes(b'not an executable')
    alternative=root/('ffprobe.exe' if os.name=='nt' else 'ffprobe');alternative.write_bytes(b'also not executed')
    before={p.name:p.read_bytes() for p in root.iterdir()}
    panel=ui.ToolInventoryPanel();panel.system.setChecked(False);panel.extra.setText(str(root))
    panel.paths['ffprobe'].setText(str(root/'explicit-missing'))
    panel.start();spin(qt_app,lambda:not panel.busy)
    assert text(panel,0,2)==str(candidate) and 'CHƯA xác minh' in text(panel,0,6)
    assert text(panel,1,2)=='—' and 'KHÔNG thay thế' in text(panel,1,6)
    assert str(alternative) in panel.candidates.toPlainText() and 'UNCHECKED' in panel.candidates.toPlainText()
    assert {p.name:p.read_bytes() for p in root.iterdir()}==before
    panel.close()


def test_close_cancels_scan_and_waits_owned_worker_without_blocking_gui(qt_app,tmp_path,monkeypatch):
    entered=threading.Event();release=threading.Event();real=ui.discover_tools
    def held(**kwargs):
        entered.set()
        while not kwargs['cancel']():time.sleep(.005)
        release.wait(3)
        return real(**kwargs)
    monkeypatch.setattr(ui,'discover_tools',held)
    with ProjectStore(tmp_path/'active.db') as store:
        window=MainWindow(store);window.show();panel=window.tool_inventory;panel.system.setChecked(False)
        panel.paths['ffmpeg'].setText(str(tmp_path/'queued-candidate'))
        pulses=[];timer=QTimer();timer.timeout.connect(lambda:pulses.append(1));timer.start(2)
        panel.start();spin(qt_app,entered.is_set);window.close()
        assert window.background_busy and panel.stopping and not panel.scan_button.isEnabled()
        release.set();spin(qt_app,lambda:not window.background_busy);timer.stop()
        assert pulses and 'PARTIAL_CANCELED' in panel.message.text()
        assert all('Chưa kiểm tra' in text(panel,r,6) for r in range(5))
        window.close()


def test_programmatic_input_change_cannot_display_old_capture(qt_app,tmp_path,monkeypatch):
    entered=threading.Event();release=threading.Event();real=ui.discover_tools
    def held(**kwargs):entered.set();release.wait(3);return real(**kwargs)
    monkeypatch.setattr(ui,'discover_tools',held)
    panel=ui.ToolInventoryPanel();panel.system.setChecked(False);panel.start();spin(qt_app,entered.is_set)
    panel.paths['ffmpeg'].setText(str(tmp_path/'new'));release.set();spin(qt_app,lambda:not panel.busy)
    assert 'bỏ kết quả cũ' in panel.message.text() and not panel.candidates.toPlainText()
    assert all('Chưa kiểm tra' in text(panel,r,6) for r in range(5))
    panel.close()


def test_read_failure_does_not_leak_exception_or_prevent_settings_retry(qt_app,monkeypatch):
    def bad(**kwargs):raise OSError('PRIVATE secret raw path')
    monkeypatch.setattr(ui,'discover_tools',bad)
    panel=ui.ToolInventoryPanel();panel.system.setChecked(False);panel.start();spin(qt_app,lambda:not panel.busy)
    assert 'PRIVATE' not in panel.message.text() and 'Không hoàn tất' in panel.message.text()
    assert panel.scan_button.isEnabled() and not panel.candidates.toPlainText()
    panel.close()


def test_relative_extra_scope_refused_and_stale_worker_ignored(qt_app):
    panel=ui.ToolInventoryPanel();panel.extra.setText('relative');panel.start()
    assert panel.worker is None and 'phải tuyệt đối' in panel.message.text()
    before=panel.message.text();old=ui.InventoryWorker({},'',False,panel)
    panel._finished(old,0)
    assert panel.message.text()==before
    old.deleteLater();panel.close()


def test_candidate_display_is_bounded_without_truncating_selected_path(qt_app):
    from fonesi_edit.dependencies.discovery import Candidate,Discovery,Selection
    panel=ui.ToolInventoryPanel();worker=ui.InventoryWorker({},'',False,panel)
    candidates=tuple(Candidate('ffmpeg','/'+'x'*600+str(i),'extra',1,i,1,0,False) for i in range(256))
    selections=tuple(Selection(tool,'NEEDS_CHECK',candidates[0]) if tool=='ffmpeg'
        else Selection(tool,'MISSING',None) for tool in ui.TOOL_NAMES)
    worker.result=Discovery('COMPLETE',256,candidates,selections,());worker.observed_at='test observation'
    panel.worker=worker;panel._finished(worker,panel.revision)
    output=panel.candidates.toPlainText()
    assert len(output.splitlines())==65 and len(output)<40000
    assert text(panel,0,2)==candidates[0].path and '…' in output
    panel.close()

def test_f5_rescans_metadata_only_from_tool_table_and_rebinds_live(qt_app,tmp_path,monkeypatch):
    from PySide6.QtCore import Qt,QSettings
    from PySide6.QtTest import QTest
    from fonesi_edit.ui.shortcuts import ShortcutRegistry
    calls=[];real=ui.discover_tools
    def scan(**kwargs):
        calls.append(threading.get_ident())
        return real(**kwargs)
    monkeypatch.setattr(ui,'discover_tools',scan)
    monkeypatch.setattr(ui,'system_search_dirs',lambda:())
    registry=ShortcutRegistry(settings=QSettings(str(tmp_path/'shortcuts.ini'),QSettings.Format.IniFormat))
    panel=ui.ToolInventoryPanel(shortcut_registry=registry)
    panel.system.setChecked(False);panel.show()
    try:
        panel.table.setFocus()
        QTest.keyClick(panel.table,Qt.Key.Key_F5)
        spin(qt_app,lambda:not panel.busy)
        assert len(calls)==1 and calls[0]!=threading.get_ident()
        registry.set_sequence('tools.rescan','Ctrl+Alt+R')
        QTest.keyClick(panel.table,Qt.Key.Key_F5)
        qt_app.processEvents()
        assert len(calls)==1
        QTest.keyClick(panel.table,Qt.Key.Key_R,Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.AltModifier)
        spin(qt_app,lambda:not panel.busy and len(calls)==2)
        assert calls[1]!=threading.get_ident()
        assert 'không chạy' in panel.message.text().lower() or 'COMPLETE' in panel.message.text()
    finally:
        panel.close();panel.deleteLater()
