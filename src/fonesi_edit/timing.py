"""Exact half-open media time maps, independent of GUI and media engines."""

from dataclasses import dataclass
from fractions import Fraction


def time_value(numerator: int, denominator: int = 1) -> Fraction:
    if type(numerator) is not int or type(denominator) is not int:
        raise ValueError("Time must use integer numerator and denominator")
    if denominator <= 0:
        raise ValueError("Time denominator must be positive")
    return Fraction(numerator, denominator)


@dataclass(frozen=True)
class Interval:
    start: Fraction
    end: Fraction

    def __post_init__(self):
        if not isinstance(self.start, Fraction) or not isinstance(self.end, Fraction):
            raise ValueError("Interval requires exact fractions")  # noqa: TRY004 - stable public validation error contract.
        if self.start < 0 or self.end <= self.start:
            raise ValueError("Interval must be nonempty and nonnegative")

    @property
    def duration(self) -> Fraction:
        return self.end - self.start

    def intersect(self, other: "Interval") -> "Interval | None":
        start, end = max(self.start, other.start), min(self.end, other.end)
        return Interval(start, end) if start < end else None


@dataclass(frozen=True)
class ClipMap:
    source: Interval
    speed: Fraction = Fraction(1)
    output_start: Fraction = Fraction(0)

    def __post_init__(self):
        if not isinstance(self.source, Interval):
            raise ValueError("Source interval required")  # noqa: TRY004 - stable public validation error contract.
        if not isinstance(self.speed, Fraction) or self.speed <= 0:
            raise ValueError("Speed must be positive exact fraction")
        if not isinstance(self.output_start, Fraction) or self.output_start < 0:
            raise ValueError("Output start must be nonnegative exact fraction")

    @property
    def output(self) -> Interval:
        return Interval(
            self.output_start, self.output_start + self.source.duration / self.speed
        )

    def map_interval(self, cue: Interval) -> Interval | None:
        clipped = self.source.intersect(cue)
        if clipped is None:
            return None
        return Interval(
            self.output_start + (clipped.start - self.source.start) / self.speed,
            self.output_start + (clipped.end - self.source.start) / self.speed,
        )
