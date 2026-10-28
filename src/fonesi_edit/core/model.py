"""Serializable, Qt-independent contracts. Time is integer microseconds, [in, out)."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from typing import Any
from uuid import uuid4
import copy
import json

SCHEMA_VERSION = 1
US = 1_000_000
SECRET_KEYS = {'password', 'cookie', 'cookies', 'token', 'access_token', 'refresh_token', 'api_key', 'authorization', 'session_token'}


def uid() -> str:
    return str(uuid4())


def reject_secrets(value: Any, trail: str = '') -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower().replace('-', '_') in SECRET_KEYS:
                raise ValueError(f'Secret field is forbidden in project/snapshot: {trail}{key}')
            reject_secrets(item, f'{trail}{key}.')
    elif isinstance(value, list):
        for item in value:
            reject_secrets(item, trail)


def canonical(value: Any) -> str:
    reject_secrets(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value: Any) -> str:
    return sha256(canonical(value).encode()).hexdigest()


def seconds(value: int) -> str:
    return f'{value / US:.6f}'


@dataclass
class TimeMap:
    source_in: int
    source_out: int
    speed: str = '1'
    offset: int = 0

    def __post_init__(self):
        if self.source_in < 0 or self.source_out <= self.source_in or self.offset < 0 or Fraction(self.speed) <= 0:
            raise ValueError('Invalid time map')

    @property
    def duration(self) -> int:
        return round(Fraction(self.source_out - self.source_in) / Fraction(self.speed))

    def point(self, source_time: int) -> int:
        return self.offset + round(Fraction(source_time - self.source_in) / Fraction(self.speed))

    def interval(self, start: int, end: int) -> tuple[int, int] | None:
        a, b = max(start, self.source_in), min(end, self.source_out)
        return (self.point(a), self.point(b)) if a < b else None


@dataclass
class Asset:
    path: str
    id: str = field(default_factory=uid)
    fingerprint: str = ''
    duration: int = 0
    width: int = 0
    height: int = 0
    fps: str = '25'
    has_audio: bool = False
    source_id: str = ''


@dataclass
class Clip:
    asset_id: str
    source_in: int
    source_out: int
    offset: int = 0
    speed: str = '1'
    id: str = field(default_factory=uid)
    fit: str = 'fit'
    flip: bool = False
    rotation: int = 0
    brightness: float = 0
    contrast: float = 1
    saturation: float = 1
    gamma: float = 1
    volume: float = 1
    locked: bool = False

    @property
    def time_map(self) -> TimeMap:
        return TimeMap(self.source_in, self.source_out, self.speed, self.offset)


@dataclass
class Keyframe:
    time: int
    value: float
    easing: str = 'linear'


def interpolate(base: float, keys: list[Keyframe], t: int) -> float:
    keys = sorted(keys, key=lambda k: k.time)
    if not keys:
        return base
    if t <= keys[0].time:
        return keys[0].value
    for a, b in zip(keys, keys[1:]):
        if t == b.time:
            return b.value
        if t < b.time:
            u = (t - a.time) / max(1, b.time - a.time)
            if a.easing == 'ease-in':
                u *= u
            elif a.easing == 'ease-out':
                u = 1 - (1-u)**2
            elif a.easing == 'ease-in-out':
                u = u*u*(3-2*u)
            elif a.easing != 'linear':
                raise ValueError(f'Unsupported easing {a.easing}')
            return a.value + (b.value-a.value)*u
    return keys[-1].value


@dataclass
class Layer:
    kind: str = 'text'
    id: str = field(default_factory=uid)
    name: str = 'Chữ'
    x: float = .1
    y: float = .1
    width: float = .4
    height: float = .12
    rotation: float = 0
    opacity: float = 1
    start: int = 0
    end: int = 5*US
    z: int = 0
    visible: bool = True
    locked: bool = False
    group: str = ''
    text: str = 'Fonesi Edit'
    asset_path: str = ''
    style: dict = field(default_factory=lambda: {'font_size': 40, 'fill': '#ffffff', 'stroke': '#000000', 'stroke_width': 2, 'align': 'center'})
    keyframes: dict[str, list[Keyframe]] = field(default_factory=dict)

    def at(self, t: int) -> dict[str, float]:
        return {k: interpolate(getattr(self, k), self.keyframes.get(k, []), t-self.start)
                for k in ('x', 'y', 'width', 'height', 'rotation', 'opacity')}


@dataclass
class Cue:
    start: int
    end: int
    text: str
    id: str = field(default_factory=uid)
    translation: str = ''
    language: str = 'und'
    locked: bool = False


@dataclass
class AudioTrack:
    path: str
    id: str = field(default_factory=uid)
    role: str = 'music'
    start: int = 0
    trim_in: int = 0
    trim_out: int = 0
    gain: float = 1
    fade_in: int = 0
    fade_out: int = 0
    loop: bool = False
    muted: bool = False
    solo: bool = False


@dataclass
class Project:
    name: str = 'Dự án mới'
    id: str = field(default_factory=uid)
    schema_version: int = SCHEMA_VERSION
    width: int = 1280
    height: int = 720
    fps: str = '25'
    seed: int = 0
    assets: list[Asset] = field(default_factory=list)
    clips: list[Clip] = field(default_factory=list)
    layers: list[Layer] = field(default_factory=list)
    cues: list[Cue] = field(default_factory=list)
    audio: list[AudioTrack] = field(default_factory=list)
    markers: list[int] = field(default_factory=list)
    settings: dict = field(default_factory=lambda: {'subtitle_target': 'vi', 'missing_subtitle': 'continue', 'burn_subtitles': True, 'hardware': 'auto'})

    @property
    def duration(self) -> int:
        return max((c.offset+c.time_map.duration for c in self.clips), default=0)

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError('Unsupported project version; original file was not modified')
        if self.width <= 0 or self.height <= 0 or self.width % 2 or self.height % 2 or Fraction(self.fps) <= 0:
            raise ValueError('Canvas must be positive even dimensions and FPS > 0')
        ids = [x.id for group in (self.assets, self.clips, self.layers, self.cues, self.audio) for x in group]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate object IDs')
        assets = {a.id for a in self.assets}
        for c in self.clips:
            c.time_map
            if c.asset_id not in assets:
                raise ValueError('Clip references missing asset')
            if c.fit not in {'fit', 'crop', 'blur'}:
                raise ValueError('Unsupported fit mode')
        for x in [*self.layers, *self.cues]:
            if x.start < 0 or x.end <= x.start:
                raise ValueError('Invalid object interval')
        for layer in self.layers:
            if layer.kind not in {'text', 'logo', 'mask'}:
                raise ValueError('Unsupported layer type')
            if not all(isfinite(getattr(layer,k)) for k in ('x','y','width','height','rotation','opacity')):
                raise ValueError('Nonfinite transform')
            if layer.width <= 0 or layer.height <= 0 or not 0 <= layer.opacity <= 1:
                raise ValueError('Invalid layer dimensions or opacity')
        canonical(self.to_dict())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        reject_secrets(data)
        data = copy.deepcopy(data)
        for name, kind in [('assets', Asset), ('clips', Clip), ('cues', Cue), ('audio', AudioTrack)]:
            data[name] = [kind(**x) for x in data.get(name, [])]
        layers = []
        for x in data.get('layers', []):
            x['keyframes'] = {k: [Keyframe(**v) for v in vs] for k, vs in x.get('keyframes', {}).items()}
            layers.append(Layer(**x))
        data['layers'] = layers
        result = cls(**data)
        result.validate()
        return result


class CommandHistory:
    """UI gestures call begin once and commit once; preview updates do not add commands."""
    def __init__(self, project: Project):
        self.project = project
        self.undo_items: list[tuple[str, dict, dict]] = []
        self.redo_items: list[tuple[str, dict, dict]] = []
        self.pending: dict | None = None

    def begin(self):
        if self.pending is not None:
            raise RuntimeError('Nested gesture')
        self.pending = self.project.to_dict()

    def _restore(self, state: dict):
        restored = Project.from_dict(state)
        self.project.__dict__.clear()
        self.project.__dict__.update(restored.__dict__)

    def commit(self, label: str):
        if self.pending is None:
            raise RuntimeError('No gesture')
        self.project.validate()
        after = self.project.to_dict()
        if self.pending != after:
            self.undo_items.append((label, self.pending, after))
            self.redo_items.clear()
        self.pending = None

    def cancel(self):
        if self.pending is not None:
            self._restore(self.pending)
            self.pending = None

    def undo(self):
        self.cancel()
        if self.undo_items:
            item = self.undo_items.pop()
            self._restore(item[1]); self.redo_items.append(item)

    def redo(self):
        if self.redo_items:
            item = self.redo_items.pop()
            self._restore(item[2]); self.undo_items.append(item)


def apply_auto(current: dict, proposed: dict, overrides: set[str], locks: set[str]) -> tuple[dict, list[str]]:
    result = copy.deepcopy(current); changed = []
    for key, value in proposed.items():
        if key not in overrides | locks and result.get(key) != value:
            result[key] = copy.deepcopy(value); changed.append(key)
    return result, changed
