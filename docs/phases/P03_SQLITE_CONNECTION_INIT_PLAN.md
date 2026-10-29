# P03-07 / P11-02 — SQLite connection lifetime on WAL initialization failures

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only integration branch:** `develop/fonesi-full`. **Status:** plan committed before production change.

## Baseline and evidence

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` P03-07/P11-02, `docs/PRODUCT_REQUIREMENTS.md`, `docs/REQUIREMENTS_TRACEABILITY.md` OPS-03/OPS-05, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, `docs/phases/P03_PLAN.md` and P03_RESULTS/P11_RESULTS. Inspected `src/fonesi_edit/storage.py` and `tests/test_storage_jobs.py` and reviewed open intermittent [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6).

Source inspection found a narrowly reproducible resource-safety gap in `Store.connect()`: after `sqlite3.connect`, the method assigns row_factory and executes `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=15000` **outside** its `try/finally` block. If SQLite initialization PRAGMA raises under contention or I/O failure, that connection is not explicitly closed, potentially retaining a file handle on Windows. This is a concrete cleanup defect; its relationship to issue #6's intermittent `database disk image is malformed` error has **NOT** been established.

## Safe implementation and test slice

1. Put row_factory and both PRAGMAs inside the `try` guarded by a `finally: conn.close()`. Continue to rollback transactions only after the caller has entered the context and yielded, preserving successful commit/exception rollback behavior. Do not change WAL mode, busy timeout, recovery, backup files or DB schema.
2. Add deterministic parameterized fault-injection regression: wrap the real SQLite connection; inject a failure separately at `journal_mode=WAL` and at `busy_timeout=15000`; assert the error is propagated, underlying connection is **closed exactly once**, and no fake success/rollback occurs. Then remove injection and check normal settings write/read plus SQLite `PRAGMA integrity_check = ok`. Test on Linux and Windows.
3. Add explicit rollback sanity test for exception from inside the yielded connection while preserving existing database values, if needed.
4. Run exact SHA CI Linux/Windows (plan validator, full test suite, desktop/native-host build and frozen packaged app proof). Record regression evidence in P03_RESULTS/P11_RESULTS/coverage/status/ledger only after CI success.

## Bounded acceptance and external gates

- [ ] WAL PRAGMA failure closes its SQLite connection and still raises the original operational error.
- [ ] Busy-timeout PRAGMA failure also closes; normal settings operations and integrity still pass afterward.
- [ ] Transaction rollback, successful commit and backup/recovery tests remain passing without schema modification.
- [ ] Linux/Windows full CI and packaged proof pass on exact source/test SHA.

**Do not mark issue #6 fixed or close it** based on this isolated resource-cleanup improvement; deterministic reproduction of the intermittent Windows proxy/shutdown corruption, WAL lifetime analysis, NTFS/ACL/power-loss tests and physical Windows machine acceptance remain separate. No secrets, media or private Chrome data are introduced.
