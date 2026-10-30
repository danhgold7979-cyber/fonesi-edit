# P05-06 / P10-02 — Bounded scan-first scheduled new-only synchronization

**Checked:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`, integration `develop/fonesi-full`. **Initial code HEAD:** `c0405c45bb8646874bf6b1a2046a6a907b5fdc9e`. **Status:** implemented with Linux/Windows source and packaged CI evidence at SHA `23f750a8b7c9b9238ca766ee1c1c8cd287379f99`; full P05/P10 OPEN.

## Master alignment and actual gap

Checked `AGENTS.md`, `README.md`, `IMPLEMENTATION_PLAN.md` P05-02/03/06 and P10-02, `PRODUCT_REQUIREMENTS.md` §3.2/8, `REQUIREMENTS_TRACEABILITY.md` SRC-03/SRC-09/SRC-10 and AUTO-02, `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, `P05_PLAN/RESULTS`, `P05_SECOND_SYNC_PLAN.md`, `P10_PLAN/RESULTS`, `automation.py`, `sync.py`, `downloads.py`, `ui/pages.py`, `storage.py`, and unit/Qt tests. Manual new-only sync already plans against historical verified files; the current `Automation.schedules()` instead unconditionally enqueues `download` on a full channel URL at every due interval, risking redundant fetching. The schedule must *not* be described as new-only until the provider scan result is validated.

## Work and safety acceptance

1. Save new UI schedules with explicit `mode='scan_new_only'`; preserve existing schedule rows in SQLite. Legacy mode-less rows are treated conservatively as scan-first, not silently downloaded. Unknown schedule modes are rejected with a recoverable diagnostic. The timer is active only while Fonesi Edit is running.
2. A due schedule enqueues one `scan` job with a 1–200 item scan-window limit (if original limit=0, cap at 100; if >200, cap at 200) and a stable per-slot key; carry immutable URL/folder/engine/media/account/expected identity and schedule ID/slot. Never treat this as a provider-native cursor, full channel or guaranteed new-only scan.
3. Track one active scan per schedule in existing persisted cache. Do not create a second scan if the previous scan is pending/running/blocked, failed/canceled awaiting explicit Queue retry, or succeeded but its new-only planning is not yet committed. Only after a validated successful scan's new-only requests have been enqueued atomically and marked processed may another due scan start.
4. Consume successful scheduled scan output through the same safe URL, selectable/duplicate, snapshot and verified-history guards as manual new-only synchronization. Cap 500 candidate items. Derive per-item jobs from that **scan's** snapshot, remove schedule-only metadata, enqueue through one transaction via `submit_many_once` with the same cross-scan identity as manual sync. Persist a processed marker *after* enqueue, permitting crash recovery/idempotent replay without duplicates. Never overwrite existing media or count malformed artifacts as complete.
5. Add synthetic unit/SQLite/Qt tests for legacy schedule migration, scan-before-download, overlap guard, failure/retry block, successful scan old+new+duplicate resolution, partial scan flag, corrupt previous artifact halting all new enqueues, repeated processing and restart, 500-item cap, provider/account isolation. No live accounts or paid APIs.
6. Run exact locked tests, plan checker, Linux and Windows desktop/native-host build and frozen packaged proof on the code SHA; only after evidence update results, traceability, coverage, status, ledger and user guide. Keep `main` unchanged.

## Remaining external gates

True provider pagination/checkpoint, live ten-platform channels, Chrome identity/permission/region behavior, user-machine Windows/installer/GPU tests, corrupted media repair, URL-alias/channel rename reconciliation, unattended OS service/Task Scheduler while app closed, and intermittent SQLite issue #6 remain OPEN. A finite scan window never proves full-channel synchronization.

## Verified results — 29/10/2026

- [x] UI stores `scan_new_only` mode; legacy mode-less schedule rows execute scan-first, never as unconditional recurring channel downloads.
- [x] Each due cycle bounds the scan at 100 items when unlimited, maximum 200 when a limit is specified; retained source/account/slot identity and one active unprocessed scan per schedule prevent silent overlap.
- [x] A successful scan uses safe URL dedupe, validated exact history, the same atomic batch job identity as manual sync, a persisted processed marker, explicit Retry for failed scans and no-overwrite of media.
- [x] Synthetic backend/Qt tests cover old+new media, corrupt old output, retry, account binding, 501-item cap, historical mode-less schedules and replay without duplicates.
- [x] [CI 40857385183](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40857385183) **SUCCESS attempt 1** on [23f750a](https://github.com/danhgold7979-cyber/fonesi-edit/commit/23f750a8b7c9b9238ca766ee1c1c8cd287379f99): **546 Linux PASS /545 Windows PASS+1 intentional POSIX skip**, desktop/native-host/frozen proof both systems PASS.
- [ ] Full provider checkpoint/channel coverage, Chrome/account/region, OS scheduling after app closure, physical Windows/GPU/installer, issue #6 and corrupt-artifact repair remain OPEN.
