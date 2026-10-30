# P11-08 / TOL-04…TOL-06 — Interrupted download and verification failure atomicity

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: 1858e7c6d761e7e28574a75a91260fbfb2b80d3f

## Evidence reviewed

Read the current master P11/P12 requirements, TOL-04…TOL-06 traceability, coverage, status, phase ledger, dependency installer, and tool/translation tests. Existing code stages downloads under a temporary directory, validates SHA-256 and archive members, runs a startup/version check before publishing, atomically activates tool paths, and retains old versions for rollback. Existing tests cover cancellation after startup verification, failed startup checks, activation transaction rollback and corrupt receipt repair, but do not directly prove that a network interruption or checksum failure during a replacement install leaves the previous active version intact and removes partial staging.

## Scope

1. Add synthetic regression for a fetch that writes a partial archive then raises a connection error.
2. Add synthetic regression for a completed download whose bytes do not match the declared SHA-256.
3. Add cancellation immediately after download returns but before digest verification/publication.
4. Add an end-to-end install regression where a correctly hashed archive is malicious and rejected by ZIP preflight.
5. In every case, first install a valid older FFmpeg/ffprobe version, then assert the old paths, bytes and active-version metadata remain unchanged; no new final version is activated; and no .staging-* directory remains.
6. Keep failure visible to the caller; never report ready or progress=1 for a failed replacement.
7. Run full Linux/Windows suite, plan checker, benchmarks, production build and frozen packaged proof.

## Acceptance

- [ ] Partial network transfer failure leaves the previous active tool and companion unchanged and cleans staging.
- [ ] SHA-256 mismatch leaves the previous active tool and companion unchanged and cleans staging.
- [ ] Cancellation after fetch but before verification leaves the previous active tool and companion unchanged and cleans staging.
- [ ] ZIP preflight failure during install does not publish or activate the new version and does not leave extracted partial files.
- [ ] Existing repair, successful reuse, atomic activation, startup check and rollback tests remain passing.
- [ ] Exact-HEAD CI passes Linux and Windows including packaged proof.

## Limits

Synthetic fetch/SQLite/filesystem fixtures do not certify physical Windows ACL, antivirus, disk-full, process-kill or power-loss behavior; signed installer/update UX; Chrome/DPAPI/session handoff; live providers; GPU/HiDPI/audio; or full P11/P12 acceptance. Do not merge main.
