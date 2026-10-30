# P09-06 / P11-02 — Cancel-safe Matrix enqueue and stale-snapshot revocation

**Date:** 2026-10-30. **Repository/branch:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`. Commit this plan before source changes.

## Master and current-code review

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` P09-04/05/06 and P11-02/05, `docs/PRODUCT_REQUIREMENTS.md` sections 7–9, `docs/REQUIREMENTS_TRACEABILITY.md` MAT-05/MAT-07/OPS-02/OPS-04/OPS-06, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, P09 plan/results, `src/fonesi_edit/matrix.py`, `src/fonesi_edit/ui/pages.py`, `src/fonesi_edit/ui/tasks.py`, `src/fonesi_edit/app.py`, `src/fonesi_edit/storage.py` and matrix/Qt/SQLite tests. Existing Matrix enqueue prebuilds row compositions with real FFprobe, then inserts all jobs/history in one transaction; it does not use Task's cooperative cancel flag. If an in-progress enqueue becomes obsolete due to user edits, the backend may still publish immutable jobs for the old visible matrix. Existing live/Chrome/GPU/physical Windows acceptance stays separate.

Previous exact source/test [CI 41021003352](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41021003352) PASS on SHA `7d1f928a`, Linux 728 tests, Windows 727 + one POSIX-only skip and both frozen builds. Follow-up documentation commit `756902c3` has a separate CI; do not attribute old results to it.

## Implementation contract

1. Add an optional cooperative `cancel` parameter to `enqueue_rows` preserving old callers. Check before and after each expensive composition preflight, before opening the SQLite transaction, between each row reservation and before commit. On cancellation raise a distinct `MatrixEnqueueCancelled` (subclass RuntimeError) so SQLite context manager rolls back all new jobs and all matrix reservations. A canceled enqueue must not mutate source media, old queue rows or on-disk output.
2. In MatrixPage, capture a versioned scene/preset/settings snapshot and a cancel token for an enqueue request. New explicit source scan, changed C/G checkbox/pin, moved C scene, matrix edited/locked/regenerated, changed output/audio/weights/durations/W/K/seed or a new generation request set this token to revoke obsolete pre-publication work. The global `Hủy tác vụ chuẩn bị / preview` task cancellation must also reach `enqueue_rows`. Reject concurrent duplicate clicks on Render Matrix. Preserve queued jobs after a successful commit; do not pretend a late cancel can undo a commit.
3. Distinguish canceled/stale preparation from completed enqueue in user messaging. Callback must avoid switching to Queue on cancellation; committed job IDs may be reported even if visible selection has since changed, with explicit immutable-snapshot note rather than claiming cancellation succeeded. Never delete existing jobs for UI changes.
4. Tests: real synthetic clips + SQLite transaction fault/cancel after multiple row inserts (zero new jobs/reservations), cancellation mid-FFprobe composition (no partial), normal unchanged queue commit, Qt background late checkbox/reorder/config change (no obsolete queue publication), global Task.cancel and double-click guard; previous full suite untouched.
5. Run check_plan, focused tests where possible, full CI Linux/Windows, production/native-host/frozen packaged proof. If an intermediate CI fails, fix rather than weaken assertions, and only close bounded acceptance after exact-SHA success. Update P09_RESULTS/CURRENT_STATUS/COVERAGE/TRACEABILITY/ledger then. Do not merge into `main`.

## Bounded acceptance

- [x] Canceled Matrix enqueue publishes no new jobs/history for a pre-publication cancel, and already existing rows remain intact.
- [x] Qt obsolete matrix/snapshot changes revoke active preparation, duplicate Render clicks are blocked, and a successful completed commit is not silently removed.
- [x] Normal legacy callers and non-canceled Matrix render/scheduler paths behave exactly as before.
- [x] Full CI Linux and Windows at exact code/test SHA and packaged synthetic proofs PASS.

**External blockers:** real NTFS/exFAT loss-of-power and SQLite intermittent issue #6, user Windows controls/HiDPI/installer, live Chrome/provider, GPU/audio and large solver performance remain OPEN; this slice does not close P09 or the 95 requirements.

## CI regression follow-up (30/10/2026, before repair)
- [CI 41022883448](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41022883448) at SHA `a09af716bbacbadafd274154105d672d132f1a94` is **FAIL** on both Linux and Windows. Source unit suite logged 6 failures all caused by `sqlite3.OperationalError: no such column: excluded.job` at `matrix.enqueue_rows` UPSERT on the newly added cancel-safe path; Linux 746 passed / 6 failed. The actual `matrix_history` column is `job_id`.
- First change the erroneous `excluded.job` to `excluded.job_id` without modifying schema, data, cancellation rules or existing assertions. Add an explicit SQLite regression for retrying a failed reservation, ensuring the new queued job owns the `job_id` after an ON CONFLICT UPSERT; existing create/duplicate/rollback tests remain mandatory. Verify exact new commit on Linux and Windows CI and packaged proof before calling this regression resolved.

## Bounded CI evidence (30/10/2026)
[CI 41025266091](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41025266091) SUCCESS, exact code/test SHA `7d2d74a7173184d1e752e508ff83aa8971f72321`: 764 Linux PASS; 763 Windows PASS + one intentional POSIX skip; 128-source synthetic FFprobe benchmark, production desktop/native-host builds, frozen packaged render/Batch/Matrix/localhost/Qt proof PASS both runners. Windows development artifact 197,335,201 bytes, expires 2026-11-06. Synthetic/localhost evidence only; NOT physical Windows/HiDPI/installer, full 100k-real-media throughput/solver optimality, NTFS/exFAT/power loss, SQLite issue #6 root cause, live Chrome/provider or GPU acceptance.
SQLite cancel/preflight/after-INSERT rollback and Qt global cancel, edit, scene order and late commit are covered by automated tests.
