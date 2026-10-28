# P11 clean rebuild plan — Integration, durability and honest coverage

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Run all tests after final edits, collect real tool/version/test evidence; audit all 95 groups against concrete code/UI and test; fix regressions and record remaining scope without percentage inflation.

## Task inventory (all original tasks retained)
- [ ] P11-01: end-to-end các workflow/nguồn hỗ trợ; dọc/ngang/CFR/VFR/rotation/audio lệch hoặc không audio/sub sau speed-trim.
- [ ] P11-02: crash worker/app/mạng/auth/rate limit/quota/tệp hỏng/thiếu font-media/quyền ghi-đĩa đầy; retry/resume.
- [ ] P11-03: lô lớn/nhiều layer/ma trận lớn/tải+render; đo UI/proxy/seek/RAM/VRAM/rò tài nguyên trên máy tham chiếu.
- [ ] P11-04: đối chiếu frame/sub/audio/duration theo dung sai; sửa nguyên nhân, không tắt kiểm tra để đạt.
- [ ] P11-05: rà mọi hàng truy vết, mọi tùy chọn/phím tắt/focus/HiDPI/theme/persistence/preset migration.
- [ ] P11-06: nguồn có phiên bản/ngày/evidence, tách lỗi app/hạn chế nguồn/blocker cấu hình; không đóng mục chưa chạy thành công.
- [ ] P11-07: log/backup/cache/dependency, lỗi còn lại theo mức ảnh hưởng và cách khắc phục.
- [ ] P11-08: missing/wrong tools, installer ngắt/verify lỗi/quyền ghi/update bận; Chrome A nhiều nền tảng, Chrome B nick khác, phiên hết hạn/challenge/mismatch/lock/bridge không dùng được, export không chứa session.

## Deliverables
tests/test_integration.py; scripts/verify_rebuild.py; docs/rebuild/evidence/verification.json

## Tests before results may claim pass
End-to-end local media → subtitles → edits → batch/matrix → validation; corrupted file, killed worker, recovery, collision, disk admission; regression UI tests; coverage audit for every requirement and shortcut.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| OPS-05 | Worker ngoài UI, lỗi tách biệt, log chẩn đoán | PR 8–9 | P03-04, P11-02 | FFmpeg/worker lỗi không sập UI hoặc mất lô |
| OPS-07 | Preset import/export/copy nhóm/tài nguyên thiếu | ED 8 | P01-04, P08-02, P11-05 | Đủ công cụ phụ, version/thiếu tài nguyên được báo |
| OPS-08 | Menu/search/folder gần dùng/theme/HiDPI | ED 1, 8 | P04-01, P11-05 | Thao tác chuột/phím, ngữ cảnh và tỉ lệ màn hình dùng được |
| AUTH-09 | Đổi nick/mismatch, không xoay tài khoản tự động | SB 5 | P05-10, P11-08 | Job cũ không chạy bằng nick mới; rate limit không tự coi hết hạn |
| AUTH-11 | Browser data riêng, export/dọn/xóa liên kết khác xóa profile | SB 4–5, 8 | P03-09, P10-07, P11-08 | Export không lộ session, cache cleanup không xóa profile, xóa dữ liệu có thao tác riêng |

## Acceptance gate
No data loss, wrong identity/language/combinations or success without validation; all tests pass or exact failures/blockers documented; incomplete requirements stay open.

## External/hardware blockers
Cannot close live/provider/Windows requirements using localhost or mocked tests.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P11_RESULTS.md`. No task/group passes because only one example works.

## Execution addendum — cross-platform CI stabilization (2026-10-28)

**Status: PLAN FIRST; no code changes in this addendum yet.**

### Evidence and diagnosed failures
- Latest rebuild CI run: `40635527059`.
- Linux: `tests/test_jobs.py::test_real_worker_process_validation_and_pause` observed the durable job state become terminal before the child process had exited and been reaped. This is a timing race in the test's wait condition; it must wait for both the terminal database state and scheduler child cleanup under one bounded deadline.
- Windows: `scripts/check_plan.py` uses implicit `Path.read_text()` encoding. The Windows runner's cp1252 default cannot decode the UTF-8 Vietnamese master plan. All repository text/JSON reads in this script must explicitly use UTF-8.

### Planned implementation order
1. Make plan/coverage/phase-plan reads in `scripts/check_plan.py` explicitly UTF-8; retain all existing assertions and validation scope.
2. Correct the worker integration test to poll until the job is terminal **and** its child process has been reaped, without removing the timeout or weakening result/attempt assertions.
3. Run `check_plan.py`, compileall, the full test suite and packaged proof on Linux and Windows through GitHub Actions.
4. Update this phase result only after observing actual CI outcomes. Do not claim Windows acceptance from a planned workflow or Linux-only result.

### Acceptance gate
- Plan checker passes on Windows with its default system encoding.
- Worker integration test passes deterministically and still proves successful media validation, one attempt and no leaked child process.
- Full Linux and Windows workflow outcomes are recorded separately; external live-source, Chrome identity handoff and GPU gates remain open.
