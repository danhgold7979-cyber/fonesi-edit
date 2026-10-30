# P11-02 / MAT-07 — Matrix output recovery at the render/database commit boundary
Date: 2026-10-30. Repository: danhgold7979-cyber/fonesi-edit. Integration branch: develop/fonesi-full.

## Reviewed evidence
Read AGENTS.md, README.md, P11_PLAN/P11_RESULTS, P09 plan/results, IMPLEMENTATION_PLAN, PRODUCT_REQUIREMENTS, IMPLEMENTATION_COVERAGE, REQUIREMENTS_TRACEABILITY, CURRENT_STATUS, PHASE_EXECUTION_LEDGER, P11_MATRIX_RECOVERY_PLAN, worker.py, jobs.py, storage.py, render.py, tests/test_matrix_recovery.py and tests/test_render_composition.py.

## Gap
render_composition publishes the validated MP4, then writes the .mp4.fonesi.json sidecar. Store.finish is a later transaction that marks the job and Matrix history succeeded. The current recovery slice covers interruption before rendering and cancellation/retry, but does not cover the crash boundary after the renderer has published the MP4 + sidecar and before Store.finish commits. The renderer already reuses an existing output only when both config_hash and SHA-256 match; otherwise it raises FileExistsError and does not overwrite.

## Scope
1. Claim a Matrix job and call the real worker execute() path so FFmpeg creates and validates the MP4 and sidecar, but deliberately do not call Store.finish. Simulate a stale worker heartbeat and run Store.recover.
2. Run the recovered job through the real Scheduler + worker. The renderer must reuse the existing validated artifact (result.reused=true), keep the same SHA-256/output target, and only then allow job + Matrix history to become succeeded exactly once.
3. Simulate an orphan destination with no sidecar. After recovery, the worker must fail closed, preserve the pre-existing bytes and leave job/history non-succeeded.
4. Simulate a valid sidecar whose output has been modified after publication. After recovery, the SHA mismatch must fail closed, preserve the modified bytes and leave the reservation failed; never silently adopt or overwrite the artifact.
5. Assert job ID, attempts, immutable payload, reservation owner/state, output hash, sidecar integrity and no duplicate history row. No schema change and no automatic adoption of an output without matching provenance.
6. Run source tests, phase reference checker, Linux/Windows packaged proof and record exact SHA evidence.

## Acceptance
- [x] A published MP4 with matching config_hash + SHA sidecar is reused after simulated interruption before Store.finish; the same artifact is committed as succeeded without a second render.
- [x] An orphan output without sidecar is not adopted or overwritten; job/history remain failed/non-succeeded.
- [x] A tampered output with a stale sidecar hash is not adopted or overwritten; job/history remain failed/non-succeeded.
- [x] Reservation is marked succeeded only after validated/reused result is committed; one job and one history row remain.
- [x] Linux/Windows regression and frozen packaged proof pass on the exact code/test SHA.

## Limits
This is a synthetic crash-boundary test using real FFmpeg and the Scheduler/worker path, not a physical power-loss test. It does not close Windows AV/ACL/NTFS/exFAT, SQLite issue #6 root cause, 100k real-media throughput, Chrome/live providers, GPU or remaining P11/P12 gates. Do not merge main.

## Exact-HEAD verification (30/10/2026)
[CI 41037280021](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41037280021) **SUCCESS** on exact code/test SHA [8101f210dfdeac160f7b9f2729fc1d01cfc33fa1](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8101f210dfdeac160f7b9f2729fc1d01cfc33fa1). Linux: 791 tests PASS; Windows: 790 PASS + 1 intentional POSIX-fixture skip. Both OS passed phase-reference validation, Batch and logical Matrix benchmarks, production desktop/native-host build and frozen packaged render/Batch/Matrix/localhost video+image download/UI proof.

Batch dry-run: Linux 5.190757 s / 840,677-byte tracemalloc peak; Windows 7.532058 s / 853,794-byte peak; failed_count=0. Matrix logical benchmark: Linux 12.819268 s / 1,379,048-byte peak; Windows 9.894325 s / 1,379,264-byte peak; theoretical capacity 10^10, 2,000 outputs, complete=true, max per-scene spread 5. These are synthetic/logical CI measurements, not real-media throughput.

Artifacts: Linux evidence 390,168 bytes (ID 12968876692, expires 2026-11-02); Windows evidence 322,849 bytes (ID 12969016070, expires 2026-11-02); Windows development build 197,355,733 bytes (ID 12969011211, expires 2026-11-06). Non-blocking warnings: optional urllib3 EMScripten import unavailable in PyInstaller; Linux CI has no PulseAudio device. Both packaged proofs passed.

The three new regressions cover a valid published artifact before Store.finish, an orphan output without sidecar, and a tampered output with a stale sidecar hash. This is synthetic crash-boundary coverage, not physical power-loss acceptance. Windows AV/ACL/NTFS/exFAT, SQLite issue #6 root cause, 100k real-media throughput, Chrome/live providers, GPU and remaining P11/P12 gates stay OPEN. Do not merge main.
