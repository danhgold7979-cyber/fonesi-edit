# P09-01 / P09-04 / P11-05 — Scene ordering in the unified Matrix UI

Date: 2026-10-30. Repository: `danhgold7979-cyber/fonesi-edit`; integration branch: `develop/fonesi-full`. This plan is committed before implementation and tests.

## Baseline and traceability

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` P09-01/04/05/06 and P11, `docs/PRODUCT_REQUIREMENTS.md` §7, `docs/REQUIREMENTS_TRACEABILITY.md` MAT-01/MAT-04/MAT-05/MAT-06/MAT-07, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, P09_PLAN/RESULTS and `src/fonesi_edit/matrix.py`, `ui/pages.py` and their integration tests. Current scan uses natural folder ordering; MatrixPage has no interactive scene-order control. The generator, edit/lock/regenerate and row render already exist. Prior exact-HEAD CI 41001886531 passed Linux and Windows packaged synthetic verification. This is **not** physical Windows/user acceptance.

## Scope and invariants

1. Add an explicit Matrix scene list with internal drag-reorder and Up/Down commands. Show original source folder, the current logical C index and number of candidate angles; no filesystem rename/deletion. Save the chosen folder order for this input root and restore it on the next scan only if the same complete set is present.
2. Add a pure `reorder_matrix_scenes` transform: validate a true permutation and all current row/lock indices, keep immutable source `path/hash/index`, renumber only the display/logical `Angle.scene`; transpose every planned row, every locked scene column and corresponding history. Preserve the current row count, selected row, W/K, and all source bytes. No silent fallback on invalid state.
3. Existing SQLite history stores ordered content hashes, not original scene-folder identities. When a saved reordered arrangement is loaded, reconcile historical hashes by *unique* current-scene membership. Reject an ambiguous/missing historical identity rather than guessing, relaxing W/K or rewriting history. In the render enqueue transaction, reconcile history against the current scene order and check duplicates/W/K again before inserting any jobs. Keep legacy callers and DB schema unchanged.
4. Reorder per-scene weight/manual-duration input vectors together with their scene; if a populated vector is malformed, reject the reorder without changing it. A drag/new order must invalidate stale async generation/regeneration/preview results so they cannot overwrite later edits; existing queued renders retain their immutable old snapshots.
5. Add backend regression for permutations, history alignment, scene/angle hash identity, original data immutability, lock remapping, W/K, invalid/ambiguous history and all-or-none enqueue refusal; Qt integration for drag/buttons, redisplay, persistence, plan revision, manual vectors and rendered/composition scene order. Run syntax/tests/check_plan, Linux + Windows full CI, build/native-host/frozen synthetic proofs.
6. Update P09_RESULTS, CURRENT_STATUS, IMPLEMENTATION_COVERAGE, traceability/evidence and ledger **only after** the code/test SHA has real CI results. Never mark entire P09 or the full 95-group product accepted on synthetic proof.

## Acceptance boundaries

- [ ] Reordering in actual Qt Matrix UI changes output clip order and C/G formula without changing source files or rewriting old queued jobs.
- [ ] Scene locks, per-scene inputs, deterministic row identity and W/K/history do not silently change; historical ambiguities fail closed.
- [ ] Stale background callbacks are discarded, saved order is restored only for matching source scenes, and malformed preferences cannot corrupt a matrix.
- [ ] Regression + exact-HEAD Linux and Windows packaged CI pass.

Still OPEN: advanced scene-level locking/exclusion and collision-proof identity across changed source archives, solver large-corpus optimality, real Windows/exFAT/NTFS/power loss, Chrome/live platforms, GPU, installer and unrelated SQLite issue #6. No force push and no merge to `main`.
