# P11-08 / TOL-06 — Validate activation receipt identity and rollback ownership

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: 25710e9de5dcc4a56cffd12ea170f93cb9a9ce26
- Alignment: P03-08 (app-managed tool ownership/version/path/rollback), P10-07 (updates must not disturb running jobs), P11-08 (missing/wrong tools, update and rollback), TOL-06.

## 1. Evidence reviewed

Read AGENTS.md, README.md, the master P11/P12 requirements, Settings/browser specification section 2.3, requirements traceability, coverage, current status, execution ledger, P11 results and tool lifecycle plans. Inspected `dependencies.py`, Store version registry/job snapshot behavior, and `tests/test_tools_and_translation.py`.

The exact previous source/test SHA `28b938589b495d9e0c8aff66a6d37a06f840cead` passed [CI 41066952938](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41066952938): Linux 873 passed; Windows 871 passed + 2 intentional platform skips; both production/native-host builds and frozen packaged proofs passed.

## 2. Gaps

1. `_save_tool_activation` now serializes activation with cleanup and checks the managed folder, executable containment/hash/startup status and optional ffprobe containment. It does not explicitly require receipt `name` and `version` to equal the activation arguments. A malformed/internal stale receipt can therefore be accepted if its path happens to resolve inside the requested version folder.
2. `rollback` checks only that the database path exists and matches its stored hash. It does not prove that the path belongs to the app-managed version directory. A tampered registry row pointing at an external byte-identical executable can be selected.
3. FFmpeg rollback derives a sibling ffprobe path and accepts `is_file()` without checking symlink status or containment. A symlinked companion could redirect the configured ffprobe path outside the managed version.

These are bounded local registry/receipt integrity gaps; no live network or credential is required to test them.

## 3. Implementation

1. Inside the activation writer transaction, require a dictionary receipt with exact matching name/version, a non-empty string executable path and a valid 64-character SHA-256. Reject mismatches before changing active rows or tool_paths.
2. Continue to resolve the target version through `_version_directory`; require the executable to be a regular non-symlink file inside that exact folder, with matching SHA-256 and a successful startup/capability check.
3. Validate an optional ffprobe companion as a regular non-symlink file inside the same managed version folder before adding it to tool_paths.
4. Harden rollback under `BEGIN IMMEDIATE`: require the registry path to resolve inside the app-managed version directory, reject symlink/external executables, verify hash and startup status, and validate any existing ffprobe companion is regular, contained and ready. If the companion is absent, remove only the app-managed ffprobe override as current behavior intends.
5. Add regressions for mismatched receipt name/version, rollback through an external path whose bytes deliberately match the stored hash, and a symlinked ffprobe companion to an external target. Verify failed operations preserve current active rows, paths and external bytes. Keep the successful FFmpeg/ffprobe rollback test.
6. Run phase checker, complete source suite, Batch/Matrix benchmarks, production desktop/native-host builds and frozen packaged proof on Linux and Windows.
7. Update activation plan, P11 results, coverage, current status and execution ledger only after exact-HEAD CI completes.

## 4. Acceptance criteria

- [ ] Activation refuses non-object or name/version-mismatched receipts without mutating active metadata or tool_paths.
- [ ] Activation requires the executable path and hash to belong to the requested managed version folder.
- [ ] Rollback refuses an external registry path even when its bytes match the recorded hash.
- [ ] Rollback refuses an external/symlinked ffprobe companion and preserves the currently active tool selection.
- [ ] Valid rollback still selects the matching FFmpeg/ffprobe pair and updates the live resolver.
- [ ] Existing activation/cleanup locks, job leases, installer failure atomicity, repair, archive safety and full suite remain passing.
- [ ] Exact-HEAD Linux and Windows CI, production builds and frozen packaged proof pass.

## 5. Limits

Synthetic SQLite/filesystem/tool fixtures do not certify physical Windows ACL/AV/disk-full/process-kill/power-loss, signed installer/update UX, real Chrome login/DPAPI/session handoff, live providers, GPU/HiDPI/audio, large real-media performance, SQLite issue #6 or complete P11/P12 acceptance. Do not merge to main or force-push.
