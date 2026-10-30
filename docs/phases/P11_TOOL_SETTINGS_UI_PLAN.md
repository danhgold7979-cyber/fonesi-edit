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

- [ ] A real Qt Settings table distinguishes eligible, active and job-leased managed versions and exposes the protection reason.
- [ ] A leased version is rejected before confirmation and remains intact.
- [ ] Confirmed cleanup removes only the selected eligible app-managed version; active version and current tool paths remain intact.
- [ ] Chrome profile directory/marker and account binding are unchanged by tool cleanup.
- [ ] Cancel leaves the managed directory, registry row and all unrelated state unchanged.
- [ ] Existing tool installer, rollback, archive, job lease and complete-suite regressions remain passing.
- [ ] Exact-HEAD Linux and Windows CI, production builds and packaged proof pass.

## 5. Limits

This is synthetic filesystem/SQLite/Qt integration evidence. It does not certify physical Windows ACL/AV/disk-full/power-loss behavior, signed installer/update UX, real Chrome login/DPAPI/session handoff, live providers, GPU/HiDPI/audio, large real-media performance, SQLite issue #6 or complete P11/P12 acceptance. Do not merge to main or force-push.
