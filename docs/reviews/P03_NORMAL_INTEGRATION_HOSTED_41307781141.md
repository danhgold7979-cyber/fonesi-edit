# Normal integration checkpoint — verified

2026-11-01. Independent read-only API/artifact inspection; no tests rerun.

Run 41307781141: four completed SUCCESS jobs, exact source `1835c790d18aeff79a6abaee4f6b985fd7058ea0`, tree `af55e0ee9e767363b6d962e0c30a56ce8340a7c8`. Four ZIP SHA256 values match GitHub API and downloaded archives. All nine member SHA256 values and ZIP/extracted bytes match. Four source receipts equal summary source/tree/runtime. All JUnit files contain 610 cases and zero failure/error:

| Target | Runtime | PASS | SKIP |
|---|---|---:|---:|
| Windows | Python 3.12.10 / SQLite 3.49.1 | 584 | 26 |
| Windows | Python 3.13.16 / SQLite 3.50.4 | 584 | 26 |
| Linux | Python 3.12.15 / SQLite 3.45.1 | 571 | 39 |
| Linux | Python 3.13.17 / SQLite 3.45.1 | 571 | 39 |

All 13 coordinator-inbox/progress tests are non-skipped PASS on all four targets. This is the normal aggregate at this source, unlike earlier scoped-delta evidence. Skips remain explicit platform branches and unavailable actual FFmpeg gates, not hidden passes.

GitHub steps confirm actual Windows 3.12 onedir build and frozen checks SUCCESS; other targets skip those steps. Frozen receipt has five passing CLI cases (schema, subtitle, malformed subtitle, empty encoding, read-only tool discovery), license hash and unchanged fixture hashes. Reported executable hash is harness evidence, not independently rehashed downloaded binary. Not GUI usability, codec/render fidelity, provider capability or release acceptance.

## Next narrow gate
Ledger remains 6/438; no new closure from aggregate counts. OPS-02.02 exact child is “Cancel terminates owned children and safe temps”. Current UI→owner cancellation and typed-validator→owned-stage cleanup have separate causal integrations. One combined real owner/UI request → actual owned child/descendant → typed retirement → cancellation acknowledgment → only-owned-stage cleanup test is a meaningful remaining integration gate, not arbitrary extra infrastructure. Include no-success/history and source/foreign/final preservation assertions; unknown-retirement must retain temps and refuse cleanup (existing negative may be reused if unchanged).

A successful target-native combined path can support reviewing that narrow child without demanding an entire default scheduler first. Default production scheduler/executor wiring, other PR-L169 semantics, P03-04/P10-06 completion and release readiness remain separate open gates. Do not expand a narrow child into full application acceptance, nor claim Python decoder stand-in proves FFmpeg.

https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41307781141
