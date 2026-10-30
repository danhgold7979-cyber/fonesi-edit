# P05-06 — Atomic cross-scan new-only enqueue and selectable-row reconciliation

**Checked:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Integration branch:** `develop/fonesi-full`. **State:** implemented and verified by synthetic CI on SHA `c0405c45bb8646874bf6b1a2046a6a907b5fdc9e`; full P05 OPEN.

## Master requirements and previous implementation

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` P05-02/03/04/05/06 and P10 scheduling, `PRODUCT_REQUIREMENTS.md` §3.2–3.3 and §8, `REQUIREMENTS_TRACEABILITY.md` SRC-03/08/09/10, `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, `P05_PLAN.md`, `P05_RESULTS.md`, `P05_SECOND_SYNC_PLAN.md`, plus `sync.py`, `storage.py`, `automation.py`, `ui/pages.py`, `tests/test_sync_new_only.py`, `tests/test_app_integration.py` and `tests/test_automation_dependencies.py`. Starting HEAD `daf6f7a` has Linux/Windows source/build/frozen-proof CI SUCCESS, but repeat-scan new-only results are not yet recorded in phase results. The existing UI runs a correct pre-enqueue plan, then submits each new item in its **own** transaction; a later insertion failure could leave a partial batch, contrary to the P05 second-sync safety plan. Duplicate URL indexing also includes explicitly unselectable rows, so such a row may hide a later safe row.

## Changes and acceptance

1. Implement `submit_many_once` with **one** SQLite `BEGIN IMMEDIATE` transaction for an approved batch of 1–500 job requests, validating all snapshots before inserting any row. Keep stable identity hash and `checked_payload` security policy; deterministic ordering, reject repeated identities with incompatible job contents and reject a pre-existing key used for a different job kind/snapshot. Return created/existing counts; rollback **all** inserts on a second-row SQL failure. Retain existing `submit_once` behavior for other workflows.
2. In `sync_new_filtered`, keep the full `plan_new_only_sync` validation and account snapshot before calling the batch helper, and report **actual** newly enqueued count. No hidden checkbox edits or partial enqueue when a group contains a corrupt prior artifact, account conflict or invalid snapshot. The independent scan result remains partial/unknown; no provider checkpoint claim.
3. Compute first selectable, safe row per URL (ignoring earlier `selectable=False` entries) consistently in scan rendering, filtering, select-all and new-only sync. Never make an unselectable row downloadable, never select the same URL twice.
4. Require that every ancestor directory of an existing output file inside the platform root be a real directory, not a symbolic link. Avoid deleting or rewriting media; continue FFprobe/QImageReader validation.
5. Test batch transaction rollback using a real SQLite trigger that rejects the second insert, duplicate key collisions, invalid payload before write, legitimate idempotence, later-selectable duplicate URL in Qt (cross-page/filter), and corrupted output/symlink directory cases. Full `check_plan.py`, `pytest -q`, Linux/Windows desktop/native-host packaging and frozen proof at exact commit via Actions.
6. Only after verified tests, update `P05_SECOND_SYNC_PLAN.md`, `P05_RESULTS.md`, `CURRENT_STATUS.md`, `IMPLEMENTATION_COVERAGE.md`, `PHASE_EXECUTION_LEDGER.md` and `USER_GUIDE.md` with SHA/CI evidence. Preserve source/account safety and never merge into main.

## Not yet accepted

Automated schedule currently schedules direct channel downloads and is **not** equivalent to scan-first new-only sync; fix separately with plan and tests (P05-06/P10). Provider-native pagination/checkpoints, moving/renamed channel and URL alias reconciliation, 10-platform/Chrome-account/region tests, damaged old artifact repair, installer/physical Windows/GPU, and intermittent SQLite issue #6 remain OPEN. CI synthetic success is not live acceptance.

## Verified results — 29/10/2026

- [x] One SQLite `BEGIN IMMEDIATE` transaction covers the 1–500 new-job group, rejecting changed/duplicate identities and rolling back every INSERT if a later row fails.
- [x] Qt filtered sync accurately reports newly created/reused jobs and keeps hidden checkboxes; disabled duplicate URL rows cannot obscure later selectable safe rows.
- [x] Existing media under symlinked channel ancestors are not considered valid; FFprobe/QImageReader and original-file preservation regressions retained.
- [x] [CI 40855868306](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40855868306) **SUCCESS attempt 1 on [c0405c4](https://github.com/danhgold7979-cyber/fonesi-edit/commit/c0405c45bb8646874bf6b1a2046a6a907b5fdc9e)**: **537 Linux /536 Windows +1 skip**, desktop/native-host build and frozen packaged proof PASS both.
- [ ] Live provider/full-channel/real Chrome/physical Windows and intermittent SQLite issue #6 remain open.
