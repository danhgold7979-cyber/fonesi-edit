"""Still-frame preview UI requires explicit FFmpeg trust and rejects stale worker results."""
import os
import sys
from pathlib import Path
from fractions import Fraction

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

from PySide6.QtCore import QBuffer,QIODevice,QCoreApplication,QEvent
from PySide6.QtGui import QImage
from fonesi_edit.media.preview import PreviewFrame
from fonesi_edit.storage.project_creation import NewProjectIntent,empty_project
from fonesi_edit.storage.projects import ProjectStore,save_project_file
from fonesi_edit.storage.timeline_commands import add_video_clip
from fonesi_edit.ui.shell import MainWindow
from test_queue_view import wait_for
from test_timeline_import_ui import _record,_scan


def _png():
    image=QImage(16,9,QImage.Format.Format_RGBA8888)
    image.fill(0xff336699)
    buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer,'PNG')
    return bytes(buffer.data())


def _open(tmp_path):
    project=empty_project(NewProjectIntent('Still preview',1920,1080,Fraction(30),Fraction(10)))
    path=tmp_path/'project.json';save_project_file(path,project)
    store=ProjectStore(tmp_path/'store.db')
    window=MainWindow(store);window.show();window.open_project(path)
    source=tmp_path/'clip.mp4';record,payload=_record(source)
    addition=add_video_clip(window.session.project,record,_scan(record),expected_revision=window.session.revision)
    window.session.commit(addition.command);window._project_changed()
    timeline=window.timeline_panel;timeline.clip_list.setCurrentRow(0);timeline.playhead_slider.setValue(15)
    return store,window,timeline,source,payload


def _close(store,window,qt_app):
    window.close()
    wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
    window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete);store.close()


def test_preview_requires_explicit_tool_and_trust_and_displays_still_image(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.timeline as module
    store,window,timeline,source,payload=_open(tmp_path)
    try:
        calls=[]
        def fake_extract(path,tool,*,expected_sha256,stream_index,decoder_time,cancel,timeout,max_width,max_height,persistent_cache=None):
            calls.append((path,tool,expected_sha256,stream_index,decoder_time))
            return PreviewFrame(_png(),expected_sha256,'b'*64,stream_index,decoder_time,16,9,False)
        monkeypatch.setattr(module,'extract_preview_frame',fake_extract)
        assert not timeline.preview_button.isEnabled()
        timeline.preview_path.setText(str(Path(sys.executable).resolve()))
        assert not timeline.preview_trust.isChecked()
        timeline.preview_trust.setChecked(True)
        assert timeline.preview_button.isEnabled()
        timeline.preview_button.click()
        wait_for(qt_app,lambda:not timeline.busy and 'timestamp decoder' in timeline.preview_message.text())
        displayed=timeline.preview_image.pixmap()
        assert displayed is not None and not displayed.isNull()
        assert len(calls)==1
        assert calls[0][0]==source and calls[0][3]==3
        assert calls[0][4]==Fraction(12,25)  # stream start -1/50 + source time 1/2
        assert 'ảnh tĩnh' in timeline.preview_message.text().lower()
        assert 'không đồng bộ audio' in timeline.preview_message.text().lower()
        assert source.read_bytes()==payload
    finally:
        _close(store,window,qt_app)


def test_preview_path_change_revokes_trust_and_playhead_change_discards_old_result(tmp_path,qt_app,monkeypatch):
    import threading
    import fonesi_edit.ui.timeline as module
    from fonesi_edit.media.preview import PreviewCanceled
    store,window,timeline,source,_=_open(tmp_path)
    try:
        entered=threading.Event();release=threading.Event()
        def fake_extract(path,tool,*,expected_sha256,stream_index,decoder_time,cancel,**kwargs):
            entered.set()
            release.wait(2)
            return PreviewFrame(_png(),expected_sha256,'b'*64,stream_index,decoder_time,16,9,False)
        monkeypatch.setattr(module,'extract_preview_frame',fake_extract)
        tool=str(Path(sys.executable).resolve())
        timeline.preview_path.setText(tool);timeline.preview_trust.setChecked(True)
        timeline.request_preview()
        wait_for(qt_app,entered.is_set)
        timeline.playhead_slider.setValue(16)
        release.set()
        wait_for(qt_app,lambda:not timeline.busy)
        stale_pixmap=timeline.preview_image.pixmap()
        assert stale_pixmap is None or stale_pixmap.isNull()
        assert 'playhead đã đổi' in timeline.preview_message.text().lower()

        timeline.preview_trust.setChecked(True)
        timeline.preview_path.setText(str(Path(sys.executable).resolve().parent/'other-ffmpeg'))
        assert not timeline.preview_trust.isChecked()
        assert not timeline.preview_button.isEnabled()
    finally:
        release.set()
        _close(store,window,qt_app)


def test_application_shutdown_waits_for_preview_worker(tmp_path,qt_app,monkeypatch):
    import threading
    import fonesi_edit.ui.timeline as module
    store,window,timeline,source,_=_open(tmp_path)
    entered=threading.Event();release=threading.Event()
    def fake_extract(path,tool,*,expected_sha256,stream_index,decoder_time,cancel,**kwargs):
        entered.set()
        while not release.wait(.01):
            if cancel():raise module.PreviewCanceled('cancelled')
        return PreviewFrame(_png(),expected_sha256,'b'*64,stream_index,decoder_time,16,9,False)
    monkeypatch.setattr(module,'extract_preview_frame',fake_extract)
    timeline.preview_path.setText(str(Path(sys.executable).resolve()));timeline.preview_trust.setChecked(True)
    timeline.request_preview()
    wait_for(qt_app,entered.is_set)
    window.close()
    assert window.isVisible() and window.background_busy
    release.set()
    wait_for(qt_app,lambda:not window.background_busy and not window.isVisible())
    window.deleteLater();QCoreApplication.sendPostedEvents(window,QEvent.Type.DeferredDelete);store.close()

def test_preview_worker_locks_when_process_retirement_is_unknown(monkeypatch):
    import fonesi_edit.ui.timeline as timeline_module
    from fonesi_edit.media.preview import PreviewRetirementUnknown
    def unknown(*args,**kwargs):
        raise PreviewRetirementUnknown('retirement unknown')
    monkeypatch.setattr(timeline_module,'extract_preview_frame',unknown)
    worker=timeline_module.PreviewWorker('/tmp/source.mp4','/tmp/ffmpeg','a'*64,0,Fraction(0))
    worker.run()
    assert worker.retirement_unknown is True
    assert worker.frame is None
    assert 'unknown' in worker.error.lower()

def test_filmstrip_generates_four_rational_frames_and_reuses_explicit_source(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.timeline as module
    store,window,timeline,source,payload=_open(tmp_path)
    try:
        calls=[]
        def fake_extract(path,tool,*,expected_sha256,stream_index,decoder_time,cancel,timeout,max_width,max_height,persistent_cache=None):
            calls.append(decoder_time)
            return PreviewFrame(_png(),expected_sha256,'b'*64,stream_index,decoder_time,16,9,False)
        monkeypatch.setattr(module,'extract_preview_frame',fake_extract)
        timeline.preview_path.setText(str(Path(sys.executable).resolve()))
        timeline.preview_trust.setChecked(True)
        assert timeline.filmstrip_button.isEnabled()
        timeline.filmstrip_button.click()
        wait_for(qt_app,lambda:not timeline.busy and 'Filmstrip 4 ảnh' in timeline.preview_message.text())
        assert calls==[Fraction(21,200),Fraction(71,200),Fraction(121,200),Fraction(171,200)]
        for label in timeline.filmstrip_labels:
            pixmap=label.pixmap()
            assert pixmap is not None and not pixmap.isNull()
        assert source.read_bytes()==payload
    finally:
        _close(store,window,qt_app)


def test_filmstrip_failure_discards_partial_frames(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.timeline as module
    from fonesi_edit.media.preview import PreviewError
    store,window,timeline,_,_=_open(tmp_path)
    try:
        calls=[]
        def fail_third(path,tool,*,expected_sha256,stream_index,decoder_time,cancel,timeout,max_width,max_height,persistent_cache=None):
            calls.append(decoder_time)
            if len(calls)==3:raise PreviewError('synthetic third frame failure')
            return PreviewFrame(_png(),expected_sha256,'b'*64,stream_index,decoder_time,16,9,False)
        monkeypatch.setattr(module,'extract_preview_frame',fail_third)
        timeline.preview_path.setText(str(Path(sys.executable).resolve()))
        timeline.preview_trust.setChecked(True)
        timeline.filmstrip_button.click()
        wait_for(qt_app,lambda:not timeline.busy and 'synthetic third frame failure' in timeline.preview_message.text())
        assert len(calls)==3
        assert all(label.pixmap() is None or label.pixmap().isNull() for label in timeline.filmstrip_labels)
        assert 'Filmstrip 4 ảnh' not in timeline.preview_image.text()
    finally:
        _close(store,window,qt_app)

def test_waveform_uses_matching_original_audio_stream_and_displays_bounded_bins(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.timeline as module
    from fonesi_edit.media.preview import AudioWaveform
    store,window,timeline,source,payload=_open(tmp_path)
    try:
        calls=[]
        def fake_waveform(path,tool,*,expected_sha256,stream_index,decoder_start,duration,cancel,timeout,bucket_count):
            calls.append((path,stream_index,decoder_start,duration,bucket_count))
            return AudioWaveform(expected_sha256,'b'*64,stream_index,decoder_start,duration,
                                 8000,4,((-1.0,-.5),(.5,1.0)),False)
        monkeypatch.setattr(module,'extract_audio_waveform',fake_waveform)
        timeline.preview_path.setText(str(Path(sys.executable).resolve()))
        timeline.preview_trust.setChecked(True)
        assert timeline.waveform_button.isEnabled()
        timeline.waveform_button.click()
        wait_for(qt_app,lambda:not timeline.busy and 'Waveform biên độ' in timeline.waveform_message.text())
        assert len(calls)==1
        assert calls[0][0]==source and calls[0][1]==5
        assert calls[0][2]==Fraction(0) and calls[0][3]==Fraction(1)
        assert calls[0][4]==256
        assert timeline.waveform_widget.peaks==((-1.0,-.5),(.5,1.0))
        assert source.read_bytes()==payload
        assert 'không phải loudness' in timeline.waveform_message.text().lower()
    finally:
        _close(store,window,qt_app)


def test_waveform_stale_result_is_discarded_when_playhead_changes(tmp_path,qt_app,monkeypatch):
    import threading
    import fonesi_edit.ui.timeline as module
    from fonesi_edit.media.preview import AudioWaveform
    store,window,timeline,_,_=_open(tmp_path)
    try:
        entered=threading.Event();release=threading.Event()
        def fake_waveform(path,tool,*,expected_sha256,stream_index,decoder_start,duration,cancel,timeout,bucket_count):
            entered.set();release.wait(2)
            return AudioWaveform(expected_sha256,'b'*64,stream_index,decoder_start,duration,
                                 8000,4,((-1.0,1.0),)*32,False)
        monkeypatch.setattr(module,'extract_audio_waveform',fake_waveform)
        timeline.preview_path.setText(str(Path(sys.executable).resolve()))
        timeline.preview_trust.setChecked(True)
        timeline.request_waveform()
        wait_for(qt_app,entered.is_set)
        timeline.playhead_slider.setValue(16)
        release.set()
        wait_for(qt_app,lambda:not timeline.busy)
        assert timeline.waveform_widget.peaks==()
        assert 'waveform cũ đã bị loại bỏ' in timeline.waveform_message.text().lower()
    finally:
        release.set()
        _close(store,window,qt_app)

def test_preview_quality_selects_bounded_decoder_dimensions(tmp_path,qt_app,monkeypatch):
    import fonesi_edit.ui.timeline as module
    store,window,timeline,source,payload=_open(tmp_path)
    try:
        calls=[]
        def fake_extract(path,tool,*,expected_sha256,stream_index,decoder_time,cancel,timeout,max_width,max_height,persistent_cache=None):
            calls.append((max_width,max_height))
            return PreviewFrame(_png(),expected_sha256,'b'*64,stream_index,decoder_time,16,9,False)
        monkeypatch.setattr(module,'extract_preview_frame',fake_extract)
        timeline.preview_path.setText(str(Path(sys.executable).resolve()))
        timeline.preview_trust.setChecked(True)
        timeline.preview_quality.setCurrentIndex(0)
        assert window.session.revision==1
        assert timeline.preview_button.isEnabled()
        timeline.preview_button.click()
        wait_for(qt_app,lambda:not timeline.busy and 'timestamp decoder' in timeline.preview_message.text())
        assert calls==[(320,180)]
        assert '320×180' in timeline.preview_quality.currentText()
        assert source.read_bytes()==payload
    finally:
        _close(store,window,qt_app)


def test_quality_change_discards_inflight_preview_and_invalidates_old_frame(tmp_path,qt_app,monkeypatch):
    import threading
    import fonesi_edit.ui.timeline as module
    store,window,timeline,_,_=_open(tmp_path)
    entered=threading.Event();release=threading.Event()
    try:
        def slow_extract(path,tool,*,expected_sha256,stream_index,decoder_time,cancel,timeout,max_width,max_height,persistent_cache=None):
            entered.set()
            release.wait(2)
            return PreviewFrame(_png(),expected_sha256,'b'*64,stream_index,decoder_time,16,9,False)
        monkeypatch.setattr(module,'extract_preview_frame',slow_extract)
        timeline.preview_path.setText(str(Path(sys.executable).resolve()))
        timeline.preview_trust.setChecked(True)
        timeline.request_preview()
        wait_for(qt_app,entered.is_set)
        assert timeline.preview_quality.isEnabled()
        timeline.preview_quality.setCurrentIndex(2)
        release.set()
        wait_for(qt_app,lambda:not timeline.busy)
        pixmap=timeline.preview_image.pixmap()
        assert pixmap is None or pixmap.isNull()
        assert 'chất lượng preview đã đổi' in timeline.preview_message.text().lower()
        assert timeline.preview_quality.currentData()==(1280,720)
    finally:
        release.set()
        _close(store,window,qt_app)

def test_preview_quality_change_does_not_cancel_waveform_observation(tmp_path,qt_app,monkeypatch):
    import threading
    import fonesi_edit.ui.timeline as module
    from fonesi_edit.media.preview import AudioWaveform
    store,window,timeline,_,_=_open(tmp_path)
    entered=threading.Event();release=threading.Event()
    try:
        def slow_waveform(path,tool,*,expected_sha256,stream_index,decoder_start,duration,cancel,timeout,bucket_count):
            entered.set();release.wait(2)
            return AudioWaveform(expected_sha256,'b'*64,stream_index,decoder_start,duration,
                                 8000,4,((-1.0,.5),(.1,1.0)),False)
        monkeypatch.setattr(module,'extract_audio_waveform',slow_waveform)
        timeline.preview_path.setText(str(Path(sys.executable).resolve()))
        timeline.preview_trust.setChecked(True)
        timeline.request_waveform()
        wait_for(qt_app,entered.is_set)
        assert timeline.preview_quality.isEnabled()
        timeline.preview_quality.setCurrentIndex(2)
        release.set()
        wait_for(qt_app,lambda:not timeline.busy)
        assert timeline.waveform_widget.peaks==((-1.0,.5),(.1,1.0))
        assert 'Waveform biên độ' in timeline.waveform_message.text()
    finally:
        release.set()
        _close(store,window,qt_app)
