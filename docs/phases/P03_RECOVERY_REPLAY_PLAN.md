# P03-07 / P11-02 — Safe recovery.json replay after SQLite autosave failure

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only integration branch:** `develop/fonesi-full`. Plan recorded before source/test edits.

## Reviewed baseline

Compared `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` P03-02/P03-07 and P11-02/P11-07, `docs/PRODUCT_REQUIREMENTS.md` §9, `docs/REQUIREMENTS_TRACEABILITY.md` OPS-03/OPS-05, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, P03/P04/P11 plans/results, the latest [CI 40899468715](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40899468715) and open intermittent SQLite [issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). Reviewed `src/fonesi_edit/app.py` (autosave/restore/closeEvent), `src/fonesi_edit/storage.py`, `src/fonesi_edit/domain.py` and the Qt integration suite.

At code/test SHA `50a0137`, `autosave()` attempts atomic `recovery.json` when `Store.save_named` or `last_project` setting fails; `closeEvent` refuses shutdown until save succeeds. **But `MainWindow.restore()` currently reads only SQLite `last_project` and project rows**; it never replays the independently preserved recovery snapshot on a subsequent healthy startup. This leaves a real recovery workflow gap even if the initial write worked.

## Implementation

1. Add conservative `recovery.json` replay on startup when SQLite itself opens normally: validate schema/version and parse the snapshot with `Composition.from_dict`; bound the file size, ignore malformed/unreadable JSON rather than crashing. Never copy untrusted source media or change browser credentials.
2. If SQLite has a selected project, replay **only** a recovery snapshot with the same `project_id` and a later filesystem modified timestamp than that project's `updated` timestamp, and only if the composition differs. A stale or cross-project snapshot must never replace the selected project.
3. If the SQLite database has no projects at all and no `last_project`, allow a valid recovery snapshot to restore a previously unregistered composition (without modifying any database rows until explicit/normal autosave). If other project rows exist but none is selected, refuse ambiguous recovery. Surface a concise UI status when a snapshot is chosen.
4. Add Qt regression for new/older/mismatched/corrupt recovery snapshots, preserved SQLite rows before autosave and successful saved/reopened project on later healthy close; one test must exercise the preceding SQLite fault-injected autosave path. Include recovery file-source and project identity invariants.
5. Run `scripts/check_plan.py`, full Linux and Windows CI (regression, desktop/native-host build, frozen packaged proof) on exact source/test HEAD. Update results/coverage/status/ledger only with complete real CI evidence. No `main` merge.

## Bounded acceptance

- [ ] Newer matching snapshot can be replayed after SQLite autosave failure, preserving edits and project ID.
- [ ] Stale, cross-project, malformed and ambiguous recovery never override a valid SQLite project or crash the UI.
- [ ] Startup replay does not immediately write SQLite; normal subsequent autosave makes recovery durable in the selected record.
- [ ] Linux/Windows full test suite and frozen desktop/native-host proof PASS on the exact source/test SHA.

**Not accepted:** recovery if SQLite itself cannot initialize/open, long physical Windows NTFS/AV and sudden power-loss soak, entire 95 requirement gates, live providers, Chrome/auth and GPU. Intermittent Windows [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remains OPEN with root cause UNKNOWN. No destructive WAL/SHM repair or automatic database file replacement.