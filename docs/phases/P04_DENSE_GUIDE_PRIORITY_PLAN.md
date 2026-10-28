# P04 — Deterministic peer-guide priority in dense layouts

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, and P04 plan/results. Basic peer edge/centre snapping and viewport-only guides are implemented. Dense-overlap guide priority remains open.

## Scope

1. Give equal-distance snap candidates a stable semantic priority: edge-to-edge alignment first, centre-to-centre alignment second, and mixed edge-to-centre alignment third.
2. Keep geometric distance as the primary ranking; semantic priority must only break equal-distance ties, so a farther guide never overrides a closer guide.
3. Keep final tie-breaking deterministic by normalized target coordinate and peer-guide coordinate, independent of graphics-scene iteration order.
4. Preserve independent X/Y decisions, group movement's single bounded delta, Alt bypass, and guide clearing on drag cancel/release.
5. Add tests where multiple peer objects produce equal-distance competing guides, plus regressions proving a closer mixed guide beats a farther same-type guide and results remain stable if peer order changes.
6. Run plan validation, full tests, and Linux/Windows packaged CI; record exact results. Dense physical layouts on Windows/HiDPI remain acceptance work.

## Acceptance boundary

No schema changes, no new dependencies, no rendering/export changes, and no source-media writes. Do not mark all of P04 complete from this increment.
