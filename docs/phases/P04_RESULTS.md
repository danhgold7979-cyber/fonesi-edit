# P04 — Implementation results and acceptance ledger

**Status: IN_PROGRESS — no P04 task or phase is accepted.**  
**Integrated repository:** danhgold7979-cyber/fonesi-edit  
**Integrated branch:** develop/fonesi-full  
**Last fully verified code checkpoint:** 9c32e09043c23ff229dcaf608bd018c10340a1d4  
**Last fully verified run:** 41625120990
**Latest code checkpoint:** 9c32e09043c23ff229dcaf608bd018c10340a1d4 (four-runner CI SUCCESS; phase acceptance remains open)

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

Implemented in subsequent P04-02 slices:
- Interactive normalized crop overlay on the explicit still-frame surface: shaded outside region, thirds grid, move, eight edge/corner handles, minimum extent, source-frame clamping and optional ratio lock.
- Crop gestures and numeric inspector edits are staged. Confirm commits one canonical crop update through ProjectSession CAS; Cancel, Escape, clip/source/quality invalidation and stale revision discard staged edits without mutating the project. A no-op click does not create a crop change.
- Ratio-locked edge/corner resizing preserves the initial ratio at source boundaries; the handle stops at the largest valid rectangle instead of distorting the ratio.
- Canvas keyboard nudge: arrow keys move selected unlocked layer/group by one output pixel; Shift+arrow moves ten output pixels. The normalized delta is derived from CompositionPlan output dimensions, independent of canvas zoom. Group members move atomically in one project revision. Shortcuts are scoped to canvas focus; tree and numeric inspector retain native arrows.
- Crop surface has accessible name/description and keyboard focus for Escape cancellation.
- Non-finite resize/anchor/rotation/drag inputs and zero/negative resize extents are rejected before rational conversion; nine-anchor resize preservation is covered.

Still not implemented:
- Text/logo/font asset editing and glyph parity.
- Complete nine-anchor interactive hit-test and preview/export geometry parity.
- Decoded continuous source-video preview, final mask-effect compositor, crop pixel compositor and render/export.
- Persistent preview/export parity or any successful render path.

Evidence:
- Layer geometry: tests/test_layer_editor_ui.py, tests/test_layer_canvas_drag.py, tests/test_layer_editor_order.py, tests/test_layer_editor_precision.py, tests/test_layer_canvas_handles.py.
- Crop: tests/test_crop_overlay.py and tests/test_timeline_crop_zoom.py.
- Keyboard nudge/focus isolation: tests/test_layer_shortcuts.py.

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

## Slice AA — persistent appearance and window-layout preferences (P04-01, 2026-11-03)

Code checkpoint: `b9ad4e814c2ac636997afc4336ac421d4fd140e4` on `develop/fonesi-full`.

The integrated UI now includes a dedicated appearance settings panel with allow-listed persisted theme (system/light/dark), base font size (9/10/11/12/14/16 pt) and in-app zoom (100/110/125/150%). Preferences are isolated under the user-level QSettings `appearance` group and are not written into project files. Live application updates include palette, font and control spacing. Reset removes only appearance preferences and preserves shortcut and window-layout settings. Qt continues to own OS-level DPI/HiDPI scaling; the in-app zoom control does not claim to change Windows display scaling.

Main-window persistence covers geometry, dock/window state, navigation row, Editor tab and Settings tab. Corrupt or oversized geometry/state fall back to defaults. A close request while the coordinator is still running does not persist an unaccepted window layout; settings are saved only after the close is accepted. The latest test-only commit adds coverage for Settings tab restoration and pending-close behavior.

Regression coverage: `tests/test_appearance_settings.py` includes allow-list persistence, live theme/font/zoom application, reset isolation, geometry/navigation/Editor/Settings tab restoration, corrupt/oversized geometry fallback and pending-close non-persistence.

Exact hosted clean-foundation run [41601897085](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41601897085) completed SUCCESS on exact HEAD `b9ad4e814c2ac636997afc4336ac421d4fd140e4`:
- Ubuntu Python 3.12.15: 954 passed, 39 skipped, 0 failed.
- Ubuntu Python 3.13.17: 954 passed, 39 skipped, 0 failed.
- Windows Python 3.12.10: 967 passed, 26 skipped, 0 failed.
- Windows Python 3.13.17: 967 passed, 26 skipped, 0 failed.
- Integrity/plan check PASS on all four runners. Windows Python 3.12 also passed the development onedir build and five scoped frozen CLI schema/subtitle/tool-discovery/license checks. Separate pinned Windows FFmpeg capability workflow remains SKIPPED.

Acceptance boundary: hosted Qt tests are offscreen. Physical Windows GUI, Explorer multi-select, mixed-DPI/HiDPI, physical Vietnamese/Chinese IME, live FFmpeg/media corpus, GPU, Chrome session/account, providers, continuous playback, synchronized A/V seek and renderer/export parity remain unaccepted or NOT_RUN. P04-01 remains IN_PROGRESS; no P04 task or phase is accepted. Global ledger remains 8/94 tasks ACCEPTED, 17 IN_PROGRESS, 69 PLANNED; 13/438 child assertions PASS, 425 NOT_RUN; 0/95 requirement groups accepted.


## Slice AB — persistent Basic/Advanced Inspector mode (P04-01, 2026-11-03)

Implementation commit: `dfeb4b32caecf12b6d85906eb4ff008a084caebe` on `develop/fonesi-full`. Documentation-only verification checkpoint: `f12419341dec4890b980fcbf5383e209703b2eb7`.

The Editor now receives the existing user-level QSettings store from MainWindow. The Inspector's Basic/Advanced checkbox reads the allow-listed boolean preference `editor/inspector_advanced` on construction and persists user toggles. Missing or malformed values fall back to Basic; legacy callers that do not inject a settings store remain backward-compatible and default to Basic. The preference is independent of project/session data and survives application window reconstruction. Appearance reset is scoped to the `appearance` settings group and preserves the Inspector preference.

Regression coverage added to `tests/test_appearance_settings.py`:
- Advanced mode restores from user settings.
- Appearance reset does not clear Inspector mode.
- Switching back to Basic persists and restores Basic.
- Toggling back to Advanced persists.
- Malformed stored values fail closed to Basic.

Exact hosted clean-foundation run 41605294255 completed SUCCESS on documentation checkpoint `f12419341dec4890b980fcbf5383e209703b2eb7`; source code under test is unchanged from implementation commit `dfeb4b32caecf12b6d85906eb4ff008a084caebe`:
- Ubuntu Python 3.12.15: 956 passed, 39 skipped, 0 failed.
- Ubuntu Python 3.13.17: 956 passed, 39 skipped, 0 failed.
- Windows Python 3.12.10: 969 passed, 26 skipped, 0 failed.
- Windows Python 3.13.17: 969 passed, 26 skipped, 0 failed.
- Preserved plan integrity PASS on all four runners.
- Windows Python 3.12 development onedir build PASS; five scoped frozen schema/subtitle/read-only tool-discovery/license checks PASS.
- The separate pinned Windows FFmpeg capability workflow was SKIPPED. Windows 3.13 did not run the onedir/frozen-only steps by workflow design.

The first CI attempt at `dfeb4b3` had all four pytest suites pass (Linux 956/39 and Windows 969/26) but failed the plan integrity step because a historical Actions URL remained in CURRENT_STATUS.md. The URL was removed in the documentation-only commit `f124193`; the exact four-runner rerun then passed. No test assertion was weakened.

Acceptance boundary: hosted Qt tests are offscreen. Physical Windows GUI, Explorer multi-select, mixed-DPI/HiDPI, physical Vietnamese/Chinese IME, actual user FFmpeg/media corpus, GPU, Chrome session/account, providers, continuous playback, synchronized A/V seek and renderer/export parity remain unaccepted or NOT_RUN. P04-01 remains IN_PROGRESS; no P04 task or phase is accepted. Global ledger remains 8/94 tasks ACCEPTED, 17 IN_PROGRESS, 69 PLANNED; 13/438 child assertions PASS, 425 NOT_RUN; 0/95 requirement groups accepted.


## Slice AC — localized Inspector accessibility metadata (P04-01, 2026-11-03)

Implementation checkpoint: `a709d45620ef51ce1bb3a014be3086cdecdd24c2`; regression test checkpoint: `e733681833e741a81b2f1dfab7b0497efcf694af`.

The layer Inspector now exposes localized accessible names and descriptions for all eight numeric transform fields and paired sliders. Anchor, horizontal/vertical flip, individual reset and transform-group reset controls have explicit accessible names and help text. This metadata does not change project commands or model state.

Regression test: `test_inspector_controls_have_localized_accessible_names_and_help` in `tests/test_layer_editor_ui.py`.

Exact four-runner run 41606760403 passed on final verification HEAD `f151e16da2be3895346d1b57f83dfdd2ffcac825`, including the accessibility implementation and tests:
- Ubuntu Python 3.12.15: 959 passed, 39 skipped, 0 failed.
- Ubuntu Python 3.13.17: 959 passed, 39 skipped, 0 failed.
- Windows Python 3.12.10: 972 passed, 26 skipped, 0 failed.
- Windows Python 3.13.17: 972 passed, 26 skipped, 0 failed.
- Plan integrity PASS on all four. Windows Python 3.12 development onedir build and five scoped frozen schema/subtitle/read-only tool-discovery/license checks PASS.

Acceptance boundary: Qt accessibility metadata is verified in hosted tests; no screen-reader certification or physical Windows accessibility/IME/HiDPI test is claimed. P04-01 remains IN_PROGRESS.

## Slice AE — finite canvas geometry validation (P04-02, 2026-11-03)

Implementation commit: `58ffe870948ef82f0d063496138aaa7d1d3c2a0b`; regression test commit: `6e65b57ffec51110f2390903308ee9ac966d6838`.

The layer canvas now rejects non-finite resize dimensions, anchor coordinates, rotation angles and drag coordinates before rational conversion. Zero/negative resize dimensions are refused. Rejected edits refresh from the authoritative project model and do not advance the project revision. Valid geometry continues through the existing one-command ProjectSession CAS path.

Regression tests in `tests/test_layer_canvas_handles.py`:
- `test_invalid_canvas_geometry_is_rejected_without_project_revision`
- `test_resize_preserves_each_of_nine_anchor_positions`

Exact four-runner CI run 41606760403 passed on final verification HEAD `f151e16da2be3895346d1b57f83dfdd2ffcac825`, including these tests:
- Ubuntu Python 3.12.15/3.13.17: 959 passed, 39 skipped, 0 failed each.
- Windows Python 3.12.10/3.13.17: 972 passed, 26 skipped, 0 failed each.
- Plan integrity PASS on all four. Windows Python 3.12 development onedir build and five scoped frozen CLI boundary checks PASS.
- The separate pinned Windows FFmpeg capability workflow was not run by this foundation workflow.

Acceptance boundary: synthetic/offscreen Qt tests do not prove physical mouse interaction, mixed-DPI scaling, source-video preview/crop compositor, renderer/export parity or end-user Windows acceptance. P04-02 remains IN_PROGRESS; no P04 task or phase is accepted.


## Slice AF — interactive normalized crop overlay (P04-02, 2026-11-03)

Implementation commits include `52a846b09f5f8ced214a53d31626094048086cc1` (crop overlay widget), `d42e7e827dbdc22e8dc2038daad6477500dd054d` (Timeline integration), `dedc23533d023416ec392bf77706e714ad19e702` (discard staged crop on preview invalidation), `f211b26f089df1e6064595e90e3d436affb569ba` (preserve crop extent on move), and `cc8134fb4d17158131ba4942cf2d82ff540296dd` (QImage-backed crop surface). The integrated code is covered by final verification HEAD `6697dc4fe5d9b58677ac09769ba013900fd1c1a7`.

Implemented:
- Dedicated still-frame crop surface, keeping crop geometry separate from the timeline graphics scene.
- Normalized crop rectangle over a still frame, shaded outside region, optional thirds grid and eight resize handles.
- Move, edge/corner resize, minimum extent and source-frame clamping.
- Optional ratio lock for edge/corner resizing.
- Staged crop edits from overlay gestures and numeric inspector; explicit Confirm commits one normalized crop change through ProjectSession CAS; Cancel discards staged edits without changing project revision.
- Stale revision, clip selection change, playhead/source preview invalidation and quality change discard staged crop rather than applying it to a different source frame/session.
- Save message explicitly states that crop preview/compositor/render is not implemented. Source media bytes are not modified.

Tests added/updated:
- `tests/test_crop_overlay.py`: normalized move, ratio-locked corner resize, source-frame clamping.
- `tests/test_timeline_crop_zoom.py`: crop stage/cancel preserves revision; Confirm commits exactly one revision and updates canonical normalized crop; existing numeric inspector validation, stale-revision, save/reopen and zoom tests remain.
- `tests/test_timeline_preview_ui.py` and other Qt UI tests now flush deferred widget deletion before leaving GUI fixtures to keep the long-lived QApplication test lifecycle deterministic.

Initial hosted diagnostics found three issues: the move gesture reduced crop extent due to stale right/bottom edges; crop compatibility methods `pixmap()`/`text()` were missing after replacing QLabel; and one integration test expected the previous status wording. These were corrected, and the crop surface uses QImage backing. A subsequent Python 3.13 offscreen run also exposed Qt teardown aborts during later tests; the affected GUI test fixtures now flush deferred QObject deletion. Final evidence below is from the later exact four-runner run, not the failed diagnostic attempts.

Exact hosted clean-foundation run 41610524340 completed SUCCESS on HEAD `6697dc4fe5d9b58677ac09769ba013900fd1c1a7`:
- Ubuntu Python 3.12.15: 964 passed, 39 skipped, 0 failed.
- Ubuntu Python 3.13.17: 964 passed, 39 skipped, 0 failed.
- Windows Python 3.12.10: 977 passed, 26 skipped, 0 failed.
- Windows Python 3.13.17: 977 passed, 26 skipped, 0 failed.
- Plan integrity PASS on all four runners.
- Windows Python 3.12 development onedir build PASS and five scoped frozen schema/subtitle/read-only tool-discovery/license checks PASS.
- Windows Python 3.13 onedir/frozen-only steps skipped by workflow design. Separate pinned Windows FFmpeg capability workflow not run.

Acceptance boundary: this slice edits canonical normalized crop geometry over an explicit still frame only. It does not crop decoded video pixels, implement a preview compositor, support continuous playback or establish crop/export parity. Physical mouse, mixed-DPI/HiDPI and end-user Windows acceptance remain NOT_RUN. P04-02 remains IN_PROGRESS; no P04 task or phase is accepted.


## Slice AG — crop gesture cancellation and ratio-safe source boundaries (P04-02, 2026-11-03)

Implementation commits: `43469e2e5f9b65fda23ffca1ff5f1a1e31ceeb2a` (gesture cancellation/no-op behavior) and `2a54d5bb063d656def08d45db8e21e9d9686bf34` (ratio-preserving source-boundary resize). Regression commits: `fb2254fb6648ef87db97d0d2fdc30a5c56c8fbb0` and `55647be8b306249e56c86d8bcbe4c7f97bcfe8fb`.

The crop overlay now cancels an active pointer gesture on Escape or when crop edit mode is disabled. Cancellation restores the exact starting crop and emits no staged update. Press/release without movement is a no-op. The crop surface receives keyboard focus on pointer interaction and exposes localized accessible name/description.

Ratio-locked edge and corner resizing now compute the largest rectangle that fits inside the normalized source frame while retaining the initial width/height ratio. When the source boundary prevents the requested pointer movement, the crop handle stops at the valid extent; it does not stretch one axis to fill the frame.

Tests in `tests/test_crop_overlay.py` cover Escape, disable-mid-drag, no-op click and ratio-lock at a source boundary. These tests supplement the earlier move, resize, clamp, confirm/cancel, stale revision and save/reopen cases.

## Slice AH — focus-scoped output-pixel layer nudge (P04-02/P04-07, 2026-11-03)

Implementation commits: `c29ae331fddb8b956380d2e5e77ea6220cdfbb3b` (remappable default bindings) and `62e9e7911952221dfcda0cedc47d7a90a1e0f90a` (normalized model nudge). Test corrections and lifecycle cleanup: `bbdc739aa851fb885af8262bbf7fa7445485fd4e`, `bf021decc6774a0767395812c5c5727ac4a36477`, `881467e215663014f1cddf22b3c85bfa66aa97b4`, `55df931a3fdd932192f987443c5121087dda523a`, `cbd522077887ff9569b3b8e3ae26948cc66012c0`.

The shared shortcut registry now provides remappable canvas actions for Left/Right/Up/Down (one output pixel) and Shift+arrows (ten output pixels). The router handles these only on the canvas and viewport, consumes key auto-repeat rather than creating an unbounded command stream, and leaves layer-tree and numeric Inspector keyboard semantics unchanged. `nudge_selected` uses exact rational deltas of `dx/output.width` and `dy/output.height`, applies one atomic CompletedCommand to all selected group members, and refuses empty, locked, stopping or reconciling selections.

Tests in `tests/test_layer_shortcuts.py` verify one/ten-pixel movement, canonical reduced rational values, zoom independence, group atomicity, lock refusal and focus boundaries. Widget cleanup flushes deferred deletion before closing the associated ProjectStore.

## Slice AI — all handle hit targets and deferred callback ownership (P04-02, 2026-11-03)

Implementation commit: `ecb37aeadd5f2c754a1064e04631e55dc20d29f3`; regression tests: `aa34f85e5975fcbd90a639a4b1e2f79454392e57`; fixture teardown follow-up: `e010b8767e8334e2a56efa5573707ff8139dddbd`.

The selected unlocked single-layer item now has explicit hit-test coverage for all eight resize handles and the rotation handle, matching the visible handle geometry. Group multi-selection and transform-locked layers do not expose individual resize/rotation handle hit targets.

The LayerBoundsItem no longer queues gesture completion lambdas against the graphics item itself. Move/resize/rotate callbacks use the owning LayerEditorWorkspace QObject as the QTimer context. If the Editor is destroyed before dispatch, Qt drops the callback instead of dereferencing a deleted item/editor. One completed gesture still flows through the existing ProjectSession command path.

Regression tests in `tests/test_layer_canvas_handles.py` cover all handle hit targets, hidden group/locked handles and callback context ownership. The canvas test fixture now flushes deferred window deletion before closing its ProjectStore.

## CI lifecycle correction — first-open tool inventory and Qt fixture cleanup (P03/P04 regression, 2026-11-03)

Implementation commit: `bcda845f96da3ab178c5659a3f3ae4a4fd77ffd7`; test commits: `9490799617a35a25f652fe8e5cca20ff23846128` and `b12e71b34f511537e55c49a0eb0aedd5741dd719`.

A queued automatic first-scan callback is now scheduled with the tool-inventory panel as its QObject context. Qt therefore owns the callback lifetime and discards it when the panel is destroyed. The callback still rechecks cancellation, navigation generation, project revision and explicit user-edited values before starting metadata-only scan. The first-open test asserts the panel context is supplied. Test fixtures now dispose completed tool panels and layer-editor windows after worker retirement and flush deferred QObject deletion.

The prior full-matrix diagnostic on commit `55df931a3fdd932192f987443c5121087dda523a` exposed Qt/Python fatal aborts during later tool-preference/first-open tests. The UI test for an ambiguous post-commit result was separated from the lower-level SQLite after-COMMIT fault-injection tests; storage fault-injection coverage remains at the storage layer. The panel-bound timer and explicit fixture disposal were then verified by the final full matrix below. No product assertion, storage guard or process-lifecycle rule was disabled.

## Exact hosted verification — crop hardening, pixel nudge and Qt lifecycle (2026-11-03)

Clean-foundation run [41613864373](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41613864373) completed SUCCESS on exact HEAD `b12e71b34f511537e55c49a0eb0aedd5741dd719`:

| Runner | Passed | Skipped | Failed |
|---|---:|---:|---:|
| Ubuntu / Python 3.12.15 | 975 | 39 | 0 |
| Ubuntu / Python 3.13.17 | 975 | 39 | 0 |
| Windows / Python 3.12.10 | 988 | 26 | 0 |
| Windows / Python 3.13.17 | 988 | 26 | 0 |

Plan integrity PASS on all four runners. Windows Python 3.12 development onedir build PASS and five scoped frozen schema/subtitle/read-only tool-discovery/license checks PASS. Windows Python 3.13 onedir/frozen-only steps were skipped by workflow design. The separate pinned Windows FFmpeg capability workflow was not run.

Acceptance boundary: hosted Qt tests use offscreen mode. This does not certify physical Windows mouse interaction, mixed-DPI/HiDPI, screen readers, Vietnamese/Chinese IME, real FFmpeg/media corpus, GPU, Chrome/account handoff, live providers, continuous playback, synchronized A/V seek, crop compositor or renderer/export parity. P04-02 remains IN_PROGRESS; no P04 task or phase is accepted. Global ledger remains 8/94 tasks ACCEPTED, 17 IN_PROGRESS, 69 PLANNED; 13/438 child assertions PASS, 425 NOT_RUN; 0/95 requirement groups accepted; P03 whole-task acceptance 0/9; P04 whole-task acceptance 0/8.


## Exact hosted verification — all handle hit targets and callback ownership (2026-11-03)

Clean-foundation run [41614862113](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41614862113) completed SUCCESS on exact HEAD `e010b8767e8334e2a56efa5573707ff8139dddbd`:

| Runner | Passed | Skipped | Failed |
|---|---:|---:|---:|
| Ubuntu / Python 3.12.15 | 978 | 39 | 0 |
| Ubuntu / Python 3.13.17 | 978 | 39 | 0 |
| Windows / Python 3.12.10 | 991 | 26 | 0 |
| Windows / Python 3.13.17 | 991 | 26 | 0 |

Plan integrity PASS on all four runners. Windows Python 3.12 development onedir build PASS and five scoped frozen schema/subtitle/read-only tool-discovery/license checks PASS. Windows Python 3.13 onedir/frozen-only steps skipped by workflow design. The separate pinned Windows FFmpeg capability workflow was not run.

Acceptance boundary: hosted QGraphicsScene hit-testing is offscreen synthetic evidence. It does not certify physical mouse input, Windows mixed-DPI/HiDPI, screen readers, IME, decoded crop compositing, GPU, real media, or renderer/export parity. P04-02 remains IN_PROGRESS; no P04 task or phase is accepted. Global ledger remains 8/94 tasks ACCEPTED, 17 IN_PROGRESS, 69 PLANNED; 13/438 child assertions PASS, 425 NOT_RUN; 0/95 requirement groups accepted; P03 whole-task acceptance 0/9; P04 whole-task acceptance 0/8.


## Slice AK — anchor-preserving viewport resize and nine-anchor pointer coverage (P04-02, 2026-11-03)

Implementation commit: `44ac412f1451c719bef184af9a6b256e1252676f`; nine-anchor pointer regression: `0c18073520ebae01f497ddc483192b48877b3085`; Qt fixture teardown follow-up: `e22b7053a6f521970c22f36f4d75c07592248b2a`.

The real QGraphicsView viewport gesture revealed that the previous resize handler stretched only the dragged edge. For a centered or otherwise non-edge anchor this moved the canonical transform origin. The resize algorithm now derives new extents from handle direction, local pointer delta and selected anchor alignment, then reconstructs the local rectangle from `offset(anchor,width,height)`. The selected anchor remains at local origin (0,0), which is the canonical scene anchor for all nine positions. Center anchors resize symmetrically; edge anchors preserve their anchor-side edge; a handle coincident with the anchor does not change that axis. Minimum extent remains 12 scene units. The release callback now records the unchanged local origin as the anchor scene position.

The viewport resize test derives its expected dimensions from the actual integer viewport endpoints mapped back into scene coordinates, so it verifies the event path without hiding geometry errors behind broad tolerances. A second pointer-path test exercises all nine anchors with the corresponding opposite resize handle and verifies one revision, unchanged canonical x/y and changed extents. The viewport rotation test derives expected rotation from the quantized scene endpoints. The canvas test fixture now drains all deferred QObject deletion events before closing ProjectStore.

Exact hosted clean-foundation run 41621095256 completed SUCCESS on exact HEAD `e87e4b136277e0ec0102f07b897325c504a005d0`:
- Ubuntu Python 3.12.15: 982 passed, 39 skipped, 0 failed.
- Ubuntu Python 3.13.17: 982 passed, 39 skipped, 0 failed.
- Windows Python 3.12.10: 995 passed, 26 skipped, 0 failed.
- Windows Python 3.13.17: 995 passed, 26 skipped, 0 failed.
- Plan integrity PASS on all four runners.
- Windows Python 3.12 development onedir build PASS and five scoped frozen schema/subtitle/read-only tool-discovery/license checks PASS.
- Windows Python 3.13 onedir/frozen-only steps skipped by workflow design. Separate pinned Windows FFmpeg capability workflow SKIPPED.

Earlier failed pointer tests exposed two independent issues: a missing Qt import in the new tests, then an actual anchor-position defect in the production resize path. The tests were corrected to calculate expectations from viewport quantization, and the production geometry was fixed; assertions were not removed. Earlier Python 3.13 Qt aborts led to a separate P03 tool-panel lifetime correction recorded in P03_RESULTS. Physical Windows pointer/HiDPI behavior, actual media, crop compositor, renderer/export parity and full P04 acceptance remain external/open. P04-02 and P04 remain IN_PROGRESS; no task or phase is accepted.


## Slice AL — shared text/logo canvas geometry and selection handle correction (P04-02, 2026-11-03)

Implementation commit: `e2ef7652f89771605922a6e807ebc6aed30c2b1b`. Schema-valid text/logo viewport tests: `c9b811394b5bec22a88c78e1b25fa8aca7e68840`.

A schema-valid synthetic CompositionPlan now exercises both a text layer with an explicit font reference and a logo layer with an explicit image asset reference. Tests drive the actual QGraphicsView viewport event path for resize and rotation on each type. They assert one project revision per gesture, unchanged canonical anchor x/y, updated normalized width/height or rotation, and unchanged layer type, content, style, font/image binding. The test saves and reopens the project and requires equality. Separate locked text/logo tests verify no individual handles and no transform/content/style mutation.

The regression exposed a real UI defect: `_sync_selection` changed selection state but left the pre-existing `LayerBoundsItem.show_handles` value stale. Selecting an existing layer could therefore leave handles hidden. The selection synchronizer now recalculates handle visibility on each selection change, calls `prepareGeometryChange()` before changing the hit shape, and refreshes the item. Multi-selection and locked layers remain without individual handles.

### P03 cancellation-test timing stabilization (test-only)

The Windows descendant-retirement test previously used a 0.6-second child sleep, which allowed the child to write its “SURVIVED” marker before cancellation reached the owned process group/job under a slow runner. The UI cancellation test had the same timing assumption. Both tests now use an explicit release-file handshake: the child waits after announcing readiness, and the test releases it only after the owner reports retirement. Any surviving child then writes a marker deterministically. The second fixture's embedded child script was also corrected to pass actual newline characters to Python. These changes strengthen the observation and do not modify production process termination or weaken assertions.

### Exact hosted verification

Clean-foundation run 41625120990 completed SUCCESS on exact HEAD `9c32e09043c23ff229dcaf608bd018c10340a1d4`:
- Ubuntu Python 3.12.15: 984 passed, 39 skipped, 0 failed.
- Ubuntu Python 3.13.17: 984 passed, 39 skipped, 0 failed.
- Windows Python 3.12.10: 997 passed, 26 skipped, 0 failed.
- Windows Python 3.13.17: 997 passed, 26 skipped, 0 failed.
- Plan integrity PASS on all four runners.
- Windows Python 3.12 development onedir build PASS; five scoped frozen schema/subtitle/read-only tool-discovery/license checks PASS.
- Windows Python 3.13 onedir/frozen-only steps skipped by workflow design.
- Separate pinned Windows FFmpeg capability workflow SKIPPED.

Hosted Qt tests are synthetic/offscreen. This evidence does not certify physical Windows pointer/HiDPI interaction, screen readers, IME, real logo image decoding, font glyph coverage, crop compositing, renderer/export parity, GPU, live providers or real-media codecs. P04-02 remains IN_PROGRESS; P04 whole-task acceptance remains 0/8. No phase acceptance is inferred from this slice.


## Slice AN — validated Timeline marker rename with shared history (P04-05, 2026-11-07)

Implementation: selected marker can be renamed through a dedicated Timeline action and native text dialog. Names are trimmed, limited to 1–64 characters, reject control characters and case-insensitive duplicates. Cancel/no-op/invalid input does not mutate the project or create an undo entry. Accepted rename is committed through the existing ProjectSession CAS path and ProjectCommandHistory, updates the marker list and scene label, and survives project save/reopen. Undo/redo restores the prior label without rewinding project revision.

Regression tests:
- `test_selected_timeline_marker_can_be_renamed_validated_and_undone`
- `test_timeline_marker_rename_is_persisted_and_shared_undo_redo`

Acceptance boundary: this slice does not implement marker drag/reposition, playback loop, continuous thumbnails or synchronized A/V seek. P04-05 and P04 remain IN_PROGRESS; no task or phase is accepted. Hosted Linux/Windows CI must run on the exact commit before claiming test PASS.


## Slice AO — frame-only bounded Timeline loop (P04-05 / ED-17.04, 2026-11-07)

Added a Timeline loop toggle backed by an owned precise Qt timer. When both In and Out are present, the loop uses the half-open frame interval [In, Out); otherwise it loops over the full output frame range. The playhead wraps deterministically, uses the project's rational FPS to set the timer interval, and stops on explicit toggle-off, project identity change or shell retirement.

A new Qt integration test covers range wrapping, full-range wrapping and retirement stop:
- `test_timeline_loop_playback_wraps_half_open_in_out_range_and_stops_cleanly`

Scope boundary: this is frame-only playhead looping. It does not decode or play video/audio, provide A/V synchronization, continuous thumbnails, sample-boundary accuracy, or marker drag. P04-05, ED-17.04 and P04 remain IN_PROGRESS and NOT_ACCEPTED pending full criteria and GUI/media evidence.


## Slice AP — rational Timeline clip move (P04-05 / ED-17.02, 2026-11-07)

Added a pure rational-time `move_video_clip` command and a Timeline-panel action that moves the selected video clip to the current playhead. The command preserves matching original audio alignment only when the audio segment has the same asset, source interval, speed and original output origin. It rejects negative starts, non-Fraction time, missing clips, output overruns and undeclared overlap through CompositionPlan invariants. The UI commits with the current ProjectSession revision and shared undo/redo history.

Regression coverage:
- Exact rational move and linked original-audio synchronization.
- Negative, overlapping and output-overrun rejection without mutating the immutable source project.
- Wrong time type and missing clip rejection.
- Qt integration for move-to-playhead and shared undo/redo.

ED-17.02 remains NOT_RUN until the complete criterion and required GUI evidence are satisfied; P04 remains IN_PROGRESS.


## Slice AQ — gap/ripple delete and source preservation (P04-05 / ED-17.03, ED-17.05, 2026-11-07)

Added a rational-time delete command and Timeline-panel action. Gap mode removes the selected clip while preserving downstream output positions; ripple mode closes the time gap by shifting later video/audio segments left. The command removes only composition references for the selected clip and the matching original-audio segment; it does not modify the media library or source file. The UI commits once against the current session revision and records shared undo/redo history.

Regression cases:
- Unit tests for gap and ripple timing differences.
- Invalid ripple type and missing clip fail closed.
- Source file bytes and existence are checked before/after delete.
- Qt integration tests both modes and shared undo/redo.

The tests require a hosted run on the exact commit. ED-17.03 and ED-17.05 remain NOT_RUN; P04 remains IN_PROGRESS.


## Slice AR — viewport-routed marker drag and cancel semantics (P04-05, 2026-11-07)

Implementation commit: [`b14c409c8abbcb34d6d94b4ded5ca1c5f2571ed6`](https://github.com/danhgold7979-cyber/fonesi-edit/commit/b14c409c8abbcb34d6d94b4ded5ca1c5f2571ed6). The exact guarded candidate diff was tested by targeted workflow run [`42341716342`](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/42341716342), which completed SUCCESS on Ubuntu 24.04 / Python 3.12 and then committed that tested diff to `develop/fonesi-full`.

Implemented:
- `TimelineGraphicsView` routes marker press/move/release through real viewport-local coordinates, scans the full item stack below the mouse-transparent playhead and clamps movement through the existing marker item bounds.
- Marker mutation now binds the canonical `session.project.id`, not the composition-plan ID, so the existing stale-project/revision CAS guard accepts the active project and still rejects stale callbacks.
- A successful drag commits exactly one shared-history command; undo/redo and project-file save/reopen preserve the moved frame.
- Collision refusal restores the prior marker frame without creating a project revision. Escape first cancels an active marker drag and restores its visual origin; when no drag is active it retains the existing In/Out clear behavior. Press/release without movement is a no-op.
- Offscreen regression input uses explicit `QMouseEvent` viewport-local coordinates because Qt's virtual global cursor can be clamped on a small offscreen screen. Assertions still exercise the production viewport event path and were not weakened.

Targeted regression evidence:
- `test_timeline_marker_viewport_drag_commits_once_and_shared_undo_redo`
- `test_timeline_marker_drag_collision_and_escape_do_not_create_commands`
- Result: 2 passed, 0 failed in the guarded apply job. Temporary transfer workflow/script/patch files were deleted by the successful product commit.

Acceptance boundary: this is targeted hosted Linux/Qt-offscreen evidence, not the required exact-HEAD four-runner foundation result and not physical Windows mouse, mixed-DPI/HiDPI, screen-reader, IME, real-media, synchronized A/V seek or render/export acceptance. P04-05 and P04 remain IN_PROGRESS; ED-17 criteria and all acceptance counters remain unchanged pending complete criteria and external gates.



## Slice AS — persistent content-addressed proxy cache boundary (P04-06, 2026-11-07)

Implementation commits:
- `a894891dc39012a803a8072212dbaf5112a2d25c`: add persistent proxy cache module.
- `e3b85ed86f6d66aafb7cca4e8cb18538f072014e`: bound cache reads and validate invalidation identity.
- `a3d76d44cd905096205fb993a54fb6ad643703ed`: add regression tests for invalidation isolation and path traversal.

Implemented in `src/fonesi_edit/media/proxy_cache.py`:
- Immutable key bound to source SHA-256, tool SHA-256, stream index, dimensions and algorithm version.
- Explicit absolute cache root; rejects parent traversal, symlink and Windows reparse-point path components.
- Bounded encoded-byte payloads and bounded reads; manifest records schema, exact key, size and payload SHA-256.
- Staged writes with file flush/fsync, cancellation check before atomic publication and safe replacement rollback.
- Read-time key/size/digest validation; corrupt or oversized entries are cache misses.
- Per-key invalidation and source-wide invalidation that validates schema/key and verifies the directory name matches the canonical cache identity, avoiding deletion of unrelated directories with forged manifests.
- This is persistent storage infrastructure only. No FFmpeg proxy generation, timeline integration, playback, A/V synchronized decoding, performance acceptance or render parity is claimed.

Regression coverage in `tests/test_proxy_cache.py`: key identity/validation, round-trip/reopen, tool/stream/size/version invalidation, corrupt manifest/payload, size bound, cancellation before and after staging, per-key/source invalidation, symlink refusal, invalid input and preservation of unrelated directories.

The initial implementation commit's full hosted foundation run 42348806219 completed SUCCESS on four runners (Ubuntu/Windows Python 3.12/3.13). This run predates the subsequent hardening commits and must not be used as their test evidence. The exact post-hardening HEAD requires a fresh four-runner CI result before PASS is recorded.

Acceptance boundary: P04-06 and P04 remain IN_PROGRESS; this slice does not satisfy persistent encoded proxy generation, worker ownership integration, cancellation of real FFmpeg proxy jobs, stale cache lifecycle integration, A/V seek, warm/cold performance or physical Windows filesystem acceptance.



### Slice AS follow-up — persistent cache budgets and root revalidation (2026-11-07)

Follow-up implementation commits:
- `83c457829d3e562a03d09a174d70823cc1dfd214`: total-byte and entry-count quotas with oldest-entry eviction, retaining the newly published entry.
- `c27729e83c1eb21511d1c3c675211703b02a9fc4`: quota regression tests.
- `a562bc0eefdd2aa34ac8d6b9aeb69a5c0e9c60be`: replacement, symlink payload/manifest and invalidation refusal tests.
- `946ed3d302d6dd7decb0c7e3309cc36e6169fb55`: revalidate cache root before each filesystem operation.
- `3ac286aaa93142e4afa63e0c83ba6d45716394aa`: root replacement/symlink regression.

Default cache bounds: 512 MiB per entry, 2 GiB total and 256 entries; caller may lower bounds within validated ceilings. LRU-style eviction uses entry directory modification time, which is refreshed by atomic replacement but not yet by cache reads. This is a bounded persistent cache with oldest-entry eviction, not a true access-updated LRU. Reads verify manifest and payload digest; cancellation and symlink/reparse guards remain fail-closed.

Latest exact-head four-runner CI is required for the follow-up changes; prior run 42348806219 tested only the first implementation commit and must not be reused as evidence. P04-06 remains partial: cache is not yet integrated with an encoder/proxy worker, and no actual proxy generation, synchronized A/V playback seek, warm/cold benchmark, GPU or render parity is claimed.



### Slice AS LRU refinement — verified reads refresh recency (2026-11-07)

Commits:
- `5d6a46e249c77696b3558ab2bf3dd531a8bd1ed3`: successful integrity-verified reads refresh the cache-entry directory modification time, used by bounded oldest-entry eviction.
- `a7bae68cd0f2a178dd598d7b1bade3a8c25d61e9`: regression verifies that a previously accessed entry is retained while the least-recently-used entry is evicted under a reduced quota.

This is now access-updated LRU-style eviction rather than write-time-only oldest-entry eviction. Failure to update recency does not invalidate a successfully verified cache read; eviction remains bounded but recency may be stale for that operation. Exact-head four-runner CI remains required.



### Slice AS corrupt-entry cleanup — 2026-11-07

Commits:
- `049f42af99ada2e8cf3ecc336f27b987b5bd5870`: quota pruning now removes a corrupt entry only when its manifest parses as a valid `ProxyCacheKey` and the directory name exactly matches that key's canonical cache ID. Unknown directories and entries without a valid canonical identity are preserved.
- `eb6b6ca27b976326765de6ffcb7bb7fd314a43e8`: regression asserts corrupt canonical entry cleanup while preserving the valid entry and new publication.

The cleanup prevents digest-corrupt cache payloads from accumulating outside the byte/entry budget. Exact-head CI remains pending; earlier matrix results do not cover these two commits.



### Slice AS malformed-manifest and root-mutation guard — 2026-11-07

Commits:
- `37d8aa4ddcb47d1b3e75aa32a6341403982f57f8`: root path is revalidated as absolute and traversal-free at every filesystem entry point; source invalidation ignores non-object JSON manifests rather than raising.
- `c94d7936db1e36e13c6b1c6131936dadef87b262`: regression covers JSON list/broken manifests and post-construction cache-root mutation.

Exact latest-head Linux/Windows matrix remains pending. No local execution is claimed.



### Slice AS Windows LRU timestamp portability fix — 2026-11-07

The exact-head matrix at commit `82408efd827f3aa5f4fdead34d7abe35fed5a6ed` exposed seven Windows Python 3.12 failures: `os.utime(..., follow_symlinks=False)` raises `NotImplementedError` on Windows. Commits `25bb61c3e92a8f45f46b347c0cfa9742ab6b3935` and `16aaf6b624a2c69cab89d249e78ed4664a69fe8e` remove the unsupported flag after the cache entry passed lstat/reparse validation and add a regression proving a verified read remains usable if recency update is unsupported. Exact new-head four-runner CI is required; prior failures and Linux PASS do not count as current acceptance.



### Slice AT — persistent cache integration into still-preview worker (P04-06, 2026-11-07)

Implementation commits:
- `d609b88eb385cb09c01102a091579a818261b13f`: optional persistent cache lookup/publication in `extract_preview_frame`, with key identity including the exact rational decoder timestamp.
- `4be75514f3fb11ab8d48f4a6da2bf5e296d410cf`: consult in-memory LRU before disk cache to avoid duplicate memory accounting and unnecessary disk reads.
- `587a6901deab89366218bd9722e5cb96c57b2dcd`: timeline `PreviewWorker` uses app-local Qt CacheLocation/preview-proxies; cache setup failure falls back to in-memory behavior.
- `296d5010d1fa1b89162f0c3126e7df1273f9cbcb`: UI fake extractors accept the optional cache dependency.
- `3ffb6d3b8ed6cdac606180c126a8ad76671ea20e` and `96dab397d73718f12535f0f3015418f57cbe28f0`: validate cache object type and test refusal of unvalidated cache inputs.

Regression coverage: persistent reuse after clearing process-memory cache; corrupt disk payload is rejected, re-decoded and repaired; exact rational timestamps map to separate entries; invalid cache objects fail before decoder launch.

Acceptance boundary: this connects persistent storage to still-frame preview only. It does not implement background proxy encoding, proxy worker queue, waveform persistence, playback or synchronized A/V seek. Latest code commits need exact-head four-runner CI before PASS is reported.



### Slice AU — Timeline playback control and shutdown regression repair (2026-11-07)

The exact-head run `42369998598` at `69bf2c9f0fc2b23d81f866e95292204b102c87a6` found two failures in the new Timeline playback UI tests:
- Resume control was disabled while paused, making the second click unable to resume. Commit `17e04a2cdc664b412ecabc08e0208ce463163d39` keeps the control enabled during an active session and changes its label to “Tiếp tục” while paused.
- The test attempted direct assignment to the read-only `ProjectSession.project` property and used no valid CAS commit. Commit `3c46c713dbf5a33ec885c4f7bb6c7e21a9010d2a` updates the fixture to create a valid next revision and commit it through `ProjectSession.commit(CompletedCommand(...))`.

Shutdown now explicitly stops an active bounded playback session before Timeline teardown (commit `af79c738d159a1bd8ef1f11e629f0184b74e4775`), with a regression test in `69bf2c9f0fc2b23d81f866e95292204b102c87a6`.

The failed run also recorded 1,179+ passed tests per runner; exact latest HEAD requires a new four-runner result. No local test execution is claimed. Finite A/V playback remains a <=5-second prototype, not full project playback acceptance.



### Slice AV — persistent waveform observation cache (P04-06, 2026-11-07)

Commits:
- `83964e5ab6e57106e21cd6e5597165a6a83823f2`: validated persistent waveform read/write using the shared bounded cache; exact rational window, source/tool hashes, stream, sample rate and bucket count are bound into cache identity.
- `55e1691027ddf49a2d72e372a87ab784e051e912`: harden cached numeric peak validation.
- `4d6fd7750d4d2cf661dfa847a05689832b5462f0`: regressions for persistent reuse, corrupt payload recovery, identity separation and invalid cache input.
- `739c15647950316959a03514d1d447051dca50e2`: Timeline WaveformWorker uses app-local Qt CacheLocation/waveform-cache, with memory-only fallback.
- `d4b3a7cfba372ee60f922311207955bc2654878b`: record integration plan.

Waveform cache payload is bounded JSON with schema, exact rational window, stream/source/tool identity, sample count and normalized min/max bins. It is verified before use; corrupt cache triggers re-decode/repair. It remains an amplitude observation only.

Exact latest-head Linux/Windows Python 3.12/3.13 CI is required before PASS. No local test run is claimed. Continuous audio/video playback, arbitrary project timeline scheduling, seek while playing, robust drift correction, render/export parity and real-device Windows acceptance remain open.



### Slice AV hardening — strict waveform cache envelope (2026-11-07)

Commits:
- `83ee081682ae86440665988de678951e9e5a1e82`: enforce 64 KiB waveform JSON cap, strict scalar/list types, exact rational window and expected bucket cardinality, finite bounded peaks and safe numeric conversion.
- `ee8c0145414172d76053a84ffd878075c2623eda`: regression injects a digest-valid cache payload with boolean schema and verifies it is rejected, re-decoded and repaired.

Exact latest-head CI is pending; no local execution is claimed.
