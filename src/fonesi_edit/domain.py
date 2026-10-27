"""Versioned, UI-independent composition and immutable job payloads."""
from dataclasses import asdict, dataclass, field
from pathlib import Path
from uuid import uuid4
import hashlib
import json
import math
import os
import re
import tempfile

SCHEMA_VERSION = 1
SECRET_KEYS = {"password", "cookies", "cookie", "api_key", "access_token", "refresh_token", "secret"}


def identifier() -> str:
    return uuid4().hex


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def checked_payload(value):
    def check(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if key.lower() in SECRET_KEYS:
                    raise ValueError(f"Secret values cannot be stored in project/job: {key}")
                check(child)
        elif isinstance(item, list):
            for child in item:
                check(child)
    check(value)
    return json.loads(canonical(value))


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(checked_payload(value))
    descriptor, name = tempfile.mkstemp(prefix=".fonesi-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


@dataclass
class Clip:
    path: str
    start: float = 0
    end: float | None = None
    speed: float = 1
    flip: bool = False
    rotation: float = 0
    volume: float = 1
    subtitles: str | None = None
    offset: float | None = None
    source_duration: float | None = None
    freeze: float = 0
    id: str = field(default_factory=identifier)

    def validate(self):
        if not self.path or not math.isfinite(self.start) or self.start < 0:
            raise ValueError("Clip path/start is invalid")
        if not math.isfinite(self.speed) or not 0.1 <= self.speed <= 10:
            raise ValueError("Speed must be 0.1–10")
        if self.end is not None and (not math.isfinite(self.end) or self.end <= self.start):
            raise ValueError("Clip end must be after start")
        if not math.isfinite(self.rotation) or not 0 <= self.volume <= 4:
            raise ValueError("Invalid rotation/volume")
        if not math.isfinite(self.freeze) or self.freeze<0:raise ValueError("Freeze duration invalid")


@dataclass
class Layer:
    kind: str = "text"
    name: str = "Chữ mới"
    text: str = "Fonesi Edit"
    path: str | None = None
    x: float = 0.05
    y: float = 0.08
    width: float = 0.3
    height: float = 0.1
    rotation: float = 0
    opacity: float = 1
    start: float = 0
    end: float | None = None
    visible: bool = True
    locked: bool = False
    style: dict = field(default_factory=lambda: {"font_size": 32, "color": "#ffffff", "outline": 2, "outline_color": "#000000"})
    motion: dict = field(default_factory=lambda: {"preset": "fixed", "speed": 20, "duration": 5, "delay": 0, "repeat": True, "easing": "linear"})
    keyframes: dict = field(default_factory=dict)
    clip_ids: list[str] = field(default_factory=list)
    group: str | None = None
    id: str = field(default_factory=identifier)

    def validate(self):
        if self.kind not in {"text", "image", "mask", "subtitle"}:
            raise ValueError("Unknown layer type")
        for value in (self.x, self.y, self.width, self.height, self.opacity, self.rotation, self.start):
            if not math.isfinite(value):
                raise ValueError("Layer transform must be finite")
        if not 0 <= self.opacity <= 1 or self.width <= 0 or self.height <= 0 or self.start < 0:
            raise ValueError("Invalid opacity/size/time")
        if self.end is not None and (not math.isfinite(self.end) or self.end <= self.start):
            raise ValueError("Layer interval is invalid")
        if self.kind == "text" and not 8 <= int(self.style.get("font_size", 32)) <= 300:
            raise ValueError("Font size must be 8–300")
        for key in ("color", "outline_color", "background", "shadow_color"):
            color = self.style.get(key)
            if color and not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                raise ValueError(f"Invalid {key}")
        for key, points in self.keyframes.items():
            if key not in {"x", "y", "rotation", "opacity", "scale"}:
                raise ValueError("Unknown keyframe property")
            last = -1.0
            for point in points:
                t, v = float(point["time"]), float(point["value"])
                if not math.isfinite(t) or not math.isfinite(v) or t <= last or t < 0:
                    raise ValueError("Keyframes must be finite, unique and sorted")
                last = t


@dataclass
class Composition:
    clips: list[Clip] = field(default_factory=list)
    layers: list[Layer] = field(default_factory=list)
    width: int = 1280
    height: int = 720
    fps: int = 30
    fit: str = "fit"
    mute_original: bool = False
    audio: list[dict] = field(default_factory=list)
    duration_target: float | None = None
    transition: float = 0
    encoder: str = "auto"
    quality: int = 22
    seed: int = 0
    subtitle_style: dict = field(default_factory=lambda: {"font_size": 32, "color": "#ffffff", "outline_color": "#000000", "outline": 2, "margin": 35})
    adjustments: dict = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def validate(self):
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Unsupported composition schema")
        if not 64 <= self.width <= 7680 or not 64 <= self.height <= 7680 or self.width % 2 or self.height % 2:
            raise ValueError("Canvas must have even dimensions between 64 and 7680")
        if not 1 <= self.fps <= 120 or self.fit not in {"fit", "crop", "blur"}:
            raise ValueError("Invalid FPS/fit mode")
        if self.encoder not in {"auto", "cpu", "nvidia", "intel", "amd"} or not 0 <= self.quality <= 51:
            raise ValueError("Invalid encoder/quality")
        if not math.isfinite(self.transition) or not 0 <= self.transition <= 5:
            raise ValueError("Invalid transition")
        if self.duration_target is not None and (not math.isfinite(self.duration_target) or self.duration_target <= 0):
            raise ValueError("Duration must be positive")
        for item in [*self.clips, *self.layers]:
            item.validate()
        ids = [item.id for item in [*self.clips, *self.layers]]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate clip/layer IDs")
        checked_payload(asdict(self))

    def to_dict(self):
        self.validate()
        return checked_payload(asdict(self))

    @classmethod
    def from_dict(cls, data):
        data = checked_payload(data)
        data["clips"] = [Clip(**item) for item in data.get("clips", [])]
        data["layers"] = [Layer(**item) for item in data.get("layers", [])]
        result = cls(**data)
        result.validate()
        return result
