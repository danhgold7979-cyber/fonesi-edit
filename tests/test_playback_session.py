"""Finite A/V session orchestration tests with injected worker/output fakes."""
from fractions import Fraction
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from fonesi_edit.media.audio_decode import PCMBuffer
from fonesi_edit.media.audio_output import QtAudioOutput
from fonesi_edit.media.audio_worker import AudioTrackSpec
from fonesi_edit.media.video_decode import RGBVideoFrame, VideoFrameBatch
from fonesi_edit.media.playback_controller import PlaybackController
from fonesi_edit.media import playback_session as session_module


class FakeOutput(QtAudioOutput):
    def __init__(self):
        QObject.__init__(self)
        self.elapsed = 0
        self.running = False
    def start(self, pcm):
        self.running = True
    def processed_us(self):
        return self.elapsed
    def state(self):
        return type("State", (), {"name": "ActiveState" if self.running else "StoppedState"})()
    def suspend(self):
        pass
    def resume(self):
        pass
    def stop(self):
        self.running = False


class FakeAudioWorker(QObject):
    finished = Signal()
    chunk_ready = Signal(object)
    chunk_failed = Signal(str)
    chunk_canceled = Signal()
    retirement_unknown = Signal(str)
    def __init__(self, tracks, ffmpeg, **kwargs):
        super().__init__()
        self.started = False
        self.canceled = False
    def start(self):
        self.started = True
        pcm = PCMBuffer("a"*64, 0, 48000, 2, 4, (0.1,-0.1)*4, 4)
        self.chunk_ready.emit(pcm)
        self.finished.emit()
    def isRunning(self):
        return False
    def request_cancel(self):
        self.canceled = True


class FakeVideoWorker(QObject):
    batch_ready = Signal(object)
    decode_failed = Signal(str)
    decode_canceled = Signal()
    retirement_unknown = Signal(str)
    finished = Signal()
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.started = False
        self.canceled = False
        self.acknowledged = 0
    def acknowledge_frames(self, count):
        self.acknowledged += count
    def start(self):
        self.started = True
        frames = (RGBVideoFrame(0,16,16,0.0,b"x"*(16*16*3)),)
        self.batch_ready.emit(VideoFrameBatch("b"*64,0,16,16,frames,True))
        self.finished.emit()
    def isRunning(self):
        return False
    def request_cancel(self):
        self.canceled = True


def test_finite_session_starts_audio_then_video_and_stops_on_master_finish(
        qt_app, monkeypatch, tmp_path):
    monkeypatch.setattr(session_module, "AudioChunkWorker", FakeAudioWorker)
    monkeypatch.setattr(session_module, "VideoFrameQueueWorker", FakeVideoWorker)
    controller = PlaybackController(FakeOutput())
    session = session_module.PlaybackSession(controller)
    states, finished = [], []
    session.state_changed.connect(states.append)
    session.finished.connect(lambda: finished.append(True))
    track = AudioTrackSpec(tmp_path/"audio.mp4", "a"*64, 0, 0, 0.0)
    session.start(audio_track=track, audio_ffmpeg=tmp_path/"ffmpeg",
        video_source=tmp_path/"video.mp4", video_ffmpeg=tmp_path/"ffmpeg",
        video_sha256="b"*64, video_stream_index=0,
        video_start_seconds=0.0, fps=Fraction(30,1),
        duration_seconds=Fraction(1,2), width=16, height=16)
    assert session.active
    assert session.audio_worker.started and session.video_worker.started
    assert controller.queued_frames == 1
    controller.playback_finished.emit()
    controller.stop()  # mirrors the controller's IdleState completion path
    assert session.video_worker.acknowledged == 1
    assert not session.active
    assert finished == [True]
    assert "playing" in states and "finished" in states


def test_finite_session_rejects_duration_over_five_seconds(qt_app, tmp_path):
    session = session_module.PlaybackSession(PlaybackController(FakeOutput()))
    track = AudioTrackSpec(tmp_path/"audio.mp4", "a"*64, 0, 0, 0.0)
    try:
        session.start(audio_track=track, audio_ffmpeg=tmp_path/"ffmpeg",
            video_source=tmp_path/"video.mp4", video_ffmpeg=tmp_path/"ffmpeg",
            video_sha256="b"*64, video_stream_index=0,
            video_start_seconds=0.0, fps=Fraction(30,1),
            duration_seconds=Fraction(6,1))
    except session_module.PlaybackSessionError as exc:
        assert "<=5" in str(exc)
    else:
        raise AssertionError("Unbounded session duration was accepted")



def test_audio_master_waits_for_video_worker_retirement_before_session_finished(
        qt_app, monkeypatch, tmp_path):
    class DelayedVideoWorker(FakeVideoWorker):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.running=False
        def start(self):
            self.started=True
            self.running=True
            frames=(RGBVideoFrame(0,16,16,0.0,b"x"*(16*16*3)),)
            self.batch_ready.emit(VideoFrameBatch("b"*64,0,16,16,frames,True))
        def isRunning(self):
            return self.running
        def request_cancel(self):
            self.canceled=True
        def retire(self):
            self.running=False
            self.finished.emit()

    monkeypatch.setattr(session_module,"AudioChunkWorker",FakeAudioWorker)
    monkeypatch.setattr(session_module,"VideoFrameQueueWorker",DelayedVideoWorker)
    controller=PlaybackController(FakeOutput())
    session=session_module.PlaybackSession(controller)
    finished=[]
    session.finished.connect(lambda:finished.append(True))
    track=AudioTrackSpec(tmp_path/"audio.mp4","a"*64,0,0,0.0)
    session.start(audio_track=track,audio_ffmpeg=tmp_path/"ffmpeg",
        video_source=tmp_path/"video.mp4",video_ffmpeg=tmp_path/"ffmpeg",
        video_sha256="b"*64,video_stream_index=0,
        video_start_seconds=0.0,fps=Fraction(30,1),
        duration_seconds=Fraction(1,2),width=16,height=16)
    video=session.video_worker
    assert video.isRunning()
    controller.playback_finished.emit()
    controller.stop()  # retire queued frames only after producer cancellation
    assert video.canceled
    assert session.active
    assert finished==[]
    video.retire()
    assert not session.active
    assert finished==[True]



def test_session_returns_credit_for_batch_arriving_after_stop(qt_app, monkeypatch, tmp_path):
    class DeferredVideoWorker(FakeVideoWorker):
        def start(self):
            self.started=True
        def isRunning(self):
            return True
    monkeypatch.setattr(session_module,"AudioChunkWorker",FakeAudioWorker)
    monkeypatch.setattr(session_module,"VideoFrameQueueWorker",DeferredVideoWorker)
    controller=PlaybackController(FakeOutput())
    session=session_module.PlaybackSession(controller)
    track=AudioTrackSpec(tmp_path/"audio.mp4","a"*64,0,0,0.0)
    session.start(audio_track=track,audio_ffmpeg=tmp_path/"ffmpeg",
        video_source=tmp_path/"video.mp4",video_ffmpeg=tmp_path/"ffmpeg",
        video_sha256="b"*64,video_stream_index=0,
        video_start_seconds=0.0,fps=Fraction(30,1),
        duration_seconds=Fraction(1,2),width=16,height=16)
    worker=session.video_worker
    session.stop()
    before=worker.acknowledged
    late_batch=VideoFrameBatch("b"*64,0,16,16,
        (RGBVideoFrame(9,16,16,0.3,b"x"*(16*16*3)),),True)
    session._video_batch(late_batch)
    assert worker.acknowledged==before+1
