# P05 clean rebuild plan — Downloads, sessions and source organization

Status: PLANNED; authored before clean implementation on `rebuild/spec-first-2026-10-28`.
Baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Previous evidence is historical, never new-code evidence.

## Alignment and dependencies
Master: [REBUILD_MASTER_PLAN.md](../REBUILD_MASTER_PLAN.md). Original scope: [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md), three source specifications.
Dependencies: P01 contracts; prior phase interfaces (independent local work proceeds while external gates remain open).

## Concrete execution order
Build adapters around pinned yt-dlp/gallery-dl without copying old source; separate scan result from download, validate image/video separately (known old packaged image issue); create official Chrome profiles and fail-closed account preflight.

## Task inventory (all original tasks retained)
- [ ] P05-01: registry/capabilities, nhiều URL, bài/kênh/playlist, ID chuẩn và loại trùng.
- [ ] P05-02: phân trang/checkpoint, ảnh/video/Reels/Shorts/album khi nguồn hỗ trợ, lọc ngày/thời lượng/số lượng/chất lượng.
- [ ] P05-03: cây nội dung, chọn mục, tổng chưa biết/quét ngắt, cancel và tiếp tục khi hỗ trợ.
- [ ] P05-04: downloader/tệp tạm/validation, tốc độ/retry/rate limit/auth; không log cookie/token.
- [ ] P05-05: folder/kênh/album Unicode có ID, video/images/subtitles/metadata, thiếu đĩa/quyền ghi/tên dài/xung đột.
- [ ] P05-06: chống trùng theo ID/chất lượng/tệp hợp lệ; bổ sung sub riêng, tải lại tệp lỗi, đồng bộ lần hai và kênh đổi tên.
- [ ] P05-07: kiểm chứng nguồn/loại media/auth, lưu ngày/phiên bản/evidence. Thiếu quyền ghi blocker, không dùng mock để báo hỗ trợ.
- [ ] P05-08: profile manager mở Chrome thật vào đúng user-data-dir/nền tảng, tạo/đặt tên/gán nhiều nền tảng, tách nick cùng nền tảng, xử lý khóa/bận mà không phá profile.
- [ ] P05-09: session broker theo cơ chế đạt P02, đăng nhập/kiểm tra/đăng nhập lại cho mọi nền tảng, nhận diện nick, trạng thái website khác khả năng connector dùng phiên và quyền nguồn.
- [ ] P05-10: chọn account theo nguồn/job, nhớ mặc định, refresh cùng danh tính/resume, mismatch chặn đúng job; không silent fallback sang công khai hoặc tự xoay nick; auth cache không lẫn tài khoản.

## Deliverables
src/fonesi_edit/services/{downloads,browser,tools}.py; tests/test_downloads.py; extension/

## Tests before results may claim pass
URL registry/normalization and duplicate handling; scan completeness; filters; bounded retry; local HTTP video/image download; validate bytes before finalizing; account identity mismatch and isolated caches.

## Requirement traceability
| ID | Requirement | Source | Tasks | Required acceptance evidence |
| --- | --- | --- | --- | --- |
| SRC-01 | Nhiều URL, nhận diện bài/kênh/playlist, loại trùng | PR 3.2 | P05-01 | URL cùng nguồn chuẩn hóa đúng ID, không coi bài là kênh |
| SRC-02 | Mọi nền tảng đã nêu, capabilities riêng | PR 3.1 | P02-02, P05-07 | Mỗi loại nguồn có trạng thái/evidence theo bảng nền tảng |
| SRC-03 | Quét kênh nhiều trang, checkpoint, dở/đủ/unknown | PR 3.2–3.3 | P05-02, P05-03 | Quét ngắt không bị báo toàn kênh xong |
| SRC-04 | Ảnh/video/cả hai, Shorts/Reels/album | PR 3 | P05-02 | Loại tải đúng checkbox, thứ tự bài nhiều ảnh đúng |
| SRC-05 | Ngày/số lượng/thời lượng/chất lượng/thứ tự | PR 3.2 | P05-02 | Dữ liệu biên được lọc đúng, tùy chọn nguồn thiếu được báo |
| SRC-06 | Đăng nhập, hết hạn, rate limit, retry/resume | PR 3.2 | P05-04 | Lỗi auth chờ đúng nguồn, retry giới hạn, không log bí mật |
| SRC-07 | Folder kênh có ID, Unicode, album và tên dài | PR 3.3 | P05-05 | Hai kênh trùng tên không nhập chung hoặc ghi đè |
| SRC-08 | Tệp tạm, validation, thiếu quyền/đĩa | PR 3.3 | P03-06, P05-04 | Tệp dở/hỏng không thành công, nguồn giữ nguyên |
| SRC-09 | Chống tải trùng, bổ sung sub, nâng chất lượng | PR 3.3 | P05-06 | Quét lại không tải dư; thiếu sub chỉ lấy sub khi phù hợp |
| SRC-10 | Đồng bộ mới, thumbnail/metadata nếu nguồn có | PR 3.2 | P05-02, P05-06 | Nội dung mới được thêm và phần không có ghi đúng |
| AUTH-01 | Mọi nền tảng có trang đăng nhập và chọn binding | PR 13; SB 4.2 | P01-08, P04-08, P05-09 | Đủ nền tảng đã nêu, capability/auth chưa thử được ghi đúng |
| AUTH-02 | Chrome thật với user-data-dir riêng, nhiều nền tảng/một hồ sơ | SB 3 | P02-10, P05-08 | Profile A lưu nhiều phiên website, đóng/mở vẫn đúng khi còn hợp lệ |
| AUTH-03 | Nhiều nick cùng nền tảng ở hồ sơ khác nhau | SB 3 | P03-09, P05-08 | Facebook A/B không chia cookie, không nhầm nhiều cửa sổ là nhiều profile |
| AUTH-04 | Tạo/đặt tên/mở/gán/default/profile bận-khóa | SB 4.1 | P04-08, P05-08 | Mở đúng hồ sơ, không xóa lock/chiếm profile cá nhân |
| AUTH-05 | Login/kiểm tra/relogin qua Chrome, người dùng xử lý xác minh | SB 4.2 | P05-09 | Mật khẩu/OTP không lưu trong app, kiểm tra sau login thật |
| AUTH-06 | Session handoff tương thích Chrome/OS/connector | SB 6 | P02-10, P05-09 | Bộ tải dùng phiên thật; không tắt mã hóa hoặc coi web login là đã đạt |
| AUTH-07 | Job gán đúng account/profile, snapshot chỉ ref | SB 5 | P03-09, P05-10 | Nick chọn được giữ, project/job không chứa cookie/token |
| AUTH-08 | Expired/challenge/bridge lỗi/quyền nguồn tách biệt | SB 4.3–5 | P05-09, P10-07 | Dừng đúng job, relogin rồi resume, không tải trùng/đổi public ngầm |
| AUTH-09 | Đổi nick/mismatch, không xoay tài khoản tự động | SB 5 | P05-10, P11-08 | Job cũ không chạy bằng nick mới; rate limit không tự coi hết hạn |

## Acceptance gate
Only independently verified capabilities labeled verified; correct source ID and folder, no incomplete scan called complete, no selected account silently falls back to public.

## External/hardware blockers
Live social APIs/accounts and Windows Chrome session bridge require user-owned accounts and real environment.

## Result recording
Record implemented code paths, exact command/commit, pass/fail/not-run/skipped, remaining UI/subproperties and external prerequisites in `P05_RESULTS.md`. No task/group passes because only one example works.
