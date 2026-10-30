# P11-02 / P09-06 — Matrix reservation recovery across interrupted workers
Date: 2026-10-30. Repository: danhgold7979-cyber/fonesi-edit. Integration branch: develop/fonesi-full.

## Reviewed evidence
Read AGENTS.md, README.md, IMPLEMENTATION_PLAN P09/P11, PRODUCT_REQUIREMENTS §7/§9, REQUIREMENTS_TRACEABILITY MAT-07/OPS-04, CURRENT_STATUS, IMPLEMENTATION_COVERAGE, PHASE_EXECUTION_LEDGER, P09/P11 plans/results, matrix.py, storage.py, jobs.py, tests/test_matrix.py, tests/test_matrix_enqueue_cancel.py and the scheduler/worker code. Matrix enqueue reserves a combination and job atomically; worker success marks history succeeded; fail/cancel marks failed; retry rebinds the same job ID; stale worker recovery requeues or cancels by cancel_requested. Existing tests cover enqueue, successful output, failed-reservation retry and pre-commit rollback, but no test drives the complete Matrix reservation lifecycle through a simulated app/worker interruption and recovery.

## Scope
1. Simulate a Matrix job claimed by a worker, then stale heartbeat/process loss. Store.recover must return it to pending without releasing or duplicating its reservation; the same job ID, immutable payload, matrix combination and output target must survive.
2. Simulate cancellation while a Matrix job is running, then stale worker recovery. The job must become canceled, its reservation failed (not succeeded), and an explicit Retry must restore the same job/reservation identity exactly once.
3. Run the recovered/retried job through the real Scheduler + worker + FFmpeg synthetic fixture and verify artifact validation precedes history state succeeded. Never mark success on missing/invalid output.
4. Assert project history, job ID, attempts, cancel_requested, output path, and no duplicate reservation/job after each transition. Ensure an unrelated succeeded reservation is unchanged.
5. Add Qt integration only if a real UI gap is found; otherwise preserve current Matrix cancel UI. Do not change schema or weaken stale-worker/SQLite locking behavior.
6. Run full source tests, phase reference checker, Linux/Windows packaged proof and record exact SHA evidence.

## Acceptance
- [ ] Interrupted running Matrix worker recovers to pending with its reservation still attached to the same job.
- [ ] Cancelled stale Matrix worker recovers as canceled/failed reservation; retry reuses same job ID and restores one reservation.
- [ ] Real recovered/retried FFmpeg job validates output then transitions history to succeeded, with no duplicate/false success.
- [ ] Linux/Windows regression and frozen packaged proof pass at exact code/test SHA.

Open external gates remain: real Windows sudden power loss/AV/ACL/NTFS/exFAT, SQLite issue #6 root cause and long-running soak. Synthetic process-state recovery tests do not claim physical power-loss acceptance. Do not merge main.
