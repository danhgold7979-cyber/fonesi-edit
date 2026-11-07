"""Bounded FFmpeg RGB24 video-frame batch decoder.

The API returns a finite frame batch for a future playback queue. It is not a
continuous decoder, scheduler, renderer or Timeline playback implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path
from typing import Callable

from fonesi_edit.jobs.process import run_owned, ProcessError, ProcessCanceled


class VideoDecodeError(RuntimeError):
    pass


class VideoDecodeCanceled(VideoDecodeError):
    pass


class VideoDecodeRetirementUnknown(VideoDecodeError):
    pass


@dataclass(frozen=True)
class RGBVideoFrame:
    index: int
    width: int
    height: int
    pts_seconds: float
    rgb24: bytes


@dataclass(frozen=True)
class VideoFrameBatch:
    source_sha256: str
    stream_index: int
    width: int
    height: int
    frames: tuple[RGBVideoFrame, ...]
    complete: bool


def _hash_file(path: Path, expected: str, cancel: Callable[[], bool]) -> None:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise VideoDecodeError("Video source must be an absolute regular file.")
    digest = sha256()
    with path.open("rb") as stream:
        while True:
            if cancel():
                raise VideoDecodeCanceled("Video fingerprint canceled.")
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise VideoDecodeError("Video source fingerprint does not match project asset.")


def decode_video_frame_batch(
    source: Path | str, ffmpeg: Path | str, *, expected_sha256: str,
    stream_index: int, start_seconds: float, fps_num: int, fps_den: int = 1,
    frame_count: int = 8, width: int = 640, height: int = 360,
    max_output_bytes: int = 16 * 1024 * 1024,
    cancel: Callable[[], bool] = lambda: False, timeout: float = 30.0,
) -> VideoFrameBatch:
    source, ffmpeg = Path(source), Path(ffmpeg)
    if type(stream_index) is not int or stream_index < 0:
        raise VideoDecodeError("An explicit non-negative video stream index is required.")
    if (not math.isfinite(start_seconds) or start_seconds < 0 or
            type(fps_num) is not int or type(fps_den) is not int or
            fps_num <= 0 or fps_den <= 0 or fps_num / fps_den > 120):
        raise VideoDecodeError("Invalid bounded video start/FPS profile.")
    if type(frame_count) is not int or not 1 <= frame_count <= 32:
        raise VideoDecodeError("Frame batch must contain 1..32 frames.")
    if (type(width) is not int or type(height) is not int or
            not 16 <= width <= 1280 or not 16 <= height <= 720):
        raise VideoDecodeError("Video output dimensions exceed supported bounds.")
    frame_bytes = width * height * 3
    required_bytes = frame_bytes * frame_count
    if type(max_output_bytes) is not int or not required_bytes <= max_output_bytes <= 64 * 1024 * 1024:
        raise VideoDecodeError("Output byte cap must hold the requested frame batch and remain <=64 MiB.")
    if not math.isfinite(timeout) or not 1 <= timeout <= 120:
        raise VideoDecodeError("Video decoder timeout must be 1..120 seconds.")
    if cancel():
        raise VideoDecodeCanceled("Video decode canceled before launch.")
    _hash_file(source, expected_sha256, cancel)
    if not ffmpeg.is_absolute() or ffmpeg.is_symlink() or not ffmpeg.is_file():
        raise VideoDecodeError("FFmpeg must be an absolute regular file.")
    vf = (f"fps={fps_num}/{fps_den},"
          f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
          f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=rgb24")
    command = [
        str(ffmpeg), "-nostdin", "-hide_banner", "-v", "error",
        "-ss", format(start_seconds, ".9f"), "-i", str(source),
        "-map", f"0:{stream_index}", "-an", "-sn", "-dn",
        "-vf", vf, "-frames:v", str(frame_count),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
    ]
    try:
        result = run_owned(command, cancel=cancel, timeout=timeout,
                           max_output_bytes=max_output_bytes)
    except ProcessCanceled as exc:
        raise VideoDecodeCanceled("Video decode canceled.") from exc
    except ProcessError as exc:
        if "retirement unconfirmed" in str(exc).lower() or "job remains active" in str(exc).lower():
            raise VideoDecodeRetirementUnknown("Video decoder process retirement is unknown.") from exc
        raise VideoDecodeError("FFmpeg video decode failed.") from exc
    if result.returncode != 0:
        raise VideoDecodeError("FFmpeg video decoder returned a non-zero exit code.")
    if len(result.stdout) > max_output_bytes or len(result.stdout) % frame_bytes:
        raise VideoDecodeError("Raw RGB output is over limit or not aligned to complete frames.")
    count = len(result.stdout) // frame_bytes
    if not 1 <= count <= frame_count:
        raise VideoDecodeError("Decoder returned no frames or exceeded the requested frame count.")
    frames = tuple(
        RGBVideoFrame(
            index=i, width=width, height=height,
            pts_seconds=start_seconds + i * fps_den / fps_num,
            rgb24=result.stdout[i * frame_bytes:(i + 1) * frame_bytes],
        )
        for i in range(count)
    )
    _hash_file(source, expected_sha256, cancel)
    return VideoFrameBatch(expected_sha256, stream_index, width, height,
                           frames, complete=count == frame_count)
