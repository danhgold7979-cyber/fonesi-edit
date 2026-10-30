"""Strict, versioned preset import/export contract."""
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
import json
import unicodedata

from .domain import Composition

PRESET_SCHEMA_VERSION = 1
MAX_PRESET_BYTES = 2 * 1024 * 1024
_ENVELOPE_KEYS = frozenset({"schema_version", "name", "composition"})
_INVALID_NAME_CHARS = frozenset('<>:"/\\|?*')
_RESERVED_WINDOWS_NAMES = frozenset({"CON", "PRN", "AUX", "NUL"})


@dataclass(frozen=True)
class ParsedPreset:
    name: str
    composition: Composition
    missing_assets: tuple[str, ...]


def validate_preset_name(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Preset name must be text")
    name = value.strip()
    if not name or len(name) > 120:
        raise ValueError("Preset name must contain 1 to 120 characters")
    if name in {".", ".."} or name[-1] in {" ", "."}:
        raise ValueError("Preset name cannot end with a space or dot")
    if any(char in _INVALID_NAME_CHARS or unicodedata.category(char) == "Cc" for char in name):
        raise ValueError("Preset name contains a character that is not portable")
    stem = name.split(".", 1)[0].upper()
    if stem in _RESERVED_WINDOWS_NAMES or (
        len(stem) == 4 and stem[:3] in {"COM", "LPT"} and stem[3] in "123456789"
    ):
        raise ValueError("Preset name is reserved by Windows")
    return name


def build_preset_document(composition: Composition, name: str) -> dict:
    """Create a validated schema-v1 document without source clip identity."""
    if not isinstance(composition, Composition):
        raise TypeError("Expected a Composition")
    safe_name = validate_preset_name(name)
    snapshot = Composition.from_dict(composition.to_dict())
    snapshot.clips = []
    for layer in snapshot.layers:
        layer.clip_ids = []
    return {
        "schema_version": PRESET_SCHEMA_VERSION,
        "name": safe_name,
        "composition": snapshot.to_dict(),
    }


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_non_finite(value):
    raise ValueError(f"Non-finite JSON number is not allowed: {value}")


def _resource_references(composition: Composition):
    references = []
    for index, layer in enumerate(composition.layers, start=1):
        if layer.path is not None:
            references.append((f"Layer {index} media", layer.path))
        font_path = layer.style.get("font_file")
        if font_path is not None:
            references.append((f"Layer {index} font", font_path))
    for index, track in enumerate(composition.audio, start=1):
        references.append((f"Audio track {index}", track.get("path")))
    return references


def _missing_assets(composition: Composition) -> tuple[str, ...]:
    missing = []
    for label, raw_path in _resource_references(composition):
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(f"{label} path must be a non-empty string")
        try:
            exists = Path(raw_path).is_file()
        except (OSError, ValueError):
            exists = False
        if not exists:
            filename = Path(raw_path).name or PureWindowsPath(raw_path).name or "invalid path"
            missing.append(f"{label}: {filename}")
    return tuple(missing)


def parse_preset_bytes(raw: bytes | bytearray) -> ParsedPreset:
    """Parse and validate an untrusted preset payload before persistence."""
    if not isinstance(raw, (bytes, bytearray)):
        raise TypeError("Preset content must be bytes")
    if len(raw) > MAX_PRESET_BYTES:
        raise ValueError(f"Preset file exceeds the {MAX_PRESET_BYTES}-byte limit")
    try:
        text = bytes(raw).decode("utf-8")
        document = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_non_finite,
        )
    except UnicodeDecodeError as exc:
        raise ValueError("Preset file must be valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Preset file is not valid JSON") from exc

    if not isinstance(document, dict):
        raise ValueError("Preset document must be a JSON object")
    if set(document) != _ENVELOPE_KEYS:
        raise ValueError("Preset document has missing or unknown fields")
    version = document["schema_version"]
    if type(version) is not int or version != PRESET_SCHEMA_VERSION:
        raise ValueError("Preset schema version is not supported")
    name = validate_preset_name(document["name"])
    composition_data = document["composition"]
    if not isinstance(composition_data, dict):
        raise ValueError("Preset composition must be a JSON object")
    try:
        composition = Composition.from_dict(composition_data)
    except (TypeError, KeyError, AttributeError, OverflowError) as exc:
        raise ValueError("Preset composition is invalid") from exc
    if composition.clips:
        raise ValueError("Preset must not contain source video clips")
    if any(layer.clip_ids for layer in composition.layers):
        raise ValueError("Preset layers must not reference source clip IDs")
    missing = _missing_assets(composition)
    return ParsedPreset(name, composition, missing)


def parse_preset_file(path: str | Path) -> ParsedPreset:
    source = Path(path)
    try:
        if source.stat().st_size > MAX_PRESET_BYTES:
            raise ValueError(f"Preset file exceeds the {MAX_PRESET_BYTES}-byte limit")
        raw = source.read_bytes()
    except OSError as exc:
        raise ValueError(f"Cannot read preset file: {exc}") from exc
    return parse_preset_bytes(raw)
