# P06-06 / P03-06 — Atomic publication of new subtitle files

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only integration branch:** `develop/fonesi-full`. **Status:** plan before source change.

## Master-plan alignment and evidence already available

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P03-06, P06-03/04/06), `docs/PRODUCT_REQUIREMENTS.md` (subtitle files and no-overwrite policy), `docs/REQUIREMENTS_TRACEABILITY.md` (SUB-04, SUB-10, OPS-06), `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/phases/P06_PLAN.md` and `P06_RESULTS.md`. Inspected `src/fonesi_edit/subtitles.py` and `tests/test_caption_translation.py`.

Existing `write_captions(overwrite=True)` stages a temporary file, fsyncs it, then replaces the destination. The default `overwrite=False` instead writes directly to the final filename using `open('xb')`: a write, fsync or power-loss failure can leave a partial subtitle at the intended final path. Worker recovery could mistake that path for a completed artifact. This is a distinct safety gap from the already-tested atomic overwrite path.

## Bounded implementation

1. Serialize the entire SRT/VTT/ASS payload **before** touching any final output. Use a hidden temporary file in the destination directory for **both** overwrite modes, flush and fsync it.
2. For `overwrite=False`, publish with an atomic hard link `os.link(temp, destination)`, which rejects even a destination appearing concurrently, then unlink only the temporary name. For `overwrite=True`, retain `os.replace`. Never delete a pre-existing destination or silently switch to a non-atomic copy. If hard links are unavailable on a filesystem, report a clear error and keep the destination unpublished.
3. Add regression tests for failed temp fsync (no final/partial file), a competing publisher (existing bytes preserved), unsupported hard link (explicit failure, temp cleaned), and successful Unicode captions. Reuse existing overwrite/recovery and worker integration tests to detect regressions.
4. Validate with `scripts/check_plan.py`, focused tests and full `pytest` in CI, then packaged desktop/native-host proof separately on Linux and Windows. Document exact SHA/run results only when both jobs complete; do not claim a pass while CI runs.

## Acceptance and remaining gates

- [x] Default create-only export never exposes partial subtitles on a staged write failure.
- [x] A competing file created before publication remains byte-for-byte unchanged; publication raises `FileExistsError`.
- [x] Unsupported hard link fails closed; all temporary filenames are cleaned.
- [x] Existing atomic overwrite, subtitle parsing, cache/translation recovery, bundled app and worker regressions remain passing on Linux and Windows.

Still **open**: live translation quality/cost, real Chrome account/session and platform permissions, physical Windows device, non-NTFS filesystem acceptance and power-loss/long-run durability. This slice must not be used to close full P06 or P03 acceptance.