"""Audio-master-clock scheduling primitives for a future A/V presenter.

This module only computes due video frame indices and queue drop decisions.
It does not own a device clock, present frames, correct decoder timestamps or
claim end-to-end A/V synchronization.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction


class AVSyncError(ValueError):
    pass


@dataclass(frozen=True)
class DueFrame:
    frame_index: int
    pts: Fraction
    dropped_before: int


def audio_clock_time(processed_microseconds: int, *, start_time: Fraction = Fraction(0)) -> Fraction:
    if type(processed_microseconds) is not int or processed_microseconds < 0:
        raise AVSyncError("Audio processed time must be a non-negative integer.")
    if type(start_time) is not Fraction:
        raise AVSyncError("Audio clock start must be an exact Fraction.")
    return start_time + Fraction(processed_microseconds, 1_000_000)


def due_video_frame(audio_time: Fraction, fps: Fraction, *, start_frame: int = 0) -> int:
    if type(audio_time) is not Fraction or audio_time < 0:
        raise AVSyncError("Audio master time must be a non-negative Fraction.")
    if type(fps) is not Fraction or fps <= 0:
        raise AVSyncError("Video FPS must be a positive Fraction.")
    if type(start_frame) is not int or start_frame < 0:
        raise AVSyncError("Video start frame must be a non-negative integer.")
    return start_frame + (audio_time * fps).__floor__()


def select_due_frame(
    queued: tuple[tuple[int, Fraction], ...] | list[tuple[int, Fraction]],
    audio_time: Fraction,
) -> DueFrame | None:
    """Select newest frame with PTS <= audio master time; count stale frames dropped."""
    if type(audio_time) is not Fraction or audio_time < 0:
        raise AVSyncError("Audio master time must be a non-negative Fraction.")
    if not isinstance(queued, (tuple, list)) or len(queued) > 256:
        raise AVSyncError("Frame queue must contain at most 256 entries.")
    previous = None
    due = []
    for item in queued:
        if (not isinstance(item, tuple) or len(item) != 2 or
                type(item[0]) is not int or item[0] < 0 or
                type(item[1]) is not Fraction or item[1] < 0):
            raise AVSyncError("Invalid queued video frame.")
        if previous is not None and item[1] < previous:
            raise AVSyncError("Queued frame PTS must be monotonic.")
        previous = item[1]
        if item[1] <= audio_time:
            due.append(item)
    if not due:
        return None
    index, pts = due[-1]
    return DueFrame(index, pts, len(due) - 1)


def audio_video_drift(audio_time: Fraction, video_pts: Fraction) -> Fraction:
    if type(audio_time) is not Fraction or type(video_pts) is not Fraction:
        raise AVSyncError("A/V timestamps must be exact Fractions.")
    return video_pts - audio_time
