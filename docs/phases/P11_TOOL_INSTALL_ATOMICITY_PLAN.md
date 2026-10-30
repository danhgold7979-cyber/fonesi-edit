# P11-08 / TOL-04…TOL-06 — Idempotent verified tool install, activation and rollback

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: e3d3272cf8753fe08652b8f1d54bf8f5359214cb
- Master alignment: P11-08 (missing/wrong tools, interrupted install, verification, permissions, busy update), TOL-04…TOL-06 (verified download, staged install, repair and rollback), OPS-04/OPS-07 (immutable tool snapshot and diagnostics).

## 1. Evidence reviewed

Read AGENTS.md, README.md, docs/IMPLEMENTATION_PLAN.md, docs/PRODUCT_REQUIREMENTS.md, docs/IMPLEMENTATION_COVERAGE.md, docs/REQUIREMENTS_TRACEABILITY.md, docs/CURRENT_STATUS.md, docs/PHASE_EXECUTION_LEDGER.md, docs/SETTINGS_AND_BROWSER_SPEC.md, docs/phases/P11_PLAN.md, docs/phases/P12_PLAN.md, src/fonesi_edit/dependencies.py, src/fonesi_edit/prototypes/tools.py, src/fonesi_edit/storage.py, src/fonesi_edit/app.py, src/fonesi_edit/ui/pages.py, tests/test_tools_and_translation.py and relevant app integration tests.

## 2. Confirmed gaps

- dependencies.install detects a pre-existing verified version and sets intact=True, but does not assign the receipt variable later used for database activation and tool_paths update. Reinstalling the same valid version can therefore raise UnboundLocalError instead of idempotently reusing it.
- install and rollback persist tool_paths but do not refresh the running process's configure_tools override map. Settings can report a new path while workers in the current process still resolve the old path until restart.
- FFmpeg rollback changes the ffmpeg path only; the ffprobe override can remain bound to a different installed version.
- Cancellation is checked during download but not consistently after download, extraction and startup verification, before publishing a staged version or activating it.
- Active tool_versions and settings.tool_paths are updated in separate SQLite transactions, so a failure between writes can leave active metadata and runtime selection inconsistent.
- Existing tests cover missing/incompatible tool discovery, but no deterministic fake-artifact regression covers idempotent reuse, interrupted activation, rollback companion consistency or live resolver refresh.

## 3. Scope

1. Validate existing receipts strictly: expected tool/version, executable hash, path confined to the version directory, startup status and any declared companion path. Reuse only a fully valid receipt.
2. Make same-version install idempotent: restore the validated receipt, skip network fetch and return the existing executable.
3. Check cancellation at every safe boundary after fetch, after extraction, after startup verification and immediately before database activation. A canceled/failed operation must not change the active version or tool_paths.
4. Publish active tool_versions and settings.tool_paths in one SQLite transaction. Refresh configure_tools only after the transaction commits.
5. Rollback only to an intact version; when rolling back FFmpeg, select the matching sibling ffprobe when present and remove a stale companion override otherwise. Commit metadata atomically and refresh the live resolver after commit.
6. Add deterministic tests with a local fake ZIP/artifact transport; no external download and no real system tool replacement. Cover same-version reuse, invalid receipt repair while preserving the old folder, checksum/startup failure, cancellation, SQLite activation fault rollback, live resolver update and FFmpeg/ffprobe rollback pairing.

## 4. Acceptance criteria

- [ ] Reinstalling an intact version returns the same receipt/path without downloading again or raising.
- [ ] Corrupt/unsafe receipts are never trusted; repair publishes to a new versioned folder and preserves the previous folder/job paths.
- [ ] Checksum/startup/cancellation failure leaves the previous active version and tool_paths unchanged.
- [ ] Active tool_versions and settings.tool_paths change atomically under injected SQLite failure.
- [ ] Successful install and rollback update the in-process tool resolver only after persistence succeeds.
- [ ] FFmpeg rollback selects its matching ffprobe companion or removes a stale override.
- [ ] Deterministic fake-artifact unit tests, full source suite, plan validation, production build and frozen packaged proof pass on Linux and Windows for the exact implementation/test commit.

## 5. Explicit limits

This slice does not claim a signed Windows installer, real Windows user-machine permissions/antivirus/ACL/power-loss acceptance, real Chrome login/DPAPI handoff, provider availability, GPU/HiDPI/audio or full P11/P12 completion. Network install_chrome remains a separate Windows-only external acceptance gate. Do not merge main.

## 6. Execution notes

The exact implementation will use fake artifacts and fault-injected SQLite tests; it will not download or replace a system executable during unit tests. Local source execution is not available in the current cloud turn, so the exact GitHub Actions commit must pass Linux and Windows before reporting PASS.
