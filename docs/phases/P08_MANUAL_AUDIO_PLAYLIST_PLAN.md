# P08-04 / AUD-03 — Explicit ordered audio playlist across multiple folders

**Date:** 30/10/2026. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Integration branch:** `develop/fonesi-full`.
**Reviewed HEAD:** `07796ca316474aa0a66c601874c3088c69e6b06a`. This plan is committed before source changes.

## 1. Master-plan and requirements alignment

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P08-04 and P08-07), `docs/PRODUCT_REQUIREMENTS.md` §6, `docs/IMPLEMENTATION_COVERAGE.md` (AUD-03/AUD-04), `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, `docs/phases/P08_PLAN.md`, `docs/phases/P08_RESULTS.md`, `docs/USER_GUIDE.md`, and current `batch.py`, `ui/pages.py`, `test_batch.py`, `test_app_integration.py`.

The current Batch implementation already supports:
- `shared`: one validated audio file for all selected videos;
- `by_name`: exactly one audio per source stem;
- `ordered`: natural-sorted audio files from one folder mapped one-to-one to selected videos;
- `random`: deterministic selection from a single folder using project seed and source path.

The remaining gap is an **explicit user-ordered playlist of absolute audio paths across multiple folders**. Folder mode cannot express a chosen order independent of natural filename sorting, nor mix audio files selected from separate directories. This is the outstanding part of P08-04/AUD-03, not a rewrite of existing mapping modes.

## 2. Scope

Add a fifth Batch audio mode, `playlist`, with a user-authored, ordered list:
- one absolute file path per line;
- the list order maps one-to-one to the selected video order (natural-sorted channel order, then the selected tree's child order);
- paths may come from different directories and may share a basename;
- reusing the same resolved audio file more than once is allowed and intentional;
- no natural re-sort, random fallback, omission, or implicit shared-audio fallback.

BatchPage will expose a multi-file picker that appends the chosen files to the editable playlist text area. Users can change line order directly; a Clear action empties the list. A short UI explanation states the exact video ordering used for mapping. Editing the list invalidates any existing dry-run snapshot. The other four modes and their defaults remain unchanged.

## 3. Backend contract and validation

Extend `batch_audio_assignments`, `batch_plan` and `batch_plan_report` with an optional keyword-only playlist path list so existing callers and positional arguments remain compatible.

For `playlist`:
1. Require a list/tuple of non-empty path strings; reject a single string, non-strings and relative paths rather than interpreting them relative to the process working directory.
2. Require exactly one playlist entry per selected video before publishing any plan.
3. Reject missing files, directories, symlinks and unsupported extensions. Resolve each entry strictly; preserve the original playlist order and allow paths from different parents.
4. Probe every distinct resolved path with FFprobe, require an actual audio stream and a finite positive duration, cache duplicate path probes within the preparation pass, and check cooperative cancellation between probes.
5. Bind each entry to one video and create an independent Composition snapshot with the mapped file as the main audio track; preserve all non-main music/SFX tracks and never mutate the input preset.
6. Include `audio_source` in each dry-run row so UI preview/summary shows the actual mapping. Any playlist-level validation failure aborts the whole mapping before any video plans are emitted.

Existing `shared/by_name/ordered/random` semantics, natural sorting, deterministic seed behavior, failure isolation for per-video video inputs, atomic queue enqueue and no-overwrite guards must remain unchanged. No database/schema migration is required because the validated absolute path is already captured in each composition snapshot.

## 4. UI behavior

- Add `playlist` to the Batch audio-mode combo.
- Provide a multi-select file picker filtered to supported audio extensions; append rather than replace existing entries.
- Keep the list editable as one absolute path per line and provide an explicit clear control.
- Display the mapping contract: line 1 maps to first selected video in natural channel/video order, etc. Do not promise order from a file dialog; the editable text area is authoritative.
- Hide/disable the playlist editor outside `playlist` mode but do not erase its contents when switching modes.
- Any edit to the playlist or selected audio mode invalidates the current dry-run; an old asynchronous plan callback must still be rejected by the existing revision token.
- Dry-run preview continues to show each assigned audio filename. Errors must be shown before Preview/Enqueue.

## 5. Required tests

Backend:
- Map two selected videos to two manually ordered audio files from different directories where manual order intentionally differs from natural sort and basenames may collide.
- Confirm duplicate playlist entries are permitted and each target snapshot contains the expected source.
- Reject count mismatch, empty/malformed list, relative path, missing path, directory, symlink (platform-gated where unsupported), unsupported extension and a valid container without an audio stream.
- Probe each distinct file once, honor cancellation, preserve the preset and preserve music/SFX tracks.
- Render at least one actual mapped output with FFmpeg and verify output validation plus audio stream/PCM presence.

Qt integration:
- Multi-file selection appends absolute paths in received order; Clear removes only playlist text.
- Manual line reorder changes the resulting video/audio mapping.
- Playlist edits invalidate existing plans; stale worker callbacks cannot publish a snapshot from a previous playlist.
- Non-playlist modes keep their existing behavior and do not consume playlist text.

Run plan checker, targeted backend/Qt tests, full regression suite, 128-file FFprobe benchmark, desktop/native-host build, frozen packaged proof and GitHub Actions Linux/Windows on the exact source/test SHA.

## 6. Acceptance and explicit blockers

The slice is accepted only when the manual playlist is demonstrably order-preserving across multiple parent directories, every item is preflighted before plan creation, snapshots map exactly to selected videos, a real FFmpeg render contains the intended audio, and Linux/Windows CI + packaged proof pass on the same code SHA.

This does not complete all P08/P11 requirements: large user corpus throughput, render ETA/output byte estimation, per-track meters/solo, true-peak/EBU loudness, physical Windows audio/driver/installer/ACL/AV/HiDPI/GPU, live Chrome/providers, long soak and SQLite issue #6 remain open. Do not mark P08/P11 or product release complete.
