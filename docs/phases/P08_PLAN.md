# P08 clean rebuild plan — Batch, audio and duration planning

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Add deterministic scans/filtering, per-clip overrides, audio selection maps and duration planner with explicit infeasibility; queue validated plans, render one sample then a batch, only retry failed work.

## Task inventory (all original tasks retained)
- [ ] P08-01: nhiều folder/đệ quy/checkbox/loại/đảo chọn/tìm/lọc, không xóa nguồn, không nhận output/cache.
- [ ] P08-02: preset/ghi đè clip/xem tác động/snapshot, output theo kênh/mẫu tên/phiên bản không đè.
- [ ] P08-03: tiếng gốc/âm chính/nhạc/SFX, mute/solo/gain/fade/trim/delay, meter/clipping/chuẩn hóa.
- [ ] P08-04: audio cả lô/theo tên/danh sách/random, nhạc lặp chuyển tiếp, SFX theo giây/cảnh/tỷ lệ, giảm nhạc theo chính sách hỗ trợ.
- [ ] P08-05: duration planner một hoặc nhiều clip; đích video/audio/nhập tay, min/max speed/đoạn, giữ cao độ, lặp/freeze/cắt theo lựa chọn.
- [ ] P08-06: tính chuyển cảnh/audio crossfade vào thời lượng, time map sub; báo bất khả thi, không tự bỏ cảnh/ghép clip ngoài chế độ.
- [ ] P08-07: chạy thử một video/đoạn, ước tính dung lượng/ETA, render lô/resume, kiểm tra duration/tracks/media.

## Deliverables
src/fonesi_edit/services/{batch,audio,duration}.py; tests/test_batch.py

## Tests before results may claim pass
Multiple folders recursive exclusions, source unchanged, scoped preset precedence, dry-run output versions; short/long audio/video speed/loop/freeze/cut with limits; multi-track gain/delay/fade/solo.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| SUB-07 | Offset/time map theo trim/speed/ghép | PR 4.2 | P06-05, P08-06 | Cue theo đúng nguồn sau mọi phép biến đổi thời gian |
| BAT-01 | Folder đệ quy/chọn/loại/tìm/lọc/đảo chọn | PR 5 | P08-01 | Không xóa folder, output/cache không bị nhận lại |
| BAT-02 | Một clip/nhiều clip/cả lô, preset/snapshot/khóa | PR 5; ED 10 | P01-04, P08-02 | Không thay job đang chạy hoặc sửa tay đã khóa |
| BAT-03 | Folder/tên output theo kênh, không đè | PR 3.3, 5 | P03-06, P08-02 | Đúng cây folder, input trùng tên không mất kết quả |
| BAT-04 | Chạy thử/dry-run/ước tính/tác vụ lỗi riêng | PR 5, 9 | P08-07, P10-03 | Xem tác động trước lô, retry riêng không làm lại việc xong |
| AUD-01 | Track gốc/chính/nền/SFX, gain/mute/solo | PR 6 | P08-03 | Track đúng vai trò, nghe solo/mute đúng |
| AUD-02 | Fade/trim/delay/meter/clipping/normalize | PR 6 | P08-03 | Mức âm và điểm vào/ra đúng, không clipping ngoài dự kiến |
| AUD-03 | Ghép audio cả lô/tên/list/random | PR 6 | P08-04 | Ánh xạ xác định, mơ hồ/thiếu audio được báo |
| AUD-04 | Lặp nhạc/crossfade/SFX theo cảnh/giây/tỷ lệ | PR 6 | P08-04, P08-06 | Đúng mốc và tổng duration, không lỗi ở biên cảnh |
| AUD-05 | Video/audio/nhập tay quyết định thời lượng | PR 6 | P08-05 | Đủ trường hợp ngắn/dài/không audio, không tự đổi mode |
| AUD-06 | Min/max speed/đoạn, loop/freeze/cut/giữ cao độ | PR 6 | P08-05 | Theo giới hạn hoặc báo bất khả thi, không kéo giọng quá mức |
| OPS-07 | Preset import/export/copy nhóm/tài nguyên thiếu | ED 8 | P01-04, P08-02, P11-05 | Đủ công cụ phụ, version/thiếu tài nguyên được báo |

## Acceptance gate
One input → one output by default; no source modified, failures isolated, all outputs have verified duration/required tracks and immutable snapshots.

## External/hardware blockers
Large real-world media corpus and hardware performance remain separate.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P08_RESULTS.md`. No task/group passes because only one example works.
