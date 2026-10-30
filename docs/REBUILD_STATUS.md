# Trạng thái làm lại Fonesi Edit

- Repo: danhgold7979-cyber/fonesi-edit
- Nhánh local: rebuild
- Main baseline: 5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d
- Integration baseline thực tế: edbb47189b0e864c74623d0a4db5b5f169f2103c (develop/fonesi-full), 616 commit sau main
- Giai đoạn: P01/P02 còn rà soát; triển khai độc lập P03-01/03/05, chưa nghiệm thu toàn phase.
- Nghiệm thu bản làm lại: 0 task; chưa khóa denominator sau audit.
- Backup: complete Git bundle verified; independent restore matches baseline.
- Đã sửa: REBUILD_REVIEW.md, REBUILD_STATUS.md (local, chưa push).
- Đã loại implementation/test/build/extension cũ khỏi nhánh rebuild trong commit riêng; lịch sử và full bundle giữ nguyên.
- Code mới: timing.py (rational time map), snapshot.py (immutable versioned intent).
- Test mới: 38/38 unittest PASS trên Python 3.12.14 Linux; chưa test Windows.
- SQLite intent/lease ledger đã có code và test mới; không có worker/render thực thi hoặc validation artifact hoàn chỉnh.
- Đã publish checkpoint foundation đầu tiên: 4037276770bff5f002f11d9e4e42cdd2ea8d9d7e; main giữ nguyên.
- Real CPU proof mới: synthetic CFR24 1s -> H.264 MP4 -> full decode/ffprobe/hash/no-overwrite; FFmpeg/ffprobe 7.1.5 Linux. Không chứng nhận editor đầy đủ hoặc VFR/GPU/Windows.
- CI 41098300494: 27 foundation tests PASS trên Linux/Windows, Python 3.12/3.13. Media increment chưa chạy CI.
- Chưa làm: UI/worker/editor render graph, acceptance Windows/live.
- Kết quả 92 tests của baseline là lịch sử, không phải pass của rebuild.
- Tiếp theo: khóa hợp đồng triển khai chi tiết và sửa toàn bộ Pxx_PLAN trước khi code.
- Blocker target: Windows/Chrome/GPU/live provider validation chưa được thực hiện cho rebuild; không chặn công việc độc lập.

## UI increment and Windows failure correction

- Added app.py, Qt UI tests, PRODUCT.md, DESIGN.md and UI slice plan. Real import/preview/export, busy/cancel/close protection; unimplemented workspaces visibly disabled.
- Local 41 tests PASS under Python3.12.14, PySide6 6.8.3, FFmpeg7.1.5; two inspected synthetic screenshots1280/1600.
- CI41099091424: Linux3.12/3.13 PASS38; Windows3.12/3.13 FAIL1/38 at fsync on read-only staged descriptor (Errno9). Fix opens ONLY owned staged output r+b before fsync; source remains read-only and no-overwrite unchanged. Windows rerun pending.
- Source proof does not establish Windows user-machine acceptance, installer, complete timeline/editor, live download/auth or provider translation.
