"""Drift-resistant output clock for a future media playback backend.

The clock schedules project frames only. It does not decode media, render video,
open an audio device or claim continuous playback support.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from time import monotonic
from typing import Callable


class PlaybackClockError(ValueError):
    pass


@dataclass(frozen=True)
class ClockSnapshot:
    frame: int
    time: Fraction
    playing: bool
    loop_start: int | None
    loop_end: int | None


class PlaybackClock:
    """Monotonic, rational frame clock with pause/seek and half-open loop bounds."""

    def __init__(self, fps: Fraction, total_frames: int, *,
                 now: Callable[[], float] = monotonic):
        if not isinstance(fps, Fraction) or fps <= 0:
            raise PlaybackClockError("FPS must be a positive Fraction.")
        if type(total_frames) is not int or total_frames < 1:
            raise PlaybackClockError("total_frames must be a positive integer.")
        if not callable(now):
            raise PlaybackClockError("now must be callable.")
        self.fps = fps
        self.total_frames = total_frames
        self._now = now
        self._frame = 0
        self._anchor_frame = 0
        self._anchor_time = now()
        self._playing = False
        self._loop: tuple[int, int] | None = None

    def _clamp(self, frame: int) -> int:
        if type(frame) is not int:
            raise PlaybackClockError("frame must be an integer.")
        return min(max(frame, 0), self.total_frames - 1)

    def _current_frame(self, stamp: float) -> int:
        elapsed = max(0.0, stamp - self._anchor_time)
        advanced = int(Fraction(str(elapsed)) * self.fps)
        frame = self._anchor_frame + advanced
        if self._loop is not None:
            start, end = self._loop
            if frame >= end:
                frame = start + (frame - start) % (end - start)
        return self._clamp(frame)

    def snapshot(self) -> ClockSnapshot:
        frame = self._current_frame(self._now()) if self._playing else self._frame
        loop_start, loop_end = self._loop if self._loop is not None else (None, None)
        return ClockSnapshot(frame, Fraction(frame, 1) / self.fps,
                             self._playing, loop_start, loop_end)

    def seek(self, frame: int) -> ClockSnapshot:
        frame = self._clamp(frame)
        self._frame = frame
        self._anchor_frame = frame
        self._anchor_time = self._now()
        return self.snapshot()

    def play(self) -> ClockSnapshot:
        if not self._playing:
            self._anchor_frame = self._frame
            self._anchor_time = self._now()
            self._playing = True
        return self.snapshot()

    def pause(self) -> ClockSnapshot:
        if self._playing:
            self._frame = self._current_frame(self._now())
            self._playing = False
        return self.snapshot()

    def stop(self) -> ClockSnapshot:
        self._playing = False
        self._frame = 0
        self._anchor_frame = 0
        self._anchor_time = self._now()
        return self.snapshot()

    def set_loop(self, start: int | None, end: int | None) -> ClockSnapshot:
        if start is None and end is None:
            self._loop = None
        else:
            if (type(start) is not int or type(end) is not int or
                    not 0 <= start < end <= self.total_frames):
                raise PlaybackClockError("Loop must be a valid half-open [start, end) frame range.")
            self._loop = (start, end)
        current = self._current_frame(self._now()) if self._playing else self._frame
        if self._loop is not None and not self._loop[0] <= current < self._loop[1]:
            current = self._loop[0]
        self._frame = current
        self._anchor_frame = current
        self._anchor_time = self._now()
        return self.snapshot()
