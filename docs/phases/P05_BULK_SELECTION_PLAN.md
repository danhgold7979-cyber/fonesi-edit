# P05 — Bounded bulk selection for filtered scan results

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/PRODUCT_REQUIREMENTS.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/phases/P05_PLAN.md`, and the scan-filter plan/results. Scan results now support search, kind/selectability filters, stable sort and 200-row UI pagination; selecting all filtered results across pages and guarding very large job batches remain open.

## Scope

1. Add explicit actions to select or deselect all currently filtered results across pages; only safe, unique, selectable source indices can be bulk-selected.
2. Keep selection bound to original scan indices and scan job ID. Changing filters/pages must not silently clear selections outside the current filtered view.
3. Add a hard cap of 500 selected items for a single scan batch. If selecting all filtered results would exceed the cap, leave selection unchanged and ask the user to narrow the filter; if a manually assembled selection exceeds the cap, reject enqueue before creating any jobs.
4. Preserve existing account/adapter snapshot validation, signed/duplicate URL protection, idempotent enqueue and current-page selection controls.
5. Add Qt tests for select-all across multiple pages, deselect-current-filter preserving hidden selections, cap rejection with no partial selection, and oversized enqueue rejection with zero jobs.
6. Run plan validation, full source suite and Linux/Windows packaged CI. Live provider pagination and account acceptance remain separate.

## Acceptance boundary

No provider API calls, no schema changes, no source-media writes, no silent truncation, and no auto-enqueue of the bulk-selected items. Selection and enqueue remain separate explicit user actions.
