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
- [ ] A published MP4 with matching config_hash + SHA sidecar is reused after simulated interruption before Store.finish; the same artifact is committed as succeeded without a second render.
- [ ] An orphan output without sidecar is not adopted or overwritten; job/history remain failed/non-succeeded.
- [ ] A tampered output with a stale sidecar hash is not adopted or overwritten; job/history remain failed/non-succeeded.
- [ ] Reservation is marked succeeded only after validated/reused result is committed; one job and one history row remain.
- [ ] Linux/Windows regression and frozen packaged proof pass on the exact code/test SHA.

## Limits
This is a synthetic crash-boundary test using real FFmpeg and the Scheduler/worker path, not a physical power-loss test. It does not close Windows AV/ACL/NTFS/exFAT, SQLite issue #6 root cause, 100k real-media throughput, Chrome/live providers, GPU or remaining P11/P12 gates. Do not merge main.
