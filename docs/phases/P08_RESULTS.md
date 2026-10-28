# P08 clean rebuild results — checkpoint 1

State: PARTIAL — full phase gate OPEN

## Implemented
Recursive safe folder scanning; batch dry-run and per-input validation failures; own subtitles resolved per clip; duration policies cut/speed/loop/freeze; audio mixer supports gain/delay/fade/loop/solo/limiter in renderer.

## Evidence
Batch scan/plan and duration-policy tests passed plus real render.

## Remaining / NOT RUN
Full duration/audio settings UI, mapping modes/ambiguity, crossfades/ducking/SFX events/meter, preset asset migration and representative multi-folder regression remain open.

Baseline evidence is not clean-code evidence. No claim that an entire requirement group passes from a single example.

## Checkpoint 2 — latest
Clip/audio settings UI now exposes trim/speed/fit/flip/rotation/color/duration policy plus audio gain/trim/start/role/loop/fade/mute/solo/normalize; proxy uses actual mixed audio. Preset group import/export, missing assets and content-hash relink added. Rename preview/two-stage apply/undo implemented and tested as service; not yet exposed in desktop. Crossfades/ducking/SFX event allocation and all-mode batch overrides remain open.
