import threading
import time
from PySide6.QtCore import QCoreApplication,QEvent
from fonesi_edit.ui import tool_preferences as io
from fonesi_edit.ui.tool_inventory import ToolInventoryPanel
from fonesi_edit.dependencies.preferences import load_preferences, save_preferences, ToolPreferences, PreferencesUnknown


def spin(app,predicate):
    end=time.monotonic()+6
    while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.005)
    assert predicate();app.processEvents()




def dispose_panel(panel):
    # The preference worker is finished before callers dispose the widget.
    # Flush this panel's deferred QObject deletion now instead of leaking a
    # closed top-level QWidget into the next test's QApplication event loop.
    if panel.busy:
        raise AssertionError('Cannot dispose a tool panel while its worker is active')
    panel.close()
    panel.deleteLater()
    QCoreApplication.sendPostedEvents(panel,QEvent.Type.DeferredDelete)


def test_explicit_load_save_reopen_no_scan_trust_or_tool_execution(qt_app,tmp_path,monkeypatch):
    import fonesi_edit.ui.tool_inventory as ui
    monkeypatch.setattr(ui,'discover_tools',lambda **kw:(_ for _ in ()).throw(AssertionError('No auto scan')))
    path=tmp_path/'tools.db';panel=ToolInventoryPanel(preferences_path=path)
    assert not path.exists() and not panel.save_button.isEnabled()
    threads=[];real=io.load_preferences
    def load(*a,**kw):threads.append(threading.get_ident());return real(*a,**kw)
    monkeypatch.setattr(io,'load_preferences',load)
    panel.load_saved();spin(qt_app,lambda:not panel.busy)
    assert not path.exists() and panel.save_button.isEnabled()
    selected=str(tmp_path/'Công cụ'/'missing.exe');panel.paths['ffmpeg'].setText(selected)
    panel.system.setChecked(False);panel.save_current();spin(qt_app,lambda:not panel.busy)
    assert panel.saved_snapshot.version==1
    dispose_panel(panel);other=ToolInventoryPanel(preferences_path=path)
    assert other.paths['ffmpeg'].text()=='' # no implicit read or grant
    other.load_saved();spin(qt_app,lambda:not other.busy)
    assert other.paths['ffmpeg'].text()==selected and not other.system.isChecked()
    assert threads and all(t!=threading.get_ident() for t in threads)
    assert all(other.table.item(row,6).text()=='Chưa kiểm tra hết / chưa quét' for row in range(5))
    assert not (tmp_path/'Công cụ').exists();dispose_panel(other)


def test_unknown_commit_requires_matching_owned_reload_not_replay(qt_app,tmp_path,monkeypatch):
    path=tmp_path/'tools.db';save_preferences(path,ToolPreferences(),load_preferences(path))
    panel=ToolInventoryPanel(preferences_path=path);panel.load_saved();spin(qt_app,lambda:not panel.busy)
    real=io.save_preferences;calls=[]
    def unknown(*args,**kwargs):
        calls.append(1)
        def fail(stage):
            if stage=='after_commit':raise OSError('private SQLite detail')
        return real(*args,**kwargs,fault=fail)
    monkeypatch.setattr(io,'save_preferences',unknown)
    selected=str(tmp_path/'ffmpeg');panel.paths['ffmpeg'].setText(selected);panel.save_current();spin(qt_app,lambda:not panel.busy)
    assert panel.uncertain_save and not panel.save_button.isEnabled() and 'private' not in panel.preference_message.text()
    panel.save_current();assert calls==[1]
    panel.load_saved();spin(qt_app,lambda:not panel.busy)
    assert panel.uncertain_save is None and panel.saved_snapshot.version==2 and panel.paths['ffmpeg'].text()==selected
    assert calls==[1];dispose_panel(panel)


def test_unknown_cannot_be_cleared_by_replacement_store(qt_app,tmp_path):
    path=tmp_path/'tools.db';old=save_preferences(path,ToolPreferences(),load_preferences(path))
    panel=ToolInventoryPanel(preferences_path=path);panel.uncertain_save=(old,ToolPreferences())
    path.rename(tmp_path/'old.db');path.with_name(path.name+'.fonesi-owner').rename(tmp_path/'old.owner')
    save_preferences(path,ToolPreferences(),load_preferences(path))
    panel.load_saved();spin(qt_app,lambda:not panel.busy)
    assert panel.uncertain_save and panel.saved_snapshot is None and not panel.save_button.isEnabled();dispose_panel(panel)


def test_stale_load_preserves_new_edit_and_close_waits_worker(qt_app,tmp_path,monkeypatch):
    path=tmp_path/'tools.db';entered=threading.Event();release=threading.Event();real=io.load_preferences
    def held(*a,**kw):entered.set();release.wait(4);return real(*a,**kw)
    monkeypatch.setattr(io,'load_preferences',held)
    panel=ToolInventoryPanel(preferences_path=path);panel.load_saved();spin(qt_app,entered.is_set)
    new=str(tmp_path/'new');panel.paths['ffprobe'].setText(new);release.set();spin(qt_app,lambda:not panel.busy)
    assert panel.paths['ffprobe'].text()==new and panel.saved_snapshot.version==0
    entered.clear();release.clear();panel.load_saved();spin(qt_app,entered.is_set)
    panel.close();assert panel.busy and panel.stopping and not panel.save_button.isEnabled()
    release.set();spin(qt_app,lambda:not panel.busy);assert not path.exists();dispose_panel(panel)


def test_foreign_config_does_not_block_manual_inventory(qt_app,tmp_path):
    path=tmp_path/'tools.db';path.write_bytes(b'foreign')
    panel=ToolInventoryPanel(preferences_path=path);panel.load_saved();spin(qt_app,lambda:not panel.busy)
    assert panel.scan_button.isEnabled() and not panel.save_button.isEnabled()
    assert path.read_bytes()==b'foreign';dispose_panel(panel)
