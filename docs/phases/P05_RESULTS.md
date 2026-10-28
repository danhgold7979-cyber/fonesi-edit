# P05 — Kết quả adapter và session

Đã code nhận diện nền tảng/URL, yt-dlp và gallery-dl scan/download trong worker, template folder, no-overwrite, lọc/ngôn ngữ sub, cookie jar theo binding và profile store. Có extension MV3 với thao tác gửi phiên rõ ràng, native messaging pairing mã hết hạn, Windows DPAPI và account mismatch cho danh tính xác định được; không đọc Chrome cookie DB.

Kiểm tra local gồm URL chống nhầm host, Windows filename, profile/binding isolation, pairing single-use và không có plaintext fallback. Download HTTP media từ server fixture nội bộ được test riêng, không thay kiểm chứng YouTube/Facebook/kênh nhiều trang. Live network/auth/Chrome thật vẫn mở.

## P05-03 — Quét → chọn mục → tải; phân trang hiển thị (28/10/2026)

Triển khai trên **một nhánh tích hợp** `develop/fonesi-full`, không tách riêng bộ tải:

- `downloads.py`: scan từ yt-dlp/gallery-dl trả metadata từng item có ID/kiểu media/adapter/URL tải lại (nếu đủ an toàn). URL có tài khoản trong authority, signed query/token/CDN query hoặc fragment không được đưa vào URL selectable; item không đủ URL bị gắn trạng thái không chọn được. Flat playlist của YouTube/Bilibili được chuẩn hóa từ **đúng loại extractor và ID đã được xác thực cú pháp**, không suy ra cho nền tảng không rõ. Không coi item scan xong là scan toàn kênh.
- `DownloadsPage`: danh sách scan chọn lại được sau mở app, cây Qt checkbox có trạng thái URL, nút chọn/bỏ chọn, tạo job tải riêng từ scan snapshot, phân trang tối đa 200 hàng hiển thị, checkbox giữ lại qua nhiều trang, không chọn URL trùng trong một scan.
- `selected_download_payloads`: giữ snapshot thư mục/tài khoản/identity/sub/lang/chất lượng/auto-edit, khóa cross-platform account binding, giữ engine video/gallery đúng theo chính item gốc kể cả nguồn mixed-media, chỉ đưa URL hợp lệ vào job. `submit_once` tránh enqueue lặp khi bấm nút hai lần; job cũ cần Retry trong hàng đợi, không tự đổi account.
- Test nguồn thật **chỉ trên localhost**: gallery scan ảnh → item được chọn → download file PNG hợp lệ. Test synthetic: URL ký bị từ chối, YouTube/Bilibili flat ID, adapter mixed, lựa chọn trùng, stale/mismatch account, Qt tree và đa chọn qua nhiều trang, reopen/history.

**Bằng chứng CI:** [run 40641870092](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40641870092) — **Linux 162 passed; Windows 161 passed + 1 skipped** (fixture lệnh shell chỉ chạy POSIX). Cả hai runner cũng build production app/native-host và chạy frozen packaged proof qua FFmpeg, batch/ma trận, tải video/ảnh từ localhost và Qt smoke/frame decode. Development binary cho Windows được lưu dưới artifact `FonesiEdit-Windows-development` có ngày hết hạn.

**Không tuyên bố P05 đã hoàn tất toàn bộ.** Phân trang checkbox chỉ là phân trang **hiển thị**, không phải phân trang/checkpoint API nguồn. Chưa có live corpus quét nguyên kênh ở 10 nền tảng, Chrome→connector qua tài khoản thực, quyền nguồn/region, album ở mọi adapter, nâng chất lượng/bổ sung sub đơn lẻ, filter/sort đầy đủ, kiểm thử click chọn cực lớn, và test mạng/xác thực trên Windows người dùng.

## P05-04/05 — strict payload validation, CookieJar transport and repeat-image safety (28/10/2026)

- `execute_download_job` now rejects malformed job/payload/URL, engine and media types, booleans/floats/non-integer limits, negative limits and non-HTTP(S) URLs before creating the destination folder.
- The gallery CookieJar fixture now requires the synthetic cookie on the localhost image endpoint, proving the initialized gallery session actually sends the selected cookie; it remains a synthetic transport test, not Chrome/live-account acceptance.
- Added scan → select → download → repeat-download coverage for gallery images in a Unicode folder. The existing file path, bytes and modification time must remain unchanged; the file is checked as a readable PNG.
- CI [run 40736655575](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40736655575) **PASS**: 421 Linux tests; 420 Windows tests + 1 intentional POSIX-fixture skip. Production desktop/native host and frozen proof passed on both runners.
- The dedicated repeat-image slice [run 40735733292](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40735733292) also passed: 413 Linux / 412 Windows + 1 intentional skip, packaged proof both systems.
- Still open: provider pagination/checkpoint, live platform corpus, Chrome/session handoff on a real account, region/permission behavior and Windows user-machine acceptance. P05 is not fully closed.

