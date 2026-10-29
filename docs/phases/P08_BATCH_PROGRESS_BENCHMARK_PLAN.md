# P08-07 / P11-03 — Bounded batch planning progress, cancellation and reproducible corpus benchmark

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only integration branch:** `develop/fonesi-full`. Plan precedes code/test writes.

## Reviewed requirements and baseline

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P08-07, P11-03), `docs/PRODUCT_REQUIREMENTS.md` sections 5, 8 and 9, `docs/REQUIREMENTS_TRACEABILITY.md` BAT-04/OPS-01/OPS-02, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, `docs/phases/P08_PLAN.md`, `P08_PARTIAL_BATCH_PLAN.md`, P08/P11 results, `src/fonesi_edit/batch.py`, `src/fonesi_edit/ui/pages.py`, `src/fonesi_edit/ui/tasks.py`, `src/fonesi_edit/app.py` and batch/Qt tests.

The previous [P08 source/test CI 40910523178](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40910523178) passed **621 Linux / 620 Windows + one intentional skip**, packaged proof both runners. The documentation-only HEAD `819f702` has separate CI; do not assume that completed until GitHub confirms. Partial batch planning now isolates per-video faults, but `BatchPage.plan` discards Task's `progress,cancel` arguments; a user pressing the global **Hủy tác vụ chuẩn bị** cannot actually cancel a large loop. No reproducible corpus benchmark script exists.

## Planned implementation

1. Make `batch_plan` and `batch_plan_report` optionally accept keyword-only `progress` and `cancel` (existing fail-fast callers unchanged). Check cancellation before costly audio preflight, during audio probes and before/after each video; do not publish partial plans as success on cancellation. For completed videos report monotonic fraction of known selected count, including individually invalid sources. Return report `cancelled: True` with no `plans`, no `failures` accepted for enqueue; an interrupted report is never a valid preview. Avoid fabricated percentages for unknown totals.
2. Wire `BatchPage.plan` through Task's cooperative cancel/progress interface. `planned` handles cancelled report with clear state and leaves Preview/Enqueue disabled; keep revision-token guard, existing checkbox state and per-video failure reporting. Avoid touching source files or scheduling any job during planning/cancel. Global audio configuration faults remain fail-fast.
3. Add `scripts/benchmark_batch.py` running the same batch planner against reproducible generated local FFmpeg fixtures with configurable number of file copies and output JSON. Report exact fixture count, valid/failed, elapsed time, throughput, measured Python-process RSS / traced Python allocations where available, and runtime/OS/tool version. Use a temporary working directory and never publish video, browser profiles, cookies or credentials as artifacts; state clearly that values are machine/fixture dependent, not user-device acceptance. A small real-media smoke can test this CLI; scaling to hundreds of files is optional via invocation, not a fragile fixed CI time threshold.
4. Tests: deterministic 500+ logical-file corpus with mocked probe proving count/order/monotonic progress, no accidental preflight repetition and untouched inputs; cancellation before/during an active scan (including audio preflight) proves no usable partial plans and stable original checkbox/queue; real local FFmpeg fixture benchmark smoke validates JSON schema and nonzero metrics. Do not disable existing tests.
5. Run `scripts/check_plan.py`, targeted regression and complete Linux/Windows CI on exact source/test SHA, with production desktop/native host and frozen packaged proof. After observing results, update P08/P11 results, coverage, current status and execution ledger; record unresolved real Windows stress and full product gates separately. No merge into `main`.

## Acceptance for this bounded slice

- [ ] Progress is monotonic, bounded and reaches 100% only on completed planning, and cancellation is cooperative without partial publish or queued work.
- [ ] Real Qt background cancellation and stale callbacks never revive plans, while normal partial-success reports and global audio failure semantics remain unchanged.
- [ ] Configurable real FFprobe/FFmpeg benchmark records machine-dependent throughput and memory with explicit fixture and limitations; large logical-corpus test scales without fragile timed thresholds.
- [ ] Full Linux and Windows CI test suite, packaged desktop/native-host and synthetic/localhost frozen proof PASS at the exact source/test SHA; record evidence.
- [ ] P08/P11 remain OPEN for user-device long-corpus performance, ETA of actual render, GPU/VRAM, physical Windows NTFS/AV/ACL, audio meters/playlist, Chrome/live sources, installer and intermittent SQLite [issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6).

**Note:** A dry-run progress fraction or synthetic benchmark is **not** an evidence-based prediction of FFmpeg render time or output file size. No secret, personal media, fake release state, schema migration or destructive SQLite workaround.
