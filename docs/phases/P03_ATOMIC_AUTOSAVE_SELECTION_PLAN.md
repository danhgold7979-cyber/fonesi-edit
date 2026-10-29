# P03-07 / P11-02 — Atomic project autosave and last-project selection

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only branch:** `develop/fonesi-full`. Plan written before code.

## Reviewed baseline

Reviewed `AGENTS.md`, `README.md`, master `docs/IMPLEMENTATION_PLAN.md` P03-02/P03-07/P11-02, `PRODUCT_REQUIREMENTS.md`, `REQUIREMENTS_TRACEABILITY.md` OPS-03/OPS-05, `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, P03/P11 plans/results, `src/fonesi_edit/storage.py`/`app.py` and storage/Qt regression tests. The source/test [CI 40902670624](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40902670624) passed both runners, 607 Linux / 606 Windows + 1 intentional skip, and frozen desktop/native-host proof. [Intermittent Windows SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) is still OPEN with unknown root cause.

`MainWindow.autosave` currently saves the project row through `Store.save_named`, then writes the `last_project` setting through a separate SQLite transaction. A fault in the second write leaves the row persisted with a missing/stale pointer. For a first project, conservative startup recovery rightly rejects an ambiguous set of DB rows, making edits effectively inaccessible in the automatic restore path. The existing atomic recovery.json fallback limits but does not eliminate this partial-commit gap. Do not select an arbitrary DB project or relax recovery identity checks.

## Implementation and regression sequence

1. Add an opt-in `select_as_last` flag to `Store.save_named`, valid only for `projects`. Upsert project data and JSON-encoded `last_project` **in one connection/transaction**, reusing existing validation, no DB schema/WAL changes. Default calls and preset handling remain unchanged.
2. Use this atomic operation in `MainWindow.autosave`, retaining the immutable composition snapshot, recovery.json on failure, original propagated SQLite error, and close-event refusal/retry behavior; only set in-memory project_id after success.
3. Test fault **after** project upsert: SQLite `BEFORE INSERT` and `BEFORE UPDATE` triggers reject the `last_project` setting. Both first-save and existing-project update must roll back the row and pointer. Test normal retry after removing trigger, preset unaffected and invalid preset selection rejected.
4. Add real Qt integration test with induced selection-setting failure: current composition reaches recovery.json; earlier SQLite row, identity and selected pointer remain intact; recovery error is propagated; a later retry saves without duplicate projects.
5. Run `scripts/check_plan.py`, targeted tests, then the complete Linux/Windows CI source suites, production desktop/native host and frozen packaged proof on the exact code/test SHA. Record only CI-confirmed outcomes in P03/P11 results, coverage, status and ledger; no `main` merge.

## Acceptance

- [x] Project and `last_project` commit or roll back together on deterministic failure.
- [x] Original data, preset/default callers, recovery on error and retry are preserved.
- [x] Exact source/test SHA passes both CI runners and frozen packaged proofs.
- [x] Update evidence; retain SQLite #6 OPEN until independently reproduced and cause-specifically fixed.

External blockers remain physical Windows NTFS/AV/ACL and power loss soak, real Chrome/auth and provider sessions, GPU/HiDPI, Windows installer and full 95-group acceptance. This is a partial-commit fix, not a claim that the intermittent SQLite corruption has been solved.

## Verified implementation and limits (2026-10-29)

[source/test d4117b5](https://github.com/danhgold7979-cyber/fonesi-edit/commit/d4117b580b90ff4b8471907b8e8b1fc56d702a4d) changes `Store.save_named(select_as_last=True)` so the project row and JSON `last_project` setting write within the same SQLite transaction, and `MainWindow.autosave` opts into it. Default project/preset saves remain unchanged. The second statement is fault-injected with real SQLite `BEFORE INSERT` and `BEFORE UPDATE` triggers, proving complete rollback for a new/existing project; a real Qt test confirms recovery.json keeps unsaved edits, the former committed row/pointer do not change, and successful retry writes one selected project.

[CI 40905102578](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40905102578) is **SUCCESS on exact source/test SHA d4117b5**: Linux **611 passed**, Windows **610 passed + 1 intentional POSIX-only skip**; plan validator, desktop/native-host build and packaged frozen synthetic/localhost verification PASS both CI runners. Windows development artifact was uploaded. This verifies atomicity under injected SQLite statement failures, **not** physical Windows/NTFS/antivirus power-loss durability or the root cause of open [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). Full P03/P11/product acceptance remains OPEN.
