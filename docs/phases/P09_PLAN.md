# P09 clean rebuild plan — Scenes, bounded matrix solver and history

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Stable content IDs with logical labels; deterministic bounded backtracking/random sampling; unique transactional reservations; per-row edits/locks, duration allocation, rendering and history commit.

## Task inventory (all original tasks retained)
- [ ] P09-01: quét C1…Cn/G1…Gm, natural sort/đổi thứ tự/khóa/loại, ID ổn định/tên logic; đổi tên thật có ánh xạ hoàn tác riêng.
- [ ] P09-02: tích tổ hợp/lọc/history dự án/hash góc/tổ hợp; phân biệt reservation và đầu ra thành công.
- [ ] P09-03: generator seed/không trùng/cân bằng/W/K, phạm vi so sánh, timeout/cancel, chưa tìm đủ khác bất khả thi.
- [ ] P09-04: bảng sửa/khóa ô/tạo lại hàng/preview/chuỗi C1G1+C2G2+…/thống kê/CSV; sửa hàng phải kiểm tra lại ràng buộc.
- [ ] P09-05: chia đều/tỷ lệ/trọng số/nhập tay, dùng duration planner P08, tính chuyển cảnh, giữ đủ/thứ tự.
- [ ] P09-06: render/validation theo hàng, snapshot nguồn/góc/preset/seed, commit lịch sử sau output hợp lệ, retry không sinh tổ hợp mới ngầm.

## Deliverables
src/fonesi_edit/services/matrix.py; tests/test_matrix.py

## Tests before results may claim pass
Exhaustive small-space oracle; large lazy space; strict W/K previous/window comparison; balance, seeded reproducibility, timeout vs proven impossible; row edits revalidate future windows, reservation/commit/failure; CSV.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| MAT-01 | Cảnh/góc, natural sort, tên logic, ID ổn định | PR 7 | P09-01 | C2 trước C10, đổi tên không thành góc mới |
| MAT-02 | Đổi tên thật có preview/rollback, không tự đổi | PR 5, 7 | P09-01 | Xung đột được chặn, hoàn tác về tên cũ |
| MAT-03 | Tích tổ hợp và sinh lazy theo số lượng | PR 7 | P09-02, P09-03 | Tập nhỏ đúng số, tập lớn không cấp phát cả tích |
| MAT-04 | Không trùng/W/K/cân bằng/history | PR 7 | P09-02, P09-03 | Ràng buộc đúng, không nới ngầm, timeout khác vô nghiệm |
| MAT-05 | Sửa/khóa ô, tạo lại hàng, CSV/thống kê/preview | PR 7 | P09-04 | Sửa ô revalidate cửa sổ ảnh hưởng, chuỗi đúng asset |
| MAT-06 | Đủ/thứ tự cảnh, chia thời lượng nhiều cách | PR 7 | P09-05 | Đủ cảnh và audio fit hoặc báo lý do không khả thi |
| MAT-07 | Reservation/commit history, retry và seed | PR 7, 9 | P09-06 | Không hai worker dùng cùng tổ hợp bị cấm, failed không thành công giả |
| OPS-04 | Snapshot/seed/version/provenance | PR 9 | P03-05, P09-06 | Truy vết được từng đầu ra, preset đổi không thay job cũ |

## Acceptance gate
Every row has every ordered scene, no duplicate/constraint relaxation; success history only follows validated artifact; no product-space allocation.

## External/hardware blockers
Large-case benchmark and interactive scene UX remain visible until measured.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P09_RESULTS.md`. No task/group passes because only one example works.
