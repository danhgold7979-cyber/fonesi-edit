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

- [x] Unsafe archive names/links fail with a controlled ValueError before extraction writes any member.
- [x] No file is created outside the staging destination in traversal/absolute/drive tests.
- [x] Safe nested archives continue to extract.
- [x] Existing install/repair/cancel/rollback regressions remain passing.
- [x] Exact-HEAD CI passes Linux and Windows including packaged proof.

## Limits

This synthetic archive-boundary slice does not certify Windows user-machine ACL/antivirus/power-loss behavior, real installer/update UX, Chrome authentication, live providers, GPU/HiDPI/audio, or full P11/P12 acceptance. No release merge to main.


## Execution result — PASS (30/10/2026)

- Implementation/test: [bf51cd9](https://github.com/danhgold7979-cyber/fonesi-edit/commit/bf51cd9ea7e09842b7f89fffea022b5f8788d58a).
- Exact-HEAD CI [41051655230](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41051655230) SUCCESS: Linux 832 passed; Windows 831 passed + 1 intentional POSIX-only skip.
- Both OS passed phase references, Batch 128-source synthetic FFprobe dry-run (failed_count=0), 2,000-output logical Matrix benchmark (complete=true, max spread 5), production desktop/native-host build and frozen packaged proof.
- Batch: 6.619013 s Linux / 10.326949 s Windows. Matrix: 15.191691 s Linux / 17.587695 s Windows.
- Artifacts: Linux evidence 390,718 bytes; Windows evidence 323,577 bytes; Windows development build 197,376,218 bytes.

This closes only the initial traversal/absolute/drive/symlink preflight slice. Windows portability and the broader P11-08 installer/authentication gates remain separate.
