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

## Follow-up integrity checks identified during implementation review
The current Store.retry branch was inspected after the first recovery tests passed. It rejects a reservation owned by another job only while that reservation is reserved or succeeded; a missing row is silently ignored, and a failed row reassigned to a newer job can be stolen by retrying the older job. This violates the same-job reservation identity required above even though normal enqueue is atomic.

Extend this slice without changing the schema or allowing silent recovery:
1. A Matrix retry must require an existing reservation whose job_id is exactly the retrying job. It may restore only a failed reservation (or idempotently retain a reserved reservation owned by the same job); it must refuse missing, succeeded, or foreign-owned reservations regardless of the foreign row state.
2. Make the reservation update conditional on scope + combination + owner + allowed state, and fail closed if exactly one row was not updated. Do not put the job back in pending when the reservation check fails.
3. Test a deleted/missing reservation and a failed reservation that has since been reassigned to a newer job. Confirm the older retry cannot create or steal a reservation and leaves both jobs/history unchanged. Confirm the newer owning job can still retry.
4. Add a real-worker negative regression: remove a source after a Matrix job has been atomically enqueued, run the worker, and assert missing/invalid media never produces a succeeded job or succeeded history row. Keep the positive recovered FFmpeg render test.
5. Explicitly assert output target/payload preservation, exact reservation owner/state and unrelated successful history across all transitions.

The initial recovery implementation/test baseline is on HEAD a4da05d0a9bad846f7e2d1b7cbc4831230b4f39b; CI run 41033348646 has Linux and Windows jobs SUCCESS for source tests, benchmark, desktop/native-host build and frozen packaged proof. This baseline does not include the follow-up integrity checks above.

Open external gates remain: real Windows sudden power loss/AV/ACL/NTFS/exFAT, SQLite issue #6 root cause and long-running soak. Synthetic process-state recovery tests do not claim physical power-loss acceptance. Do not merge main.
