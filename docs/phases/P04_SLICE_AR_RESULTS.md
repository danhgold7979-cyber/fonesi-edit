# P04 Slice AR — draggable exact-frame Timeline markers

Status: **IN_PROGRESS / final hosted verification pending**. This file is a scoped evidence receipt and does not accept P04-05 or P04.

- Repository: `danhgold7979-cyber/fonesi-edit`
- Branch: `develop/fonesi-full`
- Initial implementation: `69a538f52215c52a6054117c8b2848275cd8f331`
- Playhead hit-routing fix: `fda6343a55ffb0d12b9ce4a462aed96695edbd11`
- Final scene-coordinate drag fix: `bb33f4b0c8b2562571fd87b4a4eab34d640bbb17`
- Scope: P04-05 / ED-17.04 marker reposition portion

## Implemented

Timeline markers are actual horizontally draggable graphics items. Movement is clamped to the valid output range and converted to an integer output frame from the project's exact rational FPS. Intermediate pointer movement does not mutate the project. Release commits one `CompletedCommand`, records shared `ProjectCommandHistory`, preserves marker ID/label, updates list/scene, survives save/reopen and supports undo/redo.

The pure command rejects bool/non-integer, negative, out-of-range, missing-marker, no-op and duplicate-frame requests. The Qt path rejects stale project identity/revision and reconciliation state. Duplicate-frame drops snap back without revision. Escape and no-move gestures create no command.

## Local focused checks

- `PYTHONPATH=src python -m pytest -q tests/test_timeline_edit_commands.py` → **28 passed**.
- `python -m compileall -q src tests scripts` → **PASS**.
- `git diff --check` → **PASS**.

## Hosted diagnostics and corrections

Clean-foundation run `42336539515` on checkpoint `25252dbc3fa035ea7df8c5aaebb3f38b41179b37` executed 1,018 source tests per Ubuntu runner and exposed two failures in the new viewport-drag tests. The higher-z playhead item accepted mouse input at the selected marker position. Commit `fda6343a55ffb0d12b9ce4a462aed96695edbd11` made the playhead mouse-transparent without changing visual ordering.

Clean-foundation run `42336900810` showed that marker events then reached the correct `TimelineMarkerItem`, but Qt offscreen pointer movement quantized the default `QGraphicsItem` device delta. Temporary diagnostic run `42337302450` confirmed the marker was the scene mouse grabber while moving only a few device pixels instead of to the release scene coordinate. Commit `bb33f4b0c8b2562571fd87b4a4eab34d640bbb17` now derives movement and the authoritative final position from `event.scenePos()`, retaining scene-coordinate clamping and exact-frame conversion. Test assertions were not removed or weakened.

A full Linux/Windows matrix is required on the exact final source before recording hosted PASS.

## Acceptance boundary

Continuous playback, synchronized A/V seek, continuous thumbnails/waveform, sample-boundary evidence and physical Windows mouse/HiDPI acceptance remain open. P04-05 and P04 remain IN_PROGRESS.
