# P05 — Nguồn tải và tài khoản

Đã đọc master P05, bảng nền tảng, SETTINGS_AND_BROWSER_SPEC và nền Store/P04. Giữ nguyên trạng thái live network bị proxy chặn; không chặn code adapter.

1. Registry nhận diện 10 nền tảng, URL item/profile và account scope. yt-dlp cho video; gallery-dl cho ảnh/album, hỗ trợ source có thể truy cập khi công cụ đáp ứng.
2. Job scan riêng download; phân trang/lazy/max-items/filters, progress chưa biết tổng, metadata stable ID và thư mục video/images/subtitles.
3. Archive theo platform/account/ID, không tải lại tệp hợp lệ; validation và retry có giới hạn, không log URL chứa secret.
4. Profile/binding lưu SQLite, Google Chrome thật; extension MV3 dùng Cookies API sau thao tác người dùng, native host lưu session bằng DPAPI Windows. Không copy/giải mã Chrome DB hoặc tắt bảo vệ.
5. CookieJar trong worker đúng binding; expired/mismatch/unsupported identity báo riêng. Không tự xoay account hoặc public fallback khi đã chọn account.
6. Test adapters bằng server media cục bộ có nhãn, các lỗi parser/config/identity và profile isolation. Live platform/auth/Windows giữ cổng riêng.

UI điều khiển nằm trong app production; mỗi nền tảng có cấu hình login nhưng không gắn nhãn dùng phiên được trước phép thử thật.
