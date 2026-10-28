# P07 clean rebuild results — checkpoint 1

State: PARTIAL — full phase gate OPEN

## Implemented
Canonical Pillow compositor shared by reference/export; text/font-glyph validation, logos, masks blur/mosaic/color, relative transforms, keyframes/easing, trim/speed/fit/crop/blur background, CPU render and output full decode.

## Evidence
6 real renderer tests passed: Unicode text/sub/mask, motion, collision/source integrity, reference/export RGB RMS under 12 for sample, 3 fit modes.

## Remaining / NOT RUN
Full motion presets/path/easing UI, anchors/avoidance/random controls, advanced typography/shaping/style properties, all layer combinations, CJK font corpus, GPU and target-platform parity/performance remain open. Unsupported requested fields are rejected, not silently accepted.

Baseline evidence is not clean-code evidence. No claim that an entire requirement group passes from a single example.
