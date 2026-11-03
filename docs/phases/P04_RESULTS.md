# P04 — Implementation results and acceptance ledger

**Status: IN_PROGRESS — no P04 task or phase is accepted.**  
**Integrated repository:** danhgold7979-cyber/fonesi-edit  
**Integrated branch:** develop/fonesi-full  
**Last fully verified code checkpoint:** 78ff11a8fb45e08dc9806b015e5f2f94475476db  
**Last fully verified run:** https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41589895118
**Latest code checkpoint:** 78ff11a8fb45e08dc9806b015e5f2f94475476db (four-runner CI SUCCESS; phase acceptance remains open)

## P04-01 — partial implementation

Implemented:
- Native Editor tabs for layer workspace, media library and read-only media inspection.
- Numeric transform inspector with paired bounded sliders, explicit unit/range labels, per-property reset, anchor/flip reset and full transform-group reset. Slider drag is one project command on release; keyboard steps are individual commands.
- Explicit one-file local media import using a user-selected, explicitly trusted ffprobe executable.
- Hash-bound media identity, typed observation, non-render-ready library record and project-session revision CAS.
- Cancellation/close wait for owned process retirement; stale project/session or changed source cannot silently commit.
- One local file URL from desktop file manager can populate the source field only. It does not run ffprobe, change trust, copy/move/delete the source or write the project. The user must still press the import button.

Evidence:
- tests/test_media_import_ui.py, tests/test_media_import_drop.py, tests/test_project_media_library.py.
- tests/test_layer_editor_ui.py covers slider/spin synchronization, drag/keyboard commit counts, per-property/group resets, anchor/flip reset and locked-control disablement.
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

- **P04-05:** integer-frame playhead, split/trim-in/out, gap/ripple, zoom/scroll, project-persisted half-open In/Out range, named marker create/select/delete with M shortcut, user-triggered four-frame filmstrip and bounded 60-second mono waveform are present. Loop playback, marker rename/drag, continuous timeline thumbnails/waveform, sample-boundary acceptance and synchronized A/V seek remain open.
- **P04-06:** background still-frame/filmstrip/waveform workers, content/tool-hash-bound in-memory caches and draft/standard/high still-image quality profiles are present. Persistent encoded proxy generation, continuous playback, synchronized A/V seek, warm/cold performance and preview/render parity remain open.
- **P04-07:** QSettings-backed shortcut registry, searchable remapping panel, conflict rejection/reset, dynamic layer/timeline/tool event routing (including remappable M for marker creation), app Settings navigation and text/IME focus guards are present for the implemented subset. Full ED§9 action coverage and physical Vietnamese/Chinese IME certification remain open.
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

## Slice U — project-persisted In/Out work-area range (P04-05, 2026-11-03)

Implemented: optional `timeline_range` metadata in CompositionPlan v1; legacy plans remain valid. Stores integer output-frame In/Out boundaries as half-open `[In, Out)`. Strict validation checks `ceil(duration × fps)`, Out requires In, and invalid/reversed/out-of-range/bool/unknown fields are rejected. Buttons and I/O/Escape commit one CompletedCommand revision via ProjectSession; save/close/reopen restores the selection; clear removes it. Source media is untouched.

Tests: `test_timeline_range_is_optional_and_validated_as_half_open_output_frames`, `test_invalid_timeline_range_fails_closed`, `test_in_out_markers_persist_across_project_file_reopen_and_clear`, `test_out_marker_requires_valid_in_and_strictly_later_frame`, and `test_timeline_i_o_escape_shortcuts_persist_and_clear_range`.

Hosted run [41584573033](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41584573033) passed on the exact code checkpoint `ff86e797b662ca118189e7a19980d45bbdfdb4a5`: Ubuntu 3.12.15/3.13.17 each 924 passed, 39 skipped, 0 failed; Windows 3.12.10/3.13.17 each 937 passed, 26 skipped, 0 failed; integrity PASS all four. Windows 3.12 onedir build and scoped frozen CLI boundaries PASS; pinned Windows FFmpeg synthetic workflow SKIPPED.

Acceptance boundary: this is persistent range selection only. Arbitrary named markers (M), loop playback, export-range rendering, continuous thumbnails/waveform, synchronized A/V seek and physical Windows GUI remain open. P04-05/P04 are not accepted.
## Slice V — persistent named timeline markers and M shortcut (P04-05/P04-07, 2026-11-03)

Code checkpoint: fad21b7a1a1b77e5e967145721b6974e8f7375bd on develop/fonesi-full.

Implemented optional timeline_markers in CompositionPlan v1. Each marker has a globally unique UUID, output-frame index and bounded label. Validation enforces output-frame bounds, one marker per frame, trimmed non-control labels, 80 characters and a 1000-marker cap. Existing projects without the field remain valid. Marker navigation metadata is excluded from render_content_digest; it remains part of execution_digest.

Timeline UI adds markers at the playhead with generated M1/M2 labels, displays them in the timeline and a list, seeks to a selected marker without changing project revision, and removes the selected marker. Add/remove commit exactly one ProjectSession command. M is registered in the shared remappable shortcut registry and routed in Timeline list/canvas focus scopes; ordinary text input does not trigger it. Save/close/reopen retains markers.

Regression coverage: test_timeline_markers_are_optional_navigation_metadata_not_render_content, test_invalid_timeline_markers_fail_closed, test_timeline_marker_collection_accepts_1000_and_rejects_1001, test_m_shortcut_adds_persistent_marker_and_selected_marker_can_be_removed, and the live shortcut remap assertion in test_layer_and_timeline_shortcuts_rebind_live_without_reopening_project.

Hosted run 41588026020 completed SUCCESS on exact HEAD fad21b7a1a1b77e5e967145721b6974e8f7375bd: Ubuntu Python 3.12.15 and 3.13.17 each 938 passed, 39 skipped, 0 failed; Windows Python 3.12.10 and 3.13.17 each 951 passed, 26 skipped, 0 failed; integrity PASS on all four. Windows Python 3.12 also passed the actual development onedir build and scoped frozen schema/subtitle/tool-discovery/license boundaries. The pinned Windows FFmpeg synthetic capability workflow was SKIPPED.

Scope limits: hosted Qt tests ran offscreen. Physical Windows GUI, Vietnamese/Chinese IME, Explorer and HiDPI, marker rename/drag, loop playback, export-range renderer behavior, continuous thumbnails/waveform and synchronized A/V seek remain NOT_RUN. ED-17.04 and ED-19.26 remain NOT_RUN; P04-05/P04-07 and P04 remain IN_PROGRESS. No task/criterion/phase acceptance is inferred from this partial slice.
## Slice X — layer inspector slider synchronization and reset controls (P04-01, 2026-11-03)

Code checkpoint: 78ff11a8fb45e08dc9806b015e5f2f94475476db on develop/fonesi-full.

Implemented paired sliders for x, y, width, height, scale_x, scale_y, rotation and opacity; explicit unit/range labels; per-property reset; anchor and flip resets; and a full transform-group reset. Mouse slider drag commits exactly once on release, while keyboard slider steps commit one completed command each. Spin-box edits remain supported. Reset on an already-default transform is a no-op. Locked or non-single-selection inspector states disable sliders and reset actions.

Regression coverage in tests/test_layer_editor_ui.py: test_inspector_slider_drag_commits_once_and_keyboard_step_commits_once; test_inspector_property_and_group_resets_commit_once_and_preserve_other_fields; test_anchor_and_flip_individual_resets_restore_only_selected_property; existing lock/undo/save/reopen coverage remains enabled.

Hosted clean-foundation run 41589895118 completed SUCCESS on exact HEAD 78ff11a8fb45e08dc9806b015e5f2f94475476db: Ubuntu Python 3.12.15/3.13.17 each 941 passed, 39 skipped, 0 failed; Windows Python 3.12.10/3.13.17 each 954 passed, 26 skipped, 0 failed; integrity PASS all four. Windows Python 3.12 development onedir build and scoped frozen CLI boundary checks PASS. Pinned Windows FFmpeg synthetic capability workflow SKIPPED.

Acceptance boundary: Basic/Advanced mode, property search, complete tooltip/disabled-reason mapping, theme/font-size/HiDPI persistence, multi-file Explorer drag/drop and physical Windows GUI remain open. ED-01.02/.03 and P04-01 are NOT accepted. Hosted Qt tests used offscreen mode; this is not physical Windows user-device acceptance.
## Slice Y — Basic/Advanced inspector mode, property search and disabled reasons (P04-01, 2026-11-03)

Code checkpoint: 1038d0afa91bddcaca45fc00c832247451da19cb on develop/fonesi-full.

Layer inspector Basic mode shows X/Y/width/height/opacity. Advanced mode adds scale X/Y, rotation, anchor and flips. Search matches Vietnamese labels and stable keys; it can surface an advanced property from Basic mode. A separate state label reports why editing is disabled (no project, reconciliation, no selection, multi-selection, locked layer, shutdown) or confirms an editable single layer. Numeric, slider and all reset controls include the current reason in Vietnamese tooltips. Units/ranges are visible.

PreferenceWorker and InventoryWorker completion callbacks now dispatch through bound QObject slots using QueuedConnection, keeping QWidget and project-state updates on the GUI thread. The worker regression test records and checks GUI-thread completion.

Regression tests: test_inspector_basic_advanced_search_units_and_tooltips; test_inspector_disabled_reasons_follow_multi_selection_and_lock; test_inspector_slider_drag_commits_once_and_keyboard_step_commits_once; test_inspector_property_and_group_resets_commit_once_and_preserve_other_fields; test_anchor_and_flip_individual_resets_restore_only_selected_property; test_unknown_commit_requires_matching_owned_reload_not_replay.

Hosted clean-foundation run 41594109888 completed SUCCESS on exact HEAD 1038d0afa91bddcaca45fc00c832247451da19cb: Ubuntu Python 3.12.15 and 3.13.17 each 943 passed, 39 skipped, 0 failed; Windows Python 3.12.10 and 3.13.17 each 956 passed, 26 skipped, 0 failed; integrity PASS all four. Windows Python 3.12 actual development onedir build PASS; frozen schema/subtitle/read-only tool discovery/license boundary checks PASS (5 cases). Pinned Windows FFmpeg synthetic capability workflow SKIPPED.

Acceptance boundary: hosted Qt tests used QT_QPA_PLATFORM=offscreen. No physical Windows GUI/Explorer, HiDPI, Vietnamese/Chinese IME, theme/layout persistence or multi-file drag/drop acceptance. Basic/Advanced preference is not persisted; future effect panels are not covered by this inspector search. ED-01.02/.03/.04 remain NOT_RUN. P04-01 and P04 remain IN_PROGRESS; no task or phase acceptance is inferred.
## Slice Z — bounded multi-file local drop queue (P04-01, 2026-11-03)

Code checkpoint: 2cc8a50dad9fa1ceb9c89c6a52857a814761393b on develop/fonesi-full.

Implemented a temporary bounded queue for up to 64 valid local media files. Paths are checked as absolute UTF-8 regular files, with NUL/UNC/reparse/path-length protection, NFC/normcase deduplication and visible refusal states for remote URLs, missing files, directories, duplicates and overflow. Visible rows are capped at 128 with an overflow summary. Invalid local rows include normalized full-path tooltips; remote URL tooltips omit credentials, query strings and fragments.

Selecting one accepted row populates the existing single-file source field only. It does not invoke ffprobe, create a MediaRecord, change the project/library revision or copy/modify the source. Explicit ffprobe trust and the existing import action remain required. The queue and its actions disable while media validation is active or the panel is stopping/revoked.

Tests: test_multiple_local_file_drop_queues_without_import_until_explicit_selection; test_mixed_multi_file_drop_keeps_valid_item_and_marks_unsupported_items; test_drop_queue_deduplicates_and_caps_valid_files; test_drop_queue_rejects_nul_and_unc_paths_before_filesystem_access; test_drop_queue_keeps_visible_bounded_overflow_summary; test_directory_and_missing_file_drop_are_refused; test_symlink_drop_is_refused_when_platform_can_create_symlinks; test_cancel_during_owned_probe_does_not_mutate_project (queue disabled during active worker).

Hosted run 41599687098 completed SUCCESS on exact HEAD 2cc8a50dad9fa1ceb9c89c6a52857a814761393b: Ubuntu Python 3.12.15/3.13.17 each 948 passed, 39 skipped, 0 failed; Windows Python 3.12.10/3.13.17 each 961 passed, 26 skipped, 0 failed; integrity PASS all four. Windows Python 3.12 actual development onedir build PASS; frozen schema/subtitle/read-only tool discovery/license boundary checks PASS (5 cases). Pinned Windows FFmpeg synthetic capability workflow SKIPPED.

Acceptance boundary: Qt drag/drop was synthetic and offscreen. Physical Windows Explorer multi-select, HiDPI/mixed-DPI, network shares, directory recursion, real codec/media validity and batch/parallel import remain NOT_RUN or out of this slice. ED-L136 and P04-01 remain IN_PROGRESS; no task or phase acceptance is inferred.