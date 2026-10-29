"""Reproducible *planning-only* local media corpus benchmark (P08/P11).

Generated fixtures live in a temporary directory and are removed on exit.
This does not benchmark actual video rendering, GPU, playback or Chrome.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

import psutil

from fonesi_edit.batch import batch_plan_report
from fonesi_edit.domain import Composition
from fonesi_edit.prototypes.media import create_fixture
from fonesi_edit.prototypes.tools import locate_tool


def _version(name: str) -> str:
    executable = locate_tool(name)
    if not executable:
        return "unavailable"
    try:
        completed = subprocess.run([str(executable), "-version"], capture_output=True,
                                   text=True, errors="replace", timeout=10, check=True)
        return completed.stdout.splitlines()[0][:160]
    except (OSError, subprocess.SubprocessError, IndexError):
        return "version unavailable"


def benchmark(copies: int) -> dict:
    """Measure full FFprobe dry-run cost; file copies are synthetic and disposable."""
    if type(copies) is not int or not 1 <= copies <= 1000:
        raise ValueError("copies must be an integer from 1 to 1000")

    with tempfile.TemporaryDirectory(prefix="fonesi-batch-benchmark-") as temporary:
        root = Path(temporary)
        fixture = create_fixture(root / "fixture", duration=0.5)
        master = fixture["source"]
        footprint = master.stat().st_size
        free = shutil.disk_usage(root).free
        if footprint * (copies + 2) > free // 2:
            raise OSError("Not enough free space for a safe temporary benchmark corpus")
        sample_hash = hashlib.sha256(master.read_bytes()).hexdigest()

        channel = root / "synthetic-channel" / "videos"
        channel.mkdir(parents=True, exist_ok=True)
        sources = []
        for index in range(copies):
            destination = channel / f"video_{index:05d}.mp4"
            shutil.copyfile(master, destination)
            sources.append(str(destination))

        # RSS measurements are snapshots, not a peak RSS claim; tracemalloc is
        # peak Python allocations only, and excludes ffprobe subprocess memory.
        process = psutil.Process()
        rss_before = process.memory_info().rss
        fractions = []
        tracemalloc.start()
        start = time.perf_counter()
        try:
            report = batch_plan_report(
                {str(channel.parent): sources},
                Composition(width=320, height=180, fps=25, encoder="cpu"),
                progress=fractions.append,
            )
            elapsed = time.perf_counter() - start
            _, peak_python = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        rss_after = process.memory_info().rss

        if report.get("cancelled") or report["failures"] or len(report["plans"]) != copies:
            raise RuntimeError("Benchmark dry-run did not plan every synthetic video")
        if not fractions or fractions[-1] != 1.0 or any(
            later < earlier for earlier, later in zip(fractions, fractions[1:])
        ):
            raise RuntimeError("Benchmark progress did not complete monotonically")
        if hashlib.sha256(master.read_bytes()).hexdigest() != sample_hash:
            raise RuntimeError("Synthetic source fixture changed during planning")
        if any(Path(plan["output"]).exists() for plan in report["plans"]):
            raise RuntimeError("Dry-run unexpectedly published an output file")

        result = {
            "schema_version": 1,
            "scenario": "synthetic-ffprobe-batch-planning-only",
            "fixture_count": copies,
            "planned_count": len(report["plans"]),
            "failed_count": len(report["failures"]),
            "elapsed_seconds": round(elapsed, 6),
            "planning_files_per_second": round(copies / max(elapsed, 1e-9), 3),
            "rss_before_bytes": rss_before,
            "rss_after_bytes": rss_after,
            "peak_python_traced_bytes": peak_python,
            "sample_source_unchanged": True,
            "generated_output_count": 0,
            "progress_complete": True,
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "ffprobe_version": _version("ffprobe"),
            "ffmpeg_version": _version("ffmpeg"),
            "limitations": (
                "Local synthetic 0.5 s 640x360 MP4 clones. Measures FFprobe-based "
                "batch dry-run only, not render duration/ETA, output bytes, subprocess "
                "peak RSS, GPU, full corpus diversity or physical Windows acceptance."
            ),
        }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copies", type=int, default=32,
                        help="Synthetic MP4 copies to plan (1-1000; default 32)")
    parser.add_argument("--output", type=Path, help="Optional new JSON result path")
    args = parser.parse_args(argv)
    result = benchmark(args.copies)
    serialized = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        destination = args.output.expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Refuse overwrite; benchmark artifacts never replace existing files.
        with destination.open("x", encoding="utf-8") as stream:
            stream.write(serialized)
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
