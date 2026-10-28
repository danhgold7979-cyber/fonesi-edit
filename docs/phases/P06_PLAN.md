# P06 clean rebuild plan — Subtitle editing and configured translation

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Implement common cue model, bilingual views, editing/undo and exports; adapter capabilities and batch cache keyed by content/context/config; usage reservation before request and unknown outcome reconciliation.

## Task inventory (all original tasks retained)
- [ ] P06-01: SRT/VTT/ASS về cue chung, báo style chưa hỗ trợ; ghép bằng ID/ngôn ngữ/tên, báo mơ hồ.
- [ ] P06-02: nguồn/đích/ưu tiên, sub người đăng/tự động, chính sách thiếu sub và khác ngôn ngữ.
- [ ] P06-03: adapter dịch thật, thuật ngữ/xưng hô/tên riêng/ngữ cảnh, cache, chi phí/rate limit/retry.
- [ ] P06-04: gốc/dịch song song, sửa/tìm/thay/tách/gộp, dịch lại câu chọn, khóa câu đã sửa, lịch sử.
- [ ] P06-05: thời gian qua timeline/ô số, offset, kiểm tra chồng/tràn, time map sau trim/speed.
- [ ] P06-06: đơn/song ngữ, style cơ bản liên kết P07, xuất SRT/ASS và burn-in qua pipeline chung.

## Deliverables
src/fonesi_edit/services/{subtitles,translation}.py; tests/test_subtitles.py

## Tests before results may claim pass
SRT/VTT/ASS roundtrips; ambiguous matching; missing/automatic subtitle policy; overlap/overflow; trim-speed maps; locked cues; exact ID response validation; cache/quota; uncertain timeout does not auto-charge again.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| SUB-01 | Chọn ngôn ngữ nguồn/đích/ưu tiên, nguồn sub | PR 4.1 | P06-02 | Chọn đúng ngôn ngữ và gắn nhãn sub tự động |
| SUB-02 | SRT/VTT/ASS và ghép đúng video | PR 4.2 | P06-01 | ID/tên mơ hồ không bị ghép nhầm; báo style thiếu |
| SUB-03 | Dịch Trung–Việt, ngữ cảnh/thuật ngữ/tên riêng | PR 4.1 | P02-03, P06-03 | Provider thật, ánh xạ cue đầy đủ, mẫu được đọc soát |
| SUB-04 | Bộ dịch thay được, quota/chi phí/retry/cache | PR 4.1 | P06-03 | Cache hit không gọi mới, giới hạn hoạt động, timeout không rõ được ghi |
| SUB-05 | Gốc/dịch song song, tìm/sửa/tách/gộp | PR 4 | P06-04 | Sửa đúng cue, undo/save/open giữ nội dung |
| SUB-06 | Khóa câu, dịch lại chọn lọc | PR 4.1 | P06-04 | Auto không đổi câu khóa; chỉ câu chọn được dịch lại |
| SUB-07 | Offset/time map theo trim/speed/ghép | PR 4.2 | P06-05, P08-06 | Cue theo đúng nguồn sau mọi phép biến đổi thời gian |
| SUB-08 | Tràn/chồng/ngắn/quá cuối, thiếu sub | PR 4.2 | P06-02, P06-05 | Báo đúng, không mất chữ, không chặn cả lô |
| SUB-09 | Đơn/song ngữ, màu/cỡ/vị trí riêng | PR 4.3; ED 3.3 | P06-06, P07-02 | Hai khối đúng thứ tự và có bật/tắt riêng |
| SUB-10 | Sub rời và burn-in cùng pipeline | PR 4.2 | P06-06, P07-08 | Tệp sub mở được, video phát ngoài vẫn thấy sub |
| ED-10 | Ngôn ngữ UI/sub/font tách riêng | ED 3.3 | P04-01, P06-02, P07-01 | Đổi ngôn ngữ không giả font/provider có hỗ trợ |

## Acceptance gate
Local subtitle import/edit/export/burn works; remote translation requires explicit provider and consent/configuration, never mock success.

## External/hardware blockers
Live translation quality, provider pricing/quota and Chinese-Vietnamese review need configured provider.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P06_RESULTS.md`. No task/group passes because only one example works.
