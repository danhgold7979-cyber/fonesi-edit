# P04 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-04`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P04-01 — panel/theme/HiDPI/cỡ chữ UI, drag từ Explorer, media/inspector, slider/ô số/reset.

- **Depends on:** P03-01/07,P01-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Eight-area UX and shared project model.
- **Output/interface:** Native panel layout/theme/font-size/HiDPI persistence, Explorer multi-drag, inspector numeric+slider/reset.
- **Errors/cancellation:** Unsupported drop item shown; canceled import no source changes; layout corrupt resets only layout.
- **Tests and acceptance:** Qt UI import/resize/reset/save/reopen with keyboard focus; Windows Explorer/HiDPI physical checks separate.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P04-02 — chọn/kéo/resize/xoay logo/chữ/vùng che, crop; neo/tọa độ tương đối, lưới/safe area/snap/Alt và đưa về khung.

- **Depends on:** P04-01,P01-07,P02-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Selected layer/crop geometry and viewport transform.
- **Output/interface:** Canvas handles move/resize/rotate/crop/anchor/grid/safe-area/snap/Alt/bring-inside commands.
- **Errors/cancellation:** Locked layer not moved; crop cancel restores; zoom/pan never domain mutation; bad aspect/zero size rejected.
- **Tests and acceptance:** 9 anchors, off-center rotation, portrait/landscape, Alt snap, pixel-step and zoom invariance; export parity on manipulated fixture.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P04-03 — đa chọn/nhóm/khóa/ẩn/thứ tự layer; tránh kéo nhầm; menu ngữ cảnh.

- **Depends on:** P04-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Layer IDs/z-order/group/lock/visibility.
- **Output/interface:** Multi-select box/Shift, group/ungroup, lock/hide/reorder and context menu.
- **Errors/cancellation:** Overlapping layer selection via tree; locked drag no-op; deleted selection invalidated; cancel grouped drag atomic.
- **Tests and acceptance:** Selection/persistence/group transform and z-order parity; Delete removes objects not source files.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P04-04 — undo/redo, một drag một lệnh; inspector và canvas dùng cùng model, save/open giữ đúng.

- **Depends on:** P04-02/03,P03-07. Only independent work may proceed while external portions remain blocked.
- **Input:** Before/after scoped domain commands.
- **Output/interface:** Unified canvas/inspector/timeline command stack, one drag one undo.
- **Errors/cancellation:** Esc cancels transient, text undo stays text; stale revision fails command; grouped error rolls back whole command.
- **Tests and acceptance:** Hundreds drag events→one undo; redo/save/open equality; inspector edits visible in canvas and canonical export.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P04-05 — timeline/playhead/trim/split/in-out/gap/ripple/marker, thumbnail/waveform, zoom/scroll/loop.

- **Depends on:** P04-04,P03-03. Only independent work may proceed while external portions remain blocked.
- **Input:** Rational clips/cues/tracks, thumbnails/waveforms.
- **Output/interface:** Timeline playhead/trim/split/in-out/gap/ripple/marker/zoom/scroll/loop commands.
- **Errors/cancellation:** Trim bounds and overlaps validated; split at edge rejected; Esc leaves timeline unchanged; missing media visible.
- **Tests and acceptance:** Boundary frame/sample tests, gap vs ripple distinction, linked A/V/sub mapping; repeated split/undo round-trip.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P04-06 — proxy/cache tạo nền, đổi chất lượng/cancel/invalidation, seek đồng bộ audio/video.

- **Depends on:** P04-01/05,P02-04/07. Only independent work may proceed while external portions remain blocked.
- **Input:** Probe/fingerprint and canonical CompositionPlan revision.
- **Output/interface:** Background proxy/thumbnail/waveform jobs; quality selection; stale-request-safe A/V seek.
- **Errors/cancellation:** Cancel proxy leaves no ready cache; changed source invalidates; obsolete seek result ignored; missing audio explicit.
- **Tests and acceptance:** Warm/cold seek timing, CPU render concurrent responsiveness, proxy hash/version invalidation, canonical sample frames parity.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P04-07 — shortcut theo focus, remap/xung đột/trợ giúp; nhập Việt/Trung không kích hoạt player/canvas.

- **Depends on:** P04-01/04/05. Only independent work may proceed while external portions remain blocked.
- **Input:** ED§9 full default shortcut map and focus contexts.
- **Output/interface:** Shortcut router/remap/conflict/help UI with IME guard.
- **Errors/cancellation:** Text input/preedit owns keys; duplicate binding rejected or explicit resolution; Escape first cancels current operation.
- **Tests and acceptance:** Qt focus and repeated navigation tests for every shortcut; Vietnamese/Chinese physical IME separately NOT_RUN if unavailable.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P04-08 — UI Cài đặt tool scan/path/check/download/install-all/update/repair/rollback có progress; Chrome/profile/account tables, Ctrl+, và readiness với nút khắc phục đúng lỗi.

- **Depends on:** P03-08/09,P04-01,P01-08. Only independent work may proceed while external portions remain blocked.
- **Input:** Live tool/profile/account registry snapshots.
- **Output/interface:** Settings tables and truthful scan/path/check/install-all/update/repair/rollback, Chrome login/readiness actions.
- **Errors/cancellation:** Stale background scan ignored; cancel install per component; explicit path invalid visible; locked profile not forced.
- **Tests and acceptance:** Qt state walkthrough missing/busy/fail/success, Ctrl+, and F5 scope, repeated clicks; actual Windows tool/Chrome test remains required.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P04_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
