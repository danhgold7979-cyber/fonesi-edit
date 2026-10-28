# P04 — Preserve crop aspect ratio at handles and canvas bounds

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`  
**Baseline:** `4aabfc3e6128f0bc781922daa43416876ccda376`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/phases/P04_PLAN.md`, and `docs/phases/P04_RESULTS.md`. The current crop dialog already stores normalized coordinates and exports through FFmpeg. Coverage explicitly leaves ratio-lock edge cases open.

## Scope

1. Extract crop drag geometry into a pure, validated helper so the crop interaction can be tested without launching a dialog for every case.
2. Preserve the starting crop's normalized width/height ratio (equivalent to its pixel aspect ratio for a fixed source) when ratio lock is enabled.
3. Support creating a new rectangle, moving a crop, dragging each of four edges, and dragging each of four corners. For edge/corner resize, keep the opposite edge/corner or orthogonal centre stable as appropriate.
4. Clamp crop geometry to [0,1] and a positive minimum size without allowing out-of-frame rectangles; when a boundary limits the requested size, scale both dimensions together so ratio lock remains true.
5. Keep free-ratio behavior unchanged, keep edits local until dialog acceptance, and preserve the existing normalized project schema and Undo transaction.
6. Add table-driven tests for all eight handles, both drag directions, boundary clamps, minimum size, free-ratio behavior, and finite/in-range invariants. Run plan validator, focused tests, full suite, and Linux/Windows frozen proof.

## Acceptance boundary

No source-media mutation, no schema migration, no render-graph changes beyond the existing crop values, and no separate application. Hosted fixtures do not close real Windows/HiDPI/4K/rotated-metadata acceptance.
