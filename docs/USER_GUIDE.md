# Fonesi Edit — Hướng dẫn bản phát triển

Đây là bản phát triển desktop, không phải lời cam kết mọi mạng xã hội đã tải nguyên kênh được. Xem CURRENT_STATUS và bảng nền tảng cho phần đã thử/chưa thử.

## Chạy

Developer: `uv sync --locked` rồi `uv run fonesi-edit`. Bản đóng gói: mở FonesiEdit.exe (Windows) hoặc FonesiEdit (Linux proof). Dữ liệu app ở LocalAppData/FonesiEdit trên Windows; biến FONESI_DATA_DIR đổi vị trí khi kiểm thử. Không để dữ liệu runtime trong Git.

## Quy trình

1. Cài đặt → Công cụ: quét, chọn đường dẫn, cài thành phần thiếu hoặc rollback bản app quản lý. Tool thiếu không ngăn mở editor.
2. Editor: thêm video, chữ/logo/vùng che; kéo/resize/xoay, chỉnh inspector và keyframes. Scope clip/chọn/cả lô được lưu vào layer. Đầu ra chọn tỷ lệ/FPS/CPU-GPU/màu; Âm thanh thêm main/music/SFX và khớp duration.
3. Preview chất lượng xuất dùng compositor thật. Bấm Esc hoặc sửa thuộc tính để quay lại bố cục kéo thả; không chồng overlay lần hai lên frame đã composited.
4. Sub: mở SRT/VTT/ASS, sửa gốc/dịch/time/lock, dịch qua hàng đợi khi provider được cấu hình. Nạp kết quả là thao tác rõ ràng để giữ sửa tay; gắn sub vào clip hoặc xuất riêng.
5. Batch: chọn folder, quét, tick bỏ folder/tệp, lập kế hoạch, preview rồi enqueue. Không xóa nguồn; output nằm ở folder tên kênh kèm edit.
6. Ma trận: C1…Cn mỗi folder chứa góc, quét/sinh N/W/K/seed, sửa G1/G2 trong ô, khóa ô, preview/CSV/render. Không nới điều kiện ngầm; timeout khác vô nghiệm.
7. Tải: một URL mỗi dòng, folder, account/engine/media/limit/sub; 0 là không giới hạn ở adapter hỗ trợ. Kết quả quét không đồng nghĩa đã tải hết kênh. Có thể bật workflow edit/dịch sau tải hoặc đặt lịch.
8. Hàng đợi: pause ngừng nhận việc mới; cancel dừng đúng job; retry riêng việc lỗi. Job dùng snapshot, sửa preset sau đó không đổi việc đang chạy.

## Chrome thật

Một profile dùng nhiều nền tảng; nhiều nick cùng nền tảng dùng profile khác. Tạo hồ sơ trong Cài đặt, mở login trong Google Chrome, người dùng tự nhập mật khẩu/OTP/QR/CAPTCHA. Đăng ký native host và load extension theo extension/README.md, ghép bằng mã 5 phút. Gửi phiên hoặc bật đồng bộ riêng từng nền tảng. Windows DPAPI bảo vệ dữ liệu; không có plaintext fallback Linux.

Đăng nhập website, có snapshot cookie, danh tính và khả năng connector dùng phiên là các kiểm tra khác nhau. Không tắt Chrome protection hoặc coi HTTP 403 luôn là hết hạn. Tài khoản đổi nick bị phát hiện khi có danh tính đáng tin cậy; nền tảng khác vẫn hiển thị identity_unverified.

## Dịch và chi phí

Google hoặc LibreTranslate do bạn cấu hình. API key nhập ở Settings, không nằm trong project/preset; Windows lưu bằng DPAPI, Linux chỉ giữ trong bộ nhớ phiên. Có quota ký tự theo ngày và cache. Request timeout có thể chưa biết đã tính phí: không tự retry trả phí vô điều kiện. Giọng AI/ASR/OCR/tracking chưa thuộc bản này.

## Giới hạn và phục hồi

Thiếu sub mặc định tiếp tục có cảnh báo. Font thiếu glyph phải chọn font phù hợp. GPU phải encode thật được; Auto không có nghĩa mọi filter chạy GPU. Đóng app có thể hủy việc đang làm để lưu phục hồi; bật nền chỉ có tác dụng khi có system tray. Lịch chỉ chạy khi app/process đang hoạt động; không tự có Windows service.

Project tự lưu, có recovery và liên kết lại media. Giữ nguồn, không overwrite output khác cấu hình; output hợp lệ cùng hash/config có thể tái sử dụng. Không xuất cookie/API key hoặc gửi dữ liệu hồ sơ Chrome vào báo lỗi.
