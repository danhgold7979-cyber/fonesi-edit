# P09-03 / MAT-04 — Large-space per-scene balance selection
Date: 2026-10-30. Repository: danhgold7979-cyber/fonesi-edit. Branch: develop/fonesi-full.

## Evidence reviewed before implementation
Read AGENTS.md, README.md, master implementation plan P09 and P11, product requirements §7, traceability MAT-03/MAT-04, coverage, current status, execution ledger, P09 plan/results, P09 logical benchmark plan and atomic enqueue plan, current matrix.py, scripts/benchmark_matrix.py, tests/test_benchmark_matrix.py and tests/test_matrix.py. Latest integration HEAD before this slice: c00aab1de44089934a85d94916008e1afbae7fca; its documentation CI run 41026581188 SUCCESS. Exact code/test evidence at 7d2d74a7173184d1e752e508ff83aa8971f72321, CI 41025266091 SUCCESS (764 Linux / 763 Windows + one POSIX skip).

## Gap
The large-space (>10,000 combinations) generator samples one candidate row at a time using inverse global hash frequency. It has no bounded candidate competition, and the benchmark currently checks only uniqueness/W/K/source immutability—not the explicit MAT-04 balanced-use requirement. Hash frequency is global rather than per scene, so equal-content hashes across scene folders can cross-contaminate balancing metrics.

## Implementation
1. Add optional balance_candidates to generate, default 8, strict integer range 1..64. Preserve existing callers, seeded determinism, W/K, locks, history, cancellation, time budget and no-cartesian allocation.
2. For large spaces, sample at most this many legal candidates per output; select the candidate minimizing projected per-scene sum-of-squares use, then maximum projected use, with seeded tie-break. Count use by (scene index, angle hash), never by hash globally. A candidate is eligible only if unique and W/K-valid against the complete applicable history.
3. The bounded candidate pool must honor the same wall-clock budget and cancellation token. If no candidate is found before the budget, return the existing explicit incomplete result; never relax constraints or claim UNSAT.
4. Extend logical benchmark CLI/results with candidate-pool size and per-scene frequency min/max/spread. Benchmark only logical IDs, explicitly not media/FFmpeg/device throughput.
5. Add regression for per-scene balancing on a 65,536-combination logical space, seeded repeatability, duplicate hashes across scenes, strict candidate parameter validation, locks/W/K, and cancellation. Preserve all prior tests.
6. Run phase-reference check, full Linux/Windows CI and packaged proofs; update status/coverage/traceability/results/ledger only after exact-SHA success.

## Acceptance
- [ ] Large-space generation improves per-scene use balance measurably versus one-candidate baseline under the same deterministic seed and candidate count.
- [ ] W/K/history/locks/uniqueness and per-scene identity remain intact; duplicate content hashes in different scenes do not merge their frequency counters.
- [ ] Candidate sampling is bounded, cancellable and time-budget-aware; incomplete is never reported as proven infeasible.
- [ ] Linux/Windows regression and frozen packaged proof pass on exact code/test SHA.

External gates remain open: real 100k-media corpus and solver optimality, physical Windows/HiDPI/installer, NTFS/exFAT/power loss and SQLite issue #6, live Chrome/providers and GPU. Do not merge main.

## CI budget calibration (30/10/2026)
The first 10-scene × 10-angle × 2,000-output run on GitHub Linux reached the explicit 10-second search budget while tracemalloc was enabled: 779 tests passed and the one stress test correctly reported incomplete rather than fabricating completion. This is a valid bounded-search result, not a solver correctness failure. Keep the 10-billion theoretical space and 2,000 outputs, but raise this test/CI benchmark budget to 45 seconds (still bounded below the script's 60-second cap); do not weaken the completion, uniqueness, W/K or memory assertions. Re-run both OS and retain the JSON evidence artifact.
