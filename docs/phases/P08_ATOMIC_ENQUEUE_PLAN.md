# P08-07 / P11-02 — Atomic all-or-nothing Batch job enqueue

**Date:** 2026-10-29. **Repository/branch:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`. Written before code.

## Reviewed scope and existing implementation

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` P08-07/P11-02, `docs/PRODUCT_REQUIREMENTS.md` §5/§9 (one bad job must not lose its whole batch, persistent snapshots), `docs/REQUIREMENTS_TRACEABILITY.md` BAT-04/OPS-03/OPS-06, `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, P08/P11 plans/results, `src/fonesi_edit/batch.py`, `storage.py`, `ui/pages.py`, `matrix.py`, and related tests. The existing `enqueue_batch` calls `Store.submit('render', ...)` separately per item. Each call commits its own SQLite transaction, so a second-row disk/constraint failure leaves the first job pending with no complete batch receipt. Matrix enqueue and new-only sync already use atomic grouped transactions; Batch needs the same invariant without changing their paths.

P08 cancelled-progress/benchmark source+test SHA `6534c41` and its CI are checked independently; do not claim full acceptance until exact Linux/Windows proof. This new transaction slice must not reset previous work or merge `main`.

## Implementation and tests

1. Add `Store.submit_many(kind,payloads,priority=0)` with the same allowed kind, immutable JSON validation and app-owned `_tools` snapshot as `Store.submit`. Materialize and validate the **entire** batch and snapshot tools once before the transaction, then `BEGIN IMMEDIATE` and insert all pending jobs with independent IDs/timestamps in one `Store.connect` scope. A database error or validation failure must create **zero** new jobs; existing unrelated jobs remain.
2. Refactor `enqueue_batch` to build validated render payloads before calling `submit_many`, reject empty/malformed output paths and duplicate target paths within a batch, preserve source/composition/preset/seed/warnings exactly, never read or modify source media or publish final output files. Preserve empty-batch compatibility with `[]` and legacy `Store.submit` callers.
3. Add deterministic SQL `BEFORE INSERT` trigger rejecting the *second* render request. Confirm previous rows unchanged and transaction rollback; drop trigger and retry successfully with the same deterministic output snapshot. Verify `_tools` snapshot, no secret payload and original plans unchanged; missing output/duplicate target validation fails before enqueue.
4. Add Qt BatchPage regression: after SQLite second-row failure the UI retains the dry-run for retry, does not navigate to Queue or expose partially queued jobs; after removing the fault, both jobs commit and Queue navigation occurs. Existing cancel/partial plan tests and frozen verifier must not regress.
5. Run `scripts/check_plan.py`, focused storage/Batch/Qt tests and full Linux/Windows CI including the 128-file FFprobe benchmark, desktop/native-host build and frozen synthetic/localhost proof on the **exact** source/test SHA. Update results, coverage, status and execution ledger only after real evidence.

## Bounded acceptance

- [x] Full or zero job enqueue on real SQLite failure, previous jobs untouched; all payloads validated with a single app-owned tool snapshot.
- [x] Duplicate/malformed outputs are rejected before insertion; Qt retains safe dry-run on failure and retries with no duplicates.
- [x] Legacy `Store.submit` semantics and existing Batch/Matrix/download workflows unaffected; Linux/Windows tests, benchmark and frozen CI PASS on code/test SHA.
- [ ] Full P08/P11, physical Windows user machine/AV/NTFS/ACL/power-loss soak, live Chrome/provider/GPU/HiDPI and intermittent [SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remain OPEN.

No SQLite schema change, force push, `main` merge, destructive WAL repair, downloaded/private media or credential artifacts.

## Verified implementation and evidence

[Source 5c35b2f](https://github.com/danhgold7979-cyber/fonesi-edit/commit/5c35b2f8ab989c05346c01adefe77e27f6e8a0dc) adds `Store.submit_many`: a single app-owned tool snapshot is validated for every payload *before* the transaction, then all rows are inserted under `BEGIN IMMEDIATE` in one `Store.connect()` scope. `enqueue_batch` now checks each composition/output and rejects duplicate resolved targets before publishing anything. Existing single-job submission is unchanged. [code/test d6b218a](https://github.com/danhgold7979-cyber/fonesi-edit/commit/d6b218af9a7bd6cc0ac2a9789c3d9fec224da664) adds SQLite second-INSERT trigger faults proving rollback, preservation of earlier unrelated jobs, full retry, payload/tool consistency, and Qt no-navigation/no-partial-queue until successful retry.

[CI 40916078055](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40916078055) **SUCCESS exact SHA d6b218a**: 631 Linux passed / 630 Windows passed + 1 intentional POSIX-only skip; source, 128-file FFprobe benchmark, desktop/native-host and frozen packaged synthetic/localhost proofs passed on both runners. Windows development artifact uploaded. No real device installer/NTFS/AV/power-cut, GPU or live-source acceptance is implied, and intermittent [SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remains OPEN with UNKNOWN root cause. This prevents deterministic partial batch enqueue but does not repair database corruption.
