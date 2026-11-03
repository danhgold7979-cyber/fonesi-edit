# P04 — Implementation results and acceptance ledger

**Status: IN_PROGRESS — no P04 task or phase is accepted.**  
**Integrated repository:** danhgold7979-cyber/fonesi-edit  
**Integrated branch:** develop/fonesi-full  
**Last fully verified code checkpoint:** 8b26775559c3158497f3282b01412ffeb275b6af  
**Last fully verified run:** https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41562878790
**Latest code checkpoint:** 9ac2bdfb8b9f0311a0ac14974830253d52c3ff77 (CI queued; not yet verified)

## P04-01 — partial implementation

Implemented:
- Native Editor tabs for layer workspace, media library and read-only media inspection.
- Explicit one-file local media import using a user-selected, explicitly trusted ffprobe executable.
- Hash-bound media identity, typed observation, non-render-ready library record and project-session revision CAS.
- Cancellation/close wait for owned process retirement; stale project/session or changed source cannot silently commit.
- One local file URL from desktop file manager can populate the source field only. It does not run ffprobe, change trust, copy/move/delete the source or write the project. The user must still press the import button.

Evidence:
- tests/test_media_import_ui.py, tests/test_media_import_drop.py, tests/test_project_media_library.py.
- The UI import tests use synthetic probe metadata plus a real owned child-process lifecycle fixture; this is not actual codec or media validity acceptance.
- Physical Windows Explorer, HiDPI, IME, multi-file drop, theme and layout persistence remain open.

## P04-02 — partial implementation

Implemented:
- A geometry-only canvas for existing composition layers.
- Mask-layer creation and persistent normalized transform editing: x/y, width/height, scale, rotation, opacity, nine anchors and flips.
- Canvas movement commits once on release through the same CompletedCommand/ProjectSession CAS path.
- Transform lock, visibility and z-order controls.
- Exact rational preservation for untouched transform fields.

Not implemented:
- Text/logo/font asset editing and glyph parity.
- Crop controls, resize handles, multi-select/group transforms, grid/safe-area/snap/Alt, and bring-into-frame commands.
- Decoded source-video preview or final mask effect rendering.
- Preview/export geometry parity and any successful render path.

Evidence:
- tests/test_layer_editor_ui.py, tests/test_layer_canvas_drag.py, tests/test_layer_editor_order.py, tests/test_layer_editor_precision.py.

## P04-03 and P04-04 — partial implementation

Layer visibility, transform lock, z-order and mask-layer undo/redo are implemented and tested. Undo/redo restores prior model values by issuing new monotonic project revisions; it does not rewind revision numbers.

Multi-select, grouping/ungrouping, context menus, grouped atomic transforms and a unified undo stack covering timeline, text, subtitle and all editor commands remain open.

## P04-05 through P04-08

NOT_RUN / not accepted. Timeline/playhead/trim/split/ripple, proxy/cache/seek, complete shortcut/IME router and full tool/profile/account settings remain unimplemented or unverified.

## Exact hosted verification

Run 41490203672 ran against code checkpoint 6e4b905b36f271c0f4a585365ebebd23dfd5b6bc and completed successfully:

| Runner | Tests passed | Skipped | Failed |
|---|---:|---:|---:|
| Ubuntu / Python 3.12 | 815 | 39 | 0 |
| Ubuntu / Python 3.13 | 815 | 39 | 0 |
| Windows / Python 3.12 | 828 | 26 | 0 |
| Windows / Python 3.13 | 828 | 26 | 0 |

Windows Python 3.12 also passed five scoped frozen CLI checks for schema/subtitle/read-only tool discovery/license. This is not Windows GUI, actual media codec, GPU, provider, Chrome-session or end-user device acceptance.

The subsequent documentation-only checkpoint updates the P04 plan header and removes a duplicate supplemental slice entry; it does not change source code from the verified code checkpoint above.

## Acceptance state

The machine-readable project ledger remains unchanged by this partial implementation: 13/438 child criteria PASS, 425 NOT_RUN; 8/94 tasks ACCEPTED, 9 IN_PROGRESS, 77 PLANNED. P03 whole-task acceptance remains 0/9. P04 whole-task acceptance remains 0/8. Do not infer product completion from test counts.


## 2026-11-03 continuation — additional implementation beyond the verified checkpoint

The current branch also contains the following later code, which is **implemented but not yet covered by a completed four-runner CI result**:

- **P04-02:** canvas 5% grid, 90% safe-area overlay, snap at 0.05 normalized increments, Alt bypass, atomic bring-into-frame, single-layer resize handles and rotation handle. Locked layers hide handles; multi-selection hides individual handles. Crop remains a numeric inspector; no source-video pixel preview or export parity.
- **P04-03:** persistent group UUIDs with schema compatibility, multi-select, group auto-selection, atomic group drag (including hidden members), group/ungroup, batch lock/visibility/z-order/delete and context-menu actions.
- **P04-04:** focus-scoped layer undo/redo; still not a unified history spanning timeline, subtitle, text and every editor subsystem.
- **P04-05:** integer-frame playhead, split, trim-in/out, gap/ripple and timeline zoom/scroll. Thumbnail, waveform, loop and marker editing remain open.
- **P04-07:** initial focus-scoped shortcuts Ctrl+Z/Y, Delete, Ctrl+G, Ctrl+Shift+G, Alt+Up/Down. User remapping, conflict resolution and physical Vietnamese/Chinese IME acceptance remain open.

Additional regression files: tests/test_layer_groups.py, tests/test_layer_group_schema.py, tests/test_layer_canvas_guides.py, tests/test_layer_canvas_handles.py and tests/test_layer_shortcuts.py. The earlier modal-menu test was replaced with a non-modal fake-menu test so CI cannot wait for user input.

The latest full CI run for current code is run 41564091006 (queued at time of this checkpoint). Until it completes on Ubuntu/Windows Python 3.12/3.13, all later features above remain unverified by hosted CI. No P04 task or phase is accepted.
