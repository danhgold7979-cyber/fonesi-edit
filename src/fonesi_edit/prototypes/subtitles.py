"""SRT proof: explicit validation and time mapping, without ASR/OCR."""
from dataclasses import dataclass, replace
from fractions import Fraction
from pathlib import Path
import re


@dataclass(frozen=True)
class Cue:
    start_ms: int
    end_ms: int
    text: str

    def __post_init__(self):
        if self.start_ms < 0 or self.end_ms <= self.start_ms or not self.text.strip():
            raise ValueError("Cue must have non-empty text and 0 <= start < end")


_TIME = r"(\d+):([0-5]\d):([0-5]\d)[,.](\d{3})"
_RANGE = re.compile(rf"^{_TIME}\s*-->\s*{_TIME}\s*$")


def parse_srt(text: str) -> list[Cue]:
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        raise ValueError("Subtitle file is empty")
    result = []
    for block in re.split(r"\n\s*\n", text):
        lines = block.splitlines()
        if lines[0].strip().isdigit():
            lines = lines[1:]
        match = _RANGE.fullmatch(lines[0].strip()) if lines else None
        if not match or len(lines) < 2:
            raise ValueError(f"Invalid SRT block {len(result) + 1}")
        parts = list(map(int, match.groups()))
        def millis(p):
            return ((p[0] * 60 + p[1]) * 60 + p[2]) * 1000 + p[3]
        result.append(Cue(millis(parts[:4]), millis(parts[4:]), "\n".join(lines[1:])))
    return result


def load_srt(path: Path) -> list[Cue]:
    return parse_srt(path.read_text(encoding="utf-8-sig"))


def dump_srt(cues: list[Cue]) -> str:
    def timestamp(value: int) -> str:
        seconds, ms = divmod(value, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"
    return "\n\n".join(
        f"{i}\n{timestamp(c.start_ms)} --> {timestamp(c.end_ms)}\n{c.text}"
        for i, c in enumerate(cues, 1)
    ) + "\n"


def map_trimmed_cues(cues: list[Cue], start_ms: int, end_ms: int,
                     speed: Fraction = Fraction(1), offset_ms: int = 0) -> list[Cue]:
    if start_ms < 0 or end_ms <= start_ms or speed <= 0 or offset_ms < 0:
        raise ValueError("Invalid trim, speed or offset")
    result = []
    for cue in cues:
        left, right = max(cue.start_ms, start_ms), min(cue.end_ms, end_ms)
        if left >= right:
            continue
        mapped_start = offset_ms + round(Fraction(left - start_ms) / speed)
        mapped_end = offset_ms + round(Fraction(right - start_ms) / speed)
        if mapped_end > mapped_start:
            result.append(replace(cue, start_ms=mapped_start, end_ms=mapped_end))
    return result
