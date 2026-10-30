"""Decoded PCM sample-peak/RMS measurements, independent of Qt and output hardware.

The input is unscaled decoded stream data, not post-QAudioOutput volume,
hardware amplifier level, acoustic SPL, or EBU true-peak/loudness.
"""
from dataclasses import dataclass
import math
import struct


@dataclass(frozen=True)
class AudioLevels:
    peak: float
    rms: float
    peak_dbfs: float
    rms_dbfs: float
    clipped_samples: int
    sample_count: int


def dbfs(amplitude: float) -> float:
    """Convert a nonnegative full-scale fraction to dBFS (silence = -inf)."""
    if not math.isfinite(amplitude) or amplitude < 0:
        raise ValueError("Invalid audio amplitude")
    return 20 * math.log10(amplitude) if amplitude else -math.inf


def meter_bar(db_level: float) -> int:
    """Map -60..0 dBFS onto a 0..600 UI bar; preserve over-0 values in text."""
    if math.isnan(db_level) or db_level == math.inf:
        raise ValueError("Invalid audio dBFS")
    if db_level == -math.inf:
        return 0
    return max(0, min(600, round((db_level + 60) * 10)))


def measure_pcm(data: bytes | bytearray | memoryview, sample_format: str,
                channels: int) -> AudioLevels:
    """Measure Qt interleaved PCM samples in native platform byte order.

    Signed integer formats use their signed full-scale denominator; UInt8
    silence is byte value 128. Float is not clamped to 1.0 so above-full-scale
    decoded values remain visible and count as clipped sample candidates.
    The 0.99 threshold is a *sample-peak warning*, not a true-peak detector.
    """
    formats = {"UInt8": ("B", 1, 128), "Int16": ("h", 2, 32768),
               "Int32": ("i", 4, 2147483648), "Float": ("f", 4, 1)}
    if sample_format not in formats:
        raise ValueError("Unsupported audio sample format")
    if type(channels) is not int or not 1 <= channels <= 32:
        raise ValueError("Invalid audio channel count")
    try:
        payload = memoryview(data)
        raw = payload.tobytes()
    except (TypeError, BufferError, ValueError) as exc:
        raise ValueError("Invalid PCM sample data") from exc
    code, width, scale = formats[sample_format]
    if len(raw) % (channels * width):
        raise ValueError("PCM buffer must contain complete interleaved frames")
    if not raw:
        return AudioLevels(0, 0, -math.inf, -math.inf, 0, 0)
    largest = 0.0
    squared = 0.0
    clipped = 0
    count = len(raw) // width
    for (sample,) in struct.iter_unpack("=" + code, raw):
        value = ((sample - 128) / scale if sample_format == "UInt8"
                 else sample / scale)
        if not math.isfinite(value):
            raise ValueError("Non-finite PCM sample")
        magnitude = abs(value)
        largest = max(largest, magnitude)
        squared += value * value
        if magnitude >= .99:
            clipped += 1
    rms = math.sqrt(squared / count)
    if not math.isfinite(rms):
        raise ValueError("Invalid PCM RMS")
    return AudioLevels(largest, rms, dbfs(largest), dbfs(rms), clipped, count)
