# P11-08 / TOL-04…06 — Per-tool update-busy guard in Settings

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: c2b9424c4084f730794ffe2f5555f812fb10f211
- Alignment: P03-08 (managed tool ownership/version/staging/rollback), P10-07 (updates must not disturb jobs), P11-08 (installer update-busy and rollback), TOL-04…06.

## 1. Evidence reviewed

Read AGENTS.md, README.md, the master implementation plan, P11 plan/results, Settings/browser specification section 2.3, requirements traceability, implementation coverage, current status, execution ledger, SettingsPage, MainWindow background-task lifecycle, tool installer/rollback/cleanup and the current Qt tool lifecycle tests.

The previous source/test commit `13a044e51f96498d7b3ee0728e7892fffd8c4194` passed [CI 41072242592](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41072242592): Linux 879 passed; Windows 875 passed + 4 intentional platform skips; production/native-host builds and frozen packaged proofs passed both OS. The documentation validator fixes on `c2b9424c4084f730794ffe2f5555f812fb10f211` passed [CI 41074586521](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41074586521).

## 2. Gap

Settings currently starts a new background install every time the user presses the install action. The background scheduler permits two concurrent preparation tasks and queues additional work, but Settings does not track which tool is already downloading/installing/updating. Repeated clicks or overlapping `install_missing` calls can therefore schedule duplicate operations for the same tool. Rollback, path override and managed-version cleanup also have no UI-level guard against an update for that same tool being in flight.

FFprobe is an alias of the FFmpeg bundle and must normalize to the same busy key. Different independent tools may still install concurrently, subject to the existing background task limit.

## 3. Implementation

1. Add a SettingsPage per-tool busy registry keyed by normalized tool name; normalize ffprobe to ffmpeg.
2. Mark a tool busy synchronously before scheduling its background task so a second click cannot enqueue a duplicate. If task scheduling raises, release the busy marker immediately.
3. Release the marker from the task's finished signal regardless of success, failure or cancellation; handle a very fast task that finishes before the UI connects the signal.
4. Show a visible Vietnamese busy status and disable the selected tool's install/path/rollback actions plus cleanup of versions belonging to a busy tool. Refresh action enabled states when selection or busy state changes.
5. Make install-missing skip components already busy while still scheduling other independent missing components; do not report success for skipped/busy components.
6. Add Qt tests using a fake background task and no network/downloads: duplicate same-tool and ffprobe alias calls are rejected, busy state releases after task completion, and rollback/path override/cleanup are blocked while the matching tool is busy. Verify a different tool can still be scheduled.
7. Run phase reference checker, complete source suite, Batch/Matrix benchmarks, production desktop/native-host builds and frozen packaged proof on Linux and Windows.

## 4. Acceptance criteria

- [ ] A second install/update for the same normalized tool is rejected before another background task is queued.
- [ ] FFprobe and FFmpeg share one busy key; distinct independent tools can still be scheduled.
- [ ] install-missing skips busy tools and schedules only independent missing components.
- [ ] Busy status is visible; relevant Settings actions are disabled while the selected tool is busy.
- [ ] Rollback, manual path override and managed-version cleanup refuse the same tool while its update is in flight.
- [ ] Busy state clears after success, error or cancellation and also clears if task scheduling itself fails.
- [ ] Existing receipt/rollback integrity, cleanup leases, install failure atomicity, Settings UI and complete-suite regressions remain passing.
- [ ] Exact-HEAD Linux and Windows CI, production builds and frozen packaged proof pass.

## 5. Limits

This slice protects concurrent operations initiated through one SettingsPage/MainWindow process. It does not claim a cross-process installer mutex or certify physical Windows ACL/AV/disk-full/process-kill/power-loss, signed installer/update UX, live Chrome/provider auth, GPU/HiDPI/audio, large real-media performance, SQLite issue #6 or complete P11/P12 acceptance. Do not merge to main or force-push.
