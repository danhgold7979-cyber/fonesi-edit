# Fonesi Edit — Hướng dẫn bản phát triển

Đây là bản phát triển desktop, không phải lời cam kết mọi mạng xã hội đã tải nguyên kênh được. Xem CURRENT_STATUS và bảng nền tảng cho phần đã thử/chưa thử.

## Chạy

Developer: `uv sync --locked` rồi `uv run fonesi-edit`. Bản đóng gói: mở FonesiEdit.exe (Windows) hoặc FonesiEdit (Linux proof). Dữ liệu app ở LocalAppData/FonesiEdit trên Windows; biến FONESI_DATA_DIR đổi vị trí khi kiểm thử. Không để dữ liệu runtime trong Git.

## Quy trình

1. Cài đặt → Công cụ: quét, chọn đường dẫn, cài thành phần thiếu hoặc rollback bản app quản lý. Nếu bản đã cài bị hỏng, nút cài tải bản sửa vào thư mục mới, giữ bản cũ. Tool thiếu không ngăn mở editor.
2. Editor: thêm video, chữ/logo/vùng che; kéo/resize/xoay, chỉnh inspector và keyframes. Ctrl/Shift và hộp chọn để chọn nhiều, menu Thao tác thêm có nhóm/căn/phân bố/ẩn/khóa/copy kiểu; double-click chữ để sửa. Double-click clip mở trim/speed/flip/rotation/âm gốc. Scope clip/chọn/cả lô được lưu vào layer. Đầu ra chọn tỷ lệ/FPS/CPU-GPU/màu; Âm thanh thêm main/music/SFX, mute/solo/trim/fade/loop và khớp duration. Đầu ra có thiết lập riêng cho clip tạo trong batch/ma trận, gồm trim đầu/đuôi, speed/flip/rotation/gain và random flip/rotation/zoom có seed.
3. Preview chất lượng xuất dùng compositor thật. Bấm Esc hoặc sửa thuộc tính để quay lại bố cục kéo thả; không chồng overlay lần hai lên frame đã composited. Thao tác thêm → Preview có âm thanh dựng bản phát từ cùng compositor. Playback nguồn vừa mở chưa bao gồm mọi thay đổi; sau khi sửa cần tạo lại bản dựng. Waveform tạo nền, không chặn UI.
4. Sub: mở SRT/VTT/ASS, sửa gốc/dịch/time/lock, dịch qua hàng đợi khi provider được cấu hình. Nạp kết quả là thao tác rõ ràng để giữ sửa tay; gắn sub vào clip hoặc xuất riêng. Bật Song ngữ để tạo riêng layer gốc và bản dịch khi hai nội dung đã có. Sub đã gắn thành layer kéo được trên preview, lưu bố cục vào preset; batch/ma trận tự ghép lại file sub của từng nguồn. Bảng sub có draft tự lưu, tìm/thay/offset và dịch câu chọn; nạp bản dịch giữ câu đã sửa hoặc khóa sau khi gửi.
5. Batch: chọn folder, quét, tick bỏ folder/tệp, lập kế hoạch, preview rồi enqueue. Không xóa nguồn; output nằm ở folder tên kênh kèm edit.
6. Ma trận: C1…Cn mỗi folder chứa góc, quét/sinh N/W/K/seed, sửa G1/G2 trong ô, khóa ô, preview/CSV/render. Không nới điều kiện ngầm; timeout khác vô nghiệm. Preview đổi tên C/G cho xem ánh xạ video/sub trước khi đổi thật, giữ bytes nguồn và lưu journal trong `.fonesi-renames` để hoàn tác/phục hồi. Queue còn dùng nguồn phải hoàn tất/hủy trước; liên kết project đang mở được cập nhật.
7. Tải: một URL mỗi dòng, folder, account/engine/media/limit/sub; 0 là không giới hạn ở adapter hỗ trợ. Kết quả quét không đồng nghĩa đã tải hết kênh. Có thể bật workflow edit/dịch sau tải hoặc đặt lịch.
8. Cài đặt → Tự động / máy: giới hạn tổng và riêng scan/download/render/translate; nút gợi ý theo CPU/RAM/đĩa hiện tại. Gợi ý không thay benchmark. Tài nguyên thấp chỉ dừng nhận thêm việc.
9. Hàng đợi: pause ngừng nhận việc mới; cancel dừng đúng job; retry riêng việc lỗi. Job dùng snapshot, sửa preset sau đó không đổi việc đang chạy.

## Chrome thật

Một profile dùng nhiều nền tảng; nhiều nick cùng nền tảng dùng profile khác. Tạo hồ sơ trong Cài đặt, mở login trong Google Chrome, người dùng tự nhập mật khẩu/OTP/QR/CAPTCHA. Đăng ký native host và load extension theo extension/README.md, ghép bằng mã 5 phút. Gửi phiên hoặc bật đồng bộ riêng từng nền tảng. Quên phiên chỉ xóa snapshot trong app; Thu hồi ghép extension ngăn extension gửi tiếp đến khi ghép mã mới. Windows DPAPI bảo vệ dữ liệu; không có plaintext fallback Linux.

Đăng nhập website, có snapshot cookie, danh tính và khả năng connector dùng phiên là các kiểm tra khác nhau. Không tắt Chrome protection hoặc coi HTTP 403 luôn là hết hạn. Tài khoản đổi nick bị phát hiện khi có danh tính đáng tin cậy; nền tảng khác vẫn hiển thị identity_unverified.

## Dịch và chi phí

Google hoặc LibreTranslate do bạn cấu hình. API key nhập ở Settings, không nằm trong project/preset; Windows lưu bằng DPAPI, Linux chỉ giữ trong bộ nhớ phiên. Có quota ký tự theo ngày và cache. Request timeout có thể chưa biết đã tính phí: không tự retry trả phí vô điều kiện. Giọng AI/ASR/OCR/tracking chưa thuộc bản này.

## Giới hạn và phục hồi

Thiếu sub mặc định tiếp tục có cảnh báo. Font thiếu glyph phải chọn font phù hợp. GPU phải encode thật được; Auto không có nghĩa mọi filter chạy GPU. Đóng app có thể hủy việc đang làm để lưu phục hồi; bật nền chỉ có tác dụng khi có system tray. Lịch chỉ chạy khi app/process đang hoạt động; không tự có Windows service.

Project tự lưu, có recovery và liên kết lại media. Menu Thao tác có nhập/xuất preset `.fonesipreset` theo schema; tài nguyên logo/font/audio tham chiếu đường dẫn, cần sao chép riêng nếu chuyển máy. Giữ nguồn, không overwrite output khác cấu hình; output hợp lệ cùng hash/config có thể tái sử dụng. Không xuất cookie/API key hoặc gửi dữ liệu hồ sơ Chrome vào báo lỗi.

## Phím tắt và kiểm chứng

Ctrl+S lưu project; Ctrl+Z/Ctrl+Shift+Z undo/redo; Ctrl+B chia clip; I/O đặt In/Out; Ctrl+G/Ctrl+Shift+G nhóm/bỏ nhóm; Ctrl+L khóa layer; M đặt marker; Space phát/dừng; Ctrl+, cài đặt; F5 quét công cụ; F1 hướng dẫn. Menu Thao tác cho đổi phím và kiểm tra trùng. Mũi tên/Shift+mũi tên trên canvas dịch 1/10 pixel; trên timeline đi 1 frame/1 giây. Alt tắt snap tạm, Ctrl+con lăn zoom. Delete chỉ bỏ layer khỏi project.

Developer có thể chạy `uv run fonesi-edit --verify .local/proof-new` và `uv run python scripts/verify_packaged.py` sau build. Chỉ dùng dữ liệu synthetic/localhost, không xác nhận tải mạng xã hội hay dịch live. Xem [đối chiếu triển khai](IMPLEMENTATION_COVERAGE.md) cho các tùy chọn còn mở.


## Preview In–Out, thumbnail và proxy (bản development)

Trong **Editor / preset**, đặt In bằng **I** và Out bằng **O**, rồi vào **Thao tác thêm → Lặp đoạn In–Out (preview đã render)**. Loop chỉ seek trong video dựng bằng compositor đúng composition hiện tại, không lặp trực tiếp theo timestamp file gốc khi clip có trim/speed. Sau khi chỉnh layer/clip cần dựng lại preview.

**Thao tác thêm → Thumbnail video trên timeline (tạo nền)**: bật/tắt bằng undo/save project; app tạo 3 PNG nguồn/clip đang nhìn thấy, dùng FFmpeg/cache background, không thay media. Đây là ảnh của video *nguồn*, không phải frame chứa hiệu ứng final.

**Thao tác thêm → Proxy nguồn**: chọn Không dùng / Nhanh (640px) / Cân bằng (1280px) / Cao (1920px). FFmpeg tạo MP4 H.264/AAC theo nguồn đang chọn trong cache per-user, validate trước khi dùng; video gốc và export final luôn giữ nguyên. Proxy chỉ tăng tốc phát **nguồn**, không phản ánh toàn bộ text/logo/sub; dùng nút **Preview có âm thanh** để kiểm tra composition đã dựng.

Trong **Cài đặt → Tự động / máy**, đặt **Giới hạn cache proxy (MiB)** (128–65536, mặc định 4096) và bấm **Dọn cache proxy an toàn** nếu muốn quét ngay. App dọn file proxy cũ chỉ có filename hash khi vượt quota; không xóa thư mục tải, nguồn, render output, media đang phát, hồ sơ Chrome hoặc tool. Cache downloader/dịch có phạm vi quản lý khác.
