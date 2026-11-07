"""Bounded FFmpeg PCM decode worker for a future Qt audio output backend.

The worker returns interleaved float PCM only. It does not open an audio device,
schedule samples against a video clock, resample, mix tracks or claim playback.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path
import struct
from typing import Callable

from fonesi_edit.jobs.process import run_owned, ProcessError, ProcessCanceled


class AudioDecodeError(RuntimeError):
    pass


class AudioDecodeCanceled(AudioDecodeError):
    pass


class AudioDecodeRetirementUnknown(AudioDecodeError):
    pass


@dataclass(frozen=True)
class PCMBuffer:
    source_sha256: str
    stream_index: int
    sample_rate: int
    channels: int
    sample_count: int
    samples: tuple[float, ...]
    duration_samples: int

    @property
    def duration_seconds(self) -> float:
        return self.duration_samples / self.sample_rate


def _fingerprint(path: Path, expected: str) -> None:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise AudioDecodeError("Audio source must be an absolute regular file.")
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise AudioDecodeError("Audio source fingerprint does not match project asset.")


def decode_audio_pcm(
    source: Path | str, ffmpeg: Path | str, *, expected_sha256: str,
    stream_index: int, sample_rate: int = 48000, channels: int = 2,
    source_start_seconds: float = 0.0, duration_seconds: float = 5.0,
    max_output_bytes: int = 8 * 1024 * 1024,
    cancel: Callable[[], bool] = lambda: False, timeout: float = 30.0,
) -> PCMBuffer:
    source, ffmpeg = Path(source), Path(ffmpeg)
    if type(stream_index) is not int or stream_index < 0:
        raise AudioDecodeError("An explicit non-negative audio stream index is required.")
    if type(sample_rate) is not int or not 8000 <= sample_rate <= 96000:
        raise AudioDecodeError("Sample rate must be between 8 kHz and 96 kHz.")
    if type(channels) is not int or channels not in (1, 2):
        raise AudioDecodeError("Only mono or stereo PCM is currently supported.")
    if (not math.isfinite(source_start_seconds) or source_start_seconds < 0
            or not math.isfinite(duration_seconds) or not 0 < duration_seconds <= 5):
        raise AudioDecodeError("Audio decode window must be finite, positive and at most 5 seconds.")
    if type(max_output_bytes) is not int or not 1 <= max_output_bytes <= 8 * 1024 * 1024:
        raise AudioDecodeError("PCM output byte cap must be between 1 and 8 MiB.")
    if not math.isfinite(timeout) or not 1 <= timeout <= 120:
        raise AudioDecodeError("Audio decoder timeout must be 1..120 seconds.")
    if cancel():
        raise AudioDecodeCanceled("Audio decode canceled before launch.")
    _fingerprint(source, expected_sha256)
    if ffmpeg.is_symlink() or not ffmpeg.is_file() or not ffmpeg.is_absolute():
        raise AudioDecodeError("FFmpeg must be an absolute regular file.")
    command = [
        str(ffmpeg), "-nostdin", "-hide_banner", "-v", "error",
        "-ss", format(source_start_seconds, ".9f"), "-i", str(source),
        "-map", f"0:{stream_index}", "-vn", "-sn", "-dn",
        "-t", format(duration_seconds, ".9f"),
        "-ac", str(channels), "-ar", str(sample_rate),
        "-f", "f32le", "-acodec", "pcm_f32le", "pipe:1",
    ]
    try:
        result = run_owned(command, cancel=cancel, timeout=timeout,
                           max_output_bytes=max_output_bytes)
    except ProcessCanceled as exc:
        raise AudioDecodeCanceled("Audio decode canceled.") from exc
    except ProcessError as exc:
        message = str(exc).lower()
        if "retirement unconfirmed" in message or "job remains active" in message:
            raise AudioDecodeRetirementUnknown("Audio decoder process retirement is unknown.") from exc
        raise AudioDecodeError("FFmpeg audio decode failed.") from exc
    if result.returncode != 0:
        raise AudioDecodeError("FFmpeg audio decoder returned a non-zero exit code.")
    if len(result.stdout) % (4 * channels):
        raise AudioDecodeError("Decoded PCM payload is not aligned to complete sample frames.")
    if len(result.stdout) > max_output_bytes:
        raise AudioDecodeError("Decoded PCM payload exceeds configured output cap.")
    count = len(result.stdout) // (4 * channels)
    samples = struct.unpack("<" + "f" * (count * channels), result.stdout) if count else ()
    if any(not math.isfinite(sample) for sample in samples):
        raise AudioDecodeError("Decoded PCM contains non-finite samples.")
    _fingerprint(source, expected_sha256)
    return PCMBuffer(expected_sha256, stream_index, sample_rate, channels,
                     count, tuple(samples), count)
