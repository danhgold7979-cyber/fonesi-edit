# P04 Slice AR — draggable exact-frame Timeline markers

Status: **IN_PROGRESS / hosted verification pending**. This file is a scoped evidence receipt and does not accept P04-05 or P04.

- Repository: `danhgold7979-cyber/fonesi-edit`
- Branch: `develop/fonesi-full`
- Implementation commit: `69a538f52215c52a6054117c8b2848275cd8f331`
- Scope: P04-05 / ED-17.04 marker reposition portion

## Implemented

Timeline markers are actual horizontally draggable graphics items. Movement is clamped to the valid output range and converted to an integer output frame from the project's exact rational FPS. Intermediate pointer movement does not mutate the project. Release commits one `CompletedCommand`, records shared `ProjectCommandHistory`, preserves marker ID/label, updates list/scene, survives save/reopen and supports undo/redo.

The pure command rejects bool/non-integer, negative, out-of-range, missing-marker, no-op and duplicate-frame requests. The Qt path rejects stale project identity/revision and reconciliation state. Duplicate-frame drops snap back without revision. Escape and no-move gestures create no command.

## Local focused checks

- `PYTHONPATH=src python -m pytest -q tests/test_timeline_edit_commands.py` → **28 passed**.
- `python -m compileall -q src tests scripts` → **PASS**.
- `git diff --check` → **PASS**.

## Acceptance boundary

Hosted Linux/Windows CI is required before recording hosted PASS. Continuous playback, synchronized A/V seek, continuous thumbnails/waveform, sample-boundary evidence and physical Windows mouse/HiDPI acceptance remain open. P04-05 and P04 remain IN_PROGRESS.
