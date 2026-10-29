# P06-05 — Direct cue timing drag in Subtitle tab (bounded timeline lane)

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only development branch:** `develop/fonesi-full`.

## Scope and baseline

Reviewed AGENTS.md, README.md, IMPLEMENTATION_PLAN P06-04/05 and P11-01/05, PRODUCT_REQUIREMENTS §4.2, EDITOR_SPEC timeline/keyboard sections, REQUIREMENTS_TRACEABILITY SUB-05/07/08, IMPLEMENTATION_COVERAGE, CURRENT_STATUS, P06_PLAN/P06_RESULTS, existing Qt `SubtitlesPage`, editor `Timeline`, `Caption` and integration tests. The in-session 100-entry cue Undo/Redo slice is implemented and validated on Linux/Windows [code CI 40867450628](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40867450628). This new work must preserve that regression baseline.

Today cue timing can be typed numerically and shifted in bulk but cannot be dragged directly. The editor's clip timeline already uses source clips and layer spans; changing it to edit subtitle sidecar files would couple unrelated document/FFmpeg state and risk modifying source media. Introduce a small, integrated **cue timing lane** in the existing Subtitle tab, not a new tool or independent application.

## Implementation slice

1. Add a reusable `CueTimingView` (`QGraphicsView`) showing the selected cue's start/end against an absolute time ruler. Drag the middle to move a cue without changing duration; drag the left/right edges to change start/end. Drag computes preview geometry first; only the **release** publishes one validated timing change.
2. Use deterministic pure `retime_cue(start_ms,end_ms,delta_ms,mode)` for move/start/end: reject invalid inputs, clamp start ≥0, preserve strictly positive duration, prevent crossing endpoints and round pointer movement to 10 ms increments. No auto-rescheduling of other cues or silent fix of overlaps.
3. On release, update the two table time cells under blocked signals, then record **one** cue-history snapshot and persist the normal draft. Redo/Undo must restore exactly the prior two time fields plus stable cue ID; source/target text and lock are unchanged.
4. Invalid or incomplete selected time fields disable the draggable lane rather than parsing unsafe values. Highlight selected row; no provider or media fetch, no source/sidecar modification, no assumptions of video timeline trim/speed parity.
5. Add pure geometry and Qt integration tests for moving, edge trims, negative clamp, minimum duration, invalid cues, no-change/no extra Undo and translation/source preservation. Where reliable under offscreen Qt, simulate a mouse gesture on the scene; otherwise keep exact signal and geometry assertions and preserve manual Windows interactive validation gate.

## Acceptance and exclusions

- [ ] Selected cue shows a moveable time bar; move/edge drag changes only that cue's absolute millisecond timing and preserves content/lock.
- [ ] Release produces one Undo entry; invalid drag or canceled/no-op gesture does not record changes. Original draft and Undo/Redo recover correctly.
- [ ] Invalid table input never gets silently coerced; no source/FFmpeg/render output is changed merely by dragging a cue.
- [ ] Plan checker, full Linux/Windows source CI, production desktop/native-host and frozen packaged proof all PASS on the code/test SHA.

**Still not accepted:** editing many cues simultaneously, trim/speed composition time-map parity, long/high-FPS timeline performance, undo journal persisted across restarts, Windows user-device pointer/HiDPI, real Chinese–Vietnamese translation quality/cost/rights/Chrome and [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). Full P06 remains OPEN.
