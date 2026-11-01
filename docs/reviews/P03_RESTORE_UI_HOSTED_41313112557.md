# Restore UI affected hosted evidence — verified

2026-11-01. Independent read-only API/artifact verification; no tests rerun.

Run 41313112557 has four completed SUCCESS jobs, exact source `c44a5d3b7e21c89b5ebaef7e403f1c9339e90fa1`, tree `7ec7498feead0c4d9276589a7274400b0b12608c`. Four API ZIP digests match downloaded archives; all eight extracted members match declared hashes and exact ZIP bytes. Source receipts match summary SHA/tree/runtime. Each JUnit contains 19 PASS, zero skipped/error/failure, including all four new restore UI cases.

Actual Windows Python 3.12.10 / SQLite 3.49.1 and 3.13.16 / SQLite 3.50.4; Linux Python 3.12.15 and 3.13.17 / SQLite 3.45.1. Actual worker restore/event-loop/active-store preservation, held cancel-close uncertainty, late cancel preserving confirmed result and stale callback filtering pass all targets; shared shell/recovery/relink tests pass too.

Strengthens already accepted OPS-03.04 via UI worker route. Ledger remains **9/438**, no extra child. Does not establish interactive native picker usability, latest-state choice, live store switching, WAL-format backup support, frozen restore or full task/phase acceptance. This is affected 19-case CI, not another full aggregate.

https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41313112557
