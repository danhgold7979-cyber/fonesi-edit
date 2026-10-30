# P11-08 / TOL-06 — Tool-version leases and safe cleanup

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: 096d6bbb16768fb8c063109d2e4def5cd9e64dd6
- Master alignment: P03-08 (tool ownership/version/path/staging/lease/rollback), P10-07 (tool lease; update must not disturb running jobs), P11-08 (installer update-busy and rollback), TOL-06 (staging/repair/update/rollback and tool lease), FLOW-18 (failed install preserves old version).

## 1. Evidence reviewed

Read AGENTS.md, README.md, docs/IMPLEMENTATION_PLAN.md, docs/PRODUCT_REQUIREMENTS.md, docs/IMPLEMENTATION_COVERAGE.md, docs/REQUIREMENTS_TRACEABILITY.md, docs/CURRENT_STATUS.md, docs/PHASE_EXECUTION_LEDGER.md, P11/P12 plans and results, SETTINGS_AND_BROWSER_SPEC.md, src/fonesi_edit/storage.py, src/fonesi_edit/dependencies.py, src/fonesi_edit/worker.py, src/fonesi_edit/ui/pages.py, and tests/test_tools_and_translation.py.

Latest baseline CI before this slice: https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41056951728 SUCCESS exact HEAD 096d6bbb, both Linux and Windows source tests, production/native-host build and frozen packaged proof.

## 2. Current gap

- Store.submit and submit_many snapshot tool_paths, but read settings outside the transaction that inserts the job. A cleanup transaction could therefore race with job submission and remove a version immediately before a stale tool path is enqueued.
- tool_versions tracks installed versions and the active flag, but there is no usage-aware list/remove operation.
- Settings exposes install and rollback, but no explicit app-managed version inventory or safe cleanup action.
- A job's immutable payload contains _tools; failed/blocked/canceled jobs are retryable and must retain their original tool paths. Pending/running jobs must retain their paths too. Succeeded jobs do not need the executable to run again.
- FFmpeg receipts may include ffprobe in the same version folder. A job using either path must hold the whole version folder.
- The spec requires app-managed version cleanup only when no job uses it, never deleting system/user overrides or Chrome profile/session data.

## 3. Implementation

1. Make Store.submit and submit_many acquire BEGIN IMMEDIATE, read tool_paths and insert the immutable job snapshot in the same SQLite write transaction. Validate all submit_many payloads before the first insert.
2. Add managed_tool_versions(store) returning installed app-managed versions with active/configured/job-use state and a human-readable protection reason.
3. Add remove_tool_version(store, name, version): under BEGIN IMMEDIATE re-read the version, current tool_paths and every job snapshot in states that can still run or retry; refuse active/currently configured versions and any version referenced by pending/running/blocked/failed/canceled jobs. Compare every snapshotted executable path against the whole version directory so ffprobe companion references also protect FFmpeg.
4. Restrict deletion to a non-symlink version directory inside the exact app-managed tools root. Never delete an external executable or arbitrary path from SQLite. Remove the directory before deleting its tool_versions row; filesystem/permission failure must leave metadata and active selection intact.
5. Add a Settings inventory table with refresh and explicit confirmation before removing an eligible old version. Keep active, configured and job-held versions visibly protected. Refresh after install/rollback/removal.
6. Add tests for active protection, pending/running/retryable-job protection, succeeded-job release, ffprobe companion leases, batch submit snapshots, safe removal, path traversal/symlink tampering, and external-path non-deletion.
7. Run the complete source suite, scripts/check_plan.py, Batch/Matrix benchmarks, production desktop/native-host builds and frozen packaged proof on Linux and Windows. Update results/coverage/traceability/status/ledger only after exact-HEAD CI.

## 4. Acceptance criteria

- [ ] Job snapshot capture and version removal are serialized; no job can be queued with a binary path after that version is removed.
- [ ] Active or configured versions cannot be removed.
- [ ] Pending, running, blocked, failed and canceled jobs protect every executable in their immutable _tools snapshot; succeeded jobs do not block cleanup.
- [ ] FFprobe companion usage protects its containing FFmpeg version folder.
- [ ] Only a verified path inside the app-managed version root can be removed; system/user binaries and Chrome data are untouched.
- [ ] Filesystem/ACL errors do not clear tool_versions or change tool_paths.
- [ ] UI shows version inventory/protection reason and requires explicit confirmation for cleanup.
- [ ] Existing install, archive preflight, repair, cancel, rollback and full-suite regressions remain passing.
- [ ] Exact-HEAD Linux/Windows CI, builds and packaged proofs pass.

## 5. Explicit limits

This slice does not claim physical Windows ACL/antivirus/disk-full/power-loss behavior, signed installer/update, Chrome real login/DPAPI/bridge, live providers, GPU/HiDPI/audio or complete P11/P12 acceptance. No force-push or merge to main.