# P05 — Search, filter and stable sorting for scan results

**Date:** 2026-10-28  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Integration branch:** `develop/fonesi-full`

## Master-plan alignment

Read `docs/IMPLEMENTATION_PLAN.md`, `docs/PRODUCT_REQUIREMENTS.md`, `docs/SETTINGS_AND_BROWSER_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/phases/P05_PLAN.md`, and P05 results. Scan UI already paginates at 200 rows and retains selection by original scan index; search/filter/sort are still listed as open.

## Scope

1. Add a case-insensitive search over item title and stable ID only. Do not search or display raw media URLs or signed query values.
2. Add a media-kind filter (all/images/videos) and a safe/selectable-state filter; normalize common singular/plural kinds without mutating the stored scan result.
3. Add stable sorting by source order, title A–Z, or media kind. Ties preserve original scan index.
4. Apply pagination to the filtered/sorted index view while preserving selections against original scan indices. Changing filters must not clear selections on hidden pages or alter the scan job/account snapshot.
5. Show total scan count, visible filtered count, current page and total selected count. “Select page” must affect only currently visible/selectable rows; “Download selected” must still enqueue the original selected source indices and keep existing signed/duplicate/account guards.
6. Add Qt tests for filtering, sorting stability, filter-to-page interactions, selection persistence across filter changes/pages, and correct selected-download payloads. Include synthetic large result data without live provider requests.
7. Run plan validator, full source tests, and Linux/Windows packaged CI. Record exact results; provider pagination/checkpoint and live platform acceptance remain separate.

## Acceptance boundary

No schema changes, no source-media writes, no new dependencies, no changes to scan completeness claims, and no conversion of UI pagination into provider pagination. Raw URLs and account/session secrets must never appear in search results or UI labels.

## Evidence — scan result search/filter/sort (28/10/2026)

- Added case-insensitive title/ID search, filters for images/videos/selectable/unselectable, and stable sort by source order/title/media kind.
- Pagination now applies to filtered results while checkbox selection remains keyed to original scan indices. Selected items hidden by a filter remain selected; download uses the original safe URL/adapter/account snapshot. Raw URLs are not searchable or displayed.
- Qt offscreen regression covers filter changes, duplicate URL lockout, stable ordering, page navigation and enqueueing the original selected item.
- CI [run 40738678506](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40738678506) **PASS**: 422 Linux tests; 421 Windows tests + 1 intentional POSIX-fixture skip. Production desktop/native host and frozen proof passed on both runners.
- Still open: provider-side pagination/checkpoint, advanced metadata filters, very large bulk-selection UX and live platform/Chrome-auth acceptance.

