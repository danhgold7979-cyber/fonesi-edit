# P04 clean rebuild plan — Desktop workspace and direct editing

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Build Vietnamese workspace with media/preview/inspector/timeline, command stack shared with domain, handles and timeline edits, playback plus reference frames, settings/readiness views.

## Task inventory (all original tasks retained)
- [ ] P04-01: panel/theme/HiDPI/cỡ chữ UI, drag từ Explorer, media/inspector, slider/ô số/reset.
- [ ] P04-02: chọn/kéo/resize/xoay logo/chữ/vùng che, crop; neo/tọa độ tương đối, lưới/safe area/snap/Alt và đưa về khung.
- [ ] P04-03: đa chọn/nhóm/khóa/ẩn/thứ tự layer; tránh kéo nhầm; menu ngữ cảnh.
- [ ] P04-04: undo/redo, một drag một lệnh; inspector và canvas dùng cùng model, save/open giữ đúng.
- [ ] P04-05: timeline/playhead/trim/split/in-out/gap/ripple/marker, thumbnail/waveform, zoom/scroll/loop.
- [ ] P04-06: proxy/cache tạo nền, đổi chất lượng/cancel/invalidation, seek đồng bộ audio/video.
- [ ] P04-07: shortcut theo focus, remap/xung đột/trợ giúp; nhập Việt/Trung không kích hoạt player/canvas.
- [ ] P04-08: UI Cài đặt tool scan/path/check/download/install-all/update/repair/rollback có progress; Chrome/profile/account tables, Ctrl+, và readiness với nút khắc phục đúng lỗi.

## Deliverables
src/fonesi_edit/ui/{window,canvas,timeline,editor}.py; tests/test_ui.py

## Tests before results may claim pass
Offscreen QTest drag/resize/rotate, one-drag-one-undo, lock/visibility, zoom independence, focus-safe shortcuts, save/open and cancelled gestures; asynchronous preview responsiveness.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| ED-01 | Panel/Cơ bản–Nâng cao/tìm thiết lập/tooltip/reset | PR 2; ED 1 | P01-02, P04-01 | Mọi nhóm có nơi thao tác, đơn vị và lý do disabled |
| ED-02 | Kéo/resize/xoay/crop/neo/nhập số | ED 2 | P04-02 | Canvas/inspector cùng model, export cùng vị trí |
| ED-03 | Đa chọn/nhóm/khóa/ẩn/z-order | ED 2 | P04-03 | Đối tượng khóa không kéo nhầm, thứ tự layer đúng |
| ED-04 | Lưới/safe area/snap/Alt/căn/phân bố | ED 2.2 | P04-02, P04-03 | Căn theo canvas, zoom không đổi giá trị project |
| ED-05 | Undo/redo, double-click chữ, keyframe tại playhead | ED 1–2 | P04-04, P07-04 | Một drag một undo, nhập chữ không kích hoạt player |
| ED-10 | Ngôn ngữ UI/sub/font tách riêng | ED 3.3 | P04-01, P06-02, P07-01 | Đổi ngôn ngữ không giả font/provider có hỗ trợ |
| ED-17 | Track/trim/split/gap/ripple/marker/in-out/loop | ED 7 | P04-05 | Gap/ripple khác nhau, timeline save/open đúng |
| ED-18 | Proxy/waveform/thumbnail/seek/quality | ED 7 | P04-06 | Tạo nền/cancel được, đổi proxy không lệch thời gian |
| ED-19 | Phím tắt remap/xung đột/focus/IME | ED 9 | P04-07 | Đủ bảng phím, nhập chữ không kích hoạt lệnh khác |
| OPS-08 | Menu/search/folder gần dùng/theme/HiDPI | ED 1, 8 | P04-01, P11-05 | Thao tác chuột/phím, ngữ cảnh và tỉ lệ màn hình dùng được |
| TOL-01 | Bảng tool và quét nguồn phổ biến/tùy chỉnh | PR 13; SB 2.1 | P01-08, P04-08 | Hiện đường dẫn/version/vai trò/trạng thái, không chỉ tìm tên exe |
| TOL-04 | Tải-cài thiếu, install-all, progress/cancel | SB 2 | P03-08, P04-08 | Nút chạy thật qua tải/xác minh/cài/kiểm tra; chưa xong không báo ready |
| TOL-07 | Chrome chính thức quét/trỏ/tải-cài | SB 2.2, 3 | P02-10, P04-08, P12-07 | Google Chrome thật, không WebView/Chromium giả thay thế |
| TOL-09 | Readiness tool/phiên/quyền nguồn, nút sửa đúng lỗi | SB 7 | P04-08, P10-07 | Thiếu tool/login/nguồn có hành động khác nhau, media cục bộ không bị chặn vô cớ |
| AUTH-01 | Mọi nền tảng có trang đăng nhập và chọn binding | PR 13; SB 4.2 | P01-08, P04-08, P05-09 | Đủ nền tảng đã nêu, capability/auth chưa thử được ghi đúng |
| AUTH-04 | Tạo/đặt tên/mở/gán/default/profile bận-khóa | SB 4.1 | P04-08, P05-08 | Mở đúng hồ sơ, không xóa lock/chiếm profile cá nhân |

## Acceptance gate
A real imported clip can be edited, saved, reopened, previewed and queued. Every unavailable control gives a reason.

## External/hardware blockers
Interactive Windows HiDPI/IME/audio timing cannot be certified offscreen.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P04_RESULTS.md`. No task/group passes because only one example works.

## Execution addendum — timeline clip operations (2026-10-28)

**Status: plan first; implementation has not started in this tranche.**

### Scope
Complete a small, user-visible subset of P04-05 by wiring the existing tested domain operations into the timeline UI:
1. Select a clip from the Video track and synchronize the playhead to the clicked time.
2. Split the selected/current clip at the playhead using the project's rational speed/time map.
3. Delete a selected clip while preserving the resulting gap, or explicitly choose ripple-delete.
4. Keep each action one undoable command; reject locked clips and invalid ripple operations without changing project state.
5. Keep selection/render/cache state consistent after edits; never delete source media.

### Source and dependency review
- Read `docs/REBUILD_MASTER_PLAN.md`, the P04 task list/results, `docs/EDITOR_SPEC.md` timeline requirements and the current `services/editing.py`, `ui/timeline.py`, `ui/editor.py`, `ui/window.py`, and UI/editing tests.
- Reuse `split_clip` and `delete_clip`; do not duplicate timeline-time arithmetic in the UI.
- Make ripple deletion validate overlaps before mutating the project so an exception cannot leave a partially deleted clip.

### Required tests
- Timeline click selects the correct clip and seeks to the clicked time.
- Split respects playhead position, speed mapping and one-command undo.
- Gap-delete leaves later offsets unchanged; ripple-delete shifts subsequent clips and maps cues/layers/markers.
- Locked clips and invalid ripple operations fail without mutating the project.
- Existing Linux and Windows source tests remain green.

### Acceptance and remaining scope
This tranche does not complete P04. Direct crop/anchors/groups/alignment, full trim/split/gap/ripple controls, proxy quality/cancel/seek edge cases, shortcuts/IME/HiDPI and target Windows interaction remain separately open.
