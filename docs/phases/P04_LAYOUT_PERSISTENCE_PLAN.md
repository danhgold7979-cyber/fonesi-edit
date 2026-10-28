# P04 — Persist desktop and editor workspace layout

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, and P04 plan/results. Layout persistence remains an explicit editor coverage gap.

## Scope

1. Persist main-window geometry/state, selected navigation tab, editor splitter sizes, and inspector tab index in the existing SQLite settings store.
2. Restore after the widgets/pages are created, validate stored values and apply safe defaults on malformed/old data.
3. Save only on normal close; respect background-to-tray behavior and avoid writing partial state during shutdown retries.
4. Never persist project media/content in the layout record; use a versioned UI-layout settings object with bounded numeric sizes and safe Base64 geometry/state.
5. Add tests for round-trip layout data, invalid settings fallback, navigation and inspector-tab restoration, and graceful close persistence using the offscreen Qt fixture.
6. Run plan validator, full suite, and Linux/Windows packaged CI. Record evidence; physical Windows multi-monitor/HiDPI acceptance remains separate.

## Acceptance boundary

No database schema migration, no new dependency, no independent application, no changes to project files or rendering. Layout restore must not override a user's project composition or last-project recovery state. Do not mark all of P04 complete from this increment.
