# P10 clean rebuild plan — Workflow automation and resource admission

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Implement explicit DAG/schedules/checkpoints, dry-run auto decisions, stable-file watcher, safe cache LRU and resource profiles with separate tool/session/source readiness.

## Task inventory (all original tasks retained)
- [ ] P10-01: DAG tải→sub→dịch→edit→render→validation theo lô/cuốn chiếu, công đoạn idempotent/trạng thái riêng.
- [ ] P10-02: lịch đồng bộ/watcher đợi tệp ổn định/loại output, chống job trùng/chạy chồng, chính sách lịch bỏ lỡ; chạy khi app đóng cần chế độ nền/Windows Task Scheduler được bật rõ.
- [ ] P10-03: kênh→logo/preset/output, auto layout có giới hạn, chạy lại riêng nhóm/giữ sửa tay/dry-run.
- [ ] P10-04: CPU/RAM/GPU/VRAM/đĩa, Êm/Cân bằng/Tối đa, giới hạn riêng quét/tải/dịch/render/luồng mỗi việc.
- [ ] P10-05: benchmark gợi ý, giữ tài nguyên dự phòng/backpressure/giảm nhận việc, phục hồi có ngưỡng tránh dao động; encode khác filter GPU.
- [ ] P10-06: ETA/tốc độ/công đoạn/lô, ưu tiên/đổi job chờ/thông báo, hành động sau xong do người dùng bật, dọn cache an toàn.
- [ ] P10-07: preflight tool/Chrome/session/quyền nguồn, lease tool/profile và giới hạn theo account/domain; login lại đúng nick rồi resume, cập nhật tool không đụng job đang chạy, không dọn browser data như cache.

## Deliverables
src/fonesi_edit/services/{automation,resources}.py; tests/test_automation.py

## Tests before results may claim pass
DAG batch/rolling dependencies, failed download does not block valid files; watcher stability and symlink/output exclusions; schedule misfire/overlap; separate capacity limits; low disk/RAM admission and hysteresis.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| BAT-04 | Chạy thử/dry-run/ước tính/tác vụ lỗi riêng | PR 5, 9 | P08-07, P10-03 | Xem tác động trước lô, retry riêng không làm lại việc xong |
| AUTO-01 | Chuỗi theo lô/cuốn chiếu, chính sách lỗi | PR 2, 8 | P10-01 | Tệp hợp lệ tiếp tục, lỗi riêng không treo cả chuỗi |
| AUTO-02 | Lịch/watcher/file ổn định/chống vòng | ED 10 | P10-02 | Không đọc tệp còn copy, không nhận output, lịch không chạy chồng |
| AUTO-03 | Kênh→logo/preset, layout và chạy lại nhóm | ED 10 | P10-03 | Khóa/sửa tay giữ nguyên, có dry-run và lý do |
| AUTO-04 | CPU/GPU/Auto và metrics khả dụng | PR 8 | P02-05, P10-04 | Encode thật, unknown hiển thị đúng, fallback có log |
| AUTO-05 | Profile/gợi ý/giới hạn riêng/RAM-VRAM-đĩa | PR 8 | P10-04, P10-05 | Admission/backpressure đo được, không hứa số luồng chung |
| AUTO-06 | Cache/dọn an toàn/hành động sau xong | ED 8, 10 | P10-06 | Không dọn tệp đang dùng/nguồn, tắt máy chỉ khi chủ động bật |
| OPS-01 | Progress/ETA/tốc độ/công đoạn/thống kê | PR 9 | P03-04, P10-06 | Không biết tổng không dựng phần trăm, ETA có trạng thái ước tính |
| OPS-02 | Pause/cancel/retry/ưu tiên/đổi job chờ | PR 9 | P03-04, P10-06 | Ý nghĩa đúng, không hứa resume frame render |
| TOL-06 | Staging/repair/update/rollback và tool lease | SB 2.3 | P03-08, P10-07 | Job cũ giữ binary cũ, bản mới kích hoạt an toàn, rollback chạy được |
| TOL-09 | Readiness tool/phiên/quyền nguồn, nút sửa đúng lỗi | SB 7 | P04-08, P10-07 | Thiếu tool/login/nguồn có hành động khác nhau, media cục bộ không bị chặn vô cớ |
| AUTH-08 | Expired/challenge/bridge lỗi/quyền nguồn tách biệt | SB 4.3–5 | P05-09, P10-07 | Dừng đúng job, relogin rồi resume, không tải trùng/đổi public ngầm |
| AUTH-10 | Account-scoped cache và profile concurrency | SB 5 | P03-09, P10-07 | Cache/quyền A không dùng cho B, không giành user-data-dir |
| AUTH-11 | Browser data riêng, export/dọn/xóa liên kết khác xóa profile | SB 4–5, 8 | P03-09, P10-07, P11-08 | Export không lộ session, cache cleanup không xóa profile, xóa dữ liệu có thao tác riêng |

## Acceptance gate
No duplicate loop, preserved manual locks, paused queue admits nothing, unknown metrics remain unknown, cleanup confined to owned cache with no active leases.

## External/hardware blockers
Background Windows scheduler opt-in, GPU/temperature readings and real Chrome leases require target environment.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P10_RESULTS.md`. No task/group passes because only one example works.
