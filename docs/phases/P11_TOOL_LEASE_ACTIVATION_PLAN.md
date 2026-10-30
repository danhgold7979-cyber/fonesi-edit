# P11-08 / TOL-06 follow-up — Serialize tool activation with lease cleanup

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: 637f9b66dbf472685cc1a98eb76ed20a99743923
- Alignment: P03-08 tool registry/activation/lease/rollback; P10-07 update must not disturb jobs; P11-08 installer update-busy; TOL-06 versioned staging/repair/update/rollback and tool lease.

## 1. Evidence reviewed

Read the master implementation plan, product requirements, traceability, implementation coverage, current status, execution ledger, Settings/browser specification, P11/P12 plans/results, AGENTS.md, Store, dependency installer, Settings UI and the current tool lifecycle tests. The existing lease implementation serializes Store.submit/submit_many against remove_tool_version using SQLite BEGIN IMMEDIATE.

Exact prior full CI on 56c89f2: [run 41060151717](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41060151717) SUCCESS, Linux 867 passed; Windows 866 passed + 1 intentional POSIX-only skip; Batch/Matrix benchmarks, production/native-host build and frozen packaged proof passed both OS.

Current HEAD 637f9b66 adds a POSIX symlink-cleanup rejection regression; exact-HEAD CI [41061672601](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41061672601) is still running at planning time.

## 2. Gap

Install resolves and verifies an existing version receipt before calling _save_tool_activation. Cleanup can acquire the SQLite writer lock in between, remove the inactive version directory and its metadata, then the installer can activate the now-missing receipt. Job submission and cleanup are serialized, but version activation and cleanup are not yet serialized around filesystem validation.

## 3. Implementation

1. Inside _save_tool_activation, acquire BEGIN IMMEDIATE before re-reading tool_paths and validate the receipt's identity, managed version folder, executable containment, file existence and SHA-256 while holding that transaction.
2. If FFmpeg receipt contains ffprobe, validate that companion is a regular file inside the same managed version folder before activation.
3. If cleanup wins first, activation must fail closed and must not recreate metadata or select a missing path. If activation wins first, cleanup must observe the active/configured version and refuse removal.
4. Add deterministic threaded regressions for both orderings: cleanup removes a verified inactive receipt before activation; activation owns the writer lock before cleanup attempts to remove it.
5. Add a Qt integration regression for Settings version inventory and explicit confirmed cleanup: old eligible version disappears, active version remains, and no system/user tool or Chrome data is touched.
6. Preserve Store.submit/submit_many transaction semantics, existing pending/running/retryable leases, FFprobe companion leases, repair, cancellation and rollback behavior.
7. Run exact-HEAD phase checker, complete source suite, Batch/Matrix benchmarks, production desktop/native-host builds and frozen packaged proof on Linux and Windows.
8. Update P11 results, coverage, traceability, current status and execution ledger only after exact-HEAD CI is complete.

## 4. Acceptance criteria

- [ ] Activation verifies receipt identity, executable containment, executable SHA-256 and optional ffprobe companion while holding the same SQLite writer lock as cleanup.
- [x] Cleanup-first ordering cannot activate a deleted version or recreate stale metadata.
- [x] Activation-first ordering prevents cleanup from removing the active/configured version.
- [x] Settings inventory accurately displays eligibility and confirmed removal deletes only an eligible app-managed version.
- [x] Existing job leases continue protecting pending/running/blocked/failed/canceled snapshots; succeeded jobs release leases.
- [x] Existing install/repair/archive/cancel/rollback tests remain passing.
- [x] Exact-HEAD Linux and Windows CI, packaged proofs and production builds pass.

## Progress (30/10/2026)

Acceptance items 2–7 are now backed by the cleanup/activation race regressions, existing lease/install suite, and [exact-HEAD CI 41066952938](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41066952938) on `28b938589b495d9e0c8aff66a6d37a06f840cead`. The Settings inventory, confirmation, cancel and Chrome non-interference checks are covered by [P11_TOOL_SETTINGS_UI_PLAN.md](P11_TOOL_SETTINGS_UI_PLAN.md).

**Acceptance item 1 remains OPEN:** `_save_tool_activation` validates the managed folder, executable containment/hash and companion location, but does not yet explicitly assert that receipt `name` and `version` match the activation arguments. A follow-up slice must close this identity check before this plan can be fully accepted.

## 5. Limits

This is synthetic SQLite/filesystem and Qt integration evidence. It does not certify physical Windows ACL/AV/disk-full/power-loss, signed installer/update UX, Chrome real login/DPAPI/bridge, live providers, GPU/HiDPI/audio or full P11/P12 acceptance. No force-push or merge to main.
