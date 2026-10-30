"""Complete immutable settings for a future queued CPU export, never execution."""

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from pathlib import PurePosixPath, PureWindowsPath
from uuid import UUID

from fonesi_edit.snapshot import local_path
from fonesi_edit.timing import ClipMap, Interval, time_value

FORMAT = "fonesi-cpu-export"


def _fraction(value):
    if (
        not isinstance(value, Fraction)
        or abs(value.numerator) >= 2**63
        or value.denominator >= 2**63
    ):
        raise ValueError("INVALID_RATIONAL")
    return [value.numerator, value.denominator]


def _read_fraction(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("INVALID_RATIONAL")
    if (
        any(type(x) is not int for x in value)
        or abs(value[0]) >= 2**63
        or not 0 < value[1] < 2**63
    ):
        raise ValueError("INVALID_RATIONAL")
    result = time_value(*value)
    _fraction(result)
    return result


def _fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names):
        raise ValueError("UNKNOWN_OR_MISSING_FIELD")


@dataclass(frozen=True)
class CpuExportSnapshot:
    project_id: str
    source: str
    destination: str
    source_sha256: str
    ffmpeg: str
    ffmpeg_sha256: str
    ffprobe: str
    ffprobe_sha256: str
    clip_map: ClipMap | None
    duration_tolerance: Fraction
    seed: int
    version: int = 1

    def __post_init__(self):
        if (
            not isinstance(self.project_id, str)
            or str(UUID(self.project_id)) != self.project_id
        ):
            raise ValueError("INVALID_PROJECT_ID")
        for path in (self.source, self.destination, self.ffmpeg, self.ffprobe):
            local_path(path)
            if len(path.encode("utf-8")) > 4096:
                raise ValueError("PATH_TOO_LONG")
        if self.source == self.destination:
            raise ValueError("SOURCE_EQUALS_DESTINATION")
        if not any(
            p(self.destination).suffix.lower() == ".mp4"
            for p in (PurePosixPath, PureWindowsPath)
        ):
            raise ValueError("MP4_DESTINATION_REQUIRED")
        for digest in (self.source_sha256, self.ffmpeg_sha256, self.ffprobe_sha256):
            if (
                not isinstance(digest, str)
                or re.fullmatch("[0-9a-f]{64}", digest) is None
            ):
                raise ValueError("INVALID_DIGEST")
        if type(self.version) is not int or self.version != 1:
            raise ValueError("UNSUPPORTED_VERSION")
        if type(self.seed) is not int or not 0 <= self.seed < 2**63:
            raise ValueError("INVALID_SEED")
        _fraction(self.duration_tolerance)
        if not 0 <= self.duration_tolerance <= 1:
            raise ValueError("INVALID_TOLERANCE")
        if self.clip_map is not None:
            if not isinstance(self.clip_map, ClipMap):
                raise ValueError("INVALID_CLIP_MAP")
            if (
                self.clip_map.output_start != 0
                or not Fraction(1, 2) <= self.clip_map.speed <= 2
            ):
                raise ValueError("UNSUPPORTED_CLIP_MAP")
            for value in (
                self.clip_map.source.start,
                self.clip_map.source.end,
                self.clip_map.speed,
                self.clip_map.output_start,
            ):
                _fraction(value)

    def canonical(self):
        edit = None
        if self.clip_map is not None:
            edit = {
                "start": _fraction(self.clip_map.source.start),
                "end": _fraction(self.clip_map.source.end),
                "speed": _fraction(self.clip_map.speed),
                "output_start": _fraction(self.clip_map.output_start),
            }
        data = {
            "format": FORMAT,
            "version": self.version,
            "project_id": self.project_id,
            "source": self.source,
            "destination": self.destination,
            "source_sha256": self.source_sha256,
            "ffmpeg": self.ffmpeg,
            "ffmpeg_sha256": self.ffmpeg_sha256,
            "ffprobe": self.ffprobe,
            "ffprobe_sha256": self.ffprobe_sha256,
            "clip_map": edit,
            "duration_tolerance": _fraction(self.duration_tolerance),
            "seed": self.seed,
        }
        result = json.dumps(
            data,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        if len(result.encode("utf-8")) > 65536:
            raise ValueError("SNAPSHOT_TOO_LARGE")
        return result

    @property
    def digest(self):
        return sha256(self.canonical().encode("utf-8")).hexdigest()

    @classmethod
    def parse(cls, payload):
        if not isinstance(payload, str) or len(payload.encode("utf-8")) > 65536:
            raise ValueError("INVALID_SNAPSHOT_SIZE")

        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("DUPLICATE_KEY")
                result[key] = value
            return result

        try:
            value = json.loads(payload, object_pairs_hook=unique)
            _fields(
                value,
                (
                    "format",
                    "version",
                    "project_id",
                    "source",
                    "destination",
                    "source_sha256",
                    "ffmpeg",
                    "ffmpeg_sha256",
                    "ffprobe",
                    "ffprobe_sha256",
                    "clip_map",
                    "duration_tolerance",
                    "seed",
                ),
            )
            if value.pop("format") != FORMAT:
                raise ValueError("UNSUPPORTED_FORMAT")
            edit = value["clip_map"]
            if edit is not None:
                _fields(edit, ("start", "end", "speed", "output_start"))
                value["clip_map"] = ClipMap(
                    Interval(
                        _read_fraction(edit["start"]), _read_fraction(edit["end"])
                    ),
                    _read_fraction(edit["speed"]),
                    _read_fraction(edit["output_start"]),
                )
            value["duration_tolerance"] = _read_fraction(value["duration_tolerance"])
            return cls(**value)
        except (
            ValueError,
            TypeError,
            KeyError,
            RecursionError,
            AttributeError,
            OverflowError,
        ) as exc:
            raise ValueError("INVALID_CPU_SNAPSHOT") from exc
