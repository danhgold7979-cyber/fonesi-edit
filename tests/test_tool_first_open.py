import threading
import time
from fonesi_edit.ui import tool_inventory as ui
from fonesi_edit.ui import tool_preferences as io
from fonesi_edit.dependencies.preferences import load_preferences,save_preferences,ToolPreferences


def spin(app,predicate):
    end=time.monotonic()+6
    while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.005)
    assert predicate();app.processEvents()


def test_saved_explicit_missing_never_falls_back_first_open(qt_app,tmp_path,monkeypatch):
    path=tmp_path/'prefs.db';selected=str(tmp_path/'explicit-missing')
    save_preferences(path,ToolPreferences((selected,'','','',''),'',False),load_preferences(path))
    calls=[];real=ui.discover_tools
    def scan(**kwargs):calls.append(kwargs);return real(**kwargs)
    monkeypatch.setattr(ui,'discover_tools',scan)
    panel=ui.ToolInventoryPanel(preferences_path=path);panel.first_open();panel.first_open()
    spin(qt_app,lambda:bool(calls) and not panel.busy)
    assert len(calls)==1 and calls[0]['configured']=={'ffmpeg':selected} and calls[0]['system_dirs']==()
    assert panel.paths['ffmpeg'].text()==selected and 'KHÔNG thay thế' in panel.table.item(0,6).text()
    panel.first_open();assert len(calls)==1;panel.close()


def test_corrupt_preferences_do_not_launch_default_scan(qt_app,tmp_path,monkeypatch):
    path=tmp_path/'prefs.db';path.write_bytes(b'foreign')
    monkeypatch.setattr(ui,'discover_tools',lambda **kw:(_ for _ in ()).throw(AssertionError('fallback scan')))
    panel=ui.ToolInventoryPanel(preferences_path=path);panel.first_open();spin(qt_app,lambda:not panel.busy)
    assert panel.scan_button.isEnabled() and 'Không đọc/lưu' in panel.preference_message.text()
    panel.first_open();qt_app.processEvents();assert not panel.busy and path.read_bytes()==b'foreign';panel.close()


def test_user_edit_during_load_suppresses_automatic_scan(qt_app,tmp_path,monkeypatch):
    entered=threading.Event();release=threading.Event();real=io.load_preferences;calls=[]
    def load(*a,**kw):entered.set();release.wait(4);return real(*a,**kw)
    monkeypatch.setattr(io,'load_preferences',load);monkeypatch.setattr(ui,'discover_tools',lambda **kw:calls.append(kw))
    panel=ui.ToolInventoryPanel(preferences_path=tmp_path/'prefs.db');panel.first_open();spin(qt_app,entered.is_set)
    selected=str(tmp_path/'user-edit');panel.paths['ffmpeg'].setText(selected);release.set();spin(qt_app,lambda:not panel.busy)
    assert calls==[] and panel.paths['ffmpeg'].text()==selected
    panel.first_open();qt_app.processEvents();assert calls==[];panel.close()


def test_cancel_close_first_load_never_rearms_or_launches(qt_app,tmp_path,monkeypatch):
    entered=threading.Event();release=threading.Event();real=io.load_preferences;calls=[]
    def load(*a,**kw):entered.set();release.wait(4);return real(*a,**kw)
    monkeypatch.setattr(io,'load_preferences',load);monkeypatch.setattr(ui,'discover_tools',lambda **kw:calls.append(kw))
    panel=ui.ToolInventoryPanel(preferences_path=tmp_path/'prefs.db');panel.first_open();spin(qt_app,entered.is_set)
    panel.cancel();panel.first_open();panel.close();assert panel.busy and panel.stopping
    release.set();spin(qt_app,lambda:not panel.busy);assert calls==[] and not (tmp_path/'prefs.db').exists();panel.close()


def test_queued_scan_rechecks_explicit_operation_and_close(qt_app,tmp_path,monkeypatch):
    queued=[];calls=[];real=ui.QTimer.singleShot
    def later(delay,callback):
        if delay==0:queued.append(callback)
        else:real(delay,callback)
    monkeypatch.setattr(ui.QTimer,'singleShot',later);monkeypatch.setattr(ui,'discover_tools',lambda **kw:calls.append(kw))
    panel=ui.ToolInventoryPanel(preferences_path=tmp_path/'prefs.db');panel.first_open()
    spin(qt_app,lambda:bool(queued) and not panel.busy)
    panel.cancel();queued.pop()();assert calls==[]
    # Cancellation cannot rearm navigation; explicit Scan remains the user's choice.
    panel.first_open();qt_app.processEvents();assert calls==[];panel.close()


def test_deferred_first_scan_uses_panel_as_qtimer_context(qt_app,tmp_path,monkeypatch):
    calls=[];monkeypatch.setattr(ui,'discover_tools',lambda **kw:calls.append(kw))
    panel=ui.ToolInventoryPanel(preferences_path=tmp_path/'prefs.db')
    real=ui.QTimer.singleShot;scheduled=[]
    def capture(*args):
        if len(args)==3 and args[0]==0 and args[1] is panel:
            scheduled.append(args)
            return
        return real(*args)
    monkeypatch.setattr(ui.QTimer,'singleShot',capture)
    panel.first_open();spin(qt_app,lambda:not panel.busy)
    assert len(scheduled)==1 and scheduled[0][1] is panel
    panel.close()
