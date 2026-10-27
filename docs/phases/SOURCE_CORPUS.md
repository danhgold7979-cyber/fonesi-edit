# Corpus phát triển và nghiệm thu

Không có thông tin đăng nhập hoặc media riêng tư trong repository.

| Mẫu | Nguồn | Mục đích | Cách kiểm chứng |
| --- | --- | --- | --- |
| synthetic-landscape | FFmpeg lavfi testsrc + sine, gắn nhãn synthetic | Render/frame/time/audio và benchmark CPU | Probe + decode + đối chiếu thời gian, không coi là tải live |
| synthetic-portrait | Như trên, khung dọc | Tọa độ tương đối, crop, subtitle wrapping | Frame tại các mốc |
| unicode-path | Bản fixture có đường dẫn Việt/Trung | Path escaping/Unicode, font | Render qua argument list, kiểm tra artifact |
| subtitle-vi | SRT tiếng Việt tự tạo có timestamp xác định | Parser, burn-in, font/layout | Kiểm tra text/cue/frame |
| subtitle-zh | SRT tiếng Trung tự tạo, thuật ngữ, tên riêng | Dịch thật khi provider được cấu hình | Đọc soát bản dịch; chưa có key thì blocked |
| YouTube test item | https://www.youtube.com/watch?v=BaW_jenozKc | Mẫu công khai thường dùng bởi yt-dlp | Live request, metadata và artifact; bị chặn ghi đúng lỗi |
| channel samples | Từng platform trong PLATFORM_SUPPORT_MATRIX | Quét nhiều trang, ảnh/album/sub | Cần nguồn truy cập được; không đoán khả năng từ item đơn |
| Chrome A/B | Google Chrome chính thức trên Windows | Profile isolation, auth/bridge/mismatch | Chưa có Windows/profile/account trong cloud Linux |

Phép đo P02: elapsed wall time, FPS/output duration, probe tracks, startup/proxy/seek/UI latency; ghi OS/tool versions và sample parameters. Ngân sách Windows/UI/GPU chỉ chốt sau có máy thật, không suy từ core count.

External prerequisites hiện tại: Windows để packaging/Chrome thực; tài khoản nguồn do người dùng thao tác trong browser; cấu hình provider dịch nếu dùng API; GPU tương ứng nếu kiểm tra tăng tốc. Tiếp tục mọi phép thử CPU/local không phụ thuộc chúng.
