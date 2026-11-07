"""Finite single-video/single-audio A/V session coordinator.

This composes existing bounded decode workers with the audio-master controller
for a <=5 second test session. It is not a continuous project renderer, mixer
for arbitrary overlapping tracks, or export/playback acceptance.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from fonesi_edit.media.audio_worker import AudioChunkWorker, AudioTrackSpec
from fonesi_edit.media.playback_worker import VideoFrameQueueWorker
from fonesi_edit.media.playback_controller import PlaybackController


class PlaybackSessionError(RuntimeError):
    pass


class PlaybackSession(QObject):
    state_changed = Signal(str)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, controller: PlaybackController, *, parent=None):
        super().__init__(parent)
        if not isinstance(controller, PlaybackController):
            raise PlaybackSessionError("PlaybackController is required.")
        self.controller = controller
        self.controller.playback_finished.connect(self._audio_finished_signal)
        self.controller.playback_failed.connect(self._fail)
        self.audio_worker: AudioChunkWorker | None = None
        self.video_worker: VideoFrameQueueWorker | None = None
        self._active = False
        self._audio_ready = False
        self._video_finished = False
        self._audio_worker_finished = False
        self._audio_output_finished = False
        self._video_cancel_requested = False
        self._terminal_state = None
        self._retirement_reported = False
        self._pcm = None

    def start(
        self, *, audio_track: AudioTrackSpec, audio_ffmpeg: Path | str,
        video_source: Path | str, video_ffmpeg: Path | str,
        video_sha256: str, video_stream_index: int,
        video_start_seconds: float, fps: Fraction,
        video_start_frame: int = 0, duration_seconds: Fraction = Fraction(5),
        width: int = 640, height: int = 360,
    ) -> None:
        if self._active:
            raise PlaybackSessionError("A playback session is already active.")
        if not isinstance(audio_track, AudioTrackSpec):
            raise PlaybackSessionError("One validated audio track is required.")
        if type(fps) is not Fraction or fps <= 0:
            raise PlaybackSessionError("A positive exact frame rate is required.")
        if type(duration_seconds) is not Fraction or not 0 < duration_seconds <= 5:
            raise PlaybackSessionError("Finite session duration must be >0 and <=5 seconds.")
        if type(video_start_frame) is not int or video_start_frame < 0:
            raise PlaybackSessionError("Video start frame must be non-negative.")
        total_frames = (duration_seconds * fps).__ceil__()
        if not 1 <= total_frames <= 600:
            raise PlaybackSessionError("Video session frame count exceeds bounded limit.")
        samples = (duration_seconds * 48000).__ceil__()
        self._active = True
        self._audio_ready = False
        self._video_finished = False
        self._audio_worker_finished = False
        self._audio_output_finished = False
        self._video_cancel_requested = False
        self._terminal_state = None
        self._retirement_reported = False
        self._pcm = None
        self.state_changed.emit("decoding-audio")
        audio = AudioChunkWorker(
            [audio_track], audio_ffmpeg, chunk_start_sample=audio_track.output_start_sample,
            chunk_samples=samples, sample_rate=48000, channels=2, timeout=45, parent=self,
        )
        video = VideoFrameQueueWorker(
            video_source, video_ffmpeg, expected_sha256=video_sha256,
            stream_index=video_stream_index, start_seconds=video_start_seconds,
            fps_num=fps.numerator, fps_den=fps.denominator,
            total_frames=total_frames, width=width, height=height,
            batch_size=8, timeout=45, parent=self,
        )
        self.audio_worker, self.video_worker = audio, video
        self.controller.frames_retired.connect(video.acknowledge_frames)
        audio.chunk_ready.connect(self._audio_ready_signal)
        audio.finished.connect(self._audio_worker_finished_signal)
        audio.chunk_failed.connect(self._fail)
        audio.chunk_canceled.connect(self._canceled)
        audio.retirement_unknown.connect(self._retirement_unknown)
        video.batch_ready.connect(self._video_batch)
        video.decode_failed.connect(self._fail)
        video.decode_canceled.connect(self._canceled)
        video.retirement_unknown.connect(self._retirement_unknown)
        video.finished.connect(self._video_finished_signal)
        audio.start()

    def _audio_ready_signal(self, pcm):
        if not self._active:
            return
        self._pcm = pcm
        try:
            self.controller.start(pcm)
        except BaseException:
            self._fail("Audio output could not start; playback session stopped.")
            return
        self._audio_ready = True
        self.state_changed.emit("playing")
        if self.video_worker is not None and not self.video_worker.isRunning():
            self.video_worker.start()

    def _video_batch(self, batch):
        if not self._active or not self._audio_ready:
            if self.video_worker is not None and batch.frames:
                self.video_worker.acknowledge_frames(len(batch.frames))
            return
        try:
            self.controller.enqueue_video_batch(batch)
        except BaseException:
            # enqueue_video_batch validates atomically; this batch was not
            # adopted, so return its reservation before canceling the producer.
            if self.video_worker is not None and batch.frames:
                self.video_worker.acknowledge_frames(len(batch.frames))
            self._fail("Video presentation queue rejected a decoded frame batch.")

    def _video_finished_signal(self):
        # QThread.finished means the worker's run() returned; the worker may
        # have emitted its final batch earlier, but it is now safe to retire.
        self._video_finished = True
        self.state_changed.emit("video-decoding-finished")
        self._complete_if_retired()

    def _audio_worker_finished_signal(self):
        self._audio_worker_finished = True
        self._complete_if_retired()

    def _audio_finished_signal(self):
        if not self._active:
            return
        self._audio_output_finished = True
        # Audio is the master clock. Stop any decoder that is still producing
        # frames, but do not publish "finished" until its QThread retires.
        if self.video_worker is not None and self.video_worker.isRunning():
            self._video_cancel_requested = True
            self.video_worker.request_cancel()
        elif self.video_worker is None:
            self._video_finished = True
        self._complete_if_retired()

    def _complete_if_retired(self):
        if self._terminal_state is not None:
            if (self._audio_worker_finished and self._video_finished
                    and not self._retirement_reported):
                self._retirement_reported = True
                self.state_changed.emit(self._terminal_state + "-retired")
            return
        if not self._audio_output_finished:
            return
        if not self._audio_worker_finished or not self._video_finished:
            self.state_changed.emit("audio-finished-waiting-for-video-retirement")
            return
        self._active = False
        self._terminal_state = "finished"
        self.state_changed.emit("finished")
        self.finished.emit()

    def _fail(self, message):
        if not self._active:
            return
        self._active = False
        self._terminal_state = "failed"
        if self.audio_worker is not None and self.audio_worker.isRunning():
            self.audio_worker.request_cancel()
        else:
            self._audio_worker_finished = True
        if self.video_worker is not None and self.video_worker.isRunning():
            self.video_worker.request_cancel()
        else:
            self._video_finished = True
        self.controller.stop()
        self.failed.emit(message)
        self._complete_if_retired()

    def _canceled(self):
        if not self._active:
            return
        self._active = False
        self._terminal_state = "canceled"
        if self.audio_worker is not None and self.audio_worker.isRunning():
            self.audio_worker.request_cancel()
        else:
            self._audio_worker_finished = True
        if self.video_worker is not None and self.video_worker.isRunning():
            self.video_worker.request_cancel()
        else:
            self._video_finished = True
        self.controller.stop()
        self.state_changed.emit("canceled")
        self._complete_if_retired()

    def _retirement_unknown(self, message):
        self._fail("Decoder retirement is unknown: " + message)

    def stop(self):
        if not self._active:
            return
        self._active = False
        self._terminal_state = "stopped"
        if self.audio_worker is not None and self.audio_worker.isRunning():
            self.audio_worker.request_cancel()
        else:
            self._audio_worker_finished = True
        if self.video_worker is not None and self.video_worker.isRunning():
            self.video_worker.request_cancel()
        else:
            self._video_finished = True
        self.controller.stop()
        self.state_changed.emit("stopped")
        self._complete_if_retired()

    @property
    def active(self):
        return self._active
