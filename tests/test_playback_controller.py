"""Tests for finite-buffer A/V controller scheduling against audio clock."""
from fractions import Fraction

import pytest
from PySide6.QtCore import QObject

from fonesi_edit.media.audio_decode import PCMBuffer
from fonesi_edit.media.audio_output import QtAudioOutput
from fonesi_edit.media.video_decode import RGBVideoFrame, VideoFrameBatch
from fonesi_edit.media.playback_controller import (
    PlaybackController, PlaybackControllerError,
)


class FakeAudioOutput(QtAudioOutput):
    def __init__(self):
        QObject.__init__(self)
        self.elapsed = 0
        self._state = "StoppedState"
        self.suspended = False
        self.starts = 0
        self.stops = 0
    def start(self, pcm):
        assert isinstance(pcm, PCMBuffer)
        self.starts += 1
        self.elapsed = 0
        self._state = "ActiveState"
        self.suspended = False
    def processed_us(self):
        return self.elapsed
    def state(self):
        return type("State", (), {"name": self._state})()
    def suspend(self):
        self.suspended = True
        self._state = "SuspendedState"
    def resume(self):
        self.suspended = False
        self._state = "ActiveState"
    def stop(self):
        self.stops += 1
        self._state = "StoppedState"


def _pcm():
    return PCMBuffer("a"*64, 0, 48000, 2, 4,
                     (0.1, -0.1)*4, 4)


def _batch():
    frames = tuple(RGBVideoFrame(i, 16, 16, i/30,
                                 b"x"*(16*16*3)) for i in range(4))
    return VideoFrameBatch("a"*64, 0, 16, 16, frames, True)


def test_controller_uses_audio_clock_and_presents_newest_due_frame(qt_app):
    output = FakeAudioOutput()
    controller = PlaybackController(output)
    presented, drift = [], []
    controller.frame_presented.connect(presented.append)
    controller.drift_changed.connect(drift.append)
    controller.start(_pcm())
    controller.enqueue_video_batch(_batch())
    output.elapsed = 80_000
    controller._tick()
    assert len(presented) == 1
    assert presented[0].index == 2
    assert controller.queued_frames == 1
    assert len(drift) == 1
    assert abs(float(drift[0]) - float(Fraction(-1, 75))) < 1e-9
    controller.stop()
    assert not controller.active and output.stops >= 1


def test_controller_pause_resume_suspends_audio_without_discarding_queue(qt_app):
    output = FakeAudioOutput()
    controller = PlaybackController(output)
    controller.start(_pcm())
    controller.enqueue_video_batch(_batch())
    controller.pause()
    assert controller.active and controller.paused and output.suspended
    assert controller.queued_frames == 4
    controller.resume()
    assert controller.active and not controller.paused and not output.suspended
    controller.stop()
    assert not controller.active


def test_controller_rejects_queue_overflow_and_nonmonotonic_pts(qt_app):
    controller = PlaybackController(FakeAudioOutput(), max_queued_frames=4)
    controller.start(_pcm())
    controller.enqueue_video_batch(_batch())
    with pytest.raises(PlaybackControllerError, match="full"):
        controller.enqueue_video_batch(_batch())
    controller.stop()

    controller = PlaybackController(FakeAudioOutput())
    controller.start(_pcm())
    frames = (RGBVideoFrame(0, 16, 16, 0.2, b"x"*(16*16*3)),
              RGBVideoFrame(1, 16, 16, 0.1, b"x"*(16*16*3)))
    with pytest.raises(PlaybackControllerError, match="monotonic"):
        controller.enqueue_video_batch(VideoFrameBatch("a"*64,0,16,16,frames,True))
    assert controller.queued_frames == 0  # rejected batches are atomic
    controller.stop()


def test_controller_stops_when_audio_buffer_reaches_idle(qt_app):
    output = FakeAudioOutput()
    controller = PlaybackController(output)
    finished = []
    controller.playback_finished.connect(lambda: finished.append(True))
    controller.start(_pcm())
    output._state = "IdleState"
    controller._tick()
    assert finished == [True]
    assert not controller.active



def test_controller_releases_frame_credits_when_due_frames_and_queue_are_retired(qt_app):
    output = FakeAudioOutput()
    controller = PlaybackController(output)
    retired = []
    controller.frames_retired.connect(retired.append)
    controller.start(_pcm())
    controller.enqueue_video_batch(_batch())
    output.elapsed = 80_000
    controller._tick()
    assert retired == [3]
    assert controller.queued_frames == 1
    controller.stop()
    assert retired == [3, 1]
    assert controller.queued_frames == 0
