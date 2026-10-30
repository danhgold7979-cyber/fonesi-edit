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

## Trim/speed increment

- One immutable ClipMap can drive real video/audio trim and speed0.5–2, with explicit duration policy. Real2s audio/video fixture -> one-second interval at2x -> approximately0.5s verified.
- Qt start/end/speed controls preserve per-row edits; invalid/beyond-source interval disables export. Source preview remains clearly distinct from output.
- Local43 tests PASS; Windows/Python3.12 run41099958032 passed41 tests on prior UI/fsync checkpoint, other matrix jobs awaited. New trim/speed increment not yet CI-verified.

## Project persistence slice

New strict project schema/save-as/open, no media auto-probe on load, missing references retained and exact rational edits preserved until explicit numeric edit. Existing destination never overwritten. UI replacement requires confirmation. Current schema rejects unsupported nonzero timeline offsets. Local54 tests PASS. Saves are bounded-size local filesystem work; no claim of interruptible network-filesystem flush or autosave/migration acceptance. Project code not yet Windows CI-verified.

## SRT editor slice

- Strict UTF-8 SRT parser/exporter, exact cue time maps, overlap/order diagnostics, literal text retained. VTT/ASS/translation/burn-in NOT_IMPLEMENTED.
- Native virtual table edits text/times/lock, bounded100-command undo/redo, asynchronous new-file save/open, no overwrite. SRT does not persist manual-lock metadata; UI states this explicitly.
- Plain-text user-controlled labels prevent accidental rich-text interpretation.
- Local72 tests PASS, Python3.12.14/Qt6.8.3/Linux/FFmpeg7.1.5. All4 jobs CI41099958032 passed41 tests on prior UI/fsync checkpoint; newer increments await CI.

## Windows project reference correction

CI41101541228 Linux PASS54, Windows FAIL1/54: UI converted a preserved POSIX reference into a drive-qualified Windows path. Fix separates original reference strings from native Path objects, preserves exact reference on save, and refuses foreign paths before probe instead of guessing a drive. New OS-dependent negative test complements the existing failing roundtrip test. Local73 tests PASS; Windows rerun pending.
