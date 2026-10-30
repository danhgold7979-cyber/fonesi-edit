# P09-03 / P11-03 — Bounded matrix generator validation and stress corpus
Date: 2026-10-30. Only repository `danhgold7979-cyber/fonesi-edit`; only integration branch `develop/fonesi-full`.

## Evidence and requirements
Reviewed AGENTS.md, README.md, docs/IMPLEMENTATION_PLAN.md P09-02/03 and P11-03, PRODUCT_REQUIREMENTS.md §7, IMPLEMENTATION_COVERAGE.md, REQUIREMENTS_TRACEABILITY.md MAT-03/04 and FLOW-08, CURRENT_STATUS, PHASE_EXECUTION_LEDGER, P09 plan/results and current matrix.py/test_matrix.py. P09 scene filters, pins, reorder and SQL history already exist; do not implement them again. Prior source/test CI 41021003352 passed Linux/Windows; HEAD 756902c CI 41022474391 is not assumed passed until verified.

## Slice
1. Fail closed before invoking the bounded matrix generator on noninteger/boolean N/W/K/seed, nonfinite/nonpositive time budgets, empty scenes and invalid scene count. Avoid silently producing partial rows for bad input.
2. Build a disposable **logical** matrix benchmark without real media: configurable number of scenes, angles, requested outputs, seed and W/K. Validate uniqueness, all W/K constraints, no source mutation, no synthesized outputs, and report elapsed time/peak traced Python allocation, attempts and complete/incomplete state. Do not claim Windows user-machine performance or proof of UNSAT on large space.
3. Add fast unit/regression tests for invalid controls, cancellation, deterministic seeded candidates and a large combinatorial space where no full Cartesian product is allocated. Keep runtime thresholds nonprescriptive.
4. Check source plan/test and CI Linux/Windows plus packaged proof; update evidence only after exact-HEAD results.

## Acceptance
- [ ] All invalid generator parameters fail with explicit ValueError rather than hangs or approximate behavior.
- [ ] The benchmark reports reproducible logical-source shape and preserves W/K, source identity, bounded enumeration and honest incomplete state.
- [ ] Linux/Windows CI source tests and packaged synthetic proof pass at the exact code/test SHA.

Full P09 remains OPEN: 100k-real-media matrix and solver optimality, physical Windows GUI/HiDPI, Chrome/live providers/GPU, filesystem power loss and SQLite issue #6. Do not merge main.
