# P03-07 / P04-06 / P11-02 — Crash-safe recovery on autosave failure and bounded proxy/WAL shutdown stress

**Date:** 2026-10-29. **Only repository/branch:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`. **Status:** plan committed before changes.

## Baseline and alignment

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` P03-07/P04-06/P11-02, `docs/PRODUCT_REQUIREMENTS.md`, `docs/REQUIREMENTS_TRACEABILITY.md` OPS-03/OPS-05/ED-18, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, P03/P04/P11 plans and results, [open issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6), and current `storage.py`, `app.py`, `ui/editor.py`, `proxy.py` and Qt regression tests. Prior PRAGMA setup-handle cleanup [CI 40887831717](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40887831717) and baseline [CI 40895118199](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40895118199) PASS both runners; **neither proves the intermittent SQLite corruption fixed**.

The observed issue #6 traceback occurs at `closeEvent → autosave → Store.save_named`. Current `autosave()` writes `recovery.json` only **after** the SQLite project row and last_project setting succeed. If SQLite fails, the newest in-memory composition is not reflected in that independent recovery artifact. Current `closeEvent` does not guard failed persistence, potentially allowing an unhandled Qt close event while tasks are active. These are provable failure-boundary risks, but *not an established cause* of SQLite file corruption.

## Implementation slices

1. Make `autosave()` try to persist its current snapshot through SQLite normally, but on an SQLite/OSError write failure atomically write the same snapshot to per-user `recovery.json` before re-raising the original error. Do not silently mark the DB save successful or change schema/WAL/retry semantics. On normal completion keep the existing recovery file update.
2. On `QMainWindow.closeEvent`, attempt autosave before other settings; if any persistence operation fails, ignore the event, leave scheduler/background tasks alive for retry and display a sanitized actionable error with exception class rather than dumping database internals. Do not mark `_shutdown` true on failed persistence. Successful retry retains orderly shutdown. No destructive database or WAL cleanup.
3. Add a deterministic Qt failure-injection test simulating an SQLite `DatabaseError` during final autosave; assert event is ignored, latest composition is in atomic recovery JSON, the DB integrity remains `ok`, and clearing the injected error permits normal close/reopen with the desired composition. Preserve existing tests.
4. Add bounded repeat-open/repeat-close Qt stress (fresh SQLite database under a test-local path, alternating real proxy quality and guaranteed active cancel-aware background worker). Record SQLite `PRAGMA integrity_check`, journal_mode, database path and optional WAL/SHM presence before/after close and after reopening; verify source media bytes/mtime and all project rows are retained. Never delete/rename the database or sidecars as a workaround. Capture only synthetic fixture information, not credentials.
5. Run plan validator, focused Qt tests, full Linux+Windows suite, production desktop/native-host build and packaged frozen proof on the *exact* code/test SHA. Update P03/P11 results, coverage, status and ledger from actual evidence, not guessed metrics.

## Acceptance and exclusions

- [ ] Injection at `Store.save_named` makes the close fail safely but writes a validated latest recovery snapshot; original SQLite error is not silently discarded by direct autosave.
- [ ] Safe repeated proxy/background close/reopen yields `integrity_check=ok` and no lost project/media data; observed DB/WAL lifetimes documented.
- [ ] Same exact code SHA passes full Linux/Windows CI, desktop/native-host and frozen proof, without disabling tests.
- [ ] Root cause of the intermittent Windows corruption remains OPEN unless deterministically reproduced and tied to a verified repair. Stress non-reproduction only narrows the investigation.

**External blockers:** physical Windows NTFS/ACL/power-loss/antivirus interference, long soak and actual user media, live accounts/Chrome/GPU. No database schema change, no copying private files into Git, no `main` merge.
