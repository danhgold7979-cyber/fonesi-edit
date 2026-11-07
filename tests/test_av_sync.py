"""Deterministic audio-master-clock scheduling and stale-frame selection tests."""
from fractions import Fraction

import pytest

from fonesi_edit.media.av_sync import (
    AVSyncError, audio_clock_time, audio_video_drift,
    due_video_frame, select_due_frame,
)


def test_audio_clock_maps_microseconds_to_exact_video_frame():
    clock = audio_clock_time(1_001_000, start_time=Fraction(1, 10))
    assert clock == Fraction(1101, 1000)
    assert due_video_frame(clock, Fraction(30000, 1001)) == 32


def test_scheduler_selects_latest_due_frame_and_counts_drops():
    queue = [
        (10, Fraction(0)),
        (11, Fraction(1, 30)),
        (12, Fraction(2, 30)),
        (13, Fraction(3, 30)),
    ]
    result = select_due_frame(queue, Fraction(1, 15))
    assert result.frame_index == 12
    assert result.pts == Fraction(1, 15)
    assert result.dropped_before == 2
    assert select_due_frame(queue, Fraction(1, 120)) is not None
    assert select_due_frame([(1, Fraction(1, 10))], Fraction(0)) is None


def test_scheduler_reports_signed_av_drift():
    assert audio_video_drift(Fraction(101, 100), Fraction(1)) == Fraction(-1, 100)
    assert audio_video_drift(Fraction(1), Fraction(101, 100)) == Fraction(1, 100)


def test_scheduler_rejects_nonmonotonic_and_unbounded_queue():
    with pytest.raises(AVSyncError):
        select_due_frame([(1, Fraction(1, 10)), (2, Fraction(0))], Fraction(1))
    with pytest.raises(AVSyncError):
        select_due_frame([(i, Fraction(i, 30)) for i in range(257)], Fraction(10))
    with pytest.raises(AVSyncError):
        due_video_frame(Fraction(1), Fraction(0))
    with pytest.raises(AVSyncError):
        audio_clock_time(-1)
