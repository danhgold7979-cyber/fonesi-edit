"""Bounded deterministic scene planner. Never claims global unsatisfiability."""

import random
import time
from dataclasses import dataclass
from math import gcd, prod


@dataclass(frozen=True)
class Scene:
    id: str
    angles: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.id, str) or not 1 <= len(self.id) <= 128:
            raise ValueError("INVALID_SCENE_ID")
        if (
            not isinstance(self.angles, tuple)
            or not 1 <= len(self.angles) <= 1000
            or not all(isinstance(x, str) and 1 <= len(x) <= 128 for x in self.angles)
        ):
            raise ValueError("INVALID_ANGLES")
        if len(set(self.angles)) != len(self.angles):
            raise ValueError("DUPLICATE_ANGLE_ID")


@dataclass(frozen=True)
class History:
    scene_ids: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class MatrixResult:
    rows: tuple[tuple[str, ...], ...]
    status: str
    examined: int
    algorithm: str = "coprime-lookahead-v1"


def valid_next(row, previous, *, window, different, scope):
    if row in previous:
        return False
    if window and any(
        any(a == b for a, b in zip(row, old)) for old in previous[-window:]
    ):
        return False
    comparisons = (
        previous[-1:] if scope == "previous" else (previous[-window:] if window else [])
    )
    return all(
        sum(a != b for a, b in zip(row, old)) >= different for old in comparisons
    )


def generate(
    scenes: tuple[Scene, ...],
    count: int,
    *,
    history: History,
    seed=0,
    window=0,
    different=0,
    scope="previous",
    budget=10000,
    cancel=None,
    timeout_ms=2000,
):
    if (
        not isinstance(scenes, tuple)
        or not 1 <= len(scenes) <= 64
        or not all(isinstance(s, Scene) for s in scenes)
    ):
        raise ValueError("INVALID_SCENES")
    ids = tuple(s.id for s in scenes)
    if len(set(ids)) != len(ids):
        raise ValueError("DUPLICATE_SCENE_ID")
    if not isinstance(history, History) or history.scene_ids != ids:
        raise ValueError("HISTORY_SCOPE_MISMATCH")
    if (
        not isinstance(history.rows, tuple)
        or len(history.rows) > 10000
        or not all(
            isinstance(r, tuple)
            and len(r) == len(scenes)
            and all(isinstance(x, str) and 1 <= len(x) <= 128 for x in r)
            for r in history.rows
        )
    ):
        raise ValueError("INVALID_HISTORY")
    for value, low, high in [
        (count, 0, 1000),
        (seed, 0, 2**63 - 1),
        (window, 0, 10000),
        (different, 0, len(scenes)),
        (budget, 1, 100000),
        (timeout_ms, 1, 60000),
    ]:
        if type(value) is not int or not low <= value <= high:
            raise ValueError("INVALID_LIMIT")
    if scope not in ("previous", "window"):
        raise ValueError("INVALID_COMPARISON_SCOPE")
    if count == 0:
        return MatrixResult((), "COMPLETE", 0)
    total = prod(len(s.angles) for s in scenes)
    rng = random.Random(seed)
    offset = rng.randrange(total)
    stride = 1
    if total > 1:
        for _ in range(64):
            candidate = rng.randrange(1, total)
            if gcd(candidate, total) == 1:
                stride = candidate
                break

    def decode(number):
        values = []
        for scene in reversed(scenes):
            number, index = divmod(number, len(scene.angles))
            values.append(scene.angles[index])
        return tuple(reversed(values))

    deadline = time.monotonic() + timeout_ms / 1000
    previous = list(history.rows)
    seen = set(previous)
    usage = {}
    for row in previous:
        for i, angle in enumerate(row):
            usage[i, angle] = usage.get((i, angle), 0) + 1
    rows = []
    pool = []
    examined = 0
    while len(rows) < count:
        if cancel is not None and cancel():
            return MatrixResult(tuple(rows), "CANCELED", examined)
        if time.monotonic() >= deadline:
            return MatrixResult(tuple(rows), "SEARCH_LIMIT", examined)
        kept = []
        for row in pool:
            if time.monotonic() >= deadline:
                return MatrixResult(tuple(rows), "SEARCH_LIMIT", examined)
            if cancel is not None and cancel():
                return MatrixResult(tuple(rows), "CANCELED", examined)
            if row not in seen and valid_next(
                row, previous, window=window, different=different, scope=scope
            ):
                kept.append(row)
        pool = kept
        while len(pool) < 32 and examined < min(total, budget):
            if cancel is not None and cancel():
                return MatrixResult(tuple(rows), "CANCELED", examined)
            if time.monotonic() >= deadline:
                return MatrixResult(tuple(rows), "SEARCH_LIMIT", examined)
            row = decode((offset + stride * examined) % total)
            examined += 1
            if row not in seen and valid_next(
                row, previous, window=window, different=different, scope=scope
            ):
                pool.append(row)
        if not pool:
            return MatrixResult(tuple(rows), "SEARCH_LIMIT", examined)
        chosen = min(
            pool, key=lambda row: sum(usage.get((i, a), 0) for i, a in enumerate(row))
        )
        pool.remove(chosen)
        rows.append(chosen)
        previous.append(chosen)
        seen.add(chosen)
        for i, angle in enumerate(chosen):
            usage[i, angle] = usage.get((i, angle), 0) + 1
    return MatrixResult(tuple(rows), "COMPLETE", examined)
