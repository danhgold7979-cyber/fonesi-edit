# P08-07 / P11-02 — Batch enqueue existing-output preflight

**Date:** 2026-10-30. **Repository/branch:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`. Plan before implementation.

## Reviewed baseline
Reviewed AGENTS.md, README.md, docs/IMPLEMENTATION_PLAN.md P08-02/P08-07 and P11-02, PRODUCT_REQUIREMENTS.md §5/§11, IMPLEMENTATION_COVERAGE.md BAT-01…BAT-04, REQUIREMENTS_TRACEABILITY.md BAT-04/OPS-06, CURRENT_STATUS.md, PHASE_EXECUTION_LEDGER.md, P08 plans/results, src/fonesi_edit/batch.py, storage.py and Qt/SQLite tests. Latest HEAD `2d2ba79`; previous P08 atomic multi-enqueue proof succeeded at CI 40916078055; HEAD CI 40917626828 is independently running. Do not overwrite concurrent branch changes or merge main.

`enqueue_batch` already rejects duplicate resolved outputs and atomically inserts new jobs. However, a planned output that **already exists on disk** passes queue preflight and fails later in the no-overwrite renderer, potentially tying up the queue. A strict preflight can flag this deterministic collision while keeping already existing file bytes/mtime untouched. It is not a filesystem lease or a substitute for the final render's atomic no-overwrite publication.

## Slice
1. In `enqueue_batch`, after canonicalizing each target but before `Store.submit_many`, fail clearly on existing files, directories, or symlinks including dangling symlinks; check the *lexical* target before `resolve()` so an existing symlink does not hide a collision. Preserve duplicate target checks and composition/tool validation.
2. Regression: existing ordinary file and dangling symlink are rejected before any queue insertion; previous unrelated jobs, file bytes/mtime and plan inputs stay untouched. Valid new targets still enqueue atomically; do not delete or rename any media/output.
3. Qt regression: BatchPage keeps its dry-run and current tab on preflight collision, no new job; after choosing a distinct valid destination, retry enqueues correctly. No fake success.
4. Verify check_plan, source tests, desktop/native-host/frozen proof on exact code/test SHA Linux and Windows. Record results only after CI; real Windows filesystem/ACL/AV and race-with-concurrent-writer remain external gates.

## Acceptance
- [ ] Existing file, directory, symlink, dangling symlink do not enqueue, and original output remains unchanged.
- [ ] Batch group is all-or-none on collision; Qt retry works; no regression to no-overwrite finalizer.
- [ ] CI Linux/Windows and packaged proofs PASS on exact source/test SHA.
- [ ] Physical Windows, installer, live providers, Chrome/GPU, large-corpus render ETA and SQLite issue #6 remain OPEN.
