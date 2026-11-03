"""Qt timeline import uses a synthetic frame map plus a real owned child lifecycle."""
import json
import os
from PySide6.QtCore import QCoreApplication,QEvent
import sys
import uuid
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from fonesi_edit.domain.media_library import MediaRecord,MediaPath
from fonesi_edit.media.probe import ProbeResult
from fonesi_edit.media.observations import normalize_probe
from fonesi_edit.media.frames import FrameScan,FrameObservation
from fonesi_edit.jobs.process import run_owned
from fonesi_edit.storage.media_commands import add_media
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for


def _record(source):
    payload=b'synthetic source; not a codec fixture'
    source.write_bytes(payload)
    digest=sha256(payload).hexdigest()
    raw={'streams':[
        {'index':3,'codec_type':'video','codec_name':'mpeg4','time_base':'1/1000',
         'start_pts':-20,'duration_ts':1000,'width':32,'height':24,
         'sample_aspect_ratio':'4:3','disposition':{'attached_pic':0},
         'side_data_list':[{'side_data_type':'Display Matrix',
          'displaymatrix':'00000000: 65536 0 0\n00000001: 0 65536 0\n00000002: 0 0 1073741824',
          'rotation':'0'}]},
        {'index':5,'codec_type':'audio','codec_name':'aac','time_base':'1/48000',
         'start_pts':0,'duration_ts':48000,'sample_rate':'48000',
         'channels':2,'channel_layout':'stereo'}],
        'format':{'duration':'1'}}
    observation=normalize_probe(ProbeResult(digest,json.dumps(raw),str(Path(sys.executable).resolve()),()))
    return MediaRecord(str(uuid.uuid4()),digest,len(payload),
        MediaPath('absolute',str(source),digest),'OBSERVED',observation),payload


def _scan(record,status='OBSERVED_EOF'):
    frames=(FrameObservation(-20,-20,40,40,()),FrameObservation(20,20,40,40,()),
            FrameObservation(980,980,20,20,()))
    return FrameScan(record.sha256,'b'*64,3,Fraction(1,1000),-20,status,frames,
                     ('NOT_MEDIA_VALIDITY_OR_RENDER_READINESS',),False)


def _opened(tmp_path):
    project=empty_project(NewProjectIntent('Timeline import',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    return path


def test_selected_library_media_becomes_video_and_audio_timeline_tracks(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.media_import as ui
    source=tmp_path/'clip.mp4';record,payload=_record(source);scan=_scan(record)
    def synthetic_frames(source_path,tool,observation,stream_index,*,cancel,_lifecycle):
        result=_lifecycle.run(run_owned,[sys.executable,'-c','print("owned-frame-observer")'],
                              cancel=cancel,timeout=5)
        assert result.returncode==0
        assert stream_index==3
        return scan
    monkeypatch.setattr(ui,'observe_frames',synthetic_frames)
    path=_opened(tmp_path)
    with ProjectStore(tmp_path/'store.db') as store:
        window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            addition=add_media(window.session.project,record)
            window.session.commit(addition.command)
            window._project_changed()
            panel=window.media_import
            assert panel.table.rowCount()==1
            panel.table.selectRow(0)
            panel.tool.setText(str(Path(sys.executable).resolve()))
            panel.trust.setChecked(True)
            assert panel.timeline_button.isEnabled()
            panel.timeline_button.click()
            wait_for(qt_app,lambda:not panel.busy and window.session.revision==2)
            plan=window.session.project.plan.to_dict()
            assert len(plan['assets'])==1 and len(plan['clips'])==1
            assert len(plan['audio']['clips'])==1
            assert plan['clips'][0]['video_stream_index']==3
            assert plan['clips'][0]['source_out']==[1,1]
            assert plan['audio']['clips'][0]['audio_stream_index']==5
            assert '1 video clip' in window.timeline_panel.summary.text()
            assert '1 audio clip' in window.timeline_panel.summary.text()
            assert source.read_bytes()==payload
            assert 'Chưa phát' in panel.message.text()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)


def test_incomplete_frame_scan_does_not_commit_timeline(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.media_import as ui
    source=tmp_path/'incomplete.mp4';record,_=_record(source)
    def incomplete(source_path,tool,observation,stream_index,*,cancel,_lifecycle):
        _lifecycle.run(run_owned,[sys.executable,'-c','print("owned-frame-observer")'],
                       cancel=cancel,timeout=5)
        return _scan(record,'INCOMPLETE')
    monkeypatch.setattr(ui,'observe_frames',incomplete)
    with ProjectStore(tmp_path/'store.db') as store:
        path=_opened(tmp_path);window=MainWindow(store);window.show()
        try:
            window.open_project(path)
            window.session.commit(add_media(window.session.project,record).command)
            window._project_changed()
            panel=window.media_import;panel.table.selectRow(0)
            panel.tool.setText(str(Path(sys.executable).resolve()));panel.trust.setChecked(True)
            panel.timeline_button.click()
            wait_for(qt_app,lambda:not panel.busy)
            assert window.session.revision==1
            assert window.session.project.plan.to_dict()['clips']==[]
            assert window.session.project.plan.to_dict()['assets']==[]
            assert 'Không thể thêm clip' in panel.message.text()
        finally:
            window.close()
            wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
            window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete)
