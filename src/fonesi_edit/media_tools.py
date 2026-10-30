"""Declared CLI capability check, not executable origin/authenticity verification."""

import re
from dataclasses import dataclass
from pathlib import Path

from fonesi_edit.process import run_bounded


@dataclass(frozen=True)
class MediaTools:
    ffmpeg: Path
    ffprobe: Path
    ffmpeg_version: str
    ffprobe_version: str


def inspect_tools(ffmpeg, ffprobe, *, cancel=None):
    if cancel is not None and cancel.is_set():
        raise ValueError("TOOL_CHECK_CANCELED")
    paths = []
    for path in (ffmpeg, ffprobe):
        if not isinstance(path, Path) or not path.is_absolute() or not path.is_file():
            raise ValueError("EXPLICIT_TOOL_FILE_REQUIRED")
        paths.append(path.resolve(strict=True))
    if paths[0] == paths[1]:
        raise ValueError("DISTINCT_MEDIA_TOOLS_REQUIRED")
    versions = []
    for role, path in zip(("ffmpeg", "ffprobe"), paths):
        result = run_bounded(
            [str(path), "-hide_banner", "-version"],
            timeout=10,
            limit=65536,
            cancel=cancel,
        )
        if result.status != "OK":
            raise ValueError(role.upper() + "_VERSION_" + result.status)
        try:
            first = result.stdout.splitlines()[0].decode("ascii")
        except (UnicodeError, IndexError):
            raise ValueError("INVALID_TOOL_VERSION_OUTPUT") from None
        match = re.match(
            re.escape(role) + r" version ([A-Za-z0-9.+_-]{1,100})(?:\s|$)", first
        )
        if match is None:
            raise ValueError("UNEXPECTED_TOOL_ROLE_OR_VERSION")
        versions.append(match[1])
    result = run_bounded(
        [str(paths[0]), "-hide_banner", "-encoders"],
        timeout=10,
        limit=65536,
        cancel=cancel,
    )
    if result.status != "OK":
        raise ValueError("ENCODER_PROBE_" + result.status)
    encoders = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and re.fullmatch(rb"[A-Z.]{6}", parts[0]):
            encoders.add((parts[0][:1], parts[1]))
    if not {(b"V", b"libx264"), (b"A", b"aac")} <= encoders:
        raise ValueError("REQUIRED_CPU_ENCODERS_MISSING")
    if cancel is not None and cancel.is_set():
        raise ValueError("TOOL_CHECK_CANCELED")
    return MediaTools(paths[0], paths[1], *versions)
