# Chrome bridge (Windows)

Extension dùng Chrome Cookies API sau thao tác người dùng và native messaging, không đọc/giải mã Chrome cookie database. Đây là đường tích hợp đã code, chưa có evidence đăng nhập thật trên Windows.

1. Build/đăng ký fonesi-native-host.exe trong Cài đặt Fonesi.
2. Mở đúng hồ sơ Chrome, vào chrome://extensions, bật chế độ developer và Load unpacked thư mục extension này. Chrome chính thức có thể yêu cầu bước thủ công/chính sách quản trị; không tắt bảo vệ trình duyệt.
3. Tạo mã ghép trong app cho đúng hồ sơ, dán vào popup extension trong chính hồ sơ đó.
4. Đăng nhập website bình thường. Chọn nền tảng trong popup và bấm gửi phiên.
5. App giữ cookie bằng Windows DPAPI. Profile/project export không chứa cookie. Connector và identity chưa xác minh phải giữ trạng thái riêng.
6. Nếu muốn giữ phiên mới, bật “Tự đồng bộ” riêng từng nền tảng. Extension chỉ đồng bộ các nền tảng đã bật qua native host, khi cookie đổi hoặc mỗi 10 phút; không tự đăng nhập hay gửi tới dịch vụ ngoài.

Không dùng extension này trên hồ sơ khác với mã ghép. Không tự đăng nhập, xử lý CAPTCHA/OTP hoặc xoay tài khoản.
