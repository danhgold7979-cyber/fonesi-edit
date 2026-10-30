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

- [x] Reordering in actual Qt Matrix UI changes output clip order and C/G formula without changing source files or rewriting old queued jobs.
- [x] Scene locks, per-scene inputs, deterministic row identity and W/K/history do not silently change; historical ambiguities fail closed.
- [x] Stale background callbacks are discarded, saved order is restored only for matching source scenes, and malformed preferences cannot corrupt a matrix.
- [x] Regression + exact-HEAD Linux and Windows packaged CI pass.

Still OPEN: advanced scene-level locking/exclusion and collision-proof identity across changed source archives, solver large-corpus optimality, real Windows/exFAT/NTFS/power loss, Chrome/live platforms, GPU, installer and unrelated SQLite issue #6. No force push and no merge to `main`.

## Verified code, regression and CI (2026-10-30)

- [Plan-before-code a0c3710](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a0c371050c3ea74f6ed17647278e7914f7c0f5d7) → [matrix history/ordering ce5ce09](https://github.com/danhgold7979-cyber/fonesi-edit/commit/ce5ce096b25c9eb3ad4cd8bf9144bcf0cd94b428) → [Qt scene controls 7cefe29](https://github.com/danhgold7979-cyber/fonesi-edit/commit/7cefe2945e487f8df310d540693df06d42a089e6) → test and final concurrency hardening [3ff0e31b28d6c12caeaaf4ae60d7f79eb28818b8](https://github.com/danhgold7979-cyber/fonesi-edit/commit/3ff0e31b28d6c12caeaaf4ae60d7f79eb28818b8). All changes on `develop/fonesi-full`, not `main`.
- The actual MatrixPage has a drag-reorder scene list and Up/Down commands, original directory identification, persisted folder-specific order (only replayed for the exact complete folder set), safe logical C renumbering and reordering of row columns, locks, per-scene weights and explicit seconds. Source paths/hashes, selected row and already queued payloads remain unchanged. Stale generate/regenerate/preview callbacks are discarded; repeated identical generation requests supersede older requests.
- New pure helper reconciles legacy SQLite history only when an angle's source-scene membership is provably unique; ambiguity/missing asset causes an explicit error. The atomic render enqueue transaction checks cross-order duplicates and W/K again before writing jobs; no DB migration or historical rewrite.
- Regression includes bad permutations/locks/history, source immutability, actual FFmpeg render of a newly reordered clip sequence, same-scope reserved-history collision with zero partial jobs, Qt drag-handler/button/model/selection behavior, bad vector/preference handling and concurrent worker races.
- [GitHub Actions run 41016748802](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41016748802) **SUCCESS on exact code/test SHA `3ff0e31b28d6c12caeaaf4ae60d7f79eb28818b8`**: Linux **701 PASS**, Windows **700 PASS + 1 intentional POSIX-only skip**. Source plan check, 128-file synthetic FFprobe benchmark, production desktop/native-host builds and frozen application render/batch/matrix/localhost download/UI proof **PASS on both CI runners**. Windows development artifact was uploaded (197,307,982 bytes; expires 2026-11-06).
- **Still OPEN**: physically dragging with real Windows input devices, scene-level lock/exclusion refinements, legacy history where identical hashes belong to multiple scenes (conservatively rejected), large W/K/history solver stress, NTFS/exFAT power-loss, SQLite issue #6, GPU, live providers/Chrome and every other full release gate. This verifies the bounded reorder slice, not all of P09 or the 95 product requirements.
