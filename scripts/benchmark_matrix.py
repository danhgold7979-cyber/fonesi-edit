"""Bounded logical Matrix stress benchmark; no media or user data touched.

Measures the P09 generator, *not* FFmpeg rendering or GUI performance.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
from pathlib import Path
import time
import tracemalloc

from fonesi_edit.matrix import Angle, combination, generate, matrix_rows_valid


def benchmark(scenes: int = 12, angles: int = 5, outputs: int = 200,
              window: int = 1, different: int = 2, seed: int = 17,
              budget_seconds: float = 4.0, balance_candidates: int = 8) -> dict:
    if (any(type(value) is not int for value in
            (scenes, angles, outputs, window, different, seed))
            or not 1 <= scenes <= 100 or not 1 <= angles <= 100
            or not 1 <= outputs <= 100000
            or not 0 <= window <= 1000 or not 0 <= different <= scenes
            or type(budget_seconds) not in (int,float)
            or not 0 < budget_seconds <= 60 or not math.isfinite(budget_seconds)
            or type(balance_candidates) is not int or not 1 <= balance_candidates <= 64):
        raise ValueError("Invalid logical Matrix benchmark configuration")
    # Logical immutable identities only: these paths are never opened.
    universe = [
        [Angle(scene + 1, angle + 1, f"/synthetic/C{scene+1}/G{angle+1}.mp4",
               f"scene-{scene}-angle-{angle}")
         for angle in range(angles)]
        for scene in range(scenes)
    ]
    baseline = tuple(tuple((a.path, a.hash, a.index) for a in group)
                     for group in universe)
    tracemalloc.start()
    started = time.perf_counter()
    try:
        report = generate(universe, outputs, seed=seed, window=window,
                          different=different, compare_window=True,
                          seconds=budget_seconds,
                          balance_candidates=balance_candidates)
        elapsed = time.perf_counter() - started
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    rows = report["rows"]
    if not matrix_rows_valid(rows, [], window, different, True):
        raise RuntimeError("Matrix benchmark violated W/K or uniqueness")
    if len(rows) != len({combination(row) for row in rows}):
        raise RuntimeError("Matrix benchmark emitted duplicate combinations")
    if baseline != tuple(tuple((a.path, a.hash, a.index) for a in group)
                         for group in universe):
        raise RuntimeError("Matrix benchmark mutated source identities")
    return {
        "kind": "logical_matrix_generator_only",
        "scenes": scenes, "angles_per_scene": angles,
        "theoretical_capacity": report["capacity"],
        "requested": outputs, "generated": len(rows),
        "complete": report["complete"], "attempts": report["attempts"],
        "window": window, "different": different, "seed": seed,
        "balance_candidates": balance_candidates,
        "per_scene_usage": report["usage"],
        "max_per_scene_spread": max((item["spread"] for item in report["usage"]),default=0),
        "elapsed_seconds": round(elapsed, 6),
        "python_tracemalloc_peak_bytes": peak_bytes,
        "source_unchanged": True, "unique_and_wk_valid": True,
        "platform": platform.platform(),
        "limitations": ("Generated logical source IDs only; no FFprobe, FFmpeg "
                        "render, large real-media corpus, Windows device, GPU "
                        "; no claim that an incomplete search proves UNSAT."),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenes", type=int, default=12)
    parser.add_argument("--angles", type=int, default=5)
    parser.add_argument("--outputs", type=int, default=200)
    parser.add_argument("--window", type=int, default=1)
    parser.add_argument("--different", type=int, default=2)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--budget-seconds", type=float, default=4.0)
    parser.add_argument("--balance-candidates", type=int, default=8)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args(argv)
    report=benchmark(args.scenes, args.angles, args.outputs,
                     args.window, args.different, args.seed,
                     args.budget_seconds, args.balance_candidates)
    if args.require_complete and not report["complete"]:
        parser.error("bounded Matrix benchmark did not generate every requested row")
    payload=json.dumps(report,indent=2,sort_keys=True)
    print(payload)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(payload+"\n",encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
