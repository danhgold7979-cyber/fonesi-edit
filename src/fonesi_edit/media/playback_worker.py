"""Asynchronous bounded frame-batch producer for a future playback queue.

This worker owns FFmpeg decode on a QThread and emits immutable RGB batches.
It deliberately does not schedule presentation or claim A/V synchronization.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import replace
from fractions import Fraction

from PySide6.QtCore import QThread, Signal
from threading import Condition

from fonesi_edit.media.video_decode import (
    VideoDecodeCanceled, VideoDecodeError, VideoDecodeRetirementUnknown,
    decode_video_frame_batch,
)


class VideoFrameQueueWorker(QThread):
    batch_ready = Signal(object)
    progress_changed = Signal(int, int)
    decode_failed = Signal(str)
    decode_canceled = Signal()
    retirement_unknown = Signal(str)

    def __init__(
        self, source: Path | str, ffmpeg: Path | str, *,
        expected_sha256: str, stream_index: int, start_seconds: float,
        fps_num: int, fps_den: int, total_frames: int,
        width: int = 640, height: int = 360, batch_size: int = 8,
        timeout: float = 30.0, max_inflight_frames: int = 64, parent=None,
    ):
        super().__init__(parent)
        if type(batch_size) is not int or not 1 <= batch_size <= 32:
            raise ValueError("Video frame queue batch_size must be 1..32.")
        if type(total_frames) is not int or not 1 <= total_frames <= 100000:
            raise ValueError("Video frame queue total_frames must be 1..100000.")
        if (type(max_inflight_frames) is not int
                or not batch_size <= max_inflight_frames <= 256):
            raise ValueError("max_inflight_frames must be between batch_size and 256.")
        self.source = Path(source)
        self.ffmpeg = Path(ffmpeg)
        self.expected_sha256 = expected_sha256
        self.stream_index = stream_index
        self.start_seconds = start_seconds
        self.fps_num = fps_num
        self.fps_den = fps_den
        self.total_frames = total_frames
        self.width = width
        self.height = height
        self.batch_size = batch_size
        self.timeout = timeout
        self.max_inflight_frames = max_inflight_frames
        self._cancel_requested = False
        self._flow = Condition()
        self._inflight_frames = 0
        self.frames_decoded = 0

    def request_cancel(self) -> None:
        with self._flow:
            self._cancel_requested = True
            self.requestInterruption()
            self._flow.notify_all()

    def _reserve_frames(self, count: int) -> bool:
        with self._flow:
            while self._inflight_frames + count > self.max_inflight_frames:
                if self._cancelled():
                    return False
                self._flow.wait(timeout=0.05)
            if self._cancelled():
                return False
            self._inflight_frames += count
            return True

    def _release_frames(self, count: int) -> None:
        if type(count) is not int or count <= 0:
            return
        with self._flow:
            if count > self._inflight_frames:
                raise RuntimeError("frame-credit acknowledgement exceeds in-flight reservations")
            self._inflight_frames -= count
            self._flow.notify_all()

    def acknowledge_frames(self, count: int) -> None:
        """Release producer capacity after the presentation queue retires frames."""
        if type(count) is not int or not 1 <= count <= self.max_inflight_frames:
            raise ValueError("acknowledged frame count is outside the in-flight bound")
        self._release_frames(count)

    @property
    def inflight_frames(self) -> int:
        with self._flow:
            return self._inflight_frames

    def _cancelled(self) -> bool:
        return self._cancel_requested or self.isInterruptionRequested()

    def run(self) -> None:
        self.frames_decoded = 0
        try:
            while self.frames_decoded < self.total_frames:
                if self._cancelled():
                    raise VideoDecodeCanceled("Frame queue canceled.")
                count = min(self.batch_size, self.total_frames - self.frames_decoded)
                if not self._reserve_frames(count):
                    raise VideoDecodeCanceled("Frame queue canceled while waiting for presentation capacity.")
                reserved = count
                try:
                    offset = self.frames_decoded * self.fps_den / self.fps_num
                    batch = decode_video_frame_batch(
                        self.source, self.ffmpeg,
                        expected_sha256=self.expected_sha256,
                        stream_index=self.stream_index,
                        start_seconds=self.start_seconds + offset,
                        fps_num=self.fps_num, fps_den=self.fps_den,
                        frame_count=count, width=self.width, height=self.height,
                        cancel=self._cancelled, timeout=self.timeout,
                    )
                    if self._cancelled():
                        raise VideoDecodeCanceled("Frame queue canceled before batch adoption.")
                    if not batch.frames or len(batch.frames) > count:
                        raise VideoDecodeError("Video decoder returned an invalid frame batch size.")
                    if len(batch.frames) < reserved:
                        self._release_frames(reserved - len(batch.frames))
                        reserved = len(batch.frames)
                    # FFmpeg frame PTS are source/decoder timestamps, while
                    # the audio-master clock starts at zero for this playback
                    # segment. Rebase every decoded frame onto the segment's
                    # relative timeline so a non-zero source trim does not
                    # delay video presentation by the source in-point.
                    segment_offset = Fraction(self.frames_decoded * self.fps_den,
                                              self.fps_num)
                    indexed_frames = tuple(
                        replace(
                            frame,
                            index=self.frames_decoded + offset,
                            pts_seconds=float(segment_offset + Fraction(
                                offset * self.fps_den, self.fps_num
                            )),
                        )
                        for offset, frame in enumerate(batch.frames)
                    )
                    batch = replace(batch, frames=indexed_frames)
                    self.batch_ready.emit(batch)
                    self.frames_decoded += len(batch.frames)
                    self.progress_changed.emit(self.frames_decoded, self.total_frames)
                    reserved = 0  # consumer owns reservation until acknowledge_frames()
                    if len(batch.frames) < count:
                        # EOF before the planned clip end is a short decode, not
                        # silent success; the consumer decides whether to stop.
                        break
                finally:
                    if reserved:
                        self._release_frames(reserved)
        except VideoDecodeRetirementUnknown as exc:
            self.retirement_unknown.emit(str(exc))
        except VideoDecodeCanceled:
            self.decode_canceled.emit()
        except VideoDecodeError as exc:
            self.decode_failed.emit(str(exc))
        except BaseException:
            self.decode_failed.emit("Video frame queue failed; no further batches were emitted.")
