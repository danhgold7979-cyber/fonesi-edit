# P11-08 / TOL-04…TOL-06 — Installer archive failure-boundary hardening

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Integration branch: develop/fonesi-full
- Planning base: b43f3c53b4015e257cdc29d46a7b5d1652d08468

## Evidence reviewed

Read the current master plan P11/P12 gates, implementation coverage, requirements traceability, current status, phase ledger, P12 plan/results, dependency installer, tool discovery, and the complete tool/translation regression suite. Existing coverage includes HTTPS/checksum enforcement, safe staging, startup verification, cancellation before publication, atomic activation, repair beside corrupt versions, rollback, and explicit missing-tool behavior.

## Gap selected

The archive extraction boundary is security- and reliability-critical but has no focused regression for malicious ZIP member names and links. Current extraction rejects absolute paths, traversal components, drive-like names and Unix symlinks, and caps aggregate uncompressed size. These conditions need direct tests that prove no files escape the staging root and no unsafe member is written. The path parser also assumes every ZIP member has a first path component; malformed empty/dot-only names should fail deterministically with ValueError rather than leaking an IndexError.

## Implementation

1. Harden ZIP member validation against empty/dot-only names, NUL/control characters, absolute paths, parent traversal, drive prefixes, and symlink entries before extracting any member.
2. Ensure validation is performed for the entire archive before extraction starts, so a malicious later entry cannot leave earlier files written.
3. Preserve legitimate nested paths and platform executable names.
4. Add synthetic ZIP regression tests for traversal, absolute paths, drive prefixes, symlinks, dot/empty names, and a mixed archive where a safe member precedes a malicious member.
5. Keep extraction size limits, staging, digest verification, startup check, activation transaction, and rollback behavior unchanged.
6. Run the complete Linux/Windows source suite, plan checker, benchmarks, production build and frozen packaged proof; record evidence only for the exact CI HEAD.

## Acceptance

- [ ] Unsafe archive names/links fail with a controlled ValueError before extraction writes any member.
- [ ] No file is created outside the staging destination in traversal/absolute/drive tests.
- [ ] Safe nested archives continue to extract.
- [ ] Existing install/repair/cancel/rollback regressions remain passing.
- [ ] Exact-HEAD CI passes Linux and Windows including packaged proof.

## Limits

This synthetic archive-boundary slice does not certify Windows user-machine ACL/antivirus/power-loss behavior, real installer/update UX, Chrome authentication, live providers, GPU/HiDPI/audio, or full P11/P12 acceptance. No release merge to main.
