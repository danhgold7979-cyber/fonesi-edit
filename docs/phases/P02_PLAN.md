# P02 — Plan chi tiết trước khi code kiểm chứng

Đã đọc lại IMPLEMENTATION_PLAN v1.1 và P01_RESULTS. P01 đã chốt thiết kế; P02 xây mẫu chạy thật trước khi scaffold sản phẩm P03. Không đánh dấu P03 bắt đầu khi cổng P02 còn thiếu bằng chứng.

## Lát cắt triển khai

1. Khóa môi trường Python 3.12, Qt/PySide6, yt-dlp, gallery-dl và pytest bằng lockfile; dùng FFmpeg/ffprobe hiện có. Không tải binary không xác minh.
2. Code namespace `fonesi_edit.prototypes`: probe và render media thật, scan công cụ và Chrome chính thức, adapter dịch chỉ chạy khi có cấu hình hợp lệ.
3. Tạo fixture lavfi có nhãn synthetic, sub Việt/Trung, đường dẫn Unicode; render CPU có sub, text/logo alpha và vùng che, kiểm tra tracks/duration/decode.
4. Prototype Qt mở media cục bộ, kiểm tra tool, cấu hình render, preview tham chiếu do FFmpeg tạo và playback bằng QtMultimedia. Kéo overlay là phép thử UX, không tự nhận full editor P04.
5. Thử live public metadata/download có timeout và ghi lỗi cụ thể. Không bắt người dùng đưa tài khoản trong chat; không đọc browser profile cá nhân.
6. Kiểm tra encoder CPU/GPU bằng encode thật; so font/alpha/frame khi engine hỗ trợ. Ghi unknown/blocked thay vì pass khi chưa có phần cứng.
7. Ghi version, command, fixture, timings và kết quả ở P02_RESULTS; tách local PASS khỏi live source/translation/Windows/Chrome BLOCKED.

## Kiểm tra bắt buộc trước đóng phase

- Unit/integration có ý nghĩa: cue parser/time mapping, path Unicode/escaping, no overwrite, FFmpeg failure, media validation; real FFmpeg output và Qt offscreen smoke.
- Proof download từ một URL không thay kiểm chứng kênh nhiều trang.
- Provider thiếu key chỉ xác minh báo cấu hình thiếu; không coi là bản dịch thật.
- Windows packaging và Chrome thật cần Windows; Chromium Linux không phải evidence thay thế.
- Nếu thiếu prerequisite bên ngoài, hoàn thành mọi nhánh độc lập và ghi BLOCKED rõ; chưa chuyển phase phụ thuộc hoặc tuyên bố toàn app sẵn sàng.

## Không làm trong phase này

Chưa triển khai DB/scheduler bền vững, tất cả connector/auth, installer tự động, batch và ma trận hoàn chỉnh; chúng có phase riêng. Không dựng button giả báo thành công cho chức năng chưa có.
