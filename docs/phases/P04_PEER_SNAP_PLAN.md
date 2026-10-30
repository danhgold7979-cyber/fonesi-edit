# P04 — Snap layer to peer guides

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`  
**Baseline:** `e2516733ba53b2da88ca84f4f30ba822ee66b923`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/phases/P04_PLAN.md`, and `docs/phases/P04_RESULTS.md`. The editor already snaps to canvas centre, safe margins and optional grid. Coverage still identifies snapping to other objects as incomplete.

## Scope

1. Add a pure normalized-coordinate helper that aligns a moving layer's left/centre/right and top/centre/bottom guides with visible, unlocked peer layers.
2. Snap only when the nearest peer guide is within a bounded tolerance; deterministic tie-breaking and independent X/Y decisions must avoid jumps.
3. Exclude the moving layer, selected companions, locked layers, hidden layers and invalid geometry. Group movement must keep its existing single-delta behavior and preserve relative offsets.
4. Integrate peer snapping into the existing drag path only when snapping is enabled. Alt bypasses canvas and peer snapping; grid/canvas guides remain supported.
5. Add unit coverage for exact edge/centre matches, tolerance boundaries, hidden/locked/self/selected exclusions, invalid input and unchanged group spacing.
6. Run `uv run python scripts/check_plan.py`, focused tests, full `uv run pytest -q`, build and frozen proof through GitHub Actions on Linux and Windows. Record exact commit and results before reporting the slice tested.

## Safety and acceptance boundary

No project schema change, no source media writes, no render graph change, and no independent application. A green hosted run is not end-user Windows/HiDPI acceptance. Do not mark all of P04 accepted from this slice.
