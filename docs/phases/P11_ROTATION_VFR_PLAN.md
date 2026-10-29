# P11-01/P11-04 + P04-02/P07-07 — VFR/mixed-FPS and rotated-metadata source crop

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only integration branch:** `develop/fonesi-full`. **Status:** planned before source changes.

## Master-plan alignment and existing evidence

Read `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P04-02, P07-07/08, P11-01/04), `docs/PRODUCT_REQUIREMENTS.md` (crop, subtitle trim/speed, mixed FPS), `docs/REQUIREMENTS_TRACEABILITY.md` (ED-20/SUB-07/FLOW-14), `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, P04/P06/P11 results/plans and `src/fonesi_edit/prototypes/media.py`, `src/fonesi_edit/render.py`, `tests/test_render_composition.py`. HEAD before this slice: `14cbb7b474c4b22cd21a4b65bf23825252d8ac85`; [CI 40882402218](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40882402218) SUCCESS (587 Linux, 586 Windows + 1 intentional skip, frozen packaged proofs).

## Reproduced problem / safety boundary

`probe()` currently reports raw encoded dimensions but drops FFprobe Display Matrix rotation. `compile_graph()` generates crop geometry from the encoded width/height, while FFmpeg input defaults to auto-rotating frames **before the crop filter runs**. Local synthetic FFmpeg 7.1.5 investigation used a 320×180 left-red/right-blue video with `-display_rotation 90`; decoded frames become **180×320**. The source's left red half becomes the displayed **bottom half**, so an untransformed crop rectangle applied to the auto-rotated frame can select the wrong region without a validation error. This is a concrete metadata-coordinate regression risk, not proof of physical Windows behavior.

## Implementation plan

1. Extend `MediaInfo` with backward-compatible `display_rotation` (default zero) from FFprobe video Display Matrix rotation or legacy rotation tag; use only finite numeric metadata, with explicit handling for crop if the angle is unsupported.
2. Add pure `crop_rect_after_autorotate(clip,info)`: calculate existing bounded even-pixel crop in untransformed source coordinates, then transform the rectangle for quarter-turn display matrices (0, ±90, 180). Let FFmpeg keep its standard autorotation, preserving user-facing orientation; never change `crop_rect_pixels()` semantics for legacy manual crop or source image tools. Reject non-orthogonal rotated-metadata + nontrivial crop if no exact rectangle is representable instead of silently cropping the wrong pixels.
3. Unit tests for raw vs displayed geometry with 0/±90/180 and invalid angles, preserving full-frame defaults. Synthetic real FFmpeg 7.1.x test creates an encoded red-left/blue-right source and remuxes a display-rotation matrix; verify raw probe, expected crop expression, reference PNG's dominant red center and rendered MP4 decoded frame. Ensure source bytes unchanged.
4. Add independent synthetic VFR + mixed-FPS + video-without-audio render tests: generate differing source frame presentation timestamps, combine VFR 30-ish input with a 24 FPS CFR input, normalize to output 25 FPS, exercise trim/speed and source subtitle cue map, reference frame and MP4 decode/probe, assert output dimensions/duration and no source mutations. Do not claim a broad VFR/rotated media corpus.
5. Run `scripts/check_plan.py`, focused pytest, full Linux/Windows CI, production desktop/native-host builds and frozen packaged proof. Record exact SHA and runner results, fix failures without weakening assertions. Update P11/P04 results, coverage/status/ledger after CI verification.

## Acceptance and remaining gates

- [ ] Probe exposes real 90° display metadata and exactly maps source crop rectangle to displayed coordinates.
- [ ] Frame-based proof selects the intended source half after autorotation; preview and exported video both show the same dominant color, source bytes unchanged.
- [ ] True VFR fixture with unequal PTS gaps and a different-FPS second clip render with expected duration, normalized output FPS, and correct subtitles/no-audio behavior.
- [ ] Full Linux/Windows regression and frozen packaged/native-host proofs PASS on exact code/test SHA.

**Still open:** production VFR and rotation/flip matrices beyond synthetic fixtures, crop UX metadata coordinate documentation, physical Windows/HiDPI/4K performance, GPU codec parity, audio/video seek with real user media, Chrome/live translation/platform rights, crash/power-loss soak and intermittent Windows SQLite [issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). Do not close P04/P11 in full or merge to `main`.
