# P05 — No-overwrite proof for repeated image downloads

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/PRODUCT_REQUIREMENTS.md`, `docs/SETTINGS_AND_BROWSER_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, and `docs/phases/P05_PLAN.md`. Generic video download already proves a second run preserves the existing file; the equivalent gallery/image repeat-run assertion is missing.

## Scope

1. Extend the localhost gallery-dl fixture to run the same image download twice into the same Unicode output folder.
2. Assert the existing image remains readable, its path remains stable, its modification timestamp does not change, and the second run reports a successful item without overwriting good output.
3. Keep the test entirely local; no live provider, real account, or external network dependency.
4. Run focused tests and the full Linux/Windows source + packaged CI; record exact evidence before checking the P05 item complete.

## Acceptance boundary

No source-media mutation, no provider-specific claims, no new dependencies, and no change to download semantics unless the regression exposes a real overwrite defect.
