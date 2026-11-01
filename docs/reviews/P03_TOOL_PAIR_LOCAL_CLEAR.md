# P03-08 explicit tool-pair observation — scoped CLEAR

Reviewed 2026-11-01, read-only source review; no remote operation.

Exact SHA256 pins verified:
- checks.py: 4e1bb005c76733d66f7ec46486f7279a6523966145ec147be080cdf0314fffc1
- test_tool_checks.py: 6c1f6f858b2453fe66dd90ebc3efe50d0e939e9421de3b635cfb053e93d19864
- TOOL_DISCOVERY.md: cfd4906d0c50437c98eee15f786b28bf3e2ff92ba80c279ef64a6392ad008c2a
- reproduce.py: e282288aeecc35d2bfa4221c7a0835622c03f5b1223a0d39f281fdaae741b4c9
- summary.json: ea0427e4c961bc9a80c25188427542313e83b807809f99b857e1843fd92ad3bb

No blocking defect found for the documented caller-authorized, local observation API. Both exact executable hashes and known fixture hash are checked before launch. Version/library mismatch refuses functional fallback. Existing owned-process capture/time/cancel semantics and media full-decode validator are reused; raw output comparison is exactly 768 zero bytes. Returned scope is fixture/stream-specific, not universal tool readiness. Errors sanitize tool stderr. Fixture and tool hashes are checked again across stages.

Independent selected unit tests: 6 PASS, 7 deselected, process exit 0:
`pytest -q tests/test_tool_checks.py -k 'bad_explicit_pin or executable_drift or versions_differ or invalid_policy'`.
No unchanged real FFmpeg/baseline rerun. Reviewed recorded actual Linux receipt, source/harness hash linkage and explicit binary/fixture hashes; receipt is not independent replay evidence. No Windows proof.

Important unchanged trust boundary: pathname hashes before/after execution do not provide atomic executable identity or detect a swap-and-restore during this same observation. Caller authorization must operate with trusted stable tool paths; this is not a hostile-namespace executable capability. Dynamic libraries are not authenticated. Limits are per process (up to five launches), not a hard overall OS-I/O deadline. No persistent registry, execution lease, installer, arbitrary-workflow capability, requirement child closure or full P03 acceptance is established.
