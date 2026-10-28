# P04 clean rebuild results — checkpoint 1

State: PARTIAL — full phase gate OPEN

## Implemented
Runnable Vietnamese 8-tab desktop; canvas drag/resize/rotate/lock/visibility/nudge; one-gesture undo; property inspector/keyframes; layer/cue timing drag; project save/open/autosave; background probe/reference rendering.

## Evidence
3 offscreen UI tests passed; real Qt screenshot editor-checkpoint.png manually inspected.

## Remaining / NOT RUN
Playable normalized proxy/audio preview, waveform/thumbnails, advanced crop/anchors/groups/alignment, full shortcuts/remap/IME/HiDPI and exhaustive direct cue editing remain open. Static base-frame scrubbing is NOT certified playback.

Baseline evidence is not clean-code evidence. No claim that an entire requirement group passes from a single example.

## Checkpoint 2 — latest
Normalized video/audio proxy, waveform and real Qt decoded-frame playback added and tested. Clip/audio settings, motion presets, preset group import/export and relink UI added; invalid settings Apply restores draft. Shift multi-selection preserved. Remaining: direct crop/anchors/groups/align, complete timeline operations and shortcut remap/focus/IME/HiDPI tests, repeated playback/cancel/load interactions.
