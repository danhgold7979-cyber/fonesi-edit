# P06-05 / P11-01/04 — Preserve subtitle timing across trim, speed, clip offsets and transitions

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only integration branch:** `develop/fonesi-full`. **Status:** plan before source/test changes.

## Baseline and requirements

Read `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P06-05, P07-08, P11-01/04), `docs/PRODUCT_REQUIREMENTS.md` §4.2, `docs/REQUIREMENTS_TRACEABILITY.md` SUB-07/SUB-08/SUB-10 and FLOW-14, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, P06/P11 plans/results, and `src/fonesi_edit/prototypes/subtitles.py`, `src/fonesi_edit/render.py`, `tests/test_subtitles.py`, and `tests/test_render_composition.py`.

Existing `map_trimmed_cues` uses rational arithmetic for trim, speed and output offset, while the production compositor maps subtitle layer cues per clip and uses the same FFmpeg graph for preview/export. A **real integrity gap** remains: when a valid source cue intersects the trim window but compresses to the same rounded millisecond at high speed, `map_trimmed_cues` silently drops its text (`mapped_end <= mapped_start`). A render can therefore report success even though a cue was discarded without warning. Gap, transition, multi-clip and source/target mapping also need a focused integration regression beyond the existing single-clip timing test.

## Implementation slice

1. Fail explicitly with a bounded diagnostic identifying the cue index and the trim/speed granularity if a positive source cue intersects the selected source interval but maps to zero output milliseconds; do not fabricate duration, silently drop text, or change other cue order/timestamps. This affects only objectively unrepresentable positive intersections; fully out-of-trim cues are still intentionally omitted. Validate `map_trimmed_cues` against non-integer/bool/non-positive inputs if needed without changing valid fractional behavior.
2. Add pure rational tests for adjacent cue order and clipped boundaries, fractional-speed mappings, high-speed 1 ms collapse, out-of-window cues, negative offset and offset to absolute multi-clip output time.
3. Add a synthetic FFmpeg/FFprobe integration test for two source clips, trim/speed, transition and separate source/translated subtitle layers using unique cue texts. Inspect the actual emitted ASS cue start/end/text for both scoped clips; confirm reference-frame and exported media can be produced from the identical graph, and output duration matches the composition. No live platform or paid provider.
4. Run `scripts/check_plan.py`, focused tests and full source suite with packaged app/native host on both GitHub Actions Linux and Windows. Update P06/P11 results, coverage, current status and execution ledger **only** when CI evidence on the code/test SHA is complete.

## Acceptance and blockers

- [x]  Positive source cue intersections are never silently dropped due to ms rounding; an unrepresentable cue raises an explicit error.
- [x]  Multi-clip trim, speed, transition and subtitle-layer scopes keep cue identities/content and expected output time ranges in the compiled ASS.
- [x]  Actual synthetic export and reference preview use the same graph, retaining output duration and source bytes.
- [x]  Plan validation, regression suite and frozen packaged proof pass on exact SHA in Linux/Windows CI.

Remaining separate gates: complete VFR/rotation/mixed-FPS corpus and visual/audio tolerance on user Windows devices, huge CJK subtitles, live translation and platform/auth/Chrome, GPU, power loss, persistent Undo journal and intermittent SQLite Windows issue #6. Do not mark P06/P11 fully accepted.

## Verified implementation slice and observed precision

Source/test commits: [e42c6b7](https://github.com/danhgold7979-cyber/fonesi-edit/commit/e42c6b73d66a012ce040ae58cf6392b56b7e42ce) (fail closed on zero-ms mapped cues), [3474dbb](https://github.com/danhgold7979-cyber/fonesi-edit/commit/3474dbb67b0d031a8e61182efbad9e30d20b6c53) (pure rational tests), [969a4ee](https://github.com/danhgold7979-cyber/fonesi-edit/commit/969a4ee6bdd144c40f730d2283b88cc0807fd66c) (two-clip scoped source/target and actual FFmpeg preview/export). The first integrated [CI 40880618234](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40880618234) FAILED one new assertion on both OS: native ASS stores centiseconds, so expected 75–225 ms became 80–230 ms. No production cue was lost. [Test correction e8656dc](https://github.com/danhgold7979-cyber/fonesi-edit/commit/e8656dc8af45f80246c8a35624cad1ec602a8f40) verifies exact ASS quantized timestamps and independently bounds each edge error to 5 ms; the source safety check was retained.

[CI 40881166137](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40881166137) **SUCCESS on exact final code/test SHA e8656dc8**: Linux **587 PASS**, Windows **586 PASS + 1 intentional POSIX-only skip**. Plan checker, production desktop/native-host build, FFmpeg synthetic video/image/Qt frozen proof PASS both OS. The code/test does not prove per-pixel frame equivalence or VFR/rotation/audio sync on physical Windows hardware; full P06/P11 gates remain OPEN.
