# P04 — Custom numeric canvas grid spacing

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, and the P04 grid-spacing plan/results. Presets 5%, 10%, and 20% are implemented and verified; arbitrary custom numeric spacing remains open.

## Scope

1. Add a “Custom…” item to the existing grid-spacing menu and accept a numeric percentage in a bounded, validated range of 1–50%.
2. Persist the normalized spacing in `Composition.adjustments` using the existing Undo/Redo and project serialization path.
3. Make grid drawing use actual normalized step multiples (not an approximated equal division count) so drawn guides and snap coordinates coincide for values such as 7% or 12.5%.
4. Keep preset radio/check state coherent when a custom value is selected; show the custom percentage in menu text or an equivalent visible indicator.
5. Add tests for bounds, cancel/no-op behavior, persistence/undo, non-divisor spacing, and grid-line/snap alignment.
6. Run plan validation, full suite, and Linux/Windows packaged CI. Record exact evidence; real Windows/HiDPI acceptance remains separate.

## Acceptance boundary

No schema migration, no project layers created for guides, no render graph changes, no new dependency, and no independent app. Invalid persisted values fall back to 5%. Do not mark all of P04 complete from this increment.
