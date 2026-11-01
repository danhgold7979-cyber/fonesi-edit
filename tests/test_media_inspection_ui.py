"""Real Qt + owned Python protocol stand-ins, NOT actual Windows FFmpeg."""
import hashlib,json,sys,time,threading
from pathlib import Path
from fractions import Fraction as Q
from PySide6.QtCore import QTimer
from fonesi_edit.ui import media_inspection as ui
from fonesi_edit.jobs.process import run_owned,ProcessCanceled,ProcessError
from fonesi_edit.media.probe import ProbeResult,ProbeCanceled
from fonesi_edit.media.frames import FrameScan,FrameObservation
from fonesi_edit.storage.projects import ProjectStore
from fonesi_edit.ui.shell import MainWindow


def spin(app,predicate,seconds=8):
    end=time.monotonic()+seconds
    while not predicate() and time.monotonic()<end:app.processEvents();time.sleep(.005)
    assert predicate();app.processEvents()


def configure(panel,source):
    panel.source.setText(str(source));panel.tool.setText(sys.executable);panel.trust.setChecked(True)


def raw(source):
    return ProbeResult(hashlib.sha256(source.read_bytes()).hexdigest(),json.dumps({'streams':[{'index':3,'codec_type':'video','codec_name':'mpeg4','time_base':'1/1000','start_pts':0,'duration_ts':1000,'width':48,'height':32,'sample_aspect_ratio':'1:1','disposition':{'attached_pic':0}}]}),sys.executable,())


def test_actual_owned_probe_and_frame_standins_show_bounded_facts_without_project_apply(qt_app,tmp_path,monkeypatch):
    source=tmp_path/'media';source.write_bytes(b'owned fixture');before=source.read_bytes();calls=[]
    def inspect(path,tool,*,cancel,_lifecycle):
        calls.append('probe');_lifecycle.run(run_owned,[sys.executable,'-c','import time;time.sleep(.1);print("observed")'],cancel=cancel,timeout=5)
        return raw(path)
    def frames(path,tool,observation,index,*,cancel,_lifecycle):
        calls.append(('frames',index));_lifecycle.run(run_owned,[sys.executable,'-c','print("frames")'],cancel=cancel,timeout=5)
        return FrameScan(observation.sha256,'b'*64,index,Q(1,1000),0,'INCOMPLETE',tuple(FrameObservation(i,i,1,1,()) for i in range(100)),('FRAME_COUNT_LIMIT',))
    monkeypatch.setattr(ui,'inspect_media',inspect);monkeypatch.setattr(ui,'observe_frames',frames)
    with ProjectStore(tmp_path/'active.db') as store:
        window=MainWindow(store);panel=window.inspection_panel;configure(panel,source)
        panel.with_frames.setChecked(True);panel.stream.setValue(3);pulses=[];timer=QTimer();timer.timeout.connect(lambda:pulses.append(1));timer.start(5)
        panel.start();assert panel.busy and not panel.source.isEnabled()
        spin(qt_app,lambda:not panel.busy);timer.stop()
        output=panel.output.toPlainText()
        assert calls==['probe',('frames',3)] and pulses and '#63:' in output and '#64:' not in output
        assert 'INCOMPLETE' in output and 'KHÔNG xác nhận' in output and 'Luồng 3' in output
        assert window.project is None and window.store is store and source.read_bytes()==before
        assert panel.button.isEnabled() and not panel.revoked
        window.close()


def test_explicit_trust_reset_and_empty_success_receipt_cannot_authorize_repeat(qt_app,tmp_path,monkeypatch):
    source=tmp_path/'media';source.write_bytes(b'fixture');panel=ui.InspectionPanel();configure(panel,source)
    panel.tool.setText(str(tmp_path/'other'));assert not panel.trust.isChecked() and not panel.button.isEnabled()
    configure(panel,source);monkeypatch.setattr(ui,'inspect_media',lambda *a,**k:raw(source))
    panel.start();spin(qt_app,lambda:not panel.busy)
    assert panel.revoked and not panel.button.isEnabled() and not panel.output.toPlainText()
    panel.close()


def test_unknown_retirement_sticky_across_tool_changes_and_second_invocation(qt_app,tmp_path,monkeypatch):
    source=tmp_path/'media';source.write_bytes(b'fixture');calls=[]
    def inspect(path,tool,*,cancel,_lifecycle):
        calls.append(1)
        def unknown(*a,**k):raise ProcessError('PRIVATE unconfirmed retirement')
        _lifecycle.run(unknown,[])
    monkeypatch.setattr(ui,'inspect_media',inspect)
    panel=ui.InspectionPanel();configure(panel,source);panel.start();spin(qt_app,lambda:not panel.busy)
    assert panel.revoked and 'PRIVATE' not in panel.message.text()
    panel.tool.setText(str(tmp_path/'different'));panel.trust.setChecked(True);panel.start()
    assert calls==[1] and panel.worker is None and not panel.button.isEnabled()
    panel.close()


def test_close_cancels_actual_owned_process_and_waits_retirement(qt_app,tmp_path,monkeypatch):
    source=tmp_path/'media';source.write_bytes(b'fixture');entered=threading.Event()
    def inspect(path,tool,*,cancel,_lifecycle):
        try:_lifecycle.run(run_owned,[sys.executable,'-c','import time;print("READY",flush=True);time.sleep(30)'],cancel=cancel,timeout=5,on_stdout=lambda chunk:entered.set())
        except ProcessCanceled as exc:raise ProbeCanceled('canceled') from exc
        return raw(path)
    monkeypatch.setattr(ui,'inspect_media',inspect)
    with ProjectStore(tmp_path/'active.db') as store:
        window=MainWindow(store);window.show();panel=window.inspection_panel;configure(panel,source);panel.start()
        spin(qt_app,entered.is_set);worker=panel.worker;window.close()
        assert window.background_busy and panel.stopping
        spin(qt_app,lambda:not window.background_busy)
        assert worker.retired and worker.outcome=='CANCELED' and not panel.revoked
        window.close()


def test_stale_worker_completion_cannot_replace_current_output(qt_app,tmp_path):
    panel=ui.InspectionPanel();panel.output.setPlainText('current')
    old=ui.InspectionWorker(tmp_path/'a',tmp_path/'b',None,panel);panel._finished(old)
    assert panel.output.toPlainText()=='current' and panel.worker is None
    old.deleteLater();panel.close()


def test_retired_probe_cannot_hide_unknown_frame_invocation(qt_app,tmp_path,monkeypatch):
    source=tmp_path/'media';source.write_bytes(b'fixture')
    def inspect(path,tool,*,cancel,_lifecycle):
        _lifecycle.run(run_owned,[sys.executable,'-c','print("probe")'],cancel=cancel,timeout=5)
        return raw(path)
    def frames(path,tool,observation,index,*,cancel,_lifecycle):
        def unknown(*a,**k):raise ProcessError('Unconfirmed frame child')
        _lifecycle.run(unknown,[])
    monkeypatch.setattr(ui,'inspect_media',inspect);monkeypatch.setattr(ui,'observe_frames',frames)
    panel=ui.InspectionPanel();configure(panel,source);panel.with_frames.setChecked(True);panel.stream.setValue(3)
    panel.start();spin(qt_app,lambda:not panel.busy)
    assert panel.revoked and not panel.output.toPlainText() and not panel.button.isEnabled()
    panel.close()
