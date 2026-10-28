# Fonesi Edit — Trạng thái triển khai

Bản phát triển, chưa tuyên bố nghiệm thu toàn bộ 95 nhóm yêu cầu. Theo chỉ đạo người dùng, tiếp tục phần độc lập qua mọi phase; không dừng vì mạng/tài khoản/Windows/GPU và không gắn các mục đó là pass.

| Phase | Code/kiểm chứng hiện có | Cổng còn riêng |
| --- | --- | --- |
| P01 | Thiết kế, luồng, contracts, traceability | Cập nhật theo thay đổi đã được chấp thuận |
| P02 | Proof CPU/Qt/FFmpeg và package Linux | Live nguồn/dịch/Windows/Chrome/GPU |
| P03 | Domain, SQLite, snapshots, jobs, subprocess, recovery, registry | Độ bền dài hạn/Windows |
| P04 | Canvas/inspector/timeline/undo/project và phím tắt nền | Hoàn thiện chi tiết tương tác/parity mọi trường hợp |
| P05 | yt-dlp/gallery-dl, profile/binding, extension/native handoff | Live nguyên kênh, từng nền tảng và Chrome Windows |
| P06 | SRT/VTT/ASS, sửa/lock/cache/quota/provider adapters | Chất lượng/chi phí dịch live và kiểm tra ngôn ngữ provider |
| P07 | Compositor, motion/keyframes, font, mask, alpha, audio, reference | Từng tổ hợp style/OS/GPU, performance target |
| P08 | Folder dry-run, output theo kênh, duration solver/loop/freeze | Corpus lớn và lỗi ngoài môi trường |
| P09 | Lazy matrix, W/K/history/reservations/CSV/rows | Solver constraints lớn, thao tác tất cả kiểu khóa |
| P10 | Workflow/watch/schedule, metrics/admission/tools | Installer/auth/driver Windows thực tế |
| P11 | Test local và app integration đang mở rộng | Regression cuối và đối chiếu đầy đủ tùy chọn |
| P12 | Script/build app + native host, Linux build đã tạo | Linux frozen-worker proof đã qua; Windows packaged acceptance còn mở |

Chạy `uv run fonesi-edit`. Bản CLI/prototype cũ vẫn giữ để hồi quy. Runtime, browser profiles, video và API keys không được commit.

Kiểm chứng cuối: **92 tests qua, 0 fail/error/skip**; binary Linux chạy 4 job thật (batch/ma trận song ngữ, tải video/ảnh localhost), rename/undo, mở UI và giải mã frame Qt. 36 file source khớp hash của bundle. Xem [báo cáo](LOCAL_VERIFICATION.md), [evidence JSON](evidence/desktop-verification.json) và [phần đã có/còn mở theo 95 nhóm](IMPLEMENTATION_COVERAGE.md).

CI Windows/Linux đã có build production/native host, proof từ binary và artifact phát triển; chưa xác nhận CI Windows đã thành công. Mạng xã hội nguyên kênh, API dịch thật, Chrome Windows/GPU/HiDPI/audio máy thật vẫn cần kiểm chứng riêng. Những tùy chọn nâng cao chưa hoàn tất tiếp tục được ghi trong coverage, không tự đổi thành đã đạt hoặc loại khỏi phạm vi. Giọng AI/ASR/OCR/tracking thuộc giai đoạn sau.
