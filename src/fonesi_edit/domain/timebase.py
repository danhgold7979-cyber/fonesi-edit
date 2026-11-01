"""Exact stream-relative time maps and shared keyframe evaluation."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from math import gcd, floor
from typing import Any, Iterable

class TimeValueError(ValueError):
    pass

def rational(value: Any) -> Fraction:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise TimeValueError("Expected [integer numerator, positive denominator]")
    n, d = value
    if type(n) is not int or type(d) is not int or d <= 0:
        raise TimeValueError("Rational components must be integers; denominator positive")
    if gcd(n, d) != 1:
        raise TimeValueError("Rational must be reduced to canonical form")
    return Fraction(n, d)

def _exact(value: Fraction | int) -> Fraction:
    if type(value) not in (int,Fraction):
        raise TimeValueError("Exact Fraction or integer required; float/bool forbidden")
    return Fraction(value)

def pair(value: Fraction | int) -> list[int]:
    f = _exact(value)
    return [f.numerator, f.denominator]

def half_up(value: Fraction) -> int:
    return floor(_exact(value) + Fraction(1, 2))

def frame_count(duration: Fraction, fps: Fraction) -> int:
    duration,fps=_exact(duration),_exact(fps)
    if duration <= 0 or fps <= 0:
        raise TimeValueError("Duration and FPS must be positive")
    value = duration * fps
    return -(-value.numerator // value.denominator)

def sample_index(time: Fraction, rate: int) -> int:
    time=_exact(time)
    if time < 0 or type(rate) is not int or rate <= 0:
        raise TimeValueError("Nonnegative time and positive integer sample rate required")
    return floor(time * rate)

@dataclass(frozen=True)
class TimeSegment:
    id: str
    asset_id: str
    stream_index: int
    stream_start: Fraction
    source_in: Fraction
    source_out: Fraction
    output_start: Fraction
    speed: Fraction

    def __post_init__(self):
        for name in ('stream_start','source_in','source_out','output_start','speed'):
            object.__setattr__(self,name,_exact(getattr(self,name)))
        if type(self.stream_index) is not int or self.stream_index<0:
            raise TimeValueError("Nonnegative integer stream index required")
        if self.source_in < 0 or self.source_out <= self.source_in or self.speed <= 0 or self.output_start < 0:
            raise TimeValueError("Invalid source/output range or speed")

    @property
    def output_end(self) -> Fraction:
        return self.output_start + (self.source_out - self.source_in) / self.speed

    def output_to_decoder_pts(self, t: Fraction) -> Fraction:
        t=_exact(t)
        if not self.output_start <= t < self.output_end:
            raise TimeValueError("Output timestamp outside half-open segment")
        return self.stream_start + self.source_in + (t - self.output_start) * self.speed

    def asset_interval_to_output(self, start: Fraction, end: Fraction) -> tuple[Fraction, Fraction] | None:
        start,end=_exact(start),_exact(end)
        if end <= start:
            raise TimeValueError("Cue interval must be nonempty")
        source_start = self.stream_start + self.source_in
        left = max(start, source_start)
        right = min(end, self.stream_start + self.source_out)
        if left >= right:
            return None
        return (self.output_start + (left - source_start) / self.speed,
                self.output_start + (right - source_start) / self.speed)

@dataclass(frozen=True)
class ResolvedCue:
    source_cue_id: str
    segment_id: str | None
    output_start: Fraction
    output_end: Fraction
    text: str
    language: str

def resolve_cue(cue: dict, segments: dict[str, TimeSegment], subtitle_start: Fraction = Fraction(0)) -> tuple[ResolvedCue, ...]:
    start, end = rational(cue["start"]), rational(cue["end"])
    if end <= start:
        raise TimeValueError("Invalid cue interval")
    if cue["time_basis"] == "output":
        return (ResolvedCue(cue["id"], None, start, end, cue["text"], cue["language"]),)
    origin = rational(cue["sidecar_origin"]) if cue["subtitle_stream_index"] is None else _exact(subtitle_start)
    result = []
    for sid in cue["segment_ids"]:
        segment = segments[sid]
        if segment.asset_id != cue["asset_id"]:
            raise TimeValueError("Cue bound to segment of another asset")
        interval = segment.asset_interval_to_output(start + origin, end + origin)
        if interval:
            result.append(ResolvedCue(cue["id"], sid, *interval, cue["text"], cue["language"]))
    return tuple(result)

def interpolate_keyframes(frames: Iterable[tuple[Fraction, Fraction, str]], t: Fraction) -> Fraction:
    """Frames are (effective time, value, outgoing easing); hold outside range."""
    t=_exact(t)
    points = sorted(((_exact(at),_exact(value),easing) for at,value,easing in frames), key=lambda p: p[0])
    if not points:
        raise TimeValueError("No keyframes")
    if len({p[0] for p in points}) != len(points):
        raise TimeValueError("Duplicate effective keyframe time")
    if any(p[2] not in {"linear", "ease_in", "ease_out", "ease_in_out"} for p in points):
        raise TimeValueError("Unsupported easing")
    if t <= points[0][0]:
        return points[0][1]
    if t >= points[-1][0]:
        return points[-1][1]
    for left, right in zip(points, points[1:]):
        if left[0] <= t < right[0]:
            u = (t - left[0]) / (right[0] - left[0])
            u = {"linear": lambda: u, "ease_in": lambda: u*u,
                 "ease_out": lambda: 1-(1-u)*(1-u),
                 "ease_in_out": lambda: 3*u*u-2*u*u*u}[left[2]]()
            return left[1] + (right[1] - left[1]) * u
    raise AssertionError("Unreachable interval")
