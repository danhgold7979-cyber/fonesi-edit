"""Local bounded scan and real per-file CPU batch, no destructive source action."""

import os
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from fonesi_edit.prepared_input import capture_source
from fonesi_edit.render import Artifact, render_cpu


@dataclass(frozen=True)
class BatchInput:
    source: Path
    relative: Path
    root_id: str


@dataclass(frozen=True)
class ScanResult:
    items: tuple[BatchInput, ...]
    status: str
    warnings: tuple[str, ...]
    visited: int


@dataclass(frozen=True)
class BatchResult:
    artifacts: tuple[Artifact, ...]
    failures: tuple[tuple[int, str], ...]
    status: str
    progress_failed: bool = False


@dataclass(frozen=True)
class BatchProgress:
    total: int
    finished: int
    validated: int
    failed: int
    active_index: int | None
    state: str


def scan(
    roots: tuple[Path, ...],
    output_root: Path,
    *,
    max_items=1000,
    max_visited=10000,
    max_depth=32,
    cancel=None,
):
    if (
        not isinstance(roots, tuple)
        or not 1 <= len(roots) <= 100
        or not all(isinstance(r, Path) for r in roots)
    ):
        raise ValueError("INVALID_ROOTS")
    for value, maximum in ((max_items, 10000), (max_visited, 100000), (max_depth, 64)):
        if type(value) is not int or not 1 <= value <= maximum:
            raise ValueError("INVALID_SCAN_BOUND")
    output_root = output_root.resolve()
    items = []
    warnings = []
    visited = 0
    seen = set()
    status = "COMPLETE"
    canonical = []
    for root in roots:
        if root.is_symlink() or not root.is_dir():
            raise ValueError("REGULAR_ROOT_REQUIRED")
        root = root.resolve()
        if root == output_root or root.is_relative_to(output_root):
            raise ValueError("OUTPUT_CONTAINS_SOURCE_ROOT")
        if root not in canonical:
            canonical.append(root)
    for root in canonical:
        root_id = sha256(os.path.normcase(str(root)).encode()).hexdigest()[:16]
        stack = [(root, 0)]
        while stack:
            if cancel is not None and cancel():
                return ScanResult(tuple(items), "CANCELED", tuple(warnings), visited)
            directory, depth = stack.pop()
            if directory == output_root or directory.is_relative_to(output_root):
                continue
            if depth > max_depth:
                warnings.append("DEPTH_LIMIT")
                status = "PARTIAL"
                continue
            entries = []
            visit_limit = False
            try:
                with os.scandir(directory) as iterator:
                    for entry in iterator:
                        if visited >= max_visited:
                            visit_limit = True
                            break
                        visited += 1
                        entries.append(entry)
            except OSError:
                warnings.append("SCAN_ERROR")
                status = "PARTIAL"
                continue
            for entry in sorted(entries, key=lambda e: e.name.casefold()):
                if cancel is not None and cancel():
                    return ScanResult(
                        tuple(items), "CANCELED", tuple(warnings), visited
                    )
                path = Path(entry.path)
                try:
                    if entry.is_symlink():
                        warnings.append("SYMLINK_SKIPPED")
                        status = "PARTIAL"
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        stack.append((path, depth + 1))
                        continue
                    if not entry.is_file(
                        follow_symlinks=False
                    ) or path.suffix.lower() not in {
                        ".mp4",
                        ".mkv",
                        ".mov",
                        ".avi",
                        ".webm",
                    }:
                        continue
                    identity = os.path.normcase(str(path.resolve()))
                    if identity in seen:
                        continue
                    if len(items) >= max_items:
                        return ScanResult(
                            tuple(items),
                            "PARTIAL",
                            tuple(warnings + ["ITEM_LIMIT"]),
                            visited,
                        )
                    seen.add(identity)
                    items.append(BatchInput(path, path.relative_to(root), root_id))
                except OSError:
                    warnings.append("ENTRY_ERROR")
                    status = "PARTIAL"
            if visit_limit:
                return ScanResult(
                    tuple(items), "PARTIAL", tuple(warnings + ["VISIT_LIMIT"]), visited
                )
    return ScanResult(tuple(items), status, tuple(warnings), visited)


def render_batch(
    items: tuple[BatchInput, ...],
    output_root: Path,
    ffmpeg: Path,
    ffprobe: Path,
    *,
    duration_tolerance: Fraction,
    cancel=None,
    progress=None,
):
    if (
        not isinstance(items, tuple)
        or len(items) > 10000
        or not all(isinstance(x, BatchInput) for x in items)
    ):
        raise ValueError("INVALID_BATCH")
    output_root = output_root.resolve()
    if not output_root.is_dir():
        raise ValueError("OUTPUT_DIRECTORY_REQUIRED")
    artifacts = []
    failures = []
    progress_failed = False

    def notify(state, active_index=None):
        nonlocal progress, progress_failed
        if progress is not None:
            update = BatchProgress(
                len(items),
                len(artifacts) + len(failures),
                len(artifacts),
                len(failures),
                active_index,
                state,
            )
            try:
                progress(update)
            except Exception:  # noqa: BLE001 - advisory observer must not change published-output outcomes.
                progress_failed = True
                progress = None

    def finish(status):
        notify(status)
        return BatchResult(tuple(artifacts), tuple(failures), status, progress_failed)

    for index, item in enumerate(items):
        if cancel is not None and cancel.is_set():
            return finish("CANCELED")
        if (
            not item.root_id
            or len(item.root_id) != 16
            or any(c not in "0123456789abcdef" for c in item.root_id)
            or item.relative.is_absolute()
            or ".." in item.relative.parts
        ):
            raise ValueError("INVALID_OUTPUT_MAPPING")
        destination = (
            output_root
            / item.root_id
            / item.relative.parent
            / (
                item.relative.stem
                + "-"
                + item.relative.suffix.lstrip(".")
                + "-edit.mp4"
            )
        )
        if not destination.resolve().is_relative_to(output_root):
            raise ValueError("OUTPUT_ESCAPE")
        notify("RUNNING", index)
        try:
            if item.source.is_symlink() or not item.source.is_file():
                raise ValueError("SOURCE_NOT_REGULAR")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with capture_source(
                item.source.absolute(),
                destination.parent,
                max_bytes=max(1, item.source.stat().st_size),
                timeout=60,
                cancel=cancel,
            ) as captured:
                artifact = render_cpu(
                    captured.path,
                    destination,
                    ffmpeg,
                    ffprobe,
                    duration_tolerance=duration_tolerance,
                    cancel=cancel,
                )
            artifacts.append(artifact)
        except FileExistsError:
            failures.append((index, "OUTPUT_EXISTS"))
        except (ValueError, OSError) as exc:
            code = (
                str(exc)
                if isinstance(exc, ValueError) and str(exc).replace("_", "").isalnum()
                else type(exc).__name__
            )
            failures.append((index, code[:100]))
            if cancel is not None and cancel.is_set():
                return finish("CANCELED")
        notify("RUNNING")
    return finish("PARTIAL" if failures else "COMPLETE")
