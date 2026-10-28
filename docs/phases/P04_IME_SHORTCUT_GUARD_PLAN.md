# P04 — Guard editor shortcuts during active IME composition

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, and P04 plan/results. Focus-aware shortcuts already yield to text editors and interactive controls, but explicit IME preedit protection remains open.

## Scope

1. Track Qt input-method preedit lifecycle from `QInputMethodEvent` on the application event stream, scoped to the widget receiving composition.
2. While that widget owns active preedit, suppress editor-scoped QAction callbacks so Ctrl+A/C/V/X, Undo/Redo, play/pause and layer operations cannot mutate editor state during composition.
3. Clear composition state when preedit ends, focus leaves the composing widget, or the window shuts down; do not retain stale widget references.
4. Preserve native text editing when no composition is active, focus-aware spin-box/combo behavior, and existing user shortcut remapping.
5. Add Qt tests for preedit start/end, active-widget isolation, no layer mutation while composing, and normal shortcut routing after composition ends.
6. Run plan validation, full tests, and Linux/Windows packaged CI. Physical IME behavior across Chinese/Japanese/Korean input methods and Windows remains a separate acceptance gate.

## Acceptance boundary

No schema changes, no new dependencies, no independent app, no source-media writes, and no rendering changes. Do not claim physical IME acceptance based only on synthetic Qt events.
