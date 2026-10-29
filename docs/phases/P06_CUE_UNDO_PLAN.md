# P06-04 / SUB-05–06 — Undo/Redo for the subtitle cue table

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only branch:** `develop/fonesi-full`.

## 1. Baseline and master alignment

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P06-04, P03-07, P11-05), `docs/PRODUCT_REQUIREMENTS.md` §4.1–4.2, `docs/REQUIREMENTS_TRACEABILITY.md` (SUB-05/06, ED-05, OPS-03), `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, `docs/phases/P06_PLAN.md` and `P06_RESULTS.md`; reviewed `SubtitlesPage` and shortcut focus policy in `app.py`, plus Qt integration tests. Prior integrated HEAD `3af860c` and its [Linux/Windows successful CI](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40865037839) were verified before this plan.

Existing editor canvas Undo uses its own QUndoStack; the subtitle table currently provides no history. The table's draft persistence uses raw text, allowing temporarily invalid time fields; `collect()` converts/validates them and can fail while a user edits. A safe cue history must preserve raw cells and stable cue IDs, not call `collect()` after each keystroke and accidentally discard invalid text.

## 2. Bounded code slice

1. Add a local, bounded in-session edit history (100 table states) for **all five cue columns plus stable cue IDs**. Record user `itemChanged` cell edits/check toggles. Record each bulk operation (add, split, merge, offset, search/replace, translation result load) as one atomic step despite `refresh` replacing multiple cells.
2. Provide visible **Hoàn tác câu / Làm lại câu** actions and use the existing global Ctrl+Z / Ctrl+Shift+Z to operate on this history **only while the Subtitle tab owns the current view**, without modifying Editor canvas history. If a live QLineEdit/QTextEdit editor has focus, native text Undo/Redo retains priority, including during Qt item editing and IME.
3. Undo/Redo must restore raw invalid timestamps (without parsing them), original/translated strings, check states, row count and IDs, update cue warnings and schedule draft persistence. A new user edit after Undo invalidates redo; loading a different subtitle document resets only cue history, not editor undo.
4. Regression tests: table edit + checkbox; structural split/merge as single history steps; invalid interim time input; undone draft reopens correctly; redo invalidation; applied translation undo without altering worker data; tab-sensitive Ctrl+Z; new document reset. Keep snapshots isolated from tool credentials and downloaded media.

## 3. Acceptance and limits

- [x] Source and translated text, timing strings (including invalid drafts), lock state, row identities and row counts round-trip via Undo/Redo.
- [x] Bulk actions are single Undo steps, no spurious history from programmatic refresh, and new edits invalidate Redo.
- [x] Subtitle Undo/Redo does not consume the Editor's own history. Native text editing/IME gets priority when focused.
- [x] Draft persistence and recovery reflect the restored state; loaded new documents reset history.
- [x] Plan checker, focused tests, full Linux/Windows CI, native-host build and packaged app proof pass on the exact code/test SHA.

This is **bounded in-session** history (last 100 states), not an unlimited persisted edit journal. Remaining P06 acceptance stays **OPEN**: per-cue timeline drag, live provider translation/quality/cost, large corpora, real Windows user/HiDPI/font/GPU, Chrome-authenticated source access and power-loss/long soak. Known intermittent Windows SQLite [issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remains a separate unresolved blocker. Do not merge to `main`.

## 4. Verified implementation and acceptance (29/10/2026)

- [Source/test commit 39dc892](https://github.com/danhgold7979-cyber/fonesi-edit/commit/39dc8927cb6b372974f8e1e599331374d4f0a389) adds bounded raw-cell history, atomic bulk refresh, draft persistence and tab-aware shortcuts. [Initial CI 40867002996](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40867002996) found exactly one failed focus assumption on both runners: an editable `QComboBox` owned focus instead of its internal `QLineEdit`; this was not a production crash. [Fix 8bfddb8](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8bfddb8eef811b4421e7c2d7e2a3c02d197a3c3f) makes native Undo work for either focus proxy and updates the assertion without dropping the test.
- [CI 40867450628](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40867450628) **SUCCESS on exact fix SHA `8bfddb8`**: **568 Linux passed**, **567 Windows passed + 1 intentional POSIX fixture skip**. Plan validation, production desktop/native-host builds and frozen packaged proof PASSED on both runners; a Windows development artifact was uploaded.
- Implementation is a **100-entry, in-session** cue-table history. It covers table cells, locks, bulk edit operations, translations and raw invalid draft timestamps. It does **not** persist Undo commands across app restarts, provide unlimited history or add draggable per-cue time segments. Those full acceptance gates remain open.
