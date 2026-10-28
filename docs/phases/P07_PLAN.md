# P07 clean rebuild plan — Unified composition and export

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Implement transform evaluator, seeded motion, font discovery/glyph check; canonical layer rasterization and FFmpeg composition; source trim/speed/time maps; progressive rendering, cancellation and output validation.

## Task inventory (all original tasks retained)
- [ ] P07-01: font hệ thống/TTF/OTF riêng, tìm/yêu thích/mẫu/fallback/glyph/thiếu font; cùng font/layout preview-render.
- [ ] P07-02: chữ/viền/bóng/nền/padding/căn/giãn dòng/giãn chữ/ngắt dòng/nội dung động; nhiều logo, vị trí/lề/opacity/thời gian.
- [ ] P07-03: nhiều vùng blur/mosaic/màu, bo góc/cường độ/feather theo khả năng engine đã chứng minh; cảnh báo thuộc tính không khả dụng.
- [ ] P07-04: keyframe X/Y/scale/rotation/opacity, linear/easing, copy/paste, thời gian tuyệt đối/tương đối, playhead và undo.
- [ ] P07-05: chạy thẳng/chéo/A→B/nhiều điểm/qua góc/lặp/đi-về/nảy/zoom/xoay/fade; speed/duration/delay/hold/repeat/vùng.
- [ ] P07-06: random có seed/khoảng/xác suất, biến thể mỗi clip, vùng tránh/cảnh báo xung đột, giữ khóa tay.
- [ ] P07-07: fit/crop/nền/tỷ lệ/màu/flip/rotate/speed; thứ tự filter, time map sub, capability CPU/GPU.
- [ ] P07-08: compiler từ model chung, đối chiếu frame, progress FFmpeg/cancel/validation; tối ưu một lần encode khi có thể, ghi lý do cần intermediate.

## Deliverables
src/fonesi_edit/services/{composition,render,fonts}.py; tests/test_render.py

## Tests before results may claim pass
Real FFmpeg outputs for fit/crop/blur background, text, logo alpha, masks, layering, keyframe samples and audio; compare canonical rendered frame preview against output; reject unsupported combinations.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| SUB-09 | Đơn/song ngữ, màu/cỡ/vị trí riêng | PR 4.3; ED 3.3 | P06-06, P07-02 | Hai khối đúng thứ tự và có bật/tắt riêng |
| SUB-10 | Sub rời và burn-in cùng pipeline | PR 4.2 | P06-06, P07-08 | Tệp sub mở được, video phát ngoài vẫn thấy sub |
| ED-05 | Undo/redo, double-click chữ, keyframe tại playhead | ED 1–2 | P04-04, P07-04 | Một drag một undo, nhập chữ không kích hoạt player |
| ED-06 | Font hệ thống/TTF/OTF/tìm/yêu thích/mẫu | ED 3.1 | P07-01 | Font chọn đọc đúng, có mẫu, không bắt cài toàn hệ thống |
| ED-07 | Font glyph/fallback/thiếu font và Unicode | ED 3.1 | P02-04, P07-01 | Việt/Trung đúng; thiếu font có cảnh báo/thay hàng loạt |
| ED-08 | Mọi thuộc tính chữ/viền/bóng/nền/khoảng cách | ED 3.2 | P07-02 | Đủ thuộc tính section, preview-export layout nhất quán |
| ED-09 | Chữ động, nhiều lớp, tràn và giới hạn cỡ | ED 3.2 | P07-02 | Placeholder thay đúng, không cắt chữ ngầm |
| ED-10 | Ngôn ngữ UI/sub/font tách riêng | ED 3.3 | P04-01, P06-02, P07-01 | Đổi ngôn ngữ không giả font/provider có hỗ trợ |
| ED-11 | Nhiều logo, alpha/size/opacity/lề/time/replace | ED 4 | P07-02 | Thay logo giữ biến đổi khi chọn, không mất alpha |
| ED-12 | Chuyển động và toàn bộ tham số speed/delay/repeat | ED 5 | P07-04, P07-05 | Chạy các preset/biên, speed không đổi vì FPS/zoom |
| ED-13 | Keyframe/easing/copy/timing tuyệt đối–tương đối | ED 5 | P07-04 | Giá trị tại mốc khớp export, undo/copy đúng |
| ED-14 | Random seed/khoảng/vùng/khóa/chống che nhau | ED 5.2 | P07-06 | Tái tạo với đủ snapshot, xung đột được báo |
| ED-15 | Nhiều blur/mosaic/màu, time và keyframe vùng che | ED 6 | P07-03, P07-04 | Vùng dưới sub mới, đúng thời gian và cường độ |
| ED-16 | Tỷ lệ/fit/crop/nền/màu/flip/rotate/speed | PR 5 | P07-07 | Dọc/ngang/rotation metadata không sai khung/time map |
| ED-20 | Preview-export và CPU/GPU capability | PR 8; ED 7 | P02-04, P02-05, P07-08 | Frame/time/audio trong dung sai, unsupported báo đúng |
| OPS-06 | Output validation/atomic finalize/không đè | PR 3, 9 | P03-06, P07-08 | Exit lỗi/tệp hỏng/duration sai không báo thành công |

## Acceptance gate
Same timeline/model/font rasterization drives reference preview and export; requested unsupported effect blocks, not silently ignored.

## External/hardware blockers
GPU runtime, CJK font coverage and all Windows renderer/codec combinations need separate evidence.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P07_RESULTS.md`. No task/group passes because only one example works.
