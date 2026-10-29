# P05-02/P10-02 — Scheduled bounded yt-dlp playlist-window continuation

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Branch:** `develop/fonesi-full`. **Starting HEAD:** `6e08cb50cbd3ab5eed6ddebab20c431185e017b9`.

## Master alignment / existing evidence

Read `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` P05-02/03/06 and P10-02, `docs/PRODUCT_REQUIREMENTS.md` §3.2/3.3, `docs/REQUIREMENTS_TRACEABILITY.md` SRC-03/09/10/AUTO-02, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, `P05_PLAN.md`, `P05_RESULTS.md`, `P05_SCHEDULED_NEW_ONLY_PLAN.md`, and code `downloads.py`, `sync.py`, `automation.py`, `storage.py`, `ui/pages.py` and `tests/test_scheduled_new_only.py`. Existing [CI 40857385183](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40857385183) succeeded (546 Linux/545 Windows+1 skip, packaged proof both) on the scheduled scan-first baseline. However every due run starts the first 100/200 scanned entries and does not automatically visit later yt-dlp playlist index windows.

## Implementable slice and invariants

1. Only when a **verified explicit** `engine='video'` yt-dlp scan has `scan_window.next_start`, schedule the next finite window with the existing `continuation_scan_payload` contract. Keep immutable URL/folder/account/expected_identity, playlist index window, `sync_schedule_id` and original `sync_schedule_slot` to satisfy worker snapshot validation. Job identity remains distinct for every due schedule slot.
2. Continue only **after** the preceding scan has succeeded and its new-only reconciliation marker was persisted; pending/running/blocked/failed/canceled/unprocessed continue to prevent overlap. Invalid next-window metadata fails closed; unsupported engines/gallery, provider unknown and exhausted/2,000-item snapshots restart from the first window on subsequent due cycles, not as a provider checkpoint.
3. A continuation scan's `items` must extend its **verified parent result prefix unchanged**, have no more than one new page, match its strict parent snapshot/platform and window metadata, and not exceed the cumulative 2,000-item limit. Select only newly appended safe unique URL rows; reconcile them against exact account/adapter/output job history, then use existing atomic batch and persisted processed marker. Never re-enqueue the whole cumulative history or use a mismatched parent/account.
4. Add an optional `start_index` argument to `selectable_sync_indices`: dedupe URLs across the entire cumulative list but apply the 500-item cap only to newly appended rows. Existing manual and first-window behavior must remain unchanged. Always show unknown/partial completeness; do not infer provider-native pagination or whole-channel completion.
5. Tests: first window → next yt-dlp page → last page → next-cycle restart, prior-window duplicate URL not re-selected, unselectable URL behavior, tampered parent prefix/window/account/mode rejection without partial jobs, 2,000-item cap and preserved job snapshots. Test on real SQLite synthetic jobs; no live account or provider requests.
6. Full `scripts/check_plan.py`, source suite, build desktop/native host, frozen packaged proof on Linux/Windows at exact code SHA, followed by updates to P05/P10 results, coverage, current status, ledger, traceability and user guide. Keep `main` unchanged; never commit secrets/media.

## Excluded acceptance

Index windows are **not** provider-native checkpoints. Live 10-platform coverage, authenticated Chrome connector, region/rights, actual channel/playlist ordering changes, content older than the cumulative limit, gallery pagination, corrupt old-file repair, physical Windows/installer/GPU, OS scheduling when app is closed and SQLite issue #6 remain OPEN. Full P05/P10 acceptance cannot be claimed from synthetic tests.
