# P11-08 / TOL-06 — Settings UI regression for managed tool versions

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: 80becbc79dcc379b3d89c5eb7ccb4273eae91e6d
- Alignment: P03-08 (managed tool ownership/version/lease/rollback), P10-07 (updates must not disturb jobs), P11-08 (tool lifecycle and recovery), TOL-06.

## 1. Evidence reviewed

Read AGENTS.md, README.md, the 12-phase implementation plan, product requirements, requirements traceability, implementation coverage, current status, execution ledger, Settings/browser specification, P11 plan/results, the existing tool lease/activation plans, SettingsPage, MainWindow, browser profile storage, Store and tool lifecycle tests.

The exact planning base has successful Linux and Windows CI: [run 41063426051](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41063426051), exact SHA `80becbc79dcc379b3d89c5eb7ccb4273eae91e6d`. The branch and draft integration PR #5 still target main; no release merge is authorized.

## 2. Gap

Backend coverage already exercises managed-version inventory, active/configured protections, pending/running/retryable job leases, ffprobe companion leases, removal safety, filesystem failure, symlink rejection, and both cleanup/activation orderings. SettingsPage also renders an inventory table and asks for explicit confirmation before removal.

However, there is no Qt integration test in the existing suite that drives this Settings workflow through a real MainWindow. The earlier activation plan explicitly requires proving the UI inventory, confirmation boundary, preservation of the active tool, and non-interference with Chrome profile/account data.

## 3. Implementation

1. Add a focused `tests/test_tool_settings_ui.py`; use the production MainWindow/SettingsPage, a temporary user-data directory, actual SQLite rows and app-managed filesystem folders. Do not download external tools or use live accounts.
2. Verify Settings displays removable and protected versions accurately, including a useful tooltip/reason for a retryable job lease.
3. Confirm removal of an eligible old version through the Qt confirmation dialog. Verify only that app-managed version directory and row are removed; active tool path/version, and a Chrome profile marker plus account binding, remain byte-for-byte/record-for-record unchanged.
4. Reject removal when a job snapshot holds the version before presenting the confirmation dialog.
5. Cancel the confirmation dialog and verify the version directory, registry row, active selection and Chrome profile remain unchanged.
6. Run the phase reference checker, full source suite, Batch/Matrix benchmarks, production desktop/native-host build and frozen packaged proof on Linux and Windows.
7. Only after exact-HEAD CI completes, update this plan's acceptance checkboxes, P11 results, implementation coverage, current status and execution ledger with the observed test counts/run URL.

## 4. Acceptance criteria

- [x] A real Qt Settings table distinguishes eligible, active and job-leased managed versions and exposes the protection reason.
- [x] A leased version is rejected before confirmation and remains intact.
- [x] Confirmed cleanup removes only the selected eligible app-managed version; active version and current tool paths remain intact.
- [x] Chrome profile directory/marker and account binding are unchanged by tool cleanup.
- [x] Cancel leaves the managed directory, registry row and all unrelated state unchanged.
- [x] Existing tool installer, rollback, archive, job lease and complete-suite regressions remain passing.
- [x] Exact-HEAD Linux and Windows CI, production builds and packaged proof pass.

## 5. Results (30/10/2026)

[Plan commit e258d06](https://github.com/danhgold7979-cyber/fonesi-edit/commit/e258d06c0cd336957f876b4f20f687577ba432e9) → [Qt tests 28b9385](https://github.com/danhgold7979-cyber/fonesi-edit/commit/28b938589b495d9e0c8aff66a6d37a06f840cead) → [CI 41066952938](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41066952938) **SUCCESS exact HEAD**.

- Linux: 873 passed, 0 skipped, 0 failures/errors. Windows: 871 passed, 2 intentional skips, 0 failures/errors (POSIX-only fixture installation and Windows symlink privilege).
- Three real-MainWindow Qt regressions pass on both OS: confirmed cleanup preserves active FFmpeg and Chrome profile/account data; cancel leaves the version untouched; a retryable job lease blocks cleanup before confirmation.
- Both runners passed the 128-source synthetic FFprobe Batch dry-run (failed_count=0), 2,000-output logical Matrix benchmark (complete=true, max per-scene spread 5), production desktop/native-host build and frozen packaged proof.
- Batch planning: 7.623922 s Linux / 10.117165 s Windows. Matrix: 19.857709 s Linux / 17.514511 s Windows. Windows development artifact: 197,404,488 bytes.

This proves the bounded Settings UI/SQLite/filesystem integration only; it is not physical Windows user-machine or full P11/P12 acceptance.

## 6. Limits

This is synthetic filesystem/SQLite/Qt integration evidence. It does not certify physical Windows ACL/AV/disk-full/power-loss behavior, signed installer/update UX, real Chrome login/DPAPI/session handoff, live providers, GPU/HiDPI/audio, large real-media performance, SQLite issue #6 or complete P11/P12 acceptance. Do not merge to main or force-push.
