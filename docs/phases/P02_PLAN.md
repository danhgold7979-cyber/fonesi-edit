# P02 clean rebuild plan — Reproducible technical proof

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Measure actual toolchain first; retain every external gate as NOT RUN, not simulated pass. Pin versions that really install. Establish explicit time/frame tolerances with synthetic fixtures.

## Task inventory (all original tasks retained)
- [ ] P02-01: ghi toolchain/máy/OS/codec/filter/encoder/font; lấy công cụ từ nguồn tin cậy, giữ TLS/checksum/chữ ký, pin sau kiểm chứng.
- [ ] P02-02: thử yt-dlp/gallery-dl trên nguồn công khai và nguồn có cấu hình đăng nhập; quét nhiều trang, tải video/ảnh/sub theo bảng nền tảng.
- [ ] P02-03: thử dịch Trung–Việt với thuật ngữ/tên riêng/câu dài; so chất lượng, tốc độ, chi phí, cache và quota.
- [ ] P02-04: so engine preview cho Qt; mẫu alpha logo, chữ Việt/Trung, blur, seek, waveform, keyframe, audio; so mốc với FFmpeg export.
- [ ] P02-05: thử CPU/encoder GPU thật, phân biệt encode GPU và filter CPU; đo RAM/VRAM và fallback.
- [ ] P02-06: bản đóng gói Windows thử: mở UI, media/font/sub, FFmpeg, Unicode, startup. Không để P12 mới thử đóng gói.
- [ ] P02-07: benchmark có máy/mẫu; chốt ngân sách UI/proxy/seek, sai số hình/thời gian và mức song song ban đầu trước P04/P07.
- [ ] P02-08: ghi quyết định provider dịch, preview, FFmpeg build, packaging; blocker cho Windows/nguồn chưa truy cập được.
- [ ] P02-09: thử discovery/tool manifest, nguồn Windows đáng tin, đường dẫn tùy chỉnh/version/capability, tải-cài-verify và rollback khi job đang dùng bản cũ.
- [ ] P02-10: Google Chrome chính thức trên Windows, hồ sơ độc lập, nhiều nền tảng/một hồ sơ và nhiều nick cùng nền tảng khác hồ sơ; kiểm chứng session handoff vào downloader với Chrome đang mở, mã hóa hiện tại và account mismatch.

## Deliverables
scripts/prove_environment.py; docs/rebuild/evidence/environment.json; locked dependency manifest

## Tests before results may claim pass
Record actual OS, Python, Qt, FFmpeg/ffprobe versions, CPU encode/probe/decode with Unicode path, headless Qt startup and package smoke.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| SRC-02 | Mọi nền tảng đã nêu, capabilities riêng | PR 3.1 | P02-02, P05-07 | Mỗi loại nguồn có trạng thái/evidence theo bảng nền tảng |
| SUB-03 | Dịch Trung–Việt, ngữ cảnh/thuật ngữ/tên riêng | PR 4.1 | P02-03, P06-03 | Provider thật, ánh xạ cue đầy đủ, mẫu được đọc soát |
| ED-07 | Font glyph/fallback/thiếu font và Unicode | ED 3.1 | P02-04, P07-01 | Việt/Trung đúng; thiếu font có cảnh báo/thay hàng loạt |
| ED-20 | Preview-export và CPU/GPU capability | PR 8; ED 7 | P02-04, P02-05, P07-08 | Frame/time/audio trong dung sai, unsupported báo đúng |
| AUTO-04 | CPU/GPU/Auto và metrics khả dụng | PR 8 | P02-05, P10-04 | Encode thật, unknown hiển thị đúng, fallback có log |
| WIN-01 | Build tái lập, user data tách, không bộ dev | PR 11 | P02-06, P12-01 | App đóng gói chạy trên Windows mục tiêu |
| TOL-02 | Trỏ đường dẫn, chọn bản, kiểm tra hoạt động | SB 2.1 | P02-09, P03-08 | Unicode/timeout/sai version/capability báo đúng, không sửa tool ngoài |
| TOL-03 | FFmpeg/ffprobe/downloader và dependency theo workflow | SB 2.2 | P02-09, P03-08 | Manifest đúng kiến trúc/phiên bản/capability, không bắt cài dev tools vô cớ |
| TOL-05 | Trusted artifacts, TLS/checksum/chữ ký | SB 2.3 | P02-09, P03-08 | Artifact lỗi bị chặn, bản cũ và cấu hình được giữ |
| TOL-07 | Chrome chính thức quét/trỏ/tải-cài | SB 2.2, 3 | P02-10, P04-08, P12-07 | Google Chrome thật, không WebView/Chromium giả thay thế |
| AUTH-02 | Chrome thật với user-data-dir riêng, nhiều nền tảng/một hồ sơ | SB 3 | P02-10, P05-08 | Profile A lưu nhiều phiên website, đóng/mở vẫn đúng khi còn hợp lệ |
| AUTH-06 | Session handoff tương thích Chrome/OS/connector | SB 6 | P02-10, P05-09 | Bộ tải dùng phiên thật; không tắt mã hóa hoặc coi web login là đã đạt |

## Acceptance gate
CPU media proof and reproducible dependency install local; full gate also requires real Windows, Chrome, GPU and configured translation/live sources.

## External/hardware blockers
Windows/GPU/real Chrome and user credentials/provider unavailable in cloud. Known old Windows gallery-dl failure remains unresolved until re-tested.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P02_RESULTS.md`. No task/group passes because only one example works.
