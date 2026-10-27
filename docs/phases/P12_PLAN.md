# P12 — Đóng gói và bàn giao

Đã đọc master P12, trạng thái P11 và yêu cầu Cài đặt/Chrome. Người dùng cho hoàn tất mọi phần độc lập; Windows/auth thực chưa có evidence thì vẫn giữ mở.

1. Entrypoint app thật và worker mode trong binary; native messaging host riêng, không phụ thuộc Python cài ngoài.
2. PyInstaller collect các adapter/formats/extractor/JS EJS, Qt plugins và extension assets; FFmpeg/ffprobe binary được resolve đúng trong bundle.
3. Build Linux để kiểm tra layout/worker/frozen mode; script và CI Windows cùng build app/native host rồi chạy packaged smoke/job CPU.
4. Gói hướng dẫn tiếng Việt, notices/công cụ, dữ liệu user tách thư mục cài, version/provenance và giới hạn thật.
5. Test source và frozen app startup/media/render worker/queue, không chỉ thấy file EXE. Không tự publish release công khai; push code/plan và artifact review trong CI.
