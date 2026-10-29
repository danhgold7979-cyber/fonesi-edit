# P08-01 / P11-05 — Advanced local batch video metadata filters

**Date:** 2026-10-29. **Repository/branch:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`. Written before code.

## Source and requirement review

Read `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P08-01, P11-05), `docs/PRODUCT_REQUIREMENTS.md` §5, `docs/IMPLEMENTATION_COVERAGE.md` BAT-01…BAT-04, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, P08 plan/results, `batch.py`, `ui/pages.py`, `prototypes/media.py` and batch/Qt integration tests. Existing FFprobe metadata filter is asynchronous and covers duration + orientation-neutral short edge. `MediaInfo` already exposes codec and rational FPS; optional video-stream bitrate can be sourced from FFprobe. This slice fills one explicit P08 filtering gap without changing video source bytes, checkbox selection or batch generation.

The earlier [P03 source CI 40905102578](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40905102578) PASSED both Linux (611) and Windows (610+1 skip), including desktop/native-host/frozen proof. Subsequent documentation-only HEAD may have its own independent running CI. None of this establishes live platform/physical Windows acceptance.

## Implementation

1. Extend `MediaInfo` with a *trailing optional* `video_bitrate` field sourced from the FFprobe **video stream** `bit_rate` only when a positive integer; never substitute container bitrate (includes audio). Missing, `N/A`, zero and malformed stream values remain `None`, not fabricated. Existing 6- and 7-argument `MediaInfo` constructions remain supported.
2. Extend `probe_batch_metadata` to emit `codec`, numeric FPS derived from the validated rational value, and optional `video_bitrate_kbps`, alongside duration/width/height. Preserve deduplication/cancellation/per-file failures and worker-thread isolation.
3. Add codec choice (all/H.264/HEVC/VP9/AV1/MPEG-4), min/max FPS and min/max **video** kbps controls to BatchPage. Reject inverted ranges and display actionable UI status. The active filters hide entries with unavailable required metadata rather than treating unknown as zero. Preserve hidden checkboxes, channel groups, and stale scan/metadata callback guards. Do not auto-uncheck or silently alter dry-run plans merely by filtering the view.
4. Add synthetic FFprobe JSON tests for video bitrate present/missing/malformed (container-only bit rate deliberately ignored); real generated video metadata regression; Qt tests for combined codec/FPS/bitrate filters, missing-value behavior, invalid ranges, selected hidden files and source-revision handling.
5. Run `scripts/check_plan.py`, focused suites and full Linux/Windows CI (desktop/native-host + frozen packaged proof), update P08/P11 results, coverage, status and ledger only after reading exact SHA proof. No `main` merge.

## Bounded acceptance

- [x] Codec/FPS/video bitrate are extracted from FFprobe without inventing missing video bitrate values.
- [x] Filtering and invalid-range handling work in BatchPage without modifying selected files, settings, original media or stale jobs.
- [x] Tests and both packaged CI runners PASS at the exact code/test SHA, evidence recorded honestly.
- [ ] P08 remains OPEN for large corpus benchmarks, audio meters/playlist/solo and physical Windows user-device/installer/Chrome/GPU/live-source acceptance.

## Verified source, tests and CI (29/10/2026)

[P08 plan](https://github.com/danhgold7979-cyber/fonesi-edit/blob/develop/fonesi-full/docs/phases/P08_ADVANCED_METADATA_FILTER_PLAN.md) preceded [code 6307042](https://github.com/danhgold7979-cyber/fonesi-edit/commit/630704259e38e3ed829817230344ce7a14c993bd), then [tests 81952fd / a0d9e74](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a0d9e74e4fd356568ecaf60c49a5edc0a2bc9d6f). `MediaInfo.video_bitrate` is optional and read only from the FFprobe video stream; missing, N/A, zero or malformed stream values stay unknown (`None`), even if the **container** reports a bitrate. `probe_batch_metadata` now also produces normalized codec, rational FPS converted to a numeric value and optional video kb/s; no media is mutated. BatchPage adds codec + FPS + video-bitrate range controls. Invalid ranges fail clearly; unreadable/unknown necessary facts fail closed when the corresponding filter is active; hidden checkbox state and stale callback protection remain unchanged.

[CI 40908188050](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40908188050) **SUCCESS on exact SHA a0d9e74**: Linux **618 passed**; Windows **617 passed, 1 intentional POSIX-only skip**. Phase references, production desktop/native-host builds and frozen packaged synthetic/localhost proof PASS on both runners; Windows development build and evidence artifacts uploaded. New tests cover synthetic FFprobe stream-vs-container bitrate, 29.97 FPS rational conversion, optional bitrate legacy constructor, real media and Qt filters/unknown bitrates/range validation/selection stability. This is bounded proof, not corpus-scale throughput/ETA, live providers, Chrome/auth, full Windows user device or GPU acceptance; P08 remains OPEN.
