# P03 integration checkpoint — source CLEAR for scoped CI

2026-11-01. Independent read-only review of final local integration delta; no publication by reviewer.

Verified SHA256:
- jobs/repository.py: 5a270bf6df656cba1a175dc3af92cb55dd48509e9fa22f21b042e50fcc2d5b78
- test_jobs_open_identity.py: 47f72150137b58ee5e05d6744c50c587a12a5a15c2c81694db1a2b26523f1df0
- test_tool_discovery.py: 3d926819cd8d9ec6cb5792c6acd2aa1a7fa0455d6a8f056eefd789cd2caef44d
- clean-foundation.yml: 617ca57d911d919cafc29801c132e97348e404c8bb71dde7eb5f07697d4d2e7c
- check_frozen_boundaries.py: cab5f66875695669fa65d736aa1f1f5bdc11340cfe358653309b6bbb13aed2c0
- test_frozen_boundary_harness.py: 36e18f3df8593b0ed2496fe19be8084d0ae269158ac392edbdcd79288f012414
- tasks.json: 68e34d1ab273f5763b225f62c15291d0e30027aeb48090c11707e04fb056d762

No blocking defect found in delta. Foreign existing empty/v0 jobs files refuse before SQLite by default, invalid receipt cannot be bypassed by explicit adoption, leaf symlink is no longer resolved into another store. Initial/recovery connection uses mode=rw. Original FD identity remains anchored; continuity loss permanently revokes repository, with checks before WAL/receipt/submission COMMIT. Conditional rollback preserves observed post-COMMIT exception rather than replacing it with a no-active-transaction error. Existing explicit known-schema adoption remains a separate caller-authorized operation; no generic retry added.

Independent targeted test execution: test_jobs_open_identity.py — 7 PASS, process exit 0. Source inspected narrow recovery call-site; unchanged SQLite 1546 baseline not repeated.

Portable discovery fixtures now use Windows names and isolate common-directory environment instead of presuming real runner installations absent. Frozen harness uses bounded owned runner, exact MIT byte comparison, Unicode schema/subtitle inputs, invalid and empty-encoding cases, isolated read-only candidate scan, input/data nonmutation checks, exclusive evidence creation. Report binds expected source SHA and binary SHA. Harness itself is not frozen/native proof; upcoming target execution supplies that evidence. Normal four-target matrix and pinned actions/read-only permissions retained. Tasks changed nine P03 statuses to IN_PROGRESS with explicit NOT_ACCEPTED scope, not acceptance-count inflation.

No full aggregate, real FFmpeg or frozen executable rerun by reviewer. Source clearance allows the root-authorized coherent checkpoint CI, not full P03 acceptance or Windows runtime PASS. Initial receipt-creation crash gap and explicit recovery policy remain existing documented limitations.
