# P04 — Task-specific clean implementation plan

Generation clean-2026-11-01; integrated branch `develop/fonesi-full`. Status IN_PROGRESS; P04-01 through P04-08 have partial implementation, including layer groups, timeline editing, still-frame preview and focus-scoped shortcuts; no P04 task or phase is accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P04-01 — panel/theme/HiDPI/cỡ chữ UI, drag từ Explorer, media/inspector, slider/ô số/reset.

- **Depends on:** P03-01/07,P01-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Eight-area UX and shared project model.
- **Output/interface:** Native panel layout/theme/font-size/HiDPI persistence, Explorer multi-drag, inspector numeric+slider/reset.
- **Errors/cancellation:** Unsupported drop item shown; canceled import no source changes; layout corrupt resets only layout.
- **Tests and acceptance:** Qt UI import/resize/reset/save/reopen with keyboard focus; Windows Explorer/HiDPI physical checks separate.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Partial code exists: explicit one-file media import/drop, bounded 64-file local drop review queue with per-item refusal and explicit one-at-a-time selection, media library, numeric inspector with paired transform sliders, per-property/group reset, Basic/Advanced mode, property search and layer-specific disabled reasons/tooltips. Full effect-property catalog and complete disabled-reason mapping remain OPEN. User-level theme/font-size/in-app zoom, window/navigation/tab layout and Inspector Basic/Advanced preference persistence are implemented and hosted-tested. Physical Windows Explorer multi-select, OS-level mixed-DPI/HiDPI, screen-reader and physical IME acceptance remain OPEN. Current outcome PARTIAL_IMPLEMENTED; task acceptance NOT MET.

## P04-02 — chọn/kéo/resize/xoay logo/chữ/vùng che, crop; neo/tọa độ tương đối, lưới/safe area/snap/Alt và đưa về khung.

- **Depends on:** P04-01,P01-07,P02-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Selected layer/crop geometry and viewport transform.
- **Output/interface:** Canvas handles move/resize/rotate/crop/anchor/grid/safe-area/snap/Alt/bring-inside commands.
- **Errors/cancellation:** Locked layer not moved; crop cancel restores; zoom/pan never domain mutation; bad aspect/zero size rejected.
- **Tests and acceptance:** 9 anchors, off-center rotation, portrait/landscape, Alt snap, pixel-step and zoom invariance; export parity on manipulated fixture.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Partial code exists: mask-layer geometry, move/resize/rotation handles, crop numeric inspector, grid/safe-area/snap/Alt and bring-into-frame. Text/logo content editing, crop handles, complete interactive nine-anchor hit tests and preview/export parity remain OPEN. Current outcome PARTIAL_IMPLEMENTED; task acceptance NOT MET.

## P04-03 — đa chọn/nhóm/khóa/ẩn/thứ tự layer; tránh kéo nhầm; menu ngữ cảnh.

- **Depends on:** P04-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Layer IDs/z-order/group/lock/visibility.
- **Output/interface:** Multi-select box/Shift, group/ungroup, lock/hide/reorder and context menu.
- **Errors/cancellation:** Overlapping layer selection via tree; locked drag no-op; deleted selection invalidated; cancel grouped drag atomic.
- **Tests and acceptance:** Selection/persistence/group transform and z-order parity; Delete removes objects not source files.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Partial code exists: tree multi-select, persistent group UUIDs, group drag, lock/hide/z-order/batch delete and context-menu actions. Marquee selection and full platform interaction acceptance remain OPEN. Current outcome PARTIAL_IMPLEMENTED; task acceptance NOT MET.

## P04-04 — undo/redo, một drag một lệnh; inspector và canvas dùng cùng model, save/open giữ đúng.

- **Depends on:** P04-02/03,P03-07. Only independent work may proceed while external portions remain blocked.
- **Input:** Before/after scoped domain commands.
- **Output/interface:** Unified canvas/inspector/timeline command stack, one drag one undo.
- **Errors/cancellation:** Esc cancels transient, text undo stays text; stale revision fails command; grouped error rolls back whole command.
- **Tests and acceptance:** Hundreds drag events→one undo; redo/save/open equality; inspector edits visible in canvas and canonical export.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Partial code exists: layer inspector/canvas share CompositionPlan and ProjectSession CAS; layer drag/resize/rotate are one completed command; layer undo/redo and save/reopen tests exist. A single history spanning timeline/text/subtitle and hundreds-event gesture stress acceptance remain OPEN. Current outcome PARTIAL_IMPLEMENTED; task acceptance NOT MET.

## P04-05 — timeline/playhead/trim/split/in-out/gap/ripple/marker, thumbnail/waveform, zoom/scroll/loop.

- **Depends on:** P04-04,P03-03. Only independent work may proceed while external portions remain blocked.
- **Input:** Rational clips/cues/tracks, thumbnails/waveforms.
- **Output/interface:** Timeline playhead/trim/split/in-out/gap/ripple/marker/zoom/scroll/loop commands.
- **Errors/cancellation:** Trim bounds and overlaps validated; split at edge rejected; Esc leaves timeline unchanged; missing media visible.
- **Tests and acceptance:** Boundary frame/sample tests, gap vs ripple distinction, linked A/V/sub mapping; repeated split/undo round-trip.
- **Evidence:** Partial code includes integer-frame playhead, split, trim-in/out, audio sync, gap/ripple, zoom/scroll, project-persisted half-open In/Out range, named marker create/select/delete with M shortcut, and bounded user-triggered filmstrip/waveform. Loop playback, marker rename/drag, continuous timeline thumbnails, sample-boundary acceptance and full A/V seek remain OPEN. Current outcome PARTIAL_IMPLEMENTED; task acceptance NOT MET.

## P04-06 — proxy/cache tạo nền, đổi chất lượng/cancel/invalidation, seek đồng bộ audio/video.

- **Depends on:** P04-01/05,P02-04/07. Only independent work may proceed while external portions remain blocked.
- **Input:** Probe/fingerprint and canonical CompositionPlan revision.
- **Output/interface:** Background proxy/thumbnail/waveform jobs; quality selection; stale-request-safe A/V seek.
- **Errors/cancellation:** Cancel proxy leaves no ready cache; changed source invalidates; obsolete seek result ignored; missing audio explicit.
- **Tests and acceptance:** Warm/cold seek timing, CPU render concurrent responsiveness, proxy hash/version invalidation, canonical sample frames parity.
- **Evidence:** Slice K–M provide background still-frame/filmstrip/waveform jobs and bounded in-memory content caches; Slice P adds draft/standard/high still-preview quality profiles with resolution-bound cache keys and stale-result invalidation. Persistent encoded proxy generation, continuous timeline thumbnails, A/V synchronized seek, warm/cold seek performance and CPU-render concurrency acceptance remain OPEN. Current outcome PARTIAL_IMPLEMENTED; task acceptance NOT MET.

## P04-07 — shortcut theo focus, remap/xung đột/trợ giúp; nhập Việt/Trung không kích hoạt player/canvas.

- **Depends on:** P04-01/04/05. Only independent work may proceed while external portions remain blocked.
- **Input:** ED§9 full default shortcut map and focus contexts.
- **Output/interface:** Shortcut router/remap/conflict/help UI with IME guard.
- **Errors/cancellation:** Text input/preedit owns keys; duplicate binding rejected or explicit resolution; Escape first cancels current operation.
- **Tests and acceptance:** Qt focus and repeated navigation tests for every shortcut; Vietnamese/Chinese physical IME separately NOT_RUN if unavailable.
- **Evidence:** Partial code includes a persistent QSettings registry, searchable remapping panel, overlapping-scope conflict rejection, reset-to-default and live event-filter routing. Layer shortcuts remain limited to tree/canvas with IME preedit protection; timeline routing is limited to clip-list/canvas and their viewports; application Settings is available across the main-window widget tree while text editors and key-sequence capture retain their input; F5 is limited to the tool table. The implemented subset is not the full ED§9 map. Physical Vietnamese/Chinese IME certification, OS-specific shortcut conflict review, all remaining player/timeline actions and full global shortcut coverage remain OPEN. Current outcome PARTIAL_IMPLEMENTED; task acceptance NOT MET.

## P04-08 — UI Cài đặt tool scan/path/check/download/install-all/update/repair/rollback có progress; Chrome/profile/account tables, Ctrl+, và readiness với nút khắc phục đúng lỗi.

- **Depends on:** P03-08/09,P04-01,P01-08. Only independent work may proceed while external portions remain blocked.
- **Input:** Live tool/profile/account registry snapshots.
- **Output/interface:** Settings tables and truthful scan/path/check/install-all/update/repair/rollback, Chrome login/readiness actions.
- **Errors/cancellation:** Stale background scan ignored; cancel install per component; explicit path invalid visible; locked profile not forced.
- **Tests and acceptance:** Qt state walkthrough missing/busy/fail/success, Ctrl+, and F5 scope, repeated clicks; actual Windows tool/Chrome test remains required.
- **Evidence:** Partial settings code exists: metadata-only tool inventory, explicit path preferences, bounded background name scan, user-selected pair self-test and focus-scoped F5 rescan. The shared Settings page also exposes shortcut remapping. No download/install-all/update/repair/rollback, Chrome profile/account table, login readiness or full platform recovery workflow is implemented. Current outcome PARTIAL_IMPLEMENTED; task acceptance NOT MET.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.

## Initial local media library import — P04-01 partial, P03-07 command dependency

Entry evidence: P03 library-only persistence on `develop/fonesi-full` preserves
independent UUIDs, content-bound refs, explicit unresolved observations and
CAS project revision. The P03 desktop coordinator host is independent of import.
Whole P03 and P04 gates stay open. This bounded slice does NOT add media to the
render-ready CompositionPlan, run a download, or imply player/codec support.

A dedicated Editor import panel accepts exactly one explicit local media path
and one explicitly user-trusted absolute ffprobe executable; no auto-resolution,
credential acquisition, Chrome access, provider calls, or user media modification.
A background QThread pins regular non-reparse source identity, performs the
existing bounded `inspect_media` + typed normalization + semantic validation
inside owned validator retirement, then re-fingerprints and rechecks identity.
An observed source becomes a typed `MediaRecord` with independent UUID and
absolute hash-bound path; it remains explicitly non-render-ready. Unknown or
unconfirmed process retirement revokes the operation without adoption/retry.

Import to the active project is the existing `add_media` completed command,
CAS against the captured session identity and revision, committed exactly once
through `ProjectSession.commit`. UI close/cancel, stale project, duplicate
content or changed bytes cannot silently commit. A later explicit project Save
writes the same v2 library envelope; source media is never deleted/copied. Project
list display is bounded and read-only, showing unresolved state rather than a
claim of timeline/render readiness. Support direct UI tests with synthetic
approved tool fixture and actual native tests separately; mock output is not
codec acceptance. No project mutation before process retirement is confirmed.

Regression scope: project missing / wrong tools / symlink sources / duplicate
content / post-probe mutation / cancellation / stale session / recovery /
source bytes unchanged; Qt shell close waits for background import, owner
threads retire before QApplication. Linux/Windows 3.12/3.13 source tests; actual
FFmpeg on a physical Windows user machine remains NOT_RUN. P04-01/P03-07,
full import/drag/drop/HiDPI/timeline and release acceptance remain OPEN.

 
### Initial CI diagnostic and correction
Initial source suite on commit c4d42d59 failed three new Linux Qt tests
(run 41482065653). The tests chose the virtualenv `sys.executable`
symlink as the explicitly trusted ffprobe *path*, which correctly fails
the production non-reparse tool preflight before any synthetic probe can
run. Do not weaken that guard. Fixture path now uses the resolved regular
Python executable; the owned Python child remains a synthetic process
test, never media codec verification. Exact fix CI must run before a
PASS claim; other failures, if any, remain separate.

## Slice B — local file transfer into source selector

Accept exactly one local file URL from the desktop file manager. Check that it is absolute, bounded, existing, regular, and not a symlink or reparse point. Reject remote URLs, folders, multiple files, and missing paths. A successful drop only fills the existing source field; the user must still review it and press the existing import action. It must not start ffprobe, alter tool trust, copy/move/delete the source, or write project data. Test valid and rejected Qt events and verify source bytes, project revision, and worker state are unchanged. Physical Windows Explorer and HiDPI checks remain external.

## Slice C — first editable layer workspace

Build a native Editor workspace on the existing immutable CompositionPlan and ProjectSession. The first editable canvas scope is typed rectangular mask-layer geometry: normalized anchor position and extent, scale, clockwise rotation, opacity, visibility, z-order and explicit transform lock. A layer list and numeric inspector must read and write the same project model. Canvas movement commits once on release; numeric edits commit on editing completion. Every completed edit advances the project revision exactly once through CompletedCommand CAS. A session-local undo/redo stack restores prior values by issuing new monotonic revisions; it never rewinds a stored revision.

The canvas may show layer bounds over a neutral background. It must explicitly state that source-video decode, final blur/mosaic rendering, text/font parity and preview/export rendering are not implemented by this slice. No control may claim a render succeeded. Removing a layer removes only the project object, never its source file. Regression coverage: all nine anchors, noncentral rotation, normalized geometry, locked transforms, hidden layers, z-order, stale revision, one-drag-one-command, undo/redo/save/reopen equality, and source preservation. Multi-select/group, crop/resize handles and renderer parity remain open.

## Slice D — promote a fully observed local source into a timeline clip

Use the existing non-render-ready MediaRecord as the only source of file identity/path and typed per-stream facts. Require one selected non-attached video stream with known exact time_base/start_pts/duration/geometry/SAR/orientation, a known container duration, and only explicitly supported mono/stereo audio streams. Run bounded ffprobe frame observation on a background QThread using the same explicitly selected trusted executable and owned ValidationLifecycle. Refuse if the frame scan is not OBSERVED_EOF, source hash changes, start_pts/time_base mismatch, any frame PTS is absent/non-increasing/out of bounds, unsupported stream metadata exists, or process retirement is not confirmed. Convert raw PTS to exact stream-relative rational timestamps; never synthesize a constant frame rate or substitute best-effort timestamps for missing PTS.

On success, add a hash-bound video Asset plus one video Clip and matching original-role audio Clips for observed supported audio streams. Append at the exact end of existing timeline content, extend output duration only as required, and commit one CompletedCommand CAS. The source file is never copied, moved or deleted. No render-ready or export-success flag is set. A read-only timeline overview shows exact start/duration and track identity. Tests use typed synthetic FrameScan fixtures for pure mapping and an owned child process for lifecycle only; actual codec/PTS correctness and user-selected ffprobe remain separate runtime evidence. Trim/split/ripple/playhead/audio preview/proxy and renderer parity remain later work.

## Slice E — frame-accurate playhead, split and trim with gap/ripple distinction

Add an output-frame playhead based on the exact rational project frame rate. The displayed time is derived from integer frame index/fps; do not use wall-clock or floating-point accumulation. Selected video clip actions:
- Split at playhead creates left/right clips with exact source boundary mapping (source_in + delta_output × speed), stable left ID and new right ID.
- Trim-in moves the clip's left edge to the playhead and updates source_in; with ripple disabled, later clips remain and the gap is preserved. With ripple enabled, later non-overlapping clips/tracks shift left by the exact removed duration.
- Trim-out updates source_out and does not shift following clips.
- Synchronized audio clips sharing the same source asset are split/trimmed at the same output time when that time lies within their own intervals; unrelated tracks remain unchanged.
Reject boundary splits, zero-length clips, freeze-frame/unsupported timing cases and stale session revisions. Each action is one CompletedCommand CAS and one undoable project revision. Timeline graphics remain an overview; this slice does not add playback, thumbnails, waveform, loop or rendering.

## Slice F — selected-clip crop inspector and usable timeline zoom/scroll

Add a numeric crop inspector for the selected video clip using the canonical normalized crop rectangle (left/top/width/height). Preserve untouched rational values exactly; validate the entire rectangle against CompositionPlan before one CAS commit. Invalid intermediate edits must not mutate the project or auto-correct/clamp values. Refresh must preserve selected clip identity. Add a fit-to-view action and bounded zoom control (50–400%) over the same exact-time overview; zoom is presentation-only and must not alter timeline time or project revision. Horizontal scroll exposes offscreen portions without rescaling time. Add an explicit playhead line tied to the integer output-frame index. This is still not source-video preview, crop-handle UI or export rendering.

Tests: valid crop, out-of-bounds rejection, zero extent rejection, untouched rational preservation, stale session CAS, one revision per completed inspector edit, selection retained after refresh, zoom/scroll no model mutation, fit reset, playhead x-coordinate exact to rational frame time, and half-open final frame bounds. External video decode and pixel parity remain blocked.

## Slice G — persistent layer groups, multi-selection and atomic group actions

Extend schema-v1 Layer with an optional nullable UUID group_id. A non-null group must contain at least two existing layers; no implicit group transform or hidden asset ownership is introduced. Selecting a member selects the whole group. Ctrl/Shift multi-select works for ungrouped layers. Dragging a multi-selection moves all unlocked selected bounds by the same canvas delta and emits one CompletedCommand CAS; if any selected member is locked, the group drag is refused as a whole. Group/ungroup, batch delete, lock/unlock, hide/show and z-order actions are atomic commands over the selected IDs. Grouping existing groups expands to their full membership before assigning a new group ID; ungrouping any member clears the entire group. Right-click context menu exposes the same safe actions. Source assets are never deleted by layer operations.

Tests: schema compatibility with older plans, singleton/invalid group rejection, persistent group save/reopen, group auto-selection, ctrl/shift multi-select, group movement one revision and preserved relative offsets, mixed locked selection refuses all movement, batch lock/visibility/delete, group/ungroup and undo/redo monotonic revisions, context menu actions, source bytes unchanged. This does not implement crop handles or renderer group parity.

## Slice H — canvas grid, safe area, snap/Alt and bring-into-frame

Add non-selectable viewport overlays for a normalized 5% grid and 90% safe-area guide; toggling overlays must not change project revision or selection. Enable grid snapping for canvas drags at normalized 0.05 increments; holding Alt during the drag-release bypasses snapping for that one operation. Snapping computes one delta from the primary selected layer and applies the same delta to all selected/grouped members, including hidden members, preserving relative offsets. Add an explicit bring-into-frame command for selected layers/groups. It clamps anchor position only when the full scaled bounds can fit inside [0,1]×[0,1]; if any selected layer is larger than the output frame, refuse the entire operation without changing any member. All edits use one CompletedCommand CAS and one undo record. Overlay toggles, zoom and viewport operations are presentation-only.

Tests: grid/safe toggles leave revision and selection unchanged; snap at positive/negative coordinates; Alt bypass; group snap preserves offsets and hidden member geometry; all nine anchors for bring-into-frame; oversized layer refusal is atomic; locked member refuses group command; undo/redo and source-file immutability.

## Slice I — canvas resize and rotation handles

Selected single layers expose eight resize handles and one rotation handle. Resize operates in item-local coordinates, preserves the selected anchor semantics, converts back to normalized width/height and anchor x/y, and rejects dimensions below the minimum handle extent. Rotation uses the canonical clockwise degree field and commits once on release. Multi-selection hides individual handles rather than applying a misleading partial resize; group transforms remain a separate atomic operation. Locked layers do not expose or accept handle mutations. Every release commits through ProjectSession CAS; source assets remain untouched. Tests cover normalized resize, rotated anchors, one revision per completed handle gesture, lock refusal, and hidden handles during multi-selection. Actual mouse/HiDPI handle hit-testing remains separate from callback/model tests.

## Slice J — focus-scoped editor keyboard actions

Bind the existing layer commands to a small documented shortcut set only while focus is within the layer tree or canvas (including their viewport children): Ctrl+Z/Y, Delete, Ctrl+G, Ctrl+Shift+G, Alt+Up/Down. Do not register these shortcuts on the entire window or numeric inspector. Text/IME fields and spin boxes retain native editing shortcuts; Vietnamese/Chinese preedit is not consumed. Shortcut actions call the same validated command methods and one project CAS; no shortcut may bypass lock/group rules. A help tooltip lists this initial map. User remapping, conflict-resolution UI, complete ED§9 coverage and physical IME certification remain open.

Tests: each shortcut with tree focus and canvas focus; same key with numeric inspector/text focus does not invoke project commands; Ctrl+Z/Y monotonic revision; Delete preserves source; group shortcut follows group invariants; disabled/stopping workspace ignores actions.

## Slice K — explicit still-frame preview and bounded content cache

A selected video clip can request one still frame at the integer-frame playhead using only an explicitly selected absolute FFmpeg executable after the user confirms trust in that executable and its adjacent DLL/dependencies. The worker resolves the asset path against the opened project base, rejects symlink/reparse components, hashes the source and executable against the project asset SHA, invokes an owned bounded process with a single mapped video stream and one PNG output, then verifies both file identities remained stable. It never writes to source media or project data.

An in-memory LRU cache is keyed by source SHA256, FFmpeg SHA256, stream index, exact decoder timestamp, dimensions and preview algorithm version. It is bounded by entry count and total PNG bytes. Source/tool stat identity is checked on every use; changed bytes produce a new hash or refusal. Preview requests are generation/revision/clip bound; stale results are discarded. Closing the app requests worker cancellation and waits for owned process retirement before window teardown.

This is a convenience still image, not a decoded playback pipeline, synchronized A/V seek, timeline thumbnail/waveform service, crop/transform compositor, render output or codec acceptance. FFmpeg output seek may select the next decoded frame at/after the requested timestamp; exact PTS parity remains open. Unsupported negative/ambiguous timestamp behavior must fail visibly rather than silently claim frame accuracy.

Tests: source and executable content mismatch, source mutation, symlink/reparse refusal, project-relative path traversal, explicit stream/timestamp argv, bounded PNG dimensions/bytes, cache hit and invalidation on source/tool changes, decoder failure/cancel, no automatic tool discovery/launch before explicit trust, stale playhead/project result discarded, source bytes unchanged, application close waits for worker. Hosted synthetic runner tests are not physical FFmpeg/media corpus or audio-sync acceptance.

## Slice L — user-triggered four-frame filmstrip

Extend the still-frame worker to accept a bounded tuple of at most four exact decoder timestamps. A user may request a four-image filmstrip for the selected clip after explicitly selecting and trusting FFmpeg. Sample at 1/8, 3/8, 5/8 and 7/8 of the source interval; never sample the exclusive out-point. Extract sequentially in one owned worker, reuse the source/tool hash pins and in-memory frame cache, and publish the set only if every frame completes and the captured project revision/clip identity remains current. Cancellation or any frame failure discards the whole partial strip. Unknown process retirement locks preview and app close as in Slice K. This remains a still-image contact sheet, not continuous timeline thumbnails, playback, audio sync, or proxy media.

Tests: four strictly increasing rational timestamps; all frames use the selected stream and same source/tool hashes; cache reuse; cancellation between frames discards partial output; one failed frame does not publish a partial strip; stale project/clip/playhead result discarded; no automatic FFmpeg launch and source media remains unchanged.

## Slice M — bounded audio waveform observation

Add an explicit user-triggered waveform observation for the selected video clip's matching original-role audio stream. The user-selected/trusted FFmpeg is reused; no audio file is written. Decode at most the first 60 seconds from the exact source stream/time interval to mono 8 kHz float32 PCM in a bounded owned process, validate finite samples and aggregate them into at most 256 min/max amplitude buckets. Source/tool hashes and stream/timing/sample policy form a bounded in-memory cache key. The waveform is a visual amplitude summary only; it is not playback, loudness metering, clipping analysis, audio/video synchronization, or an audio render. Stale clip/project/tool/playhead results are discarded and app close waits for worker retirement. Unknown process retirement locks the application session as in Slice K.

Tests: exact selected audio stream and decoder start, rational duration cap, PCM byte/sample limits, NaN/Inf rejection, deterministic bucket aggregation, source/tool hash and cache invalidation, process failure/cancel/unknown retirement, UI no-audio state, stale request discard, close wait, and original source bytes unchanged.

## Slice N — application-wide Settings navigation shortcut

Use Ctrl+, to focus the existing Preset/Cài đặt navigation page (index 7); do not create a second Settings window or duplicate settings model. A shared-registry KeyPress event filter is installed on the main-window widget tree. It is available from numeric inspectors, suppresses the registered chord while a text editor owns focus, and leaves QKeySequenceEdit capture available. It must not change project/session state. Test from navigation and a focused numeric inspector, and verify text-focus exclusion, navigation/page indices and project identity/revision. This is only navigation; P04-08 tool install/update/repair/Chrome/profile/account readiness remains incomplete.

## Slice O — focus-scoped timeline frame-navigation shortcuts

Bind Left/Right to one output frame, Shift+Left/Right to ten frames, and Home/End to the timeline bounds. A shared-registry KeyPress event filter is installed only on the clip list, its viewport, the timeline canvas and its viewport; crop/numeric inputs and text editors remain outside that scope. Navigation changes only playhead/UI state, not project revision. Tests cover frame bounds, exact step sizes, Home/End and native numeric-input isolation. Playback/spacebar, J/K/L transport and the complete ED§9 action map remain unimplemented.

## Slice P — still-preview quality selection and resolution-bound cache

Expose three explicit still-preview quality profiles: draft 320×180, standard 640×360 and high 1280×720. The selected dimensions are passed to the bounded FFmpeg worker and are already part of the frame-cache key; changing quality invalidates any in-flight/stale UI result but does not mutate project state or revoke the user's explicit FFmpeg trust. Filmstrip extraction uses the same selected quality. Unknown quality values fail closed. This is still-image decode quality, not a persistent encoded proxy or synchronized A/V seek.

Tests: each profile passes its exact bounds to the worker; changing quality during a running request discards its stale result; same source/time at different dimensions produces distinct cache entries; selection never changes project revision; cancellation/unknown retirement behavior is unchanged.

## Slice Q — persistent shortcut remapping, conflict detection and live rebinding

Provide a QSettings-backed user preference registry for the implemented shortcut subset. The searchable Settings panel lists action, focus scope and current binding; QKeySequenceEdit captures a replacement; save rejects empty/invalid sequences and collisions in overlapping scopes without modifying the previous binding; reset selected/reset all restore documented defaults. Project files do not contain user shortcut preferences. Layer tree/canvas event routing reads the registry dynamically and does not consume keys during IME preedit or from numeric inspector fields. Timeline and tool-inventory event filters read the registry at event time, so remapping applies immediately. The app Settings shortcut also updates live while respecting text-entry and key-capture focus. This is not the complete ED§9 map; only currently implemented actions may be offered as active bindings.

Tests: QSettings persistence across registry instances; same-scope and app-global conflict rejection; failed remap leaves old value; panel search/save/reset; live layer and timeline remapping without project revision change; inspector and IME focus isolation; no default action fires after remap.

## Slice R — transient timeline In/Out work-area markers

Add In and Out controls plus focus-scoped I/O/Escape shortcuts. In marks the current output frame; Out marks the exclusive boundary immediately after the current frame, producing a half-open [In, Out) range. Out requires an earlier In and must not exceed the project's frame count. Invalid changes leave the prior range unchanged. A translucent region and distinct IN/OUT lines are view-only state; they do not mutate CompositionPlan or increment project revision and are cleared when the project identity closes/changes. This is a work-area selection only: no loop playback or render-range behavior is claimed.

Tests: valid half-open range, one-frame range at final output frame, Out-before-In rejection, invalid Out rejection, clear/Escape, project identity reset, keyboard focus scope, and no project revision change.

## Slice S — F5 metadata-only tool inventory rescan

Bind F5 only to the tool inventory table and its child focus. It reuses the existing bounded background metadata scan, never launches a candidate executable, never grants trust, and never affects a real Chrome window. The action is registered in the shared shortcut preferences and can be remapped with the same conflict checks/live rebinding. Tests cover table-focus activation, no activation from unrelated settings/Chrome scope, live remapping and worker execution off the UI thread. This does not implement installation, update, repair, rollback or Chrome/account workflows.


## 2026-11-03 CI remediation slice — P04-07 shortcut routing

**Entry checkpoint:** `3f1ab9ff0a4923ad166190d998fafb71fd4f37e6`; workflow run `41573785927`.

**Observed evidence:** all four hosted source-suite runners failed with the same 10 tests. The logs identify a PySide6 enum conversion exception in `ShortcutRegistry.matches` (`int(KeyboardModifier)`), plus focus/activation failures in Settings, timeline, and tool inventory shortcuts and one case-sensitive Vietnamese assertion. This slice must correct the production enum conversion first, then re-run all four OS/Python combinations. Do not weaken IME handling, shortcut focus scopes, tool scan safety, or assertions. If independent focus failures remain after the enum correction, diagnose them from the next exact run before editing.

**Implementation:** use the documented integer `.value` of the masked Qt keyboard-modifier enum; preserve the portable QKeySequence comparison. Add/retain a direct regression for Control/Shift/Alt combinations and ensure existing layer, timeline, Settings, and F5 UI tests remain enabled.

**Acceptance:** targeted shortcut tests and full four-runner clean-foundation matrix pass on the resulting exact HEAD; all skipped platform checks remain separately reported. This slice does not accept P04-07 or P04 overall.


## 2026-11-03 CI remediation slice 2 — deterministic focus routing

**Entry checkpoint:** `fd1b097c125810f86e7b7895a1c20961c6d57d3a`; run `41576103614`. Four runners reduced the suite from 10 to 6 failures. Remaining failures: Ctrl+, app navigation, custom Alt+Ctrl layer remap, timeline frame/In-Out shortcuts, F5 table rescan, and a crop test that incorrectly expects Right Arrow to increment a QDoubleSpinBox.

**Root-cause direction:** Qt shortcut-map activation is not reliable for the current offscreen/hosted focus tests and fails to demonstrate the required target-widget focus scope. Replace QShortcut-only dispatch for Settings, timeline and tool inventory with explicit KeyPress event filters installed on the exact intended widgets and their viewport children. App Settings must be available across the main-window widget tree, including numeric inspectors, but must not steal registered chords from text editors or key-sequence capture. Timeline dispatch is restricted to clip-list/canvas widgets; crop spin boxes stay outside that filter. F5 dispatch is restricted to the tool table and viewport and continues to call only the existing bounded metadata worker. All routers read the shared registry at event time so remaps take effect immediately.

**Layer remap hardening:** preserve the existing layer-only router and IME preedit guard; clear stale preedit state on focus transitions and retain explicit Ctrl+Alt event coverage. No layer shortcut is installed on numeric inspectors or globally.

**Numeric-input test correction:** Qt spin boxes use Up/Down to change the numeric value; Left/Right move the text cursor. Keep a regression proving Left/Right do not move the timeline playhead and Up increments the focused numeric value. Do not change production spin-box semantics to satisfy an incorrect assertion.

**Acceptance:** retain all functional assertions; add event-filter tests for main-window scope/text-entry exclusion, timeline scope/crop isolation, tool-table scope/live remap, and layer Ctrl+Alt remap. Run targeted Qt tests, then all four hosted Linux/Windows Python 3.12/3.13 jobs on the exact resulting HEAD. No task or phase is accepted by this slice alone.


### Slice 2 refinement from hosted Windows evidence

Run `41577723521` passed Linux Python 3.12/3.13 (904 passed, 39 skipped each) and Windows Python 3.13 (917 passed, 26 skipped); Windows Python 3.12 had 916 passed, 26 skipped and one teardown assertion in `test_desktop_coordinator_host`. The host had already reported `isRunning() == false`, but the test called `wait(0)` only once and asserted immediately. Correct the helper to poll the actual `wait(0)` completion predicate within its existing five-second bound; retain the requirement that the native thread is joined before teardown.

Clarify application shortcut scope: Ctrl+, must work from the numeric inspector as required by Slice N. It does not collide with the spin box's native arrow keys. Continue suppressing it while a text editor or QKeySequenceEdit owns focus, including when Qt propagates a key event to a parent widget. The timeline's Left/Right and Up/Down numeric semantics remain isolated by the timeline's exact installed scopes.


### Exact hosted verification for deterministic focus routing — 2026-11-03

Current code checkpoint: `3e0efdc1b5a9fb4bf5fad978ed1345956463f663`. Clean-foundation run [41578597866](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41578597866) completed SUCCESS on all four runners:

| Runner | Passed | Skipped | Failed | Integrity |
|---|---:|---:|---:|---|
| Ubuntu / Python 3.12 | 904 | 39 | 0 | PASS |
| Ubuntu / Python 3.13 | 904 | 39 | 0 | PASS |
| Windows / Python 3.12 | 917 | 26 | 0 | PASS |
| Windows / Python 3.13 | 917 | 26 | 0 | PASS |

Windows Python 3.12 also completed the development onedir build and scoped frozen CLI boundary checks. The separate pinned Windows FFmpeg synthetic capability workflow was SKIPPED. This is hosted source/Qt and scoped packaged-boundary evidence, not physical user-device GUI, live Chrome, provider, GPU, codec-corpus, playback or render/export acceptance. No P04 task or phase is accepted.


## Slice T — P04-08 read-only profile/account metadata tables

**Dependencies:** P03-09 owned metadata repository exists as a partial local capability; no live Chrome/profile path or authenticated handoff is available. This slice consumes only persisted BrowserProfile/Binding observations and does not claim to create or control Chrome profiles.

**Input:** Existing user-data `accounts.sqlite3` created explicitly by the account domain. Missing store is a normal empty state, not permission to initialize it.

**Output/interface:** A third Settings tab with separate profile and platform-binding tables. Display profile label/ownership and last-recorded browser state; display platform identity, profile association, last-recorded web/bridge states, default binding and observation timestamps. Every status is labelled last-known metadata, not a live browser/authentication check. Do not display profile paths, credential references, cookies, passwords or session material.

**Storage boundary:** Add a read-only bounded snapshot API to AccountStore. It must return no-store when the file is absent without creating the parent/database/receipt; require regular non-reparse file identity, valid ownership receipt, exact application/schema identity and valid bounded payloads; reject active WAL/rollback-journal state rather than create sidecars or read stale data; open SQLite immutable/read-only; never migrate, initialize, register ownership, update defaults or write rows. Recheck file identity and stable metadata after reading. Cap profile/binding rows and report truncation explicitly.

**Lifecycle:** Read on a background QThread only after the user opens Settings or presses Refresh. Ignore stale completions, sanitize errors, and make MainWindow close wait for actual worker retirement. No Chrome process, network, cookie access, login prompt, profile-directory operation or account rebind is permitted in this slice.

**Regression/acceptance:** missing-store no-create; existing owned-store typed snapshot and byte/sidecar invariance; foreign/unmarked/corrupt/newer/WAL-active refusal without modification; bounds and default-binding integrity; Qt background-thread rendering, refresh, close/cancel and error state. This slice is partial P04-08 evidence only; AUTH-01.01, AUTH-04.01/.04 and live Chrome/profile/login/bridge gates remain NOT_RUN. Do not accept P04-08 or any AUTH group.


## Slice T hosted-test correction — P04-08 metadata tab containment

**Entry checkpoint:** `f7be849d6bd2cbc41fdb5e03e270488002ae06c3`; clean-foundation run `41581193827`.

**Observed failure:** the test `test_main_window_settings_tab_mounts_metadata_panel_without_creating_store` calls `window.account_metadata.parentWidget()` and expects that immediate parent to be a `QTabWidget`. Qt's QTabWidget reparents each tab page into its internal QStackedWidget, so the immediate parent is correctly a QStackedWidget even though the actual tab widget exists above it. The production shell already constructs the Settings tabs using QTabWidget and adds AccountMetadataPanel as the fourth tab. This is a test ancestry assumption, not a missing UI tab.

**Correction:** walk the QObject/widget parent chain to locate the containing QTabWidget, then assert the metadata panel's tab index and expected label. Preserve the existing main-window page index and missing-store no-create assertions. Do not replace the shell's eight-area QStackedWidget or remove the Settings QTabWidget.

**Acceptance:** targeted account metadata UI tests and all four clean-foundation runners pass on the exact resulting HEAD. P04-08 and P04 remain IN_PROGRESS; live Chrome/profile/login/bridge gates remain NOT_RUN.


## Slice U — persist timeline In/Out work-area markers (P04-05)

**Master alignment:** P04-05 timeline/playhead/trim/split/In-Out/marker; requirement ED-17 (especially ED-17.02/04); source contract `docs/EDITOR_SPEC.md` sections 7.1–7.2 and ED§9 shortcuts I/O/Escape. This is a narrow continuation, not whole P04-05 acceptance.

**Entry checkpoint:** `c91c3f86abee50fa082db0eab5aa453a486dda57`; exact clean-foundation run `41581386658` passed all four runners (Ubuntu 3.12/3.13: 913 passed, 39 skipped each; Windows 3.12/3.13: 926 passed, 26 skipped each). The pinned Windows FFmpeg synthetic workflow was skipped.

**Observed gap:** the existing In/Out range is held only in `TimelinePanel._in_frame/_out_frame`, resets on project switch/reopen and does not survive project-file save/open. The current UI correctly models a half-open frame interval but does not persist it.

**Design:** add an optional strict `timeline_range` object to CompositionPlan v1 for backward-compatible reads of existing plans. It stores integer output-frame boundaries `in_frame` and `out_frame` (nullable while the user has set only In); the interval is half-open `[In, Out)`. Validate against `ceil(output.duration × output.fps)`: In must identify an existing frame, Out must be in 1..frame_total, Out requires In, and Out must be greater than In. An empty range is represented by omitting the object. Do not alter project envelope/database schema versions or existing project files.

**Implementation:** I/O/Escape and the buttons issue one ordinary `CompletedCommand` revision through `ProjectSession.commit`; the shared plan is the single source of truth. Reopen reconstructs the markers from the validated plan. Saving the project file retains them. A failed/uncertain commit must not optimistically change UI state or replay the write. The selected range remains UI/export-range metadata within the composition; it does not mutate source media or trim clips.

**Tests:** legacy plan without `timeline_range`; valid In-only, final-frame Out, one-frame and multi-frame half-open ranges; reject Out without In, equal/reversed bounds, negative/out-of-range frame indices, bool-as-int and unknown fields; I/O/Escape persistence and clear; project-file save/close/reopen round-trip; marker display and project revision increments exactly once per completed marker command.

**Acceptance boundary:** this proves only persistent range selection and its validation. It does not implement arbitrary named timeline markers (M), loop playback, export-range rendering, synchronized A/V seek, continuous thumbnails or the full ED-17 group. P04-05/P04 remain IN_PROGRESS until all criteria and external gates pass.

### Slice U hosted verification — 2026-11-03

Implementation checkpoint: `ff86e797b662ca118189e7a19980d45bbdfdb4a5`. Clean-foundation run [41584573033](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41584573033) completed SUCCESS:

| Runner | Passed | Skipped | Failed | Integrity |
|---|---:|---:|---:|---|
| Ubuntu / Python 3.12.15 | 924 | 39 | 0 | PASS |
| Ubuntu / Python 3.13.17 | 924 | 39 | 0 | PASS |
| Windows / Python 3.12.10 | 937 | 26 | 0 | PASS |
| Windows / Python 3.13.17 | 937 | 26 | 0 | PASS |

Windows Python 3.12 also passed the development onedir build and scoped frozen CLI boundaries. Pinned Windows FFmpeg synthetic capability was SKIPPED. Tests used QT_QPA_PLATFORM=offscreen; no physical Windows GUI/IME/HiDPI/Explorer, real-media, GPU, Chrome/provider, playback, A/V sync or render/export acceptance.

P04-05 and P04 remain IN_PROGRESS; no ED-17 criterion or task is accepted by this slice.
## Slice V — persistent named timeline markers and M shortcut (P04-05/P04-07)

**Master alignment:** P04-05 timeline marker behavior; P04-07 focus-scoped shortcut behavior; source clauses ED-L125 (timeline marker), ED-L174 (M adds marker); child criteria ED-17.04 and ED-19.26. This is a partial slice, not whole task or criterion acceptance.

**Entry checkpoint:** `5af6ffdcdcd75a025f48760f438b7171b1847bdb`; clean-foundation run `41585646476` passed all four runners. The prior exact code checkpoint `ff86e797b662ca118189e7a19980d45bbdfdb4a5` also verified persisted In/Out range selection.

**Observed gap:** the timeline supports persisted In/Out range selection and frame navigation but has no independent named marker object or M action, although ED§7 and ED§9 require markers.

**Design:** add optional `timeline_markers` to CompositionPlan v1. Each marker has a globally unique UUID, one output-frame index and a bounded non-empty label; cap at 1000 markers and allow at most one marker per frame in this slice. Existing plans without the field remain valid. Marker IDs/labels/positions are navigation/editor metadata and must be excluded from `render_content_digest`; the In/Out work area remains render-range input and stays included.

**UI/behavior:** add marker at the current playhead with default labels M1, M2…; show markers in the timeline scene and a selectable list; selecting a marker seeks the playhead without changing the project; remove the selected marker explicitly. The M shortcut is registered/remappable and dispatched only from Timeline list/canvas scopes; it must not activate from crop/text/key-sequence inputs. Every add/remove is one CompletedCommand revision. Save/open restores markers. Source media is never modified.

**Tests:** legacy plan without markers; valid first/final-frame markers; reject bool/out-of-range/duplicate-frame/duplicate-ID/blank/control-character/overlong/unknown-field data; adding/removing markers leaves render-content digest unchanged; M focus scope and live remap; selection seeks without project revision; add/save/close/reopen/remove round-trip and one revision per mutation.

**Acceptance boundary:** this slice does not implement loop playback, marker editing/dragging, export markers as render instructions, continuous thumbnails/waveform or synchronized A/V seek. ED-17.04 and ED-19.26 remain NOT_RUN until all their assertions and required GUI evidence are met. P04-05/P04 remain IN_PROGRESS.

**Implementation and hosted verification — 2026-11-03:** optional CompositionPlan timeline_markers is implemented with UUID, output-frame and label fields, a 1000-item cap, unique global IDs/frames, output-boundary checks, trimmed non-control labels and an 80-character limit. The M shortcut is remappable and routed only in Timeline list/canvas scopes. The timeline supports add, list/display, select-to-seek without project revision, remove, and project save/reopen. Marker metadata is excluded from render_content_digest but retained in execution_digest.

Regression tests cover optional legacy compatibility, digest behavior, malformed/out-of-range/duplicate/overlong markers, the 1000/1001 collection boundary, M text-field isolation, live remapping, save/reopen, selection and deletion.

Exact hosted clean-foundation run 41588026020 passed on HEAD fad21b7a1a1b77e5e967145721b6974e8f7375bd: Ubuntu Python 3.12.15/3.13.17 each 938 passed, 39 skipped, 0 failed; Windows Python 3.12.10/3.13.17 each 951 passed, 26 skipped, 0 failed; integrity PASS all four. Windows Python 3.12 onedir build and scoped frozen CLI boundaries PASS; pinned Windows FFmpeg synthetic capability workflow SKIPPED.

This remains partial hosted offscreen Qt evidence. It does not certify physical Vietnamese/Chinese IME, Windows user-device GUI, loop playback, marker rename/drag, continuous thumbnails/waveform, synchronized A/V seek, export-range rendering or the complete ED-17/ED-19 assertions. No task/criterion/phase acceptance is claimed.
## Slice X — layer inspector slider synchronization and reset controls (P04-01)

**Master alignment:** P04-01 inspector numeric/slider/reset; requirements ED-01.02/.03 and source clauses PR-L029, ED-L009, ED-L033. This is a partial inspector slice, not full P04-01 or ED-01 acceptance.

**Entry checkpoint:** integrated HEAD 11b5dc6d2706240cb511ee47a27f520bc2c7146b on develop/fonesi-full. Latest exact clean-foundation run 41588961987 passed all four Linux/Windows Python 3.12/3.13 runners; Windows 3.12 onedir and scoped frozen boundaries passed. Main remains unchanged.

**Observed gap:** LayerEditorWorkspace exposes numeric QDoubleSpinBox controls but no paired sliders or per-property/group reset. P04-01 and ED-L009 explicitly require numeric controls alongside sliders and reset controls.

**Design:** preserve the existing spin-box API and canonical rational model. Add a bounded QSlider for each numeric transform property (x, y, width, height, scale_x, scale_y, rotation, opacity) with explicit integer-to-domain scaling. Spin edits commit on editingFinished. Mouse slider drags update the spin continuously but commit exactly once on slider release; keyboard slider steps commit one completed command per step. Programmatic refresh must block feedback and never mutate the project.

**Reset behavior:** each numeric property gets an explicit reset action to its documented layer default; anchor and flip controls also get individual reset actions; one group reset restores the complete default transform in one ProjectSession revision. Reset on an already-default value is a no-op. Locked layers, no selection, multi-selection and reconciliation-required sessions must keep inspector edits/sliders/resets disabled.

**Tests:** numeric spin↔slider round-trip; mouse drag multiple values produces one project revision; keyboard slider step produces one revision; per-property reset preserves unrelated rational fields; group reset restores x/y/width/height/scale/rotation/opacity/anchor/flip; default reset is no-op; lock and selection states disable both sliders and reset controls; undo/redo and save/reopen preserve the committed transform.

**Acceptance boundary:** this slice does not implement Basic/Advanced mode, property search, complete tooltip/disabled-reason coverage, theme/font-size/HiDPI persistence, multi-file Explorer drag/drop or physical Windows GUI/HiDPI acceptance. ED-01.02/.03 and P04-01 remain NOT_RUN/IN_PROGRESS until their full assertions and GUI evidence are complete.

**Implementation and hosted verification — 2026-11-03:** each numeric transform property now has a bounded QSlider paired with its QDoubleSpinBox, explicit units/range labels and a per-property reset. Anchor and flip fields have individual resets; a group reset restores the complete default transform. Slider drags update the numeric value continuously but commit one ProjectSession revision on release; keyboard slider steps commit one revision each. Programmatic refresh is feedback-blocked; locked/no-selection/multi-selection/reconciliation states disable sliders and reset controls.

Regression tests cover slider/spin synchronization, one commit per drag, keyboard step commits, per-property reset preserving unrelated rational values, full group reset/no-op reset, anchor/flip reset and locked-control disablement.

Exact hosted clean-foundation run 41589895118 passed on HEAD 78ff11a8fb45e08dc9806b015e5f2f94475476db: Ubuntu Python 3.12.15/3.13.17 each 941 passed, 39 skipped, 0 failed; Windows Python 3.12.10/3.13.17 each 954 passed, 26 skipped, 0 failed; integrity PASS all four. Windows Python 3.12 onedir build and scoped frozen CLI boundaries PASS; pinned Windows FFmpeg synthetic capability workflow SKIPPED.

This is hosted offscreen Qt evidence only. It does not certify physical Windows GUI, HiDPI, Explorer drag/drop, IME, theme/layout persistence, or full ED-01.02/.03 assertions. P04-01/P04 remain IN_PROGRESS; no task/criterion/phase acceptance is claimed.
## Slice Y — Basic/Advanced inspector mode, property search and actionable disabled reasons (P04-01)

**Master alignment:** P04-01 panel/property inspector and requirements ED-01.02/.03/.04; source clauses PR-L029, ED-L009 and ED-L033. This is a partial inspector usability slice, not full ED-01 or P04-01 acceptance.

**Entry checkpoint:** integrated HEAD 0871679fa972d20bad387a270c971cdbd7456da4 on develop/fonesi-full. Clean-foundation run 41592562955 passed all four Linux/Windows Python 3.12/3.13 runners; Windows 3.12 onedir build and scoped frozen CLI boundary checks passed. Main remains unchanged.

**Observed gap:** numeric/slider controls and resets exist, but the inspector has no Basic/Advanced mode, no property search and no explicit actionable reason explaining disabled edits.

**Design:** Basic mode shows common transform controls (X, Y, width, height and opacity). Advanced mode additionally exposes scale X/Y, rotation, anchor and flips. A Vietnamese search field filters all inspector properties by stable key, label and common term; a matching advanced property may be revealed by search even when Basic mode is active, so search never returns an apparently empty result solely because of mode.

**Disabled reasons:** a dedicated status label must explain the current edit gate: no project, project reconciliation required, no selected layer, multiple selected layers, or locked transform. It must distinguish these states from an editable single-layer selection. Each disabled spin box, slider and reset button receives a matching Vietnamese tooltip/reason; numeric labels continue to expose normalized frame units, multiplier, degrees and opacity range.

**Tests:** Basic default visibility; Advanced reveals advanced fields; search filters by Vietnamese label and stable property key; search can find an advanced field from Basic mode; clearing search restores mode visibility; tooltips and units are present; disabled reason changes for no project/no selection/multi-selection/locked layer; locked/no-selection/multi-selection controls remain disabled; selecting one unlocked layer restores editability; reset and slider behavior remains unchanged.

**Acceptance boundary:** this slice does not implement persistent Basic/Advanced preference, full property catalog/search across all future effect panels, theme/font-size/HiDPI persistence, multi-file Explorer drag/drop, complete tooltip/disabled-reason mapping outside the layer inspector or physical Windows GUI acceptance. ED-01.02/.03/.04 and P04-01 remain NOT_RUN/IN_PROGRESS until full requirements and external GUI evidence are met.

**Implementation and hosted verification — 2026-11-03:** Basic mode shows X/Y/width/height/opacity; Advanced reveals scale X/Y, rotation, anchor and flips. Vietnamese search matches stable property keys and labels, including an advanced field while Basic mode is active. A dedicated reason label distinguishes no project, reconciliation required, no selection, multi-selection, locked transform, shutdown and editable single-layer state. Spin boxes, sliders, numeric resets, anchor/flip controls and group reset expose the current reason in Vietnamese tooltips; unit/range labels remain explicit.

Worker retirement hardening: PreferenceWorker and InventoryWorker completion handlers now use bound QObject slots with QueuedConnection so all QWidget/model updates occur on the GUI thread. Regression coverage asserts preference completion runs on the QApplication thread.

Regression tests: test_inspector_basic_advanced_search_units_and_tooltips; test_inspector_disabled_reasons_follow_multi_selection_and_lock; test_inspector_slider_drag_commits_once_and_keyboard_step_commits_once; test_inspector_property_and_group_resets_commit_once_and_preserve_other_fields; test_anchor_and_flip_individual_resets_restore_only_selected_property; and test_unknown_commit_requires_matching_owned_reload_not_replay.

Exact hosted clean-foundation run 41594109888 (https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41594109888) completed SUCCESS on HEAD 1038d0afa91bddcaca45fc00c832247451da19cb: Ubuntu Python 3.12.15/3.13.17 each 943 passed, 39 skipped, 0 failed; Windows Python 3.12.10/3.13.17 each 956 passed, 26 skipped, 0 failed; integrity PASS all four. Windows Python 3.12 onedir build PASS and frozen schema/subtitle/read-only tool-discovery/license boundary checks PASS (5 cases). The pinned Windows FFmpeg synthetic capability workflow was SKIPPED.

Scope limits: hosted Qt tests used offscreen mode. This does not certify physical Windows Explorer, HiDPI, IME, theme/layout persistence or multi-file drag/drop. Basic/Advanced preference is not persisted. ED-01.02/.03/.04 remain NOT_RUN; P04-01/P04 remain IN_PROGRESS. No task/criterion/phase acceptance is claimed.
## Slice Z — bounded multi-file Explorer drop queue with explicit one-at-a-time import (P04-01)

**Master alignment:** P04-01 Explorer multi-drag and media-library import; source clauses ED-L136 and PR-L029. This slice adds a bounded selection queue only; it does not claim batch media import or physical Explorer acceptance.

**Implementation checkpoint:** final code HEAD 2cc8a50dad9fa1ceb9c89c6a52857a814761393b on develop/fonesi-full; exact hosted clean-foundation run 41599687098 passed all four Linux/Windows Python 3.12/3.13 runners. Main remains unchanged at e514b51d764d972fbf7c018e0dbdbdf964ece267.

**Observed gap:** the existing LocalMediaPathEdit accepts exactly one local regular file. Multiple Explorer items are rejected, so there is no bounded review queue or per-item refusal state.

**Design:** add a separate LocalMediaDropQueue list that accepts up to 64 local file URLs per drop/session. Validate each path independently: absolute local path, UTF-8 and path-length bounds, regular file only, no symlink/reparse point, no directory, no UNC/network URL. Deduplicate normalized path identities. Each accepted item is displayed as pending explicit selection; each invalid/duplicate/overflow item is retained as a visible refusal row with a short reason and full path in its tooltip. The existing one-file source selector remains compatible.

**Safety and interaction:** dropping never runs ffprobe, changes project/library revision or copies/modifies source files. The user selects one valid queued item and explicitly chooses 'Dùng tệp đã chọn' to populate the existing single-source field; the existing explicit trust checkbox and 'Kiểm tra và thêm' action remain mandatory. Import remains one file per worker, preventing concurrent writer/process ambiguity. Queue is bounded and ephemeral, not project data.

**Tests:** two or more valid files populate separate queue rows without import; mixed valid/remote/directory/missing/reparse items retain valid rows and visibly refuse invalid ones; duplicates and >64 entries are bounded; selecting a queued item only populates the source field; project revision/library and source bytes remain unchanged until explicit import; existing one-file LocalMediaPathEdit behavior remains unchanged; busy/close disables queue interaction.

**Acceptance boundary:** this slice does not implement batch/parallel import, directory recursion, network shares, physical Windows Explorer drag/drop, file-format/codec support or full P04-01 acceptance. ED-L136 and P04-01 remain NOT_RUN/IN_PROGRESS until real Windows Explorer multi-select, HiDPI and unsupported-item behavior are tested on a user device.

**Implementation and hosted verification — 2026-11-03:** `LocalMediaDropQueue` accepts up to 64 valid local regular files, deduplicates NFC/normcase-normalized paths, and keeps refusal rows for remote URLs, missing files, directories, symlinks/reparse points, duplicate paths and overflow. The list is bounded to 128 visible rows with an explicit overflow summary; each refused local item exposes its normalized full path in the tooltip without echoing URL credentials/query tokens. NUL, UNC, UTF-8 and path-length checks are applied before queueing. The existing one-file source selector remains unchanged. Selecting a queue row only populates that selector; the user must still explicitly trust the selected ffprobe and press the import button. Queue actions are disabled while an owned media worker is active or the panel is stopping/revoked.

Regression coverage: test_multiple_local_file_drop_queues_without_import_until_explicit_selection; test_mixed_multi_file_drop_keeps_valid_item_and_marks_unsupported_items; test_drop_queue_deduplicates_and_caps_valid_files; test_drop_queue_rejects_nul_and_unc_paths_before_filesystem_access; test_drop_queue_keeps_visible_bounded_overflow_summary; test_directory_and_missing_file_drop_are_refused; test_symlink_drop_is_refused_when_platform_can_create_symlinks; and the busy-state assertions in test_cancel_during_owned_probe_does_not_mutate_project.

Exact hosted clean-foundation run [41599687098](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41599687098) completed SUCCESS on HEAD `2cc8a50dad9fa1ceb9c89c6a52857a814761393b`: Ubuntu Python 3.12.15/3.13.17 each 948 passed, 39 skipped, 0 failed; Windows Python 3.12.10/3.13.17 each 961 passed, 26 skipped, 0 failed; integrity PASS all four. Windows Python 3.12 development onedir build PASS and frozen schema/subtitle/read-only tool-discovery/license boundary checks PASS (5 cases). The pinned Windows FFmpeg synthetic capability workflow was SKIPPED.

Scope limits: drag/drop was tested with synthetic Qt QMimeData events on hosted offscreen runners, not physical Windows Explorer. This does not certify Windows Explorer multi-select, HiDPI/mixed-DPI, network shares, directory recursion, codec support or actual media validity. The queue is a temporary selection aid, not batch/parallel import. ED-L136 and P04-01 remain NOT_RUN/IN_PROGRESS; no task or phase acceptance is claimed.
## Slice Z — bounded multi-file Explorer drop queue with explicit one-at-a-time import (P04-01)

**Master alignment:** P04-01 Explorer multi-drag and media-library import; source clauses ED-L136 and PR-L029. This slice adds a bounded selection queue only; it does not claim batch media import or physical Explorer acceptance.

**Entry checkpoint:** code HEAD 1038d0afa91bddcaca45fc00c832247451da19cb on develop/fonesi-full. Clean-foundation run 41594109888 passed all four Linux/Windows Python 3.12/3.13 runners. Documentation/evidence checkpoint 055249da73533afad0f5b6d384a4cc04a0fdcda1 also passed clean-foundation run 41595185031 on all four runners; main remains unchanged.

**Observed gap:** the existing LocalMediaPathEdit accepts exactly one local regular file. Multiple Explorer items are rejected, so there is no bounded review queue or per-item refusal state.

**Design:** add a separate LocalMediaDropQueue list that accepts up to 64 local file URLs per drop/session. Validate each path independently: absolute local path, UTF-8 and path-length bounds, regular file only, no symlink/reparse point, no directory, no UNC/network URL. Deduplicate normalized path identities. Each accepted item is displayed as pending explicit selection; each invalid/duplicate/overflow item is retained as a visible refusal row with a short reason and full path in its tooltip. The existing one-file source selector remains compatible.

**Safety and interaction:** dropping never runs ffprobe, changes project/library revision or copies/modifies source files. The user selects one valid queued item and explicitly chooses 'Dùng tệp đã chọn' to populate the existing single-source field; the existing explicit trust checkbox and 'Kiểm tra và thêm' action remain mandatory. Import remains one file per worker, preventing concurrent writer/process ambiguity. Queue is bounded and ephemeral, not project data.

**Tests:** two or more valid files populate separate queue rows without import; mixed valid/remote/directory/missing/reparse items retain valid rows and visibly refuse invalid ones; duplicates and more than 64 entries are bounded; selecting a queued item only populates the source field; project revision/library and source bytes remain unchanged until explicit import; existing one-file LocalMediaPathEdit behavior remains unchanged; busy/close disables queue interaction.

**Acceptance boundary:** this slice does not implement batch/parallel import, directory recursion, network shares, physical Windows Explorer drag/drop, file-format/codec support or full P04-01 acceptance. ED-L136 and P04-01 remain NOT_RUN/IN_PROGRESS until real Windows Explorer multi-select, HiDPI and unsupported-item behavior are tested on a user device.
## Slice AA — persistent appearance, UI zoom and window layout (P04-01)

**Master alignment:** P04-01 native panel/theme/HiDPI/font-size/layout persistence; product requirement PR-L029 and the P04-01 task contract. This is a user-preference persistence slice, not full P04-01 or physical Windows HiDPI acceptance.

**Entry checkpoint:** integrated HEAD 026342d4dbde1859a780603085ff81c0be36acd7 on develop/fonesi-full. Exact clean-foundation run 41600507531 passed all four Linux/Windows Python 3.12/3.13 runners; main remains unchanged.

**Design:** add an Appearance settings panel backed by QSettings under an isolated `appearance/` key group. Theme options are System, Light and Dark; font size is a bounded allow-list (9, 10, 11, 12, 14, 16 pt); application zoom is a bounded allow-list (100, 110, 125, 150%). Changes apply immediately and persist only after successful QSettings sync. Reset removes only the appearance group and must preserve shortcuts, tool preferences, account metadata and window state.

**HiDPI contract:** Qt 6 continues to consume the operating-system/device pixel ratio automatically. The application zoom setting changes application font and control spacing; it must not set QT_SCALE_FACTOR late, override Windows display scaling or claim to change the monitor's OS DPI. Physical mixed-DPI/multi-monitor verification remains external.

**Window layout persistence:** persist bounded `saveGeometry`/`saveState` blobs, selected navigation area, Editor tab and Settings tab. Restore only valid bounded QByteArray state; corrupt/oversized geometry/state is ignored and defaults remain usable. Save only after the main window close is accepted (not while background workers keep close pending). No project document or media data is stored in QSettings.

**Tests:** allow-listed settings save/reopen; invalid settings fallback; live palette/font/zoom changes; reset appearance without deleting shortcut/window keys; main-window geometry/navigation/tab save-close-reopen; corrupt/oversized geometry fallback; pending close does not persist an unaccepted layout; default system palette can be restored after Dark/Light.

**Acceptance boundary:** this slice does not certify physical Windows Explorer, mixed-DPI monitor movement, OS high-contrast, per-monitor scaling transitions or Windows user-device layout. It does not persist Basic/Advanced inspector mode (tracked separately), nor implement a complete future effect-property catalog. ED-01.01/.02/.03 and P04-01 remain NOT_RUN/IN_PROGRESS until the complete requirement map and physical GUI evidence are met.

## Slice AB — persist Basic/Advanced Inspector mode (P04-01)

**Status before implementation:** planned as the next bounded P04-01 slice; existing Inspector mode is session-only.  
**Master alignment:** P04-01 (panel/UI preferences) and P04-04 (UI state must not mutate the project model).  
**Dependencies:** existing `MainWindow.ui_settings` QSettings instance; no new dependency or schema migration.

### Contract

- Input: the user's Basic/Advanced selection in the layer Inspector.
- Output: a boolean user-interface preference stored under the dedicated `editor/inspector_advanced` key in the existing user QSettings store.
- Default: Basic mode when the key is absent or malformed.
- Lifecycle: load the preference when the Editor workspace is constructed; persist only when the user changes the checkbox; a subsequent MainWindow/Editor construction restores it.
- Isolation: do not write the preference to CompositionPlan, ProjectStore, autosave, undo history or project files. Switching projects must not change it. Appearance reset must not clear it.
- Failure behavior: a QSettings write error must not change the in-memory UI mode into a false persisted-success claim; show/retain the selected state with no project mutation, and do not crash the Editor.
- Compatibility: callers that construct LayerEditorWorkspace without an explicit settings object continue to receive the Basic default; existing project files remain byte-compatible.

### Implementation

1. Pass the existing MainWindow user settings object into LayerEditorWorkspace.
2. Read and validate the allow-listed boolean setting before the first inspector filter pass.
3. Connect user toggles to a small persistence handler; keep search/filter operations side-effect free.
4. Keep the preference outside project/session command paths.

### Tests and acceptance

- Default Basic mode when no key exists.
- Persist Advanced and restore it in a newly constructed MainWindow.
- Persist Basic after switching back and restore it on the next construction.
- Malformed stored value falls back to Basic.
- Switching/opening projects does not change the preference or project revision.
- Appearance reset does not remove the Inspector mode key.
- Existing callers without injected settings retain backward-compatible defaults.
- Run focused Inspector/UI tests, `scripts/check_plan.py`, then the exact four-runner clean-foundation workflow. Hosted/offscreen tests do not replace physical Windows GUI/HiDPI acceptance.

### Artifacts

- `src/fonesi_edit/ui/layer_editor.py`
- `src/fonesi_edit/ui/shell.py`
- `tests/test_layer_editor_ui.py`
- `tests/test_appearance_settings.py`
- `docs/phases/P04_RESULTS.md` and `docs/CURRENT_STATUS.md` after exact CI evidence.

### Acceptance boundary

This slice can close only its own local implementation contract after tests and CI pass. It does not accept P04-01 or P04, and it does not establish physical Windows GUI/IME/HiDPI behavior.


## Slice AC — accessible names and keyboard-facing Inspector controls (P04-01)

**Status before implementation:** numeric Inspector controls and reset actions exist; accessible naming is only partially applied to search, reset buttons and the overall disabled-state label.  
**Master alignment:** P04-01 panel/inspector usability; P04-07 focus and keyboard semantics.  
**Dependencies:** existing Qt Inspector widgets and translated Vietnamese property labels.

### Contract

- Every editable transform spin box and paired slider has a stable, localized accessible name that identifies the property and unit.
- Anchor combo and horizontal/vertical flip checkboxes have explicit accessible names and concise help text.
- Basic/Advanced toggle exposes its checked state through the native checkbox semantics and retains its existing tooltip.
- Every reset action has an accessible name and a tooltip describing the affected property; reset-transform remains a separate group action.
- Names must not depend on widget objectName, internal snake_case IDs, or visual label association alone.
- No behavior, command count, project revision, or stored CompositionPlan field changes from adding accessibility metadata.
- Existing keyboard editing, focus routing, IME guard and disabled-reason behavior remain unchanged.

### Implementation

1. Apply localized accessible names to each spin box and slider using the existing Vietnamese field label and unit.
2. Apply names/help text to anchor, flip controls and group reset.
3. Add Qt tests asserting names are non-empty, distinct, localized and mapped to the correct property; assert controls remain enabled/disabled under existing lock and selection states.
4. Run focused Inspector tests, plan integrity and exact four-runner CI.

### Acceptance boundary

This slice verifies programmatic accessibility metadata and existing keyboard semantics in hosted Qt tests. It does not claim screen-reader certification, physical Windows accessibility inspection, HiDPI or IME acceptance, and it does not close P04-01/P04.


## Slice AE — reject non-finite canvas geometry (P04-02)

**Scope:** harden the existing canvas resize, rotate and drag command boundary. This is an input-validation slice; it does not add a new rendering capability.

- Reject NaN and positive/negative infinity for resize width/height, normalized anchor coordinates, rotation angle and drag positions before converting values to rational model fields.
- Reject zero/negative resize dimensions.
- On rejection, preserve the canonical CompositionPlan and ProjectSession revision; refresh the view from the authoritative project model and show a localized reason.
- Valid edits continue through the existing single CompletedCommand CAS path.
- Tests cover non-finite resize dimensions/anchor points and rotation, plus all nine anchor positions retaining their anchor coordinates after a valid resize.
- Regression suite includes tests/test_layer_canvas_handles.py, tests/test_layer_canvas_guides.py, tests/test_layer_canvas_drag.py and existing transform precision/lock tests.
- Acceptance is limited to finite-value model safety and synthetic Qt tests. Physical drag, display scaling, preview/render parity and target-device interaction remain external/open.


## Slice AF — interactive normalized crop overlay (P04-02)

**Master source:** EDITOR_SPEC.md §2.2, especially crop grid, locked ratio, outside-area shading and explicit confirm/cancel. **Task:** P04-02; depends on P04-01 UI state and the existing canonical clip crop model.

### Contract
- Render the user-requested still source frame in a dedicated crop-edit surface. The surface is a crop geometry editor, not a composition preview or renderer.
- Display the current normalized clip crop rectangle over the still frame, shade the outside region, and draw optional thirds-grid guides and resize handles.
- Allow dragging the crop rectangle and its eight handles; clamp all edges to the source frame and reject zero/near-zero extents. Keep the selected clip and crop revision pinned during the gesture.
- Optional ratio lock preserves the crop's starting aspect ratio. The lock is a UI gesture constraint, not a change to the clip's canonical crop schema.
- Gesture edits are staged only in UI memory. Confirm commits one normalized crop update through the existing ProjectSession CAS; Cancel restores the last committed crop. No source bytes are changed.
- A stale project revision refuses the staged crop and reloads authoritative values. Switching clip or invalidating the still preview discards pending geometry.
- Numeric crop fields remain available and use the same canonical crop representation.

### Tests and acceptance
- Pure geometry tests for move/edge/corner resize, clamping, minimum extent, ratio lock and portrait/landscape pixmap fitting.
- Qt tests for staged drag, confirm exactly one project revision, cancel zero revisions, stale revision refusal, selection change discard, and save/reopen equality.
- Existing tests/test_timeline_crop_zoom.py must remain valid or be updated to the explicit apply/cancel semantics with equivalent assertions.
- Exact four-runner clean-foundation CI and plan integrity. Hosted/offscreen tests do not prove physical mouse/HiDPI or crop renderer parity.

### Acceptance boundary
- This slice edits canonical normalized crop geometry only. It does not render/crop the video, prove frame parity, create proxy media, or export. Crop compositor/export parity remains open for P07/P11.


## Slice AG — crop gesture cancellation and ratio-safe source boundaries (P04-02)

**Scope:** harden the existing Slice AF crop overlay without replacing its still-frame-only behavior.

### Contract

- Escape during an active pointer gesture restores the exact starting normalized crop and emits no staged change.
- Turning crop edit mode off during a gesture cancels that gesture; a later mouse release cannot stage it.
- Press/release without pointer movement is a no-op and emits no crop change.
- Ratio-locked resize must preserve the starting width/height ratio even when the source-frame boundary limits the requested size. The handle may stop before the pointer if further movement would violate the ratio or source bounds.
- All crop coordinates remain within [0,1], width/height remain positive, and source media/project state are unchanged until explicit Confirm.
- Add accessible name/description and keyboard focus to the crop surface.

### Tests and verification

- Qt offscreen tests for Escape, disabling edit mid-drag, no-op click and ratio-locked edge resize at source boundary.
- Existing crop move, corner resize, source clamp, Confirm/Cancel, stale revision, clip switch and save/reopen tests remain enabled.
- Run `tests/test_crop_overlay.py`, `tests/test_timeline_crop_zoom.py`, plan integrity and exact four-runner CI.
- Physical mouse, HiDPI and Windows end-user interaction remain external acceptance gates.

### Acceptance boundary

This slice validates safe staging and normalized geometry only. It does not add decoded-pixel crop composition, playback or export parity, and does not accept P04-02/P04.


## Slice AH — focus-scoped pixel-step layer nudge (P04-02/P04-07)

### Contract

- With a single unlocked layer or a selected unlocked group and canvas focus, arrow keys move the selected object(s) by exactly one output pixel in normalized project coordinates; Shift+arrow moves exactly ten output pixels.
- The nudge is independent of canvas zoom, viewport size and device pixel ratio because the delta is derived from CompositionPlan output width/height, not widget coordinates.
- One key press commits exactly one ProjectSession CompletedCommand revision. Auto-repeat is consumed to avoid unbounded repeated commands unless an explicit repeat policy is added later.
- Shortcuts are installed only on the canvas/viewports, not the layer list or numeric inspector; list navigation and spin-box editing retain native behavior.
- If there is no selection, the project is reconciling/stopping, or any selected target is transform-locked, no project mutation occurs.
- Group selection uses the same atomic normalized delta for every member and one project revision.
- New defaults use the existing remappable shortcut registry and must not conflict with timeline arrow navigation because scopes are disjoint.

### Tests

- Exact one-pixel and ten-pixel normalized deltas for portrait and landscape output.
- Same output-pixel movement at two canvas zoom levels / viewport sizes.
- Group nudge is atomic and preserves relative offsets.
- Locked/missing selection and key auto-repeat do not mutate the project.
- Layer tree arrow keys remain native; numeric inspector arrow keys remain native.
- Run focused shortcut/layer tests, plan integrity and exact four-runner CI.

### Acceptance boundary

This slice implements positional keyboard nudging only. It does not add text/logo content editing, snap guides for keyboard movement, preview/export parity or physical HiDPI/IME certification.


## Slice AI — complete single-layer handle hit testing and deferred callback ownership (P04-02)

### Contract

- Every one of the eight resize handles and the rotation handle must be included in the selected layer's actual QGraphicsItem hit-test shape, not merely painted.
- Hit-test geometry must remain aligned with the visible handle after the layer's normalized transform, rotation and canvas zoom.
- Locked layers and group multi-selection continue to hide/disable individual handles; their model cannot be mutated through a hidden handle.
- Resize/rotate/move completion callbacks are dispatched on the owning LayerEditorWorkspace QObject context. If the Editor is destroyed before the queued callback is dispatched, Qt must discard the callback rather than invoke a stale QGraphicsItem/editor reference.
- A completed handle gesture still produces one ProjectSession CAS command. No source media or unrelated layer is changed.

### Tests

- Scene hit-test all eight resize handle centers and the rotation handle on a selected unlocked layer.
- Confirm locked and group-selected layers do not expose individual handles to scene hit testing.
- Verify callbacks use the bound editor QObject context; widget teardown with a queued callback must not invoke a deleted object.
- Keep existing normalized resize, rotation, non-finite input, nine-anchor preservation, lock and one-command tests.
- Run focused canvas tests, plan integrity and exact four-runner CI.

### Acceptance boundary

This slice validates Qt hit-test and callback ownership for geometry controls only. It does not certify physical Windows pointer/HiDPI interaction, text/logo editing, decoded crop compositor or renderer/export parity.


## Slice AJ — end-to-end Qt pointer gestures for single-layer resize and rotation (P04-02)

### Contract

- Exercise the actual QGraphicsView viewport event path, not only direct calls to `resized`/`rotated`.
- A pointer drag on a visible resize handle changes normalized width/height and commits exactly one ProjectSession revision on release.
- A pointer drag on the rotation handle changes the normalized rotation around the layer's position/anchor and commits exactly one revision on release.
- The gesture remains one command regardless of intermediate mouse-move events.
- Locked and multi-selected layers do not expose handles; clicks on those handle locations must not change the project model.
- Callback dispatch remains bound to the owning Editor QObject and no queued operation runs after editor teardown.

### Tests

- Qt offscreen QTest press/move/release through the real view viewport for a corner resize.
- Qt offscreen QTest press/move/release through the real view viewport for an off-center rotation.
- Assert exact project revision delta (one per completed gesture), canonical normalized dimensions/rotation and unchanged anchor position.
- Keep scene hit-test coverage for all eight resize handles and the rotation handle.
- Run focused canvas handle tests, plan integrity and exact four-runner CI.

### Acceptance boundary

These are synthetic Qt event-path tests, not physical Windows mouse/HiDPI acceptance. They do not prove preview/export geometry parity or a rendered crop/text/logo result.


## Slice AK — anchor-preserving interactive resize geometry (P04-02)

### Finding from Slice AJ
The real viewport event path exposed a production geometry defect: resizing the southeast handle while the transform anchor is centered expanded the rectangle from one edge but then moved the canonical anchor position. Direct model-level resize tests had not exercised this pointer-path invariant. The failure is not resolved by loosening expected coordinates.

### Contract
- The selected transform anchor remains at the exact same scene position through every completed resize gesture.
- Resize dimensions are derived from handle direction, pointer delta and anchor alignment:
  - left/right and top/bottom anchors keep the anchor-side edge fixed;
  - center anchors expand symmetrically, so a handle displacement changes the corresponding full extent by twice that displacement;
  - dragging the handle coincident with the selected anchor does not change that axis.
- The updated local rectangle is reconstructed from the canonical anchor offset, not by stretching one edge and inferring a new anchor position afterward.
- Minimum extent is bounded and geometry never flips through zero.
- One gesture still commits one ProjectSession revision; cancel/locked/group behavior remains unchanged.
- The test oracle derives the requested delta from integer viewport coordinates mapped back to scene coordinates. It does not use arbitrary tolerance to hide a geometry defect.

### Tests
- Real QGraphicsView viewport resize on a centered anchor preserves canonical x/y and changes width/height symmetrically.
- Real viewport resize across all nine anchors preserves the local origin/scene anchor; test each available opposite handle direction.
- Handle coincident with anchor is a no-op on that axis.
- Minimum-size clamping and invalid/locked/group refusal remain intact.
- Existing real viewport rotation test compares to the exact angle implied by quantized viewport endpoints.
- Run focused canvas tests, plan integrity and exact four-runner CI.

### Acceptance boundary
This fixes normalized layer geometry interaction only. It does not implement text/logo content, source-video crop compositing, preview/export parity or physical Windows pointer/HiDPI acceptance.
