"""Timeline Play/Pause/Stop wiring for the bounded A/V session prototype."""
import os
from pathlib import Path
from fractions import Fraction

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from fonesi_edit.media.video_decode import RGBVideoFrame
from fonesi_edit.storage.autosave import CompletedCommand
from fonesi_edit.ui import timeline as timeline_module
from test_timeline_preview_ui import _open, _close


class FakeController:
    def __init__(self, *_args, **_kwargs):
        self.paused = False
    def pause(self):
        self.paused = True
    def resume(self):
        self.paused = False


class FakePlaybackSession(QObject):
    frame_presented = Signal(object)
    state_changed = Signal(str)
    failed = Signal(str)
    finished = Signal()
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.active = False
        self.options = None
        self.stopped = False
    def start(self, **kwargs):
        self.options = kwargs
        self.active = True
        self.state_changed.emit("playing")
        self.frame_presented.emit(RGBVideoFrame(0,16,16,0.0,b"\x40"*(16*16*3)))
    def stop(self):
        self.active = False
        self.stopped = True


def test_timeline_playback_buttons_start_bounded_session_and_render_frame(
        tmp_path, qt_app, monkeypatch):
    store, window, timeline, source, payload = _open(tmp_path)
    try:
        ffmpeg = tmp_path / "ffmpeg"
        ffmpeg.write_bytes(b"test ffmpeg tool")
        ffmpeg.chmod(0o700)
        monkeypatch.setattr(timeline_module, "PlaybackController", FakeController)
        monkeypatch.setattr(timeline_module, "QtAudioOutput", lambda parent: object())
        monkeypatch.setattr(timeline_module, "PlaybackSession", FakePlaybackSession)
        original_seek = timeline_module.plan_preview_seek
        planned_seeks = []
        def recording_seek(plan, clip_id, output_frame):
            result = original_seek(plan, clip_id, output_frame)
            planned_seeks.append(result)
            return result
        monkeypatch.setattr(timeline_module, "plan_preview_seek", recording_seek)
        timeline.preview_path.setText(str(ffmpeg))
        timeline.preview_trust.setChecked(True)
        assert timeline.play_button.isEnabled()
        before = window.session.project.plan.to_dict()
        timeline.play_button.click()
        playback = timeline.playback_session
        assert playback is not None and playback.active
        assert playback.options["duration_seconds"] <= Fraction(5)
        assert playback.options["fps"] == Fraction(30)
        assert len(planned_seeks) == 1
        assert planned_seeks[0].output_frame == timeline._playhead
        assert playback.options["video_start_seconds"] == float(planned_seeks[0].video.decoder_time) == 0.48
        assert playback.options["audio_track"].source_start_seconds == float(planned_seeks[0].audio[0].decoder_time) == 0.5
        assert planned_seeks[0].video.output_time == planned_seeks[0].audio[0].output_time
        assert timeline.preview_image.pixmap() is not None
        assert timeline.pause_button.isEnabled()
        timeline.pause_button.click()
        assert playback.controller.paused
        timeline.pause_button.click()
        assert not playback.controller.paused
        timeline.stop_playback_button.click()
        assert playback.stopped and not playback.active
        assert window.session.project.plan.to_dict() == before
        assert source.read_bytes() == payload
    finally:
        _close(store, window, qt_app)


def test_timeline_playback_refuses_video_speed_effect(tmp_path, qt_app, monkeypatch):
    store, window, timeline, source, payload = _open(tmp_path)
    try:
        ffmpeg = tmp_path / "ffmpeg"
        ffmpeg.write_bytes(b"test ffmpeg tool")
        ffmpeg.chmod(0o700)
        timeline.preview_path.setText(str(ffmpeg))
        timeline.preview_trust.setChecked(True)
        data = window.session.project.plan.to_dict()
        data["clips"][0]["speed"] = [2, 1]
        data["revision"] += 1
        data["provenance"]["project_revision"] = data["revision"]
        from fonesi_edit.domain.composition import CompositionPlan
        changed = CompositionPlan.parse(data)
        window.session.commit(CompletedCommand(
            window.session.project.with_plan(changed), window.session.revision
        ))
        window._project_changed()
        # Keep the playhead inside the shortened interval so this test isolates
        # the unsupported speed effect rather than the half-open end guard.
        timeline.playhead_slider.setValue(0)
        timeline.play_button.click()
        assert timeline.playback_session is None
        assert "tốc độ 1×" in timeline.playback_status.text()
        assert source.read_bytes() == payload
    finally:
        _close(store, window, qt_app)



def test_timeline_shutdown_stops_active_playback_session(tmp_path, qt_app, monkeypatch):
    store, window, timeline, source, payload = _open(tmp_path)
    try:
        ffmpeg = tmp_path / "ffmpeg"
        ffmpeg.write_bytes(b"test ffmpeg tool")
        ffmpeg.chmod(0o700)
        monkeypatch.setattr(timeline_module, "PlaybackController", FakeController)
        monkeypatch.setattr(timeline_module, "QtAudioOutput", lambda parent: object())
        monkeypatch.setattr(timeline_module, "PlaybackSession", FakePlaybackSession)
        timeline.preview_path.setText(str(ffmpeg))
        timeline.preview_trust.setChecked(True)
        timeline.play_button.click()
        playback = timeline.playback_session
        assert playback is not None and playback.active
        timeline.request_stop()
        assert playback.stopped and not playback.active
        assert not timeline.busy
        assert source.read_bytes() == payload
    finally:
        _close(store, window, qt_app)
