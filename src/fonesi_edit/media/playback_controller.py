"""Bounded A/V presentation coordinator using decoded PCM as master clock.

This controller presents frames against one finite PCM buffer. It is a useful
playback integration slice, not a continuous multi-chunk playback engine.
"""
from __future__ import annotations

from fractions import Fraction

from PySide6.QtCore import QObject, QTimer, Signal

from fonesi_edit.media.audio_output import AudioOutputError, QtAudioOutput
from fonesi_edit.media.audio_decode import PCMBuffer
from fonesi_edit.media.video_decode import VideoFrameBatch, RGBVideoFrame
from fonesi_edit.media.av_sync import audio_clock_time, select_due_frame, audio_video_drift


class PlaybackControllerError(RuntimeError):
    pass


class PlaybackController(QObject):
    frame_presented = Signal(object)
    frames_retired = Signal(int)
    state_changed = Signal(str)
    drift_changed = Signal(object)
    playback_finished = Signal()
    playback_failed = Signal(str)

    def __init__(self, audio_output: QtAudioOutput, *, tick_interval_ms: int = 5,
                 max_queued_frames: int = 256, parent=None):
        super().__init__(parent)
        if not isinstance(audio_output, QtAudioOutput):
            raise PlaybackControllerError("A QtAudioOutput instance is required.")
        if type(tick_interval_ms) is not int or not 1 <= tick_interval_ms <= 50:
            raise PlaybackControllerError("Tick interval must be 1..50 ms.")
        if type(max_queued_frames) is not int or not 1 <= max_queued_frames <= 256:
            raise PlaybackControllerError("Frame queue bound must be 1..256.")
        self.audio_output = audio_output
        self.max_queued_frames = max_queued_frames
        self._queue: list[tuple[int, Fraction, RGBVideoFrame]] = []
        self._next_frame_id = 0
        self._last_presented = -1
        self._audio_start = Fraction(0)
        self._timer = QTimer(self)
        self._timer.setInterval(tick_interval_ms)
        self._timer.timeout.connect(self._tick)
        self._active = False
        self._paused = False

    def start(self, pcm: PCMBuffer, *, audio_start_time: Fraction = Fraction(0)):
        if self._active:
            self.stop()
        if not isinstance(pcm, PCMBuffer) or type(audio_start_time) is not Fraction:
            raise PlaybackControllerError("Validated PCM and exact audio start time are required.")
        self._queue.clear()
        self._next_frame_id = 0
        self._last_presented = -1
        self._audio_start = audio_start_time
        try:
            self.audio_output.start(pcm)
        except AudioOutputError as exc:
            self.playback_failed.emit(str(exc))
            raise PlaybackControllerError("Audio output could not start.") from exc
        self._active = True
        self._paused = False
        self._timer.start()
        self.state_changed.emit("playing")

    def enqueue_video_batch(self, batch: VideoFrameBatch):
        if not self._active:
            return
        if not isinstance(batch, VideoFrameBatch):
            raise PlaybackControllerError("Validated VideoFrameBatch required.")
        if len(self._queue) + len(batch.frames) > self.max_queued_frames:
            raise PlaybackControllerError("Video presentation queue is full; producer must apply backpressure.")
        for frame in batch.frames:
            pts = Fraction(str(frame.pts_seconds))
            if self._queue and pts < self._queue[-1][1]:
                raise PlaybackControllerError("Video PTS must be monotonic.")
            self._queue.append((self._next_frame_id, pts, frame))
            self._next_frame_id += 1

    def _tick(self):
        if not self._active:
            return
        try:
            elapsed = self.audio_output.processed_us()
            master = audio_clock_time(elapsed, start_time=self._audio_start)
            due = select_due_frame([(index, pts) for index, pts, _ in self._queue], master)
            if due is not None:
                # Present the newest due frame and discard it plus every stale frame.
                selected = self._queue[due.dropped_before]
                retired_count = due.dropped_before + 1
                del self._queue[:retired_count]
                self.frames_retired.emit(retired_count)
                frame = selected[2]
                self._last_presented = selected[0]
                self.frame_presented.emit(frame)
                self.drift_changed.emit(audio_video_drift(master, due.pts))
            if self.audio_output.state().name == "IdleState":
                # Notify the session first so it can cancel a producer that is
                # still decoding before queue retirement releases its credits.
                self.playback_finished.emit()
                self.stop()
        except BaseException:
            self.stop()
            self.playback_failed.emit("A/V presentation tick failed; playback stopped.")

    def pause(self):
        if not self._active or self._paused:
            return
        self._timer.stop()
        self.audio_output.suspend()
        self._paused = True
        self.state_changed.emit("paused")

    def resume(self):
        if not self._active or not self._paused:
            return
        self.audio_output.resume()
        self._paused = False
        self._timer.start()
        self.state_changed.emit("playing")

    def stop(self):
        self._timer.stop()
        self.audio_output.stop()
        self._active = False
        self._paused = False
        retired_count = len(self._queue)
        self._queue.clear()
        if retired_count:
            self.frames_retired.emit(retired_count)
        self.state_changed.emit("stopped")

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def queued_frames(self) -> int:
        return len(self._queue)

    @property
    def active(self) -> bool:
        return self._active
