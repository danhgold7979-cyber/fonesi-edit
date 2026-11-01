# Scoped review: 64221f2863292c849b7e3023dbc6d330f841e4d5

Verdict: subtitle staging CLEAR; media observation NOT CLEAR pending one resource-bound fix.

## Blocking finding
`src/fonesi_edit/media/validation.py::_number`: length <=80 does not bound scientific-notation expansion by Fraction. Reviewer safely reproduced `_number('1e10000')` constructing a 33,220-bit numerator. Much larger short exponents can exhaust CPU/memory before any process timeout or cancellation applies. Reject exponent syntax before conversion (bounded fixed-decimal/integer/rational grammar suffices for expected ffprobe fields), or enforce exponent and arithmetic-size bounds before constructing Fraction. Add negative tests proving rejected exponent inputs never reach Fraction plus normal decimal/rational positives.

## Checks and scope
Reviewed both new source modules and tests. Independently ran non-real-tool affected cases: 19 PASS, 1 actual-tool test deselected. Did not repeat unchanged FFmpeg/frozen/aggregate execution. Existing actual Linux H264/AAC evidence is author-attributed; Windows media evidence remains open.

Subtitle staging binds parser observation to same immutable bytes supplied to exclusive owned-stage writer, checks digest/length, returns retained receipt on post-write cancellation, and never publishes/deletes/transitions jobs. CLEAR for that bounded substrate only.

Media expectation checks and full mapped decode-to-null remain observations, not publication authority or visual fidelity. Missing stream duration fails closed. No new assertion closure, no phase acceptance, no permission to bypass the pending specific remote publication denial.

## Targeted fix closure — 4213529bacdaa6b81d604ef536bbb987d434d531

Combined bounded substrate verdict: CLEAR. `_number` now gates at most 80 characters of ASCII signed integer/fixed decimal or numerator/denominator syntax before Fraction. No exponent expansion remains. Independently ran the new constructor-trap negatives and exact rational positives: 11 PASS, 15 deselected. Working tree clean. Unchanged real FFmpeg/frozen/aggregate execution not repeated.

Inspected `runtime/probe_corrupt_payload.py`: it preserves MP4 metadata while zeroing only mdat payload, requires inspect_media codec success and specifically `Output failed full decode`, and verifies damaged bytes unchanged. Author reports one actual Linux PASS; reviewer inspected harness, did not rerun or independently attest its execution. This is stronger decode-path evidence than the earlier truncated fixture, which could fail during probing.

Still only parser/stage and metadata/full-decode observations. No Windows media proof, visual parity, publication/job authority, restart acceptance, new child criterion closure or remote publication authorization.
