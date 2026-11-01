# Windows discovery harness correction — scoped CLEAR

2026-11-01. Read-only review, no remote operation.
Verified hashes:
- tests/test_tool_discovery.py 2a9de25bba287fd3ddd627b839a1c91d25a95b639e9c81ae85a55f16fbc508cf
- scripts/check_frozen_boundaries.py 76e3eba4fce34620902d5d4d415214d533a2739128080ee36302963ae0ce7af3
- .github/workflows/clean-foundation.yml 086ed5a936bfccd35a53003827dfecfe518af97103ff5b80192883f422a1c4d9

No blocker. An empty host candidate list is not the discovery requirement. Replacement assertions require COMPLETE enumeration, every observed candidate UNCHECKED, an explicitly missing Chrome selection INVALID_EXPLICIT_PATH with no fallback candidate, and only non-ready selection states. The fresh subprocess still traps GUI/storage imports. Frozen checks retain input hashes and absent application-data directory. No application source changed; no ownership or no-fallback check removed.

Independent exact fresh-process regression: 1 PASS, exit 0. No unchanged harness, aggregate or frozen run repeated. Host Chrome visibility and its startup/environment mechanism are not independently explained; removal of the earlier asserted restoration cause is appropriate. Preserve original failed test evidence rather than relabeling it successful.

Workflow uses paired [integration-repair] [windows-boundary] markers to select both Windows versions and affected four tests, followed by pending plan/schema and Windows312 frozen checks. Ordinary unmarked matrix unchanged. Do not combine coordinator markers. Prior runs' passing cases remain evidence at their original source identities; this repair run is not a new aggregate or full-phase acceptance.
