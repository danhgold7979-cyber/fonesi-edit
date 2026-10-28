# P04 — Inspector property search and reset

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, and P04 plan/results. The coverage ledger still lists property search/reset as open.

## Scope

1. Add a compact search field above the existing inspector tabs; search matches property labels and field keys case-insensitively.
2. Filter form rows without rebuilding widgets, changing values, changing selection, or writing project state. Empty query restores all rows.
3. Add an explicit reset action for the selected layer's editable transform, style, motion and keyframe properties. Preserve layer identity, name, text/content, image path, group, clip scope and layer order.
4. Reset to safe per-kind defaults, including the editor's normal mask defaults. Apply as one undoable transaction; invalid/locked/no-selection behavior must be clear and safe.
5. Add tests for case-insensitive filtering, clearing the query, no project mutation from searching, per-kind reset defaults, preserved identity/content/linkage, and a single undo/redo step.
6. Run plan validation, focused and full test suites, and Linux/Windows packaged CI. Record exact evidence; real Windows/HiDPI acceptance remains separate.

## Acceptance boundary

No schema migration, no new dependency, no separate application, no source-media writes, and no render-graph changes. Reset must be reversible through Undo. Search must be a view-only operation. Do not mark all of P04 complete from this increment.
