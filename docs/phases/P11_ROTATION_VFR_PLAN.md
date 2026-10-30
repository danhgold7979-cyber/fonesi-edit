# P11-01/P11-04 + P04-02/P07-07 — VFR/mixed-FPS and rotated-metadata source crop

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only integration branch:** `develop/fonesi-full`. **Status:** planned before source changes.

## Master-plan alignment and existing evidence

Read `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P04-02, P07-07/08, P11-01/04), `docs/PRODUCT_REQUIREMENTS.md` (crop, subtitle trim/speed, mixed FPS), `docs/REQUIREMENTS_TRACEABILITY.md` (ED-20/SUB-07/FLOW-14), `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, P04/P06/P11 results/plans and `src/fonesi_edit/prototypes/media.py`, `src/fonesi_edit/render.py`, `tests/test_render_composition.py`. HEAD before this slice: `14cbb7b474c4b22cd21a4b65bf23825252d8ac85`; [CI 40882402218](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40882402218) SUCCESS (587 Linux, 586 Windows + 1 intentional skip, frozen packaged proofs).

## Reproduced problem / safety boundary

`probe()` currently reports raw encoded dimensions but drops FFprobe Display Matrix rotation. `compile_graph()` generates crop geometry from the encoded width/height, while FFmpeg input defaults to auto-rotating frames **before the crop filter runs**. Local synthetic FFmpeg 7.1.5 investigation used a 320×180 left-red/right-blue video with `-display_rotation 90`; decoded frames become **180×320**. The source's left red half becomes the displayed **bottom half**, so an untransformed crop rectangle applied to the auto-rotated frame can select the wrong region without a validation error. This is a concrete metadata-coordinate regression risk, not proof of physical Windows behavior.

## Implementation plan

1. Extend `MediaInfo` with backward-compatible `display_rotation` (default zero) from FFprobe video Display Matrix rotation or legacy rotation tag; use only finite numeric metadata, with explicit handling for crop if the angle is unsupported.
2. Add pure `crop_rect_after_autorotate(clip,info)`: after checking the quarter-turn Display Matrix, derive FFmpeg's **display-oriented** width/height (swap for ±90°) and run the existing even-pixel crop calculator on that displayed geometry. Keep FFmpeg autorotation. Importantly, `CropDialog` uses `extract_frame()`, which also autorotates; its normalized crop rectangle is already in **display space**, so re-rotating crop coordinates would contradict the actual UI. Preserve `crop_rect_pixels()` and existing projects. Reject non-orthogonal metadata with a nontrivial crop instead of silently using uncertain bounds.
3. Unit tests for raw vs displayed dimensions with 0/±90/180 and invalid angles, preserving full-frame defaults. Synthetic FFmpeg 7.1.x test creates an encoded red-left/blue-right source and remuxes +90° Display Matrix; the UI-visible bottom half is red. Select **bottom 50% in displayed coordinates**, verify raw probe, expected displayed crop expression, reference PNG's dominant red center and rendered MP4 decoded frame. Ensure source bytes unchanged.
4. Add independent synthetic VFR + mixed-FPS + video-without-audio render tests: generate differing source frame presentation timestamps, combine VFR 30-ish input with a 24 FPS CFR input, normalize to output 25 FPS, exercise trim/speed and source subtitle cue map, reference frame and MP4 decode/probe, assert output dimensions/duration and no source mutations. Do not claim a broad VFR/rotated media corpus.
5. Run `scripts/check_plan.py`, focused pytest, full Linux/Windows CI, production desktop/native-host builds and frozen packaged proof. Record exact SHA and runner results, fix failures without weakening assertions. Update P11/P04 results, coverage/status/ledger after CI verification.

## Acceptance and remaining gates

- [x] Probe exposes real 90° display metadata; the **display-space** normalized crop from CropDialog maps to the correct displayed dimensions without re-rotating its coordinates.
- [x] Frame-based proof selects the intended source half after autorotation; preview and exported video both show the same dominant color, source bytes unchanged.
- [x] True VFR fixture with unequal PTS gaps and a different-FPS second clip render with expected duration, normalized output FPS, and correct subtitles/no-audio behavior.
- [x] Full Linux/Windows regression and frozen packaged/native-host proofs PASS on exact code/test SHA.

**Still open:** production VFR and rotation/flip matrices beyond synthetic fixtures, crop UX metadata coordinate documentation, physical Windows/HiDPI/4K performance, GPU codec parity, audio/video seek with real user media, Chrome/live translation/platform rights, crash/power-loss soak and intermittent Windows SQLite [issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). Do not close P04/P11 in full or merge to `main`.

## Review correction before final regression

Source inspection confirmed `src/fonesi_edit/ui/dialogs.py::CropDialog._load_frame` uses FFmpeg's auto-oriented `extract_frame`, then draws/interacts with the crop rectangle on that displayed frame. An early source-only commit tried rotating the rectangle itself; this would select the wrong region for UI-authored projects. The integration fix must instead swap dimensions for quarter-turn metadata and apply the **unchanged** normalized rectangle after auto-rotation. This mismatch was identified during implementation review, before any P11 acceptance claim. Keep CI and actual frame-color assertions active.

## Implementation evidence and specific validation (29/10/2026)

- [Probe/display metadata 5f8dd26](https://github.com/danhgold7979-cyber/fonesi-edit/commit/5f8dd264eb23440edfaf6123fec0beec7988b971) reads FFprobe Display Matrix (fallback legacy rotate tag) into a backward-compatible `MediaInfo.display_rotation` field, while preserving encoded pixel dimensions.
- [Initial source-space attempt ef9fade](https://github.com/danhgold7979-cyber/fonesi-edit/commit/ef9fadef61f5f58a57b6ac480bc420b2029ec192) was corrected before final acceptance: reviewing `CropDialog` established that normalized coordinates are already **display-oriented**. [Correction 2c14c2c](https://github.com/danhgold7979-cyber/fonesi-edit/commit/2c14c2cba8f1d286da1e22f7118003a95e21522f) uses the swapped post-autorotation frame dimensions without rotating the user's rectangle a second time. It rejects non-orthogonal display metadata with a non-full crop rather than silently choosing incorrect bounds.
- [Regression 5ab1bca](https://github.com/danhgold7979-cyber/fonesi-edit/commit/5ab1bcad256eb0a1fe131f1dbf63de8bf52cd534) checks pure 0/±90/180/270° geometry, actual FFmpeg +90° rotated red/blue source and dominant red output pixel in both reference PNG and final MP4, source bytes unchanged; it also generates **genuine variable input frame timestamps**, combines the VFR source with a 24 FPS source without audio, checks subtitle cue timing and normalized 25 FPS output, actual preview and final MP4 validation.
- [CI 40885720673](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40885720673) **SUCCESS on exact source/test SHA `5ab1bcad256eb0a1fe131f1dbf63de8bf52cd534`**: **595 Linux PASS / 594 Windows PASS + 1 intentional POSIX-only skip**. Plan validator, production desktop/native-host build and frozen packaged synthetic/localhost proof PASS both runner OS. Windows development artifact uploaded.

These checks close only this bounded **synthetic crop metadata + VFR/mixed FPS** slice. Full physical Windows/HiDPI, real rotated phone media, audio/video seek under real VFR, GPU, Android/Chrome sessions, installer, large corpora, power loss and [SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) are separate OPEN gates.
