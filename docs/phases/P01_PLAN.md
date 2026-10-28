# P01 clean rebuild plan — Contracts, screen map and traceability

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: source specifications and baseline inventory.

## Concrete execution order
Read three original specs and traceability, preserve baseline, approve normalized time/geometry and command ownership before any implementation.

## Task inventory (all original tasks retained)
- [ ] P01-01: đánh mã yêu cầu, tách phạm vi hiện tại/tích hợp sau; ghi mặc định và trường hợp lỗi.
- [ ] P01-02: wireframe bảy khu vực, media/preview/inspector/timeline, Cơ bản/Nâng cao, trạng thái rỗng/đang làm/lỗi.
- [ ] P01-03: luồng thêm kênh, folder, âm thanh, chỉnh sub/logo, ma trận và hàng đợi; đếm thao tác đường dùng thường xuyên.
- [ ] P01-04: preset từng nhóm, một clip/nhiều clip/cả lô; thuộc tính khóa và ghi đè tay.
- [ ] P01-05: định nghĩa W/K, ưu tiên khớp âm thanh, thiếu sub, tên logic, trùng tên và tệp đã xử lý.
- [ ] P01-06: corpus media, nguồn thử, quyền truy cập/cấu hình cần, tiêu chí và phép đo preview/export.
- [ ] P01-07: hợp đồng project/preset/job, module và sổ quyết định cần thực nghiệm ở P02.
- [ ] P01-08: wireframe Cài đặt công cụ/hồ sơ Chrome/tài khoản mọi nền tảng, luồng scan→download/install→check, login→verify→use; readiness ba trục.

## Deliverables
docs/REBUILD_MASTER_PLAN.md; docs/phases/P01_DESIGN.md; docs/rebuild/coverage.json

## Tests before results may claim pass
Validate all 94 task IDs and 95 requirement groups; ensure every group maps to phase/task, artifact, test and explicit evidence state.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| ED-01 | Panel/Cơ bản–Nâng cao/tìm thiết lập/tooltip/reset | PR 2; ED 1 | P01-02, P04-01 | Mọi nhóm có nơi thao tác, đơn vị và lý do disabled |
| BAT-02 | Một clip/nhiều clip/cả lô, preset/snapshot/khóa | PR 5; ED 10 | P01-04, P08-02 | Không thay job đang chạy hoặc sửa tay đã khóa |
| OPS-07 | Preset import/export/copy nhóm/tài nguyên thiếu | ED 8 | P01-04, P08-02, P11-05 | Đủ công cụ phụ, version/thiếu tài nguyên được báo |
| TOL-01 | Bảng tool và quét nguồn phổ biến/tùy chỉnh | PR 13; SB 2.1 | P01-08, P04-08 | Hiện đường dẫn/version/vai trò/trạng thái, không chỉ tìm tên exe |
| AUTH-01 | Mọi nền tảng có trang đăng nhập và chọn binding | PR 13; SB 4.2 | P01-08, P04-08, P05-09 | Đủ nền tảng đã nêu, capability/auth chưa thử được ghi đúng |

## Acceptance gate
Every requirement retained; defaults, failure states, ownership and success claims defined.

## External/hardware blockers
None; design only.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P01_RESULTS.md`. No task/group passes because only one example works.
