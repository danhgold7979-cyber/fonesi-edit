# P04 — Implementation results and acceptance ledger

**Status: IN_PROGRESS — no P04 task or phase is accepted.**  
**Integrated repository:** danhgold7979-cyber/fonesi-edit  
**Integrated branch:** develop/fonesi-full  
**Last fully verified code checkpoint:** 3e0efdc1b5a9fb4bf5fad978ed1345956463f663  
**Last fully verified run:** https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41578597866
**Latest code checkpoint:** 3e0efdc1b5a9fb4bf5fad978ed1345956463f663 (four-runner CI SUCCESS; phase acceptance remains open)

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
- Interactive crop handles and complete nine-anchor hit-test/export parity; crop is currently numeric-inspector editing.
- Decoded continuous source-video preview, final mask-effect compositor and render/export.
- Preview/export geometry parity and any successful render path.

Evidence:
- tests/test_layer_editor_ui.py, tests/test_layer_canvas_drag.py, tests/test_layer_editor_order.py, tests/test_layer_editor_precision.py.

## P04-03 and P04-04 — partial implementation

Implemented and tested: tree multi-selection, persistent group UUIDs/schema compatibility, group/ungroup, group drag, batch lock/visibility/z-order/delete, context-menu actions and layer-scoped undo/redo. Undo/redo restores prior model values by issuing new monotonic project revisions; it does not rewind revision numbers.

Still open: canvas marquee selection, group resize/rotation and a unified undo stack spanning timeline, text, subtitle and all editor commands.

## P04-05 through P04-08 — partial implementation, not accepted

- **P04-05:** integer-frame playhead, split/trim-in/out, gap/ripple, zoom/scroll, transient half-open In/Out work-area markers, user-triggered four-frame filmstrip and bounded 60-second mono waveform are present. Loop playback, persistent markers, continuous timeline thumbnails/waveform, sample-boundary acceptance and synchronized A/V seek remain open.
- **P04-06:** background still-frame/filmstrip/waveform workers, content/tool-hash-bound in-memory caches and draft/standard/high still-image quality profiles are present. Persistent encoded proxy generation, continuous playback, synchronized A/V seek, warm/cold performance and preview/render parity remain open.
- **P04-07:** QSettings-backed shortcut registry, searchable remapping panel, conflict rejection/reset, dynamic layer/timeline/tool event routing, app Settings navigation and text/IME focus guards are present for the implemented subset. Full ED§9 action coverage and physical Vietnamese/Chinese IME certification remain open.
- **P04-08:** metadata-only tool inventory, explicit path preferences, one-shot background first-open scan, user-selected FFmpeg/ffprobe pair self-test and table-scoped F5 rescan are present. Managed download/install/update/repair/rollback, Chrome profile/account tables, live login/bridge/rights readiness and full platform recovery workflows remain open.

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

The machine-readable project ledger records 13/438 child criteria PASS and 425 NOT_RUN; 8/94 tasks ACCEPTED, 17 IN_PROGRESS and 69 PLANNED after reconciling all eight partially implemented P04 tasks. P03 whole-task acceptance remains 0/9. P04 whole-task acceptance remains 0/8. No P04 requirement group is accepted. Do not infer product completion from test counts.


## 2026-11-03 continuation — additional implementation beyond the verified checkpoint

The current branch also contains the following later code, which is **implemented but not yet covered by a completed four-runner CI result**:

- **P04-02:** canvas 5% grid, 90% safe-area overlay, snap at 0.05 normalized increments, Alt bypass, atomic bring-into-frame, single-layer resize handles and rotation handle. Locked layers hide handles; multi-selection hides individual handles. Crop remains a numeric inspector; no source-video pixel preview or export parity.
- **P04-03:** persistent group UUIDs with schema compatibility, multi-select, group auto-selection, atomic group drag (including hidden members), group/ungroup, batch lock/visibility/z-order/delete and context-menu actions.
- **P04-04:** focus-scoped layer undo/redo; still not a unified history spanning timeline, subtitle, text and every editor subsystem.
- **P04-05:** integer-frame playhead, split, trim-in/out, gap/ripple and timeline zoom/scroll. Thumbnail, waveform, loop and marker editing remain open.
- **P04-07:** initial focus-scoped shortcuts Ctrl+Z/Y, Delete, Ctrl+G, Ctrl+Shift+G, Alt+Up/Down. User remapping, conflict resolution and physical Vietnamese/Chinese IME acceptance remain open.

Additional regression files: tests/test_layer_groups.py, tests/test_layer_group_schema.py, tests/test_layer_canvas_guides.py, tests/test_layer_canvas_handles.py and tests/test_layer_shortcuts.py. The earlier modal-menu test was replaced with a non-modal fake-menu test so CI cannot wait for user input.

These later features were subsequently verified at the exact checkpoint recorded below by the completed four-runner run 41578597866. That hosted result does not close P04 task gates or external acceptance. No P04 task or phase is accepted.


## Slice K — explicit still-frame preview (2026-11-03)

Implemented on develop/fonesi-full:
- Explicit absolute FFmpeg path and per-path trust checkbox; no PATH discovery, auto-execution, download or installation.
- Project-relative/absolute asset resolution with symlink/reparse component refusal.
- Background owned worker, content-hash pinning for source and executable, single selected stream, exact rational decoder timestamp and one PNG output.
- In-memory LRU cache keyed by source/tool SHA256, stream, timestamp, dimensions and algorithm version; capped at 64 entries / 48 MiB.
- Bounded PNG dimensions/bytes and FFmpeg thread/allocation controls.
- Stale project/clip/playhead requests are discarded; changing tool path revokes trust.
- Application close waits for preview worker retirement. Unknown process/job retirement permanently locks preview and app close for that session rather than retrying or claiming safety.
- Preview is a still image only. No playback, audio sync, exact PTS parity, crop/transform compositor, waveform/thumbnail generation or export parity.

Regression coverage added: tests/test_media_preview.py and tests/test_timeline_preview_ui.py. Initial hosted run 41567567876 exposed four test failures: two shortcut tests targeted a hidden Editor page; missing absolute path escaped as FileNotFoundError; Qt returns a null QPixmap object rather than Python None. Those causes were corrected and the current four-runner run 41578597866 passed. The still-frame feature remains a convenience observation, not playback or render acceptance.


## Slice L and M — filmstrip and waveform implementation

Current code includes user-triggered four-frame filmstrip extraction and bounded audio waveform observation:
- Filmstrip samples four rational timestamps at 1/8, 3/8, 5/8 and 7/8 of the selected source interval; it discards the entire strip on any failure/cancel.
- Waveform uses the matching original-role audio stream, mono float32 at 8 kHz, at most 60 seconds, bounded output and finite sample validation, aggregated into at most 256 min/max bins.
- Both use the explicit trusted FFmpeg path, source/tool content hashes, in-memory bounded cache and stale request rejection. Neither writes source media.
- These are still images and amplitude visualization only: no continuous playback, synchronized A/V seek, loudness/clipping meter or render parity.

Latest fully completed four-runner run 41570055537 at 457817662c5fb6e70038b19a84b7a52f6ee33fc6: Ubuntu 3.12/3.13 each 888 passed, 39 skipped; Windows 3.12/3.13 each 901 passed, 26 skipped; all zero failed and integrity PASS. This is hosted CI, not real user media corpus or physical Windows acceptance.

Slice N adds Ctrl+, navigation to the existing Preset/Cài đặt page with a regression test. It is in current HEAD `43b0d97575167c10f65968bafdf267fc8e4735ea`; run 41571515314 is pending. It does not complete P04-08 Settings workflows.


## Slice N and O — Settings and timeline navigation shortcuts

Implemented:
- Ctrl+, opens the existing Preset/Cài đặt navigation page; it does not create a second window or mutate project state.
- Timeline Left/Right steps one frame; Shift+Left/Right steps ten frames; Home/End jumps to bounds.
- Shortcuts are scoped to the relevant tree/canvas widgets. Numeric crop inputs keep their native arrow-key behavior.

Regression tests include `tests/test_settings_shortcut.py`, `tests/test_timeline_shortcuts.py`, `tests/test_shortcut_registry.py`, `tests/test_layer_shortcuts.py` and `tests/test_tool_inventory_ui.py`. The current focus-routing implementation and these tests are covered by run 41578597866 at HEAD `3e0efdc1b5a9fb4bf5fad978ed1345956463f663`.

P04 remains IN_PROGRESS. P04-08 is still incomplete: Ctrl+, navigation does not implement tool installation/update/repair/rollback, Chrome profiles, account readiness or full settings acceptance.


## 2026-11-03 — deterministic shortcut routing and current hosted verification

Current integrated code checkpoint: `3e0efdc1b5a9fb4bf5fad978ed1345956463f663` on `develop/fonesi-full`. The implementation replaces QShortcut-only dispatch for the relevant scopes with shared-registry KeyPress event filters:

- Layer tree/canvas routing uses the Qt modifier enum's integer value, preserves IME preedit handling and clears stale preedit on focus transitions.
- Ctrl+, routes to the existing Settings page across the main-window widget tree, does not mutate project state, remains available from numeric inspectors, and is suppressed while a text editor owns focus; QKeySequenceEdit retains capture.
- Timeline Left/Right, Shift+Left/Right, Home/End and I/O/Escape are scoped to the clip list/canvas and their viewports. Crop spin boxes retain native Left/Right cursor and Up/Down value semantics.
- F5 is scoped to the tool table and viewport and invokes only the existing bounded metadata scan; registry remapping takes effect at event time.
- The Windows coordinator test helper now polls the native QThread `wait(0)` completion predicate within its five-second bound, rather than asserting once immediately after `isRunning()` changes. This is a test synchronization correction; production coordinator ownership semantics are unchanged.

Exact hosted run [41578597866](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41578597866) completed SUCCESS:

| Runner | Passed | Skipped | Failed | Integrity |
|---|---:|---:|---:|---|
| Ubuntu / Python 3.12 | 904 | 39 | 0 | PASS |
| Ubuntu / Python 3.13 | 904 | 39 | 0 | PASS |
| Windows / Python 3.12 | 917 | 26 | 0 | PASS |
| Windows / Python 3.13 | 917 | 26 | 0 | PASS |

Windows Python 3.12 also passed the development onedir build and scoped frozen schema/subtitle/tool-discovery/license boundary checks. The separate pinned Windows FFmpeg synthetic capability workflow was SKIPPED. These results verify the exact source and headless Qt tests plus the named packaged boundaries only; they do not establish physical Windows GUI/Explorer/IME/HiDPI acceptance, actual user FFmpeg/GPU/media corpus, Chrome session handoff, provider access, continuous playback, synchronized A/V seek or render/export parity.

P04 task states are now reconciled in `docs/requirements/tasks.json`: P04-01 through P04-08 are IN_PROGRESS, not ACCEPTED. Overall: 8/94 tasks ACCEPTED, 17 IN_PROGRESS, 69 PLANNED; 13/438 child criteria PASS, 425 NOT_RUN; 0/95 requirement groups accepted; P03 whole-task acceptance 0/9; P04 whole-task acceptance 0/8.
