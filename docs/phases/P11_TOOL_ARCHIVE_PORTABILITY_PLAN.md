# P11-08 follow-up — Windows archive path collisions and special entries

- Date: 2026-10-30
- Repository: danhgold7979-cyber/fonesi-edit
- Branch: develop/fonesi-full
- Base: bf51cd9ea7e09842b7f89fffea022b5f8788d58a

## Evidence and rationale

The first archive hardening slice has exact-HEAD CI evidence: run 41051655230 passed Linux (832 tests) and Windows (831 tests + 1 intentional POSIX-only skip), including both production builds and frozen packaged proofs. Its path checks cover traversal, absolute paths, drive prefixes, dot/empty names and symlinks.

A remaining portability gap exists because the app's install target includes Windows. ZIP members may be valid POSIX paths but unsafe or ambiguous on Windows: reserved device names (CON/NUL/COM1/LPT1), trailing dots/spaces, invalid Windows filename characters, duplicate paths differing only by case, file-vs-directory collisions, and special Unix file types other than regular files/directories. Encrypted members also cannot be extracted by the current installer and should fail before any write.

## Scope

1. Reject Windows-invalid/reserved path components and trailing dots/spaces after normalizing ZIP separators.
2. Detect duplicate/case-folded path collisions and parent file-vs-child conflicts across the entire archive.
3. Permit only unspecified, regular-file, and directory Unix entry types; reject symlink/FIFO/socket/block/character devices.
4. Reject encrypted members before extraction.
5. Keep validation preflight all-or-nothing: no archive member is written until every entry passes.
6. Add synthetic tests for reserved names, invalid characters, trailing dot/space, backslash traversal, duplicate case-folded paths, parent conflicts, special Unix modes, encryption flags and safe archives.
7. Preserve valid nested FFmpeg/Node archives, staging, digest verification, startup checks, transactional activation and rollback.

## Acceptance

- [ ] All unsafe and ambiguous archive entries fail with ValueError before writing any file.
- [ ] Case-folded duplicate names and file/directory collisions are rejected deterministically.
- [ ] Safe nested archives and explicit directory entries still extract.
- [ ] Existing installer, repair, cancellation, rollback, and tool-path tests remain passing.
- [ ] Exact-HEAD Linux and Windows CI, phase checker, benchmarks, builds and packaged proofs pass.

## Limits

Synthetic CI does not certify Windows user-machine ACL/AV/power-loss behavior, signed installer/update UX, live Chrome/provider authentication, GPU/HiDPI/audio, or full P11/P12. Do not merge main.
