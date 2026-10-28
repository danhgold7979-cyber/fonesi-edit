# P12 clean rebuild plan — Packaging and user handoff

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Package app/worker with dependency lock, preserve licenses and installer ownership rules, document supported and pending workflows; record exact commits/build hash and manual target acceptance checklist.

## Task inventory (all original tasks retained)
- [ ] P12-01: đóng gói tái lập theo P02, FFmpeg/thư viện/font hợp lệ; chạy không cần bộ dev/admin nếu không thiết yếu.
- [ ] P12-02: phân biệt install/user data, Unicode/quyền ghi/antivirus thực tế, CPU-only và GPU phù hợp khi có.
- [ ] P12-03: chạy workflow từ bản đóng gói, save/open/crash/restart/migration/cấu hình thiếu, mở kết quả bằng player ngoài.
- [ ] P12-04: hướng dẫn Việt, preset mẫu, cấu hình dịch/phiên nguồn an toàn, phím tắt/chẩn đoán/báo lỗi.
- [ ] P12-05: cập nhật tool/adapter có version/xác minh/tương thích/rollback, backup trước đổi schema.
- [ ] P12-06: manifest, capabilities, máy thật, release notes/giới hạn, lưu bản phục hồi.
- [ ] P12-07: Windows mới thiếu dependency/Chrome: từ Cài đặt tải-cài-kiểm tra, mở Chrome thật/login, dùng phiên tải mẫu; tool ngoại không bị sửa, offline vẫn dùng media cục bộ, giới hạn auth được ghi đúng.

## Deliverables
scripts/build_desktop.py; packaging/; .github/workflows/rebuild.yml; docs/USER_GUIDE.md

## Tests before results may claim pass
Build frozen Linux app and worker then run same proof from binary; prepare Windows build matrix and Unicode smoke, source/bundle version match; notices and safe update tests.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| WIN-01 | Build tái lập, user data tách, không bộ dev | PR 11 | P02-06, P12-01 | App đóng gói chạy trên Windows mục tiêu |
| WIN-02 | Unicode/CPU-only/GPU/font/codec | PR 11 | P12-02, P12-03 | Workflow từ binary thật, không chỉ từ source |
| WIN-03 | Hướng dẫn/preset mẫu/version/giới hạn | PR 11 | P12-04, P12-06 | Người dùng chạy quy trình theo tài liệu, giới hạn rõ |
| WIN-04 | Update có xác minh/version/rollback | Kế hoạch | P12-05 | Cập nhật lỗi khôi phục được, project backup trước migration |
| TOL-07 | Chrome chính thức quét/trỏ/tải-cài | SB 2.2, 3 | P02-10, P04-08, P12-07 | Google Chrome thật, không WebView/Chromium giả thay thế |
| TOL-08 | Runtime/font/model/driver có điều kiện | SB 2.2 | P03-08, P12-07 | Chỉ thành phần cần được yêu cầu, driver không tự thay, API không tự tải model |

## Acceptance gate
No full release acceptance until binary executes on target Windows without developer tools and real required workflows pass. Local build does not close Windows.

## External/hardware blockers
No Windows host/CI run without push authorization; no push/merge/deploy authorized in this task.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P12_RESULTS.md`. No task/group passes because only one example works.
