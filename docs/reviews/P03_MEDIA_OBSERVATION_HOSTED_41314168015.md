# Media observation hosted evidence — verified

2026-11-01. Read-only API/artifact verification; no tests rerun.

Four SUCCESS jobs at source `68cb784ad1f74a1dba234b32b697db8f242d98f0`, tree `0cbe4c4b9a3210f8eef6b8642a6387123cea6eed`. Four API ZIP digests match local archives; all eight members match declared hashes and ZIP bytes. Source receipts match exact source/tree/runtime. Each JUnit has 37 PASS, zero skipped/error/failure.

Windows Python 3.12.10 / SQLite 3.49.1 and 3.13.16 / SQLite 3.50.4; Linux Python 3.12.15 and 3.13.17 / SQLite 3.45.1. This is typed normalization/headless boundary CI, not actual Windows ffprobe, decoded-frame map or render proof. Ledger remains 9/438; no child proposed/accepted.

## Next decoded-frame observation protocol notes
Preserve pts and best_effort_timestamp as separately named facts with explicit selection provenance; do not silently substitute one as the other's original timestamp. Keep decode/presentation order as reported and discontinuities/missing durations explicit. Bind global selected stream/timebase, content fingerprint and tool hash; any pre/post mismatch invalidates the entire purported binding.

Distinguish command/transport completion from complete trustworthy frame coverage and from media validity. Exit0/JSON EOF alone cannot establish that damaged or missing source frames were not skipped. Frame cap, byte cap, timeout, cancellation or malformed/truncated JSON cannot yield complete map. With existing bounded all-at-once JSON capture, failure may yield no safely parsed prefix at all; it is fine to return unavailable rather than fabricate PARTIAL frames from truncated JSON. Do not trust nb_frames or average rate to synthesize missing events/last duration. Any bounded interval/window scan must identify its scope and never masquerade as full-stream scan.

No additional conceptual blocker beyond these and prior design gates. Keep frame observation distinct from render-ready conversion and native codec support.

https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41314168015
