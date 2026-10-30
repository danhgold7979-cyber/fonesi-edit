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

- [x] All unsafe and ambiguous archive entries fail with ValueError before writing any file.
- [x] Case-folded duplicate names and file/directory collisions are rejected deterministically.
- [x] Safe nested archives and explicit directory entries still extract.
- [x] Existing installer, repair, cancellation, rollback, and tool-path tests remain passing.
- [x] Exact-HEAD Linux and Windows CI, phase checker, benchmarks, builds and packaged proofs pass.

## Limits

Synthetic CI does not certify Windows user-machine ACL/AV/power-loss behavior, signed installer/update UX, live Chrome/provider authentication, GPU/HiDPI/audio, or full P11/P12. Do not merge main.


## Execution result — PASS (30/10/2026)

- Implementation chain: [8f70309](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8f703094607398fc398161664feacaa75dea58e5) → [e2c2a08](https://github.com/danhgold7979-cyber/fonesi-edit/commit/e2c2a085474eed80901d95e1dd4eabb01d4d2b72) → [f880daf](https://github.com/danhgold7979-cyber/fonesi-edit/commit/f880dafcfed0143a9a3416bc073718446e5a4b4f) → final [85654ec](https://github.com/danhgold7979-cyber/fonesi-edit/commit/85654ec780f3ab8752af834e081a46f406d124d8).
- Final exact-HEAD CI [41053597336](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41053597336) SUCCESS: Linux 850 passed; Windows 849 passed + 1 intentional POSIX-only skip.
- Both runners passed phase references, 128-source synthetic FFprobe Batch dry-run (failed_count=0), 2,000-output logical Matrix benchmark (complete=true, max spread 5), production desktop/native-host build and frozen packaged render/Batch/Matrix/localhost download/UI proof.
- Batch: 5.012570 s Linux / 10.882223 s Windows. Matrix: 9.079294 s Linux / 17.686874 s Windows.
- Artifacts: [Linux evidence 390,874 bytes](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41053597336/artifacts/12975194835), [Windows evidence 323,726 bytes](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41053597336/artifacts/12976023012), [Windows development build 197,380,520 bytes](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41053597336/artifacts/12975818540).

Two intermediate CI attempts exposed defects in backslash extraction: first, validation normalization did not normalize the extracted path; second, changing ZipInfo.filename while relying on extractall's implicit name lookup caused a KeyError. The final code preflights all members, normalizes names after preflight and passes the validated ZipInfo list explicitly. The exact final Linux/Windows run passes.

This closes the synthetic archive portability/collision slice only. Physical Windows ACL/AV/disk-full/power-loss, signed installer/update, Chrome authentication, providers, GPU/HiDPI/audio and all P11/P12 gates remain open.
