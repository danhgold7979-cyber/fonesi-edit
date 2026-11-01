# P03 source-only readiness for hosted CI

Independent reviewer inspected source commit `9bfc1ea9ffaa413270a0fd66e0ffe8ef54149f2e` (2026-11-01): **CLEAR FOR HOSTED CI**, not Windows runtime/P03 acceptance.

Original digest alias, exponential font graph, unbounded file-read and nonfinite probe findings closed. Matching-ID malformed database residual closed by exact schema signatures before WAL (5 focused foreign/schema regressions PASS). Win32 JOB_LIST/HANDLE_LIST, noninherited owned job, atomic suspended assignment/membership, bounded capture, job termination and explicit retirement errors reviewed against Microsoft documentation. POSIX WNOWAIT group retirement reviewed for nonescaping descendants. Reviewer did not duplicate the110-test aggregate.

Remaining gate: leader termination alone is not separately observed job ACTIVE_PROCESS_ZERO for every descendant. Coordinator must prove complete quiescence before reusing/deleting output/cleanup resources. Current code has no artifact publication success path and claims no Windows runtime verification. Actual Windows nested-job/crash/handle/sibling tests and hosted results remain necessary.

Following source review, CI-only tightening pins official Action commit SHAs, checks out exact PR head/push SHA, asserts SHA before tests, and records tree/platform/Python identity. 2 focused identity tests PASS. No application source change after reviewed9bfc1ea.

## Focused quiescence/CI recheck

Independent reviewer inspected `a8d1b31aba890d8a1c339edc235e53480aba25d2`: **CLEAR FOR CI**. Owned-job ActiveProcesses==0 observation after process/thread release closes source-level quiescence gap; query failure/timeout remains explicit. Exact-SHA/source artifact CI changes also clear.6 focused checks PASS;10 actual Windows cases deselected/not executed; aggregate not duplicated. Actual Windows runtime and full P03 remain pending.

## Later independent increments through d501491

- Account pure domain6e96f09 and later `check_auth_rights` boundary/time regressions d0946ce: CLEAR for scoped CI inclusion. No I/O/live auth or permission to acquire locked profile; coordinator lease/capability/rate-limit gates remain separate.
- Real owned-child project interruption tests support process-kill atomicity, not power-loss or JOBS publication acceptance.
- Public rational interfaces now reject float/bool/nonfinite values; reviewer9 selected time checks PASS.
- Adjacent lock foreign-write correctionbe6f869: CLEAR;2 focused foreign/symlink regressions PASS. Final one-line O_BINARY follow-upd501491 independently checked and included in source clearance.
- Exclusive lock creation interrupted before marker completion may leave an unmarked file. Current behavior is explicit fail-closed diagnostic, not silent repair/deletion; future explicit recovery must establish ownership or select a different save path. Concurrent initialization also fails closed. Actual Windows byte locking still needs target tests.

Final application source `d501491f02686e7434c94ecc98ce487dec2275e6`: **CLEAR FOR CI only**. All later documentation-only commits retain this source qualification. Whole P03 and target runtime remain unaccepted until actual evidence.
