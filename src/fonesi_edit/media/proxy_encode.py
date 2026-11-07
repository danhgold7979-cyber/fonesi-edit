"""Bounded FFmpeg video-proxy encoding and validation.

This module generates an encoded video-only proxy. It deliberately does not
implement Timeline playback or synchronized audio/video seek.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Callable

from fonesi_edit.jobs.process import run_owned, ProcessError, ProcessCanceled
from .proxy_cache import (
    PersistentProxyCache, ProxyCacheKey, ProxyCacheError, ProxyCacheCanceled,
)

_MAX_SOURCE_BYTES = 32 * 1024**3
_MAX_TOOL_BYTES = 1024**3
_MAX_PROXY_BYTES = 256 * 1024**2
_PROGRESS_LINE_BYTES = 4096
_PROGRESS_TOTAL_BYTES = 1024 * 1024


class ProxyEncodeError(RuntimeError):
    pass


class ProxyEncodeCanceled(ProxyEncodeError):
    pass


class ProxyEncodeRetirementUnknown(ProxyEncodeError):
    """Owned FFmpeg descendants may still be alive; staging must be retained."""


@dataclass(frozen=True)
class ProxySpec:
    width: int = 960
    height: int = 540
    fps_num: int = 30
    fps_den: int = 1
    codec: str = "libx264"
    pixel_format: str = "yuv420p"
    preset: str = "veryfast"
    crf: int = 28
    algorithm_version: str = "video-proxy-v1"

    def __post_init__(self):
        if type(self.width) is not int or not 16 <= self.width <= 1920:
            raise ProxyEncodeError("proxy width must be 16..1920")
        if type(self.height) is not int or not 16 <= self.height <= 1080:
            raise ProxyEncodeError("proxy height must be 16..1080")
        if type(self.fps_num) is not int or type(self.fps_den) is not int:
            raise ProxyEncodeError("FPS must be an exact positive rational")
        if not 1 <= Fraction(self.fps_num, self.fps_den) <= 60:
            raise ProxyEncodeError("proxy FPS must be between 1 and 60")
        if self.codec not in {"libx264", "mpeg4"} or self.pixel_format != "yuv420p":
            raise ProxyEncodeError("only reviewed H.264 or MPEG-4/yuv420p profiles are allowed")
        if self.preset not in {"ultrafast", "veryfast", "faster"}:
            raise ProxyEncodeError("unsupported proxy preset")
        if type(self.crf) is not int or not 18 <= self.crf <= 35:
            raise ProxyEncodeError("CRF must be 18..35")
        if self.algorithm_version != "video-proxy-v1":
            raise ProxyEncodeError("unknown proxy algorithm version")


@dataclass(frozen=True)
class ProxyProgress:
    frame: int | None
    fps: float | None
    out_time_us: int | None
    speed: str | None
    progress: str | None


@dataclass(frozen=True)
class EncodedVideoProxy:
    path: Path
    cache_key: ProxyCacheKey
    payload_sha256: str
    size_bytes: int
    duration: Fraction
    width: int
    height: int
    codec: str
    pixel_format: str
    cache_hit: bool = False


def _regular_file(path: Path, *, maximum: int) -> tuple[int, int, int, int]:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ProxyEncodeError("source/tool path is unavailable") from exc
    if path.is_symlink() or not path.is_file() or info.st_size <= 0 or info.st_size > maximum:
        raise ProxyEncodeError("source/tool must be a bounded regular file")
    if getattr(info, "st_file_attributes", 0) & getattr(__import__("stat"), "FILE_ATTRIBUTE_REPARSE_POINT", 0):
        raise ProxyEncodeError("source/tool reparse points are refused")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _sha256_file(path: Path, *, maximum: int, cancel: Callable[[], bool]) -> tuple[str, tuple]:
    before = _regular_file(path, maximum=maximum)
    digest = sha256()
    total = 0
    try:
        with path.open("rb") as stream:
            while True:
                if cancel():
                    raise ProxyEncodeCanceled("proxy encoding canceled during fingerprint")
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > maximum:
                    raise ProxyEncodeError("source/tool exceeds fingerprint bound")
                digest.update(chunk)
    except OSError as exc:
        raise ProxyEncodeError("cannot fingerprint source/tool") from exc
    after = _regular_file(path, maximum=maximum)
    if before != after or total != before[2]:
        raise ProxyEncodeError("source/tool changed while fingerprinting")
    return digest.hexdigest(), after


def _safe_fraction(value: str) -> Fraction | None:
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError, TypeError):
        return None
    return result if result > 0 else None


def build_proxy_command(ffmpeg: Path | str, source: Path | str, output: Path | str,
                        *, stream_index: int, spec: ProxySpec) -> list[str]:
    ffmpeg, source, output = Path(ffmpeg), Path(source), Path(output)
    if not ffmpeg.is_absolute() or not source.is_absolute() or not output.is_absolute():
        raise ProxyEncodeError("FFmpeg, source and output paths must be absolute")
    if type(stream_index) is not int or not 0 <= stream_index <= 2**31 - 1:
        raise ProxyEncodeError("explicit non-negative video stream index required")
    fps = f"{spec.fps_num}/{spec.fps_den}"
    vf = (f"scale={spec.width}:{spec.height}:force_original_aspect_ratio=decrease,"
          f"pad={spec.width}:{spec.height}:(ow-iw)/2:(oh-ih)/2,"
          f"setsar=1,fps={fps},format={spec.pixel_format}")
    return [
        str(ffmpeg), "-nostdin", "-hide_banner", "-loglevel", "error",
        "-y", "-protocol_whitelist", "file,pipe",
        "-i", str(source), "-map", f"0:{stream_index}", "-an", "-sn", "-dn",
        "-vf", vf, "-c:v", spec.codec, "-preset", spec.preset,
        "-crf", str(spec.crf), "-pix_fmt", spec.pixel_format,
        "-movflags", "+faststart", "-f", "mp4",
        "-progress", "pipe:1", "-nostats", str(output),
    ]


class _ProgressParser:
    def __init__(self, callback):
        self.callback = callback
        self.pending = bytearray()
        self.total = 0
        self.fields: dict[str, str] = {}

    def feed(self, chunk: bytes):
        if type(chunk) is not bytes:
            raise ProxyEncodeError("FFmpeg progress chunk must be bytes")
        self.total += len(chunk)
        if self.total > _PROGRESS_TOTAL_BYTES:
            raise ProxyEncodeError("FFmpeg progress output exceeds bound")
        self.pending.extend(chunk)
        if len(self.pending) > _PROGRESS_LINE_BYTES and b"\n" not in self.pending:
            raise ProxyEncodeError("FFmpeg progress line exceeds bound")
        while b"\n" in self.pending:
            raw, _, rest = self.pending.partition(b"\n")
            self.pending[:] = rest
            if len(raw) > _PROGRESS_LINE_BYTES:
                raise ProxyEncodeError("FFmpeg progress line exceeds bound")
            line = raw.rstrip(b"\r").decode("ascii", "strict")
            if "=" not in line:
                raise ProxyEncodeError("malformed FFmpeg progress record")
            key, value = line.split("=", 1)
            if not re.fullmatch(r"[a-z_]{1,32}", key) or len(value) > 128:
                raise ProxyEncodeError("invalid FFmpeg progress field")
            self.fields[key] = value
            if key == "progress":
                frame = self.fields.get("frame")
                fps = self.fields.get("fps")
                out_time = self.fields.get("out_time_us")
                parsed_fps = None
                try:
                    candidate = float(fps) if fps is not None else None
                    if candidate is not None and math.isfinite(candidate) and candidate >= 0:
                        parsed_fps = candidate
                except ValueError:
                    pass
                parsed_frame = int(frame) if frame and frame.isdigit() else None
                parsed_time = int(out_time) if out_time and out_time.isdigit() else None
                if self.callback is not None:
                    self.callback(ProxyProgress(parsed_frame, parsed_fps, parsed_time,
                                                self.fields.get("speed"), value))
                self.fields.clear()


def _probe_proxy(ffprobe: Path, output: Path, *, cancel, timeout: float, expected_codec: str = "h264") -> tuple[Fraction, int, int]:
    args = [str(ffprobe), "-v", "error", "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,pix_fmt",
            "-of", "json", str(output)]
    try:
        result = run_owned(args, cancel=cancel, timeout=min(timeout, 30),
                           max_output_bytes=256 * 1024)
    except ProcessCanceled as exc:
        raise ProxyEncodeCanceled("proxy validation canceled") from exc
    except ProcessError as exc:
        if "retirement unconfirmed" in str(exc).lower() or "job remains active" in str(exc).lower():
            raise ProxyEncodeRetirementUnknown(str(exc)) from exc
        raise ProxyEncodeError("ffprobe could not validate the generated proxy") from exc
    if result.returncode != 0:
        raise ProxyEncodeError("ffprobe rejected the generated proxy")
    try:
        data = json.loads(result.stdout.decode("utf-8"))
        streams = data["streams"]
        fmt = data["format"]
        video = [s for s in streams if s.get("codec_type") == "video"]
        if len(video) != 1:
            raise ValueError("expected exactly one video stream")
        stream = video[0]
        duration = _safe_fraction(fmt["duration"])
        width, height = stream["width"], stream["height"]
        if (duration is None or type(width) is not int or type(height) is not int
                or width < 1 or height < 1 or width > 1920 or height > 1080
                or stream.get("codec_name") != expected_codec
                or stream.get("pix_fmt") != "yuv420p"):
            raise ValueError("proxy metadata outside accepted profile")
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise ProxyEncodeError("generated proxy metadata is invalid") from exc
    return duration, width, height


def encode_video_proxy(source: Path | str, ffmpeg: Path | str, ffprobe: Path | str,
                       cache: PersistentProxyCache, *, expected_source_sha256: str,
                       stream_index: int, spec: ProxySpec = ProxySpec(),
                       cancel: Callable[[], bool] = lambda: False,
                       progress: Callable[[ProxyProgress], None] | None = None,
                       timeout: float = 900) -> EncodedVideoProxy:
    """Encode, validate and cache one video-only proxy; never modifies source."""
    source, ffmpeg, ffprobe = Path(source), Path(ffmpeg), Path(ffprobe)
    if not source.is_absolute() or not ffmpeg.is_absolute() or not ffprobe.is_absolute():
        raise ProxyEncodeError("source, FFmpeg and ffprobe paths must be absolute")
    if not isinstance(cache, PersistentProxyCache):
        raise ProxyEncodeError("validated persistent proxy cache required")
    if not callable(cancel) or (progress is not None and not callable(progress)):
        raise ProxyEncodeError("cancel/progress callbacks must be callable")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 1 <= timeout <= 3600:
        raise ProxyEncodeError("timeout must be finite and between 1 and 3600 seconds")
    source_hash, source_sig = _sha256_file(source, maximum=_MAX_SOURCE_BYTES, cancel=cancel)
    if source_hash != expected_source_sha256:
        raise ProxyEncodeError("source hash does not match the selected project asset")
    tool_hash, tool_sig = _sha256_file(ffmpeg, maximum=_MAX_TOOL_BYTES, cancel=cancel)
    probe_hash, probe_sig = _sha256_file(ffprobe, maximum=_MAX_TOOL_BYTES, cancel=cancel)
    identity = json.dumps({
        "profile": spec.__dict__, "ffprobe_sha256": probe_hash,
        "container": "mp4", "audio": "none",
    }, sort_keys=True, separators=(",", ":")).encode()
    algorithm = "v1-" + sha256(identity).hexdigest()[:61]
    key = ProxyCacheKey(source_hash, tool_hash, stream_index, spec.width, spec.height, algorithm)
    try:
        cached = cache.get(key)
    except ProxyCacheError:
        cached = None
    if cached is not None:
        # A cached payload is still independently probed; a manifest digest alone
        # is not evidence that the bytes are a decodable MP4.
        with tempfile.TemporaryDirectory(prefix="fonesi-proxy-hit-") as temp:
            cached_path = Path(temp) / "cached.mp4"
            cached_path.write_bytes(cached)
            duration, width, height = _probe_proxy(ffprobe, cached_path, cancel=cancel, timeout=timeout,
                                                       expected_codec="h264" if spec.codec == "libx264" else "mpeg4")
        if _sha256_file(source, maximum=_MAX_SOURCE_BYTES, cancel=cancel)[0] == source_hash:
            return EncodedVideoProxy(cache.root / key.cache_id / "proxy.bin", key,
                                     sha256(cached).hexdigest(), len(cached), duration,
                                     width, height, "h264", "yuv420p", True)
        raise ProxyEncodeError("source changed before cached proxy could be returned")
    root = cache.root
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ProxyEncodeError("unsafe cache staging root")
    staging_dir = Path(tempfile.mkdtemp(prefix=".video-proxy-stage-", dir=root))
    staged = staging_dir / "proxy.mp4"
    parser = _ProgressParser(progress)
    try:
        if cancel():
            raise ProxyEncodeCanceled("proxy encoding canceled before launch")
        command = build_proxy_command(ffmpeg, source, staged, stream_index=stream_index, spec=spec)
        try:
            result = run_owned(command, cancel=cancel, timeout=timeout,
                               max_output_bytes=1024 * 1024, on_stdout=parser.feed)
        except ProcessCanceled as exc:
            raise ProxyEncodeCanceled("proxy encoding canceled") from exc
        except ProcessError as exc:
            if "retirement unconfirmed" in str(exc).lower() or "job remains active" in str(exc).lower():
                raise ProxyEncodeRetirementUnknown(str(exc)) from exc
            raise ProxyEncodeError("FFmpeg proxy encoding failed") from exc
        if result.returncode != 0:
            raise ProxyEncodeError("FFmpeg proxy encoder returned a non-zero exit code")
        if cancel():
            raise ProxyEncodeCanceled("proxy encoding canceled before validation")
        if not staged.is_file() or staged.is_symlink() or not 1 <= staged.stat().st_size <= _MAX_PROXY_BYTES:
            raise ProxyEncodeError("FFmpeg did not produce a bounded proxy file")
        duration, width, height = _probe_proxy(ffprobe, staged, cancel=cancel, timeout=timeout,
                                                      expected_codec="h264" if spec.codec == "libx264" else "mpeg4")
        if _regular_file(source, maximum=_MAX_SOURCE_BYTES) != source_sig:
            raise ProxyEncodeError("source changed during proxy encoding")
        if _regular_file(ffmpeg, maximum=_MAX_TOOL_BYTES) != tool_sig or _regular_file(ffprobe, maximum=_MAX_TOOL_BYTES) != probe_sig:
            raise ProxyEncodeError("FFmpeg/ffprobe changed during proxy encoding")
        payload = staged.read_bytes()
        if len(payload) != staged.stat().st_size or sha256(payload).hexdigest() == source_hash:
            raise ProxyEncodeError("proxy payload validation failed")
        if cancel():
            raise ProxyEncodeCanceled("proxy encoding canceled before cache publication")
        try:
            cache.put(key, payload, cancel=cancel)
        except ProxyCacheCanceled as exc:
            raise ProxyEncodeCanceled("proxy cache publication canceled") from exc
        except ProxyCacheError as exc:
            raise ProxyEncodeError("proxy cache publication failed") from exc
        # Return a cache-owned path only through the content-addressed API; caller
        # obtains bytes with cache.get(key), avoiding a temporary-path lifetime bug.
        return EncodedVideoProxy(cache.root / key.cache_id / "proxy.bin", key,
                                 sha256(payload).hexdigest(), len(payload), duration,
                                 width, height, spec.codec, "yuv420p", False)
    except ProxyEncodeRetirementUnknown:
        # Never remove staging while an owned process/job may still be alive.
        raise
    finally:
        # run_owned guarantees retirement before returning/raising except the
        # explicit unknown-retirement path, which intentionally retains staging.
        if not isinstance(__import__("sys").exc_info()[1], ProxyEncodeRetirementUnknown):
            import shutil
            shutil.rmtree(staging_dir, ignore_errors=True)
