"""Narrow CPU proof renderer; no timeline, subtitle or platform support implied."""

import os
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from fonesi_edit.media import LOCAL_MEDIA_INPUT_OPTIONS, probe
from fonesi_edit.process import run_bounded
from fonesi_edit.timing import ClipMap


@dataclass(frozen=True)
class Artifact:
    path: Path
    digest: str
    duration: Fraction
    size: int


def render_cpu(
    source: Path,
    destination: Path,
    ffmpeg: Path,
    ffprobe: Path,
    *,
    duration_tolerance: Fraction,
    cancel=None,
    clip_map: ClipMap | None = None,
) -> Artifact:
    if not isinstance(duration_tolerance, Fraction) or not 0 <= duration_tolerance <= 1:
        raise ValueError("EXPLICIT_DURATION_POLICY_REQUIRED")
    source = source.resolve(strict=True)
    destination = destination.absolute()
    if destination.suffix.lower() != ".mp4" or not destination.parent.is_dir():
        raise ValueError("INVALID_DESTINATION")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("OUTPUT_EXISTS")
    original = probe(source, ffprobe, cancel=cancel)
    if "video" not in original.stream_types:
        raise ValueError("VIDEO_REQUIRED")
    filters = []
    expected_duration = original.duration
    if clip_map is not None:
        if (
            not isinstance(clip_map, ClipMap)
            or clip_map.output_start != 0
            or clip_map.source.end > original.duration
            or not Fraction(1, 2) <= clip_map.speed <= 2
        ):
            raise ValueError("UNSUPPORTED_CLIP_MAP")
        start = f"{float(clip_map.source.start):.9f}"
        end = f"{float(clip_map.source.end):.9f}"
        ratio = f"{clip_map.speed.numerator}/{clip_map.speed.denominator}"
        filters = [
            "-vf",
            f"trim=start={start}:end={end},setpts=(PTS-STARTPTS)/({ratio})",
            "-fps_mode",
            "vfr",
        ]
        if "audio" in original.stream_types:
            filters += [
                "-af",
                f"atrim=start={start}:end={end},asetpts=PTS-STARTPTS,atempo={float(clip_map.speed):.9f}",
            ]
        expected_duration = clip_map.output.duration
    with tempfile.TemporaryDirectory(
        prefix=".fonesi-render-", dir=destination.parent
    ) as folder:
        staged = Path(folder) / "validated.mp4"
        result = run_bounded(
            [
                str(ffmpeg),
                "-nostdin",
                "-v",
                "error",
                "-n",
                *LOCAL_MEDIA_INPUT_OPTIONS,
                "-i",
                str(source),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0?",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                *filters,
                "-movflags",
                "+faststart",
                str(staged),
            ],
            timeout=60,
            cancel=cancel,
        )
        if result.status != "OK":
            raise ValueError("ENCODE_" + result.status)
        output = probe(staged, ffprobe, cancel=cancel)
        if (
            "video" not in output.stream_types
            or abs(output.duration - expected_duration) > duration_tolerance
        ):
            raise ValueError("OUTPUT_DURATION_OR_STREAM_MISMATCH")
        if "audio" in original.stream_types and "audio" not in output.stream_types:
            raise ValueError("OUTPUT_AUDIO_MISSING")
        decoded = run_bounded(
            [
                str(ffmpeg),
                "-nostdin",
                "-v",
                "error",
                *LOCAL_MEDIA_INPUT_OPTIONS,
                "-i",
                str(staged),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0?",
                "-f",
                "null",
                "-",
            ],
            timeout=60,
            cancel=cancel,
        )
        if decoded.status != "OK":
            raise ValueError("DECODE_" + decoded.status)
        digest = sha256()
        # Windows FlushFileBuffers requires a writable owned staging handle.
        with staged.open("r+b") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
            os.fsync(stream.fileno())
        size = staged.stat().st_size
        if size <= 0:
            raise ValueError("EMPTY_OUTPUT")
        # Never replace an existing name. Unsupported filesystems fail here.
        if cancel is not None and cancel.is_set():
            raise ValueError("CANCELED")
        os.link(staged, destination)
        return Artifact(destination, digest.hexdigest(), output.duration, size)
