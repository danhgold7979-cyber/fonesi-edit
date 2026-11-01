# Typed validator retirement — source CLEAR for scoped CI

2026-11-01. Verified eight supplied source/test/workflow hashes; bounded source review, no baseline/real FFmpeg repeat.

## Finding
Windows run_windows_owned finally unconditionally confirms WINDOWS_JOB_EMPTY after absence of retirement errors. If CreateJobObjectW fails before job assignment, no job exists and await_job_empty never executes, yet the receipt claims Windows empty-job proof. No process could launch in this branch, so safe classification is NO_PROCESS, not ActiveProcesses0-derived evidence.
Independent platform-neutral mock reproduces: CreateJobObjectW→0, ProcessError raised, observation.mechanism nevertheless WINDOWS_JOB_EMPTY. No actual native API or process launched.
Fix: confirm WINDOWS_JOB_EMPTY only where an actual owned job was observed empty and all retirements succeeded; no-child setup branch may confirm NO_PROCESS; otherwise UNKNOWN. Add explicit setup-before-job failure test, labelled mock/control-flow not Windows execution.

## Other review result
No additional blocker found. Fresh invocation UNKNOWN registered before adapter entry; single-use/thread-bound/max2 sequential validation lifecycle; invalid reuse/nesting revokes; sanitizer never confirms; actual validator entry/unwind seals; unobserved runner/unentered validator remains unsafe. Session validates lifecycle on both return and failure and does not erase sticky unknown. POSIX group_retired separate from early stop flag and all owned closes attempted, receipt only after success. Workflow marker alone selects four affected targets, no unchanged aggregate/frozen/Qt work.

Independent selected tests: actual owned decoder cancellation/descendant retirement; retired probe followed by sanitized UNKNOWN decode; POSIX finally-close uncertainty —3 PASS/10 deselected, exit0. Actual Python child is explicitly a decoder stand-in, not FFmpeg media evidence. Windows typed-proof/cleanup integration remains pending native CI.

## Targeted correction recheck — 12:21 UTC
Verified final Windows source SHA256 `5a197f1696ac77e16d92dcb41abb6c11e019feba4af96a7b11cc427650ce4fcf`, test `0b99a507b4da4982c122e28d81127ddbc82e1bb6d8196089916f07cc32d9485d`, contract `87e3786b25630b0b2f74147572c5350d24130ca24ad4b065a75246d986aed6d5`. Windows now sets job_empty only after await_job_empty returns, checks all retirement errors before confirmation, confirms WINDOWS_JOB_EMPTY only for actual observed empty job; no-job/no-process branch confirms NO_PROCESS. Other uncertain branches stay unconfirmed. Finding causally closed.

Independent exact new setup-before-job mock regression: **1 PASS / 13 deselected, exit 0**. No previous selected tests or native baseline repeated. This is control-flow proof, not native Windows execution. Source CLEAR for the already scoped validator-retirement CI; Windows typed retirement, forced-finalizer uncertainty and child/descendant cancellation-to-owned-stage cleanup remain actual target gates. No phase/criterion acceptance inferred.
