"""One requested source frame, not playback or output/effect parity."""

import struct
from fractions import Fraction
from pathlib import Path

from fonesi_edit.media import LOCAL_MEDIA_INPUT_OPTIONS
from fonesi_edit.process import run_bounded


def source_frame(source: Path, executable: Path, at: Fraction, *, cancel=None):
    if not isinstance(at, Fraction) or not 0 <= at <= 31536000:
        raise ValueError("INVALID_SOURCE_TIME")
    if cancel is not None and cancel.is_set():
        raise ValueError("CANCELED")
    micros = at * 1000000
    if micros.denominator != 1:
        raise ValueError("MICROSECOND_TIME_REQUIRED")
    seconds, fraction = divmod(micros.numerator, 1000000)
    result = run_bounded(
        [
            str(executable),
            "-nostdin",
            "-v",
            "error",
            *LOCAL_MEDIA_INPUT_OPTIONS,
            "-i",
            str(source),
            "-ss",
            f"{seconds}.{fraction:06}",
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            "-vf",
            "scale=640:480:force_original_aspect_ratio=decrease",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "pipe:1",
        ],
        timeout=60,
        limit=1048576,
        cancel=cancel,
    )
    if result.status != "OK" or not result.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("SOURCE_FRAME_UNAVAILABLE")
    if len(result.stdout) < 24 or result.stdout[12:16] != b"IHDR":
        raise ValueError("INVALID_FRAME_HEADER")
    width, height = struct.unpack(">II", result.stdout[16:24])
    if not 1 <= width <= 640 or not 1 <= height <= 480:
        raise ValueError("FRAME_DIMENSIONS_EXCEEDED")
    if cancel is not None and cancel.is_set():
        raise ValueError("CANCELED")
    return result.stdout
