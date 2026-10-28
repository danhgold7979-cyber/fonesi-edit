# P04 — Configurable canvas grid spacing

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, and the P04 plan/results. Canvas grid visibility is persisted, but grid spacing is currently hard-coded to 5%; coverage still lists custom grid as open.

## Scope

1. Add a validated, persisted grid spacing setting with supported presets 5%, 10%, and 20%; default remains 5% for existing projects.
2. Expose spacing selection in the existing editor menu without replacing or duplicating the editor application.
3. Draw only the selected grid spacing in the canvas and use the same spacing for snap calculations.
4. Keep grid overlays editor-only; do not persist generated lines as layers or include them in the FFmpeg render graph.
5. Add unit tests for each supported spacing, invalid setting fallback/validation, and normalized snap behavior; add UI round-trip tests for saving/reopening the project adjustment.
6. Run plan validation, full tests, and Linux/Windows packaged CI. Record evidence and leave real Windows/HiDPI acceptance open.

## Acceptance boundary

No project schema migration is needed; the existing `Composition.adjustments` dictionary stores the option. Unsupported values must safely fall back to 5%. Do not mark all of P04 complete from this increment.
