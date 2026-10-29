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

- [ ] Positive source cue intersections are never silently dropped due to ms rounding; an unrepresentable cue raises an explicit error.
- [ ] Multi-clip trim, speed, transition and subtitle-layer scopes keep cue identities/content and expected output time ranges in the compiled ASS.
- [ ] Actual synthetic export and reference preview use the same graph, retaining output duration and source bytes.
- [ ] Plan validation, regression suite and frozen packaged proof pass on exact SHA in Linux/Windows CI.

Remaining separate gates: complete VFR/rotation/mixed-FPS corpus and visual/audio tolerance on user Windows devices, huge CJK subtitles, live translation and platform/auth/Chrome, GPU, power loss, persistent Undo journal and intermittent SQLite Windows issue #6. Do not mark P06/P11 fully accepted.
