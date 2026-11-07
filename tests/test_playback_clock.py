"""Deterministic tests for the rational playback clock."""
from fractions import Fraction

import pytest

from fonesi_edit.media.playback_clock import PlaybackClock, PlaybackClockError


class FakeTime:
    def __init__(self):
        self.value = 0.0
    def __call__(self):
        return self.value
    def advance(self, seconds):
        self.value += seconds


def test_clock_play_pause_resume_uses_exact_project_frame_rate():
    now = FakeTime()
    clock = PlaybackClock(Fraction(30000, 1001), 10000, now=now)
    assert clock.snapshot().frame == 0
    clock.play()
    now.advance(1001 / 30000 * 90)
    assert clock.snapshot().frame == 90
    paused = clock.pause()
    assert paused.frame == 90 and not paused.playing
    now.advance(5)
    assert clock.snapshot().frame == 90
    clock.play()
    now.advance(1001 / 30000 * 10)
    assert clock.snapshot().frame == 100


def test_clock_seek_and_stop_reanchor_without_drift():
    now = FakeTime()
    clock = PlaybackClock(Fraction(24), 240, now=now)
    clock.play()
    now.advance(1.25)
    assert clock.snapshot().frame == 30
    clock.seek(100)
    now.advance(0.5)
    assert clock.snapshot().frame == 112
    clock.stop()
    assert clock.snapshot().frame == 0 and not clock.snapshot().playing


def test_clock_loop_is_half_open_and_wraps_multiple_cycles():
    now = FakeTime()
    clock = PlaybackClock(Fraction(10), 100, now=now)
    clock.set_loop(20, 30)
    clock.seek(28)
    clock.play()
    now.advance(0.5)
    assert clock.snapshot().frame == 23
    now.advance(2.0)
    assert clock.snapshot().frame == 23
    snapshot = clock.pause()
    assert snapshot.loop_start == 20 and snapshot.loop_end == 30


def test_clock_rejects_invalid_fps_frames_and_loop_bounds():
    with pytest.raises(PlaybackClockError):
        PlaybackClock(Fraction(0), 10)
    with pytest.raises(PlaybackClockError):
        PlaybackClock(Fraction(24), 0)
    clock = PlaybackClock(Fraction(24), 100)
    for start, end in ((-1, 5), (5, 5), (8, 101), (True, 10)):
        with pytest.raises(PlaybackClockError):
            clock.set_loop(start, end)
    with pytest.raises(PlaybackClockError):
        clock.seek(True)
