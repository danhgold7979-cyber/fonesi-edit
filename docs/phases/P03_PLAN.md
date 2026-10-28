# P03 clean rebuild plan — Durable core and safe work execution

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Implement rational microsecond time maps and typed models; atomic project persistence; SQLite migrations and immutable jobs; leased scheduler and subprocess runner; tool/account reference schemas.

## Task inventory (all original tasks retained)
- [ ] P03-01: scaffold module, môi trường tái lập, dependency lock, config và user data tách khỏi thư mục chương trình.
- [ ] P03-02: schema/version/migration cho project/media/preset/job/artifact/history/cache; backup và phục hồi khi migration lỗi.
- [ ] P03-03: probe, ID/fingerprint, rational timestamp/time map; media không audio hoặc metadata lỗi.
- [ ] P03-04: scheduler/worker process, công đoạn/progress/cancel/pause/retry, quản lý tiến trình con trên Windows và lease phục hồi sau crash.
- [ ] P03-05: snapshot cấu hình/seed, log lọc bí mật, phân loại lỗi và UI hàng đợi đầu tiên.
- [ ] P03-06: output tạm → kiểm tra → tên cuối an toàn, không đè; truy vết nguồn; bỏ output/cache khi quét.
- [ ] P03-07: save/autosave/recovery, relink media, cache theo fingerprint/phiên bản; thử đóng bất thường có kiểm soát.
- [ ] P03-08: dependency registry/resolver, tool ownership/version/path/capabilities, trusted manifests, cài per-user, staging/self-test/activation/lease/rollback, không đè tool ngoài.
- [ ] P03-09: schema BrowserProfile/PlatformAccountBinding, profile ownership/browser state/auth state, credential refs và account-scoped cache; không lưu cookie/mật khẩu trong project.

## Deliverables
src/fonesi_edit/core/{model,storage,jobs,process,paths}.py; tests/test_core.py

## Tests before results may claim pass
Schema migration backup and rollback; secret rejection; snapshot immutability; lease recovery; state transitions; subprocess timeout/cancel; Unicode/no-clobber outputs; source exclusion.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| SRC-08 | Tệp tạm, validation, thiếu quyền/đĩa | PR 3.3 | P03-06, P05-04 | Tệp dở/hỏng không thành công, nguồn giữ nguyên |
| BAT-03 | Folder/tên output theo kênh, không đè | PR 3.3, 5 | P03-06, P08-02 | Đúng cây folder, input trùng tên không mất kết quả |
| OPS-01 | Progress/ETA/tốc độ/công đoạn/thống kê | PR 9 | P03-04, P10-06 | Không biết tổng không dựng phần trăm, ETA có trạng thái ước tính |
| OPS-02 | Pause/cancel/retry/ưu tiên/đổi job chờ | PR 9 | P03-04, P10-06 | Ý nghĩa đúng, không hứa resume frame render |
| OPS-03 | Save/autosave/recovery/relink/migration | PR 9 | P03-02, P03-07 | Crash/mở lại giữ việc xong, thiếu asset relink được |
| OPS-04 | Snapshot/seed/version/provenance | PR 9 | P03-05, P09-06 | Truy vết được từng đầu ra, preset đổi không thay job cũ |
| OPS-05 | Worker ngoài UI, lỗi tách biệt, log chẩn đoán | PR 8–9 | P03-04, P11-02 | FFmpeg/worker lỗi không sập UI hoặc mất lô |
| OPS-06 | Output validation/atomic finalize/không đè | PR 3, 9 | P03-06, P07-08 | Exit lỗi/tệp hỏng/duration sai không báo thành công |
| TOL-02 | Trỏ đường dẫn, chọn bản, kiểm tra hoạt động | SB 2.1 | P02-09, P03-08 | Unicode/timeout/sai version/capability báo đúng, không sửa tool ngoài |
| TOL-03 | FFmpeg/ffprobe/downloader và dependency theo workflow | SB 2.2 | P02-09, P03-08 | Manifest đúng kiến trúc/phiên bản/capability, không bắt cài dev tools vô cớ |
| TOL-04 | Tải-cài thiếu, install-all, progress/cancel | SB 2 | P03-08, P04-08 | Nút chạy thật qua tải/xác minh/cài/kiểm tra; chưa xong không báo ready |
| TOL-05 | Trusted artifacts, TLS/checksum/chữ ký | SB 2.3 | P02-09, P03-08 | Artifact lỗi bị chặn, bản cũ và cấu hình được giữ |
| TOL-06 | Staging/repair/update/rollback và tool lease | SB 2.3 | P03-08, P10-07 | Job cũ giữ binary cũ, bản mới kích hoạt an toàn, rollback chạy được |
| TOL-08 | Runtime/font/model/driver có điều kiện | SB 2.2 | P03-08, P12-07 | Chỉ thành phần cần được yêu cầu, driver không tự thay, API không tự tải model |
| AUTH-03 | Nhiều nick cùng nền tảng ở hồ sơ khác nhau | SB 3 | P03-09, P05-08 | Facebook A/B không chia cookie, không nhầm nhiều cửa sổ là nhiều profile |
| AUTH-07 | Job gán đúng account/profile, snapshot chỉ ref | SB 5 | P03-09, P05-10 | Nick chọn được giữ, project/job không chứa cookie/token |
| AUTH-10 | Account-scoped cache và profile concurrency | SB 5 | P03-09, P10-07 | Cache/quyền A không dùng cho B, không giành user-data-dir |
| AUTH-11 | Browser data riêng, export/dọn/xóa liên kết khác xóa profile | SB 4–5, 8 | P03-09, P10-07, P11-08 | Export không lộ session, cache cleanup không xóa profile, xóa dữ liệu có thao tác riêng |

## Acceptance gate
Local job crosses worker process, validates real media before publication, survives restart without losing succeeded records.

## External/hardware blockers
Windows process tree and interrupted filesystem validation require Windows.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P03_RESULTS.md`. No task/group passes because only one example works.
