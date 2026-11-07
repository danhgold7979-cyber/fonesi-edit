"""Persistent content-addressed cache for already-encoded preview proxy bytes.

This module does not generate proxies or play media. Callers must supply bytes
from an independently owned and validated encoder operation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
from threading import RLock
from typing import Callable


class ProxyCacheError(RuntimeError):
    """A proxy cache operation failed closed."""


class ProxyCacheCanceled(ProxyCacheError):
    """Publication was canceled before an entry became visible."""


@dataclass(frozen=True)
class ProxyCacheKey:
    source_sha256: str
    tool_sha256: str
    stream_index: int
    width: int
    height: int
    algorithm_version: str

    def __post_init__(self) -> None:
        for name in ("source_sha256", "tool_sha256"):
            value = getattr(self, name)
            if (type(value) is not str or len(value) != 64
                    or any(ch not in "0123456789abcdef" for ch in value)):
                raise ProxyCacheError(f"{name} must be a lowercase SHA-256 digest")
        if type(self.stream_index) is not int or not 0 <= self.stream_index <= 2**31 - 1:
            raise ProxyCacheError("stream_index must be a non-negative 32-bit integer")
        if (type(self.width) is not int or type(self.height) is not int
                or not 1 <= self.width <= 3840 or not 1 <= self.height <= 2160):
            raise ProxyCacheError("proxy dimensions exceed the 3840x2160 bound")
        if (type(self.algorithm_version) is not str or not self.algorithm_version
                or len(self.algorithm_version) > 64
                or any(ord(ch) < 32 for ch in self.algorithm_version)):
            raise ProxyCacheError("algorithm_version must be a bounded printable string")

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def cache_id(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode()
        return sha256(encoded).hexdigest()


class PersistentProxyCache:
    """Atomic, bounded cache of encoded proxy bytes under an explicit root."""

    _SCHEMA = 1
    _MANIFEST = "manifest.json"
    _PAYLOAD = "proxy.bin"
    _LOCK = RLock()

    def __init__(self, root: Path | str, *, max_entry_bytes: int = 512 * 1024 * 1024):
        self.root = Path(root)
        if not self.root.is_absolute() or ".." in self.root.parts:
            raise ProxyCacheError("cache root must be absolute and contain no parent traversal")
        if (type(max_entry_bytes) is not int
                or not 1 <= max_entry_bytes <= 2 * 1024 * 1024 * 1024):
            raise ProxyCacheError("invalid cache entry size bound")
        self.max_entry_bytes = max_entry_bytes
        self._ensure_directory(self.root)

    @staticmethod
    def _is_reparse(info) -> bool:
        return bool(getattr(info, "st_file_attributes", 0) & 0x400)

    @classmethod
    def _ensure_directory(cls, path: Path) -> None:
        current = Path(path.anchor)
        try:
            root_info = current.lstat()
        except OSError as exc:
            raise ProxyCacheError("cache filesystem root is unavailable") from exc
        if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode) or cls._is_reparse(root_info):
            raise ProxyCacheError("cache root traverses an unsafe filesystem root")
        for part in path.parts[1:]:
            current = current / part
            try:
                info = current.lstat()
            except FileNotFoundError:
                try:
                    current.mkdir()
                except FileExistsError:
                    pass
                info = current.lstat()
            except OSError as exc:
                raise ProxyCacheError("cache directory is inaccessible") from exc
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or cls._is_reparse(info):
                raise ProxyCacheError("cache directory contains a symlink or reparse point")

    @classmethod
    def _regular_file(cls, path: Path) -> bool:
        try:
            info = path.lstat()
        except OSError:
            return False
        return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode) and not cls._is_reparse(info)

    def _entry(self, key: ProxyCacheKey) -> Path:
        if not isinstance(key, ProxyCacheKey):
            raise ProxyCacheError("validated ProxyCacheKey required")
        return self.root / key.cache_id

    def get(self, key: ProxyCacheKey) -> bytes | None:
        entry = self._entry(key)
        with self._LOCK:
            try:
                info = entry.lstat()
            except FileNotFoundError:
                return None
            except OSError as exc:
                raise ProxyCacheError("cache entry cannot be inspected") from exc
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or self._is_reparse(info):
                raise ProxyCacheError("cache entry is not a safe directory")
            manifest_path = entry / self._MANIFEST
            payload_path = entry / self._PAYLOAD
            if not self._regular_file(manifest_path) or not self._regular_file(payload_path):
                return None
            try:
                if manifest_path.stat().st_size > 16 * 1024:
                    return None
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                payload_size = payload_path.stat().st_size
                if (manifest.get("schema") != self._SCHEMA
                        or manifest.get("key") != key.to_dict()
                        or type(manifest.get("size")) is not int
                        or manifest["size"] != payload_size
                        or not 1 <= payload_size <= self.max_entry_bytes):
                    return None
                with payload_path.open("rb") as stream:
                    payload = stream.read(self.max_entry_bytes + 1)
                if len(payload) != payload_size or len(payload) > self.max_entry_bytes:
                    return None
            except (OSError, ValueError, TypeError, AttributeError):
                return None
            if sha256(payload).hexdigest() != manifest.get("payload_sha256"):
                return None
            return payload

    def put(self, key: ProxyCacheKey, payload: bytes, *, cancel: Callable[[], bool] = lambda: False) -> bool:
        entry = self._entry(key)
        if type(payload) is not bytes or not 1 <= len(payload) <= self.max_entry_bytes:
            raise ProxyCacheError("encoded proxy payload is empty or exceeds the configured bound")
        if not callable(cancel):
            raise ProxyCacheError("cancel must be callable")
        if cancel():
            raise ProxyCacheCanceled("proxy cache publication canceled before staging")
        with self._LOCK:
            staging = Path(tempfile.mkdtemp(prefix=".proxy-pending-", dir=self.root))
            backup = self.root / (".proxy-backup-" + key.cache_id)
            try:
                payload_path = staging / self._PAYLOAD
                with payload_path.open("xb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                manifest = {
                    "schema": self._SCHEMA,
                    "key": key.to_dict(),
                    "size": len(payload),
                    "payload_sha256": sha256(payload).hexdigest(),
                }
                manifest_path = staging / self._MANIFEST
                with manifest_path.open("x", encoding="utf-8", newline="\n") as stream:
                    json.dump(manifest, stream, sort_keys=True, separators=(",", ":"))
                    stream.flush()
                    os.fsync(stream.fileno())
                if cancel():
                    raise ProxyCacheCanceled("proxy cache publication canceled before commit")
                if entry.exists():
                    info = entry.lstat()
                    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or self._is_reparse(info):
                        raise ProxyCacheError("refusing to replace an unsafe cache entry")
                    if backup.exists():
                        raise ProxyCacheError("stale cache backup requires manual inspection")
                    os.replace(entry, backup)
                try:
                    os.replace(staging, entry)
                except OSError:
                    if backup.exists() and not entry.exists():
                        os.replace(backup, entry)
                    raise
                if backup.exists():
                    shutil.rmtree(backup)
                return True
            except ProxyCacheError:
                raise
            except OSError as exc:
                raise ProxyCacheError("atomic proxy cache publication failed") from exc
            finally:
                if staging.exists():
                    shutil.rmtree(staging, ignore_errors=True)

    def invalidate(self, key: ProxyCacheKey) -> bool:
        entry = self._entry(key)
        with self._LOCK:
            try:
                info = entry.lstat()
            except FileNotFoundError:
                return False
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or self._is_reparse(info):
                raise ProxyCacheError("refusing to invalidate an unsafe cache entry")
            shutil.rmtree(entry)
            return True

    def invalidate_source(self, source_sha256: str) -> int:
        if (type(source_sha256) is not str or len(source_sha256) != 64
                or any(ch not in "0123456789abcdef" for ch in source_sha256)):
            raise ProxyCacheError("source_sha256 must be a lowercase SHA-256 digest")
        removed = 0
        with self._LOCK:
            for entry in self.root.iterdir():
                info = entry.lstat()
                if stat.S_ISLNK(info.st_mode) or self._is_reparse(info):
                    raise ProxyCacheError("cache root contains an unsafe entry")
                if not stat.S_ISDIR(info.st_mode) or not self._regular_file(entry / self._MANIFEST):
                    continue
                try:
                    if (entry / self._MANIFEST).stat().st_size > 16 * 1024:
                        continue
                    manifest = json.loads((entry / self._MANIFEST).read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                key_data = manifest.get("key")
                if (manifest.get("schema") != self._SCHEMA or type(key_data) is not dict
                        or key_data.get("source_sha256") != source_sha256):
                    continue
                try:
                    validated_key = ProxyCacheKey(**key_data)
                except (TypeError, ProxyCacheError):
                    continue
                if entry.name == validated_key.cache_id:
                    shutil.rmtree(entry)
                    removed += 1
        return removed
