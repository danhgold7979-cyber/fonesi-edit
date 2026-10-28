# P04 — Visible peer-snap guides during layer drag

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`  
**Baseline:** `62b5912bb8798e69243d5b61538390087e3a2439`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/phases/P04_PLAN.md`, `docs/phases/P04_RESULTS.md` and `docs/phases/P04_PEER_SNAP_PLAN.md`. The peer snapping algorithm is implemented; this increment adds visible feedback to make the alignment interaction discoverable and verifiable.

## Implementation steps

1. Extend the pure snap calculation to report the peer guide coordinate responsible for a successful snap, while preserving the existing two-coordinate helper contract.
2. Draw cosmetic dashed vertical/horizontal guide lines over the canvas viewport only while a peer snap is active. Map normalized scene coordinates to viewport coordinates; do not add guide lines to the scene, project data or rendered export.
3. Clear guides immediately when the drag ends, Alt bypasses snapping, or the moving item no longer aligns to a peer.
4. Keep selected/group companions, hidden layers and locked layers excluded as snap targets. Keep one bounded common delta for group movement.
5. Add pure tests for returned guide coordinates and no-guide cases, plus Qt tests for visible guide lifecycle where practical.
6. Run plan validation, focused tests and full source suite, then rely on the Linux/Windows CI and frozen-app proof. Record exact results; do not claim Windows end-user/HiDPI acceptance.

## Safety and acceptance boundary

No project schema change, no source media mutation, no FFmpeg graph change, no new dependency, and no separate application. The guides are editor-only overlays and must never be exported or persisted. A successful hosted test does not close the full P04 or P12 gates.
