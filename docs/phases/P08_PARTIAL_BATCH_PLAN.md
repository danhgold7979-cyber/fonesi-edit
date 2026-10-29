# P08-07 / P11-02 — Isolated per-video batch planning failures

**Date:** 2026-10-29. **Only repo/branch:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`. Plan committed before production/test changes.

## Reviewed baseline and requirement alignment

Reviewed `AGENTS.md`, `README.md`, master `docs/IMPLEMENTATION_PLAN.md` P08-01/P08-07 and P11-02, `docs/PRODUCT_REQUIREMENTS.md` §5/6, `docs/IMPLEMENTATION_COVERAGE.md` BAT-01…BAT-04, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, P08 plan/results, `src/fonesi_edit/batch.py`, `src/fonesi_edit/ui/pages.py`, and current Batch/Qt regression tests. Existing `batch_plan()` calls FFprobe and builds per-source composition inside one loop. A bad/missing source or clip-specific invalid duration currently raises and aborts **every** selected video, contrary to P08 completion gate “lỗi một tệp không làm lại lô”. Global audio mapping errors must continue to fail closed, rather than silently reassigning another audio source to a video.

Baseline previous source/test [CI 40908188050](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40908188050) SUCCESS (618 Linux / 617 Windows + 1 intentional skip, frozen proof both runners). Documentation-only HEAD has a separate CI. Full P08 and physical Windows acceptance remain OPEN.

## Implementation

1. Keep `batch_plan(...)` legacy fail-fast behavior for non-UI callers and synthetic packaged verifier; add a strictly opt-in `failures` list for per-source planning failures. Catch only expected per-source media/validation/I/O errors. Collect source path + safe bounded reason category, never an exception string that may contain credentials. Valid files keep deterministic output/preset hashes and original channel order.
2. Expose `batch_plan_report(...)` returning `{'plans': ..., 'failures': ...}`, with the same audio mapping validation performed once before the per-source loop. Fatal **global** audio mapping/mode errors are not downgraded to per-file skips. Do not invent replacement audio, mutate originals or mark failed files as succeeded.
3. In BatchPage's asynchronous dry-run callback consume the report. Show count of planned outputs, count and short filenames/reasons for skipped sources. If all selected sources failed, keep `self.plans` empty and forbid Preview/Enqueue. Keep existing scan/plan revision guards and explicit checkbox selection semantics.
4. Add real FFmpeg fixture tests with good+corrupt video and good+infeasible duration, old fail-fast API, global mapping failure, stable output hashes, unchanged source bytes, and queue only validated plans. Add real Qt test with failed source, async callback, and all-failed UI state. Run plan validator + full Linux/Windows CI, desktop/native-host build and frozen proof at exact source/test SHA.
5. Record results, coverage, status and ledger only after actual CI evidence; no force push/merge to `main`.

## Bounded acceptance

- [x] Good media continues to plan when one selected video is invalid, and every skipped source is explicitly reported without secrets.
- [x] Global audio-mode/assignment errors still raise; original fail-fast API still behaves as before; no invalid video is queued.
- [x] UI shows partially failed/all-failed cases, refuses empty enqueue, and drops stale async reports after settings changes.
- [x] Linux and Windows full tests + desktop/native-host + frozen packaged proof pass on same code/test SHA.

**Still OPEN:** very large batch benchmarks/ETA, real Windows device/NTFS/AV/ACL, audio playlist/meters, live providers/Chrome/auth, GPU/HiDPI and the independent intermittent SQLite [issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) with unknown root cause. This slice cannot close all P08/P11 or 95 release gates.

## Verified code and CI (29/10/2026)

[code 0e9cb5c](https://github.com/danhgold7979-cyber/fonesi-edit/commit/0e9cb5cbc8f345dcd8e152912effe0b849380e8a) implements opt-in per-video error collection in `batch_plan`, preserving default fail-fast callers, plus `batch_plan_report` for the Qt BatchPage. Bad media and per-video invalid duration are reported with a bounded reason category rather than raw third-party exceptions. Global audio mapping problems remain fatal and are not reclassified as individual skips. UI dry-run displays valid outputs and skipped items, forbids preview/enqueue when no plans survive, preserves source checkbox selection and rejects obsolete callbacks.

[tests d0753e3](https://github.com/danhgold7979-cyber/fonesi-edit/commit/d0753e3586266fda33ae8e4f8367a124d718ac37) includes real FFmpeg good/corrupt media and infeasible-duration cases, unchanged source bytes, old fail-fast behavior, global invalid audio, deterministic successful output plan and one validated queue enqueue; Qt tests exercise partial/all-failed reports and stale callback invalidation. [CI 40910523178](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40910523178) **SUCCESS on exact source/test SHA d0753e3**: Linux **621 passed**; Windows **620 passed + 1 intentional POSIX-only skip**; plan references, production desktop/native-host build, frozen packaged synthetic/localhost proof PASS on both runners. Windows development artifact uploaded. P08/P11 and physical Windows/live-provider acceptance remain OPEN.
