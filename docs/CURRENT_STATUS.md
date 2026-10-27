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
| P12 | Script/build app + native host, Linux build đã tạo | Frozen-worker proof cuối và Windows packaged acceptance |

Chạy `uv run fonesi-edit`. Bản CLI/prototype cũ vẫn giữ để hồi quy. Runtime, browser profiles, video và API keys không được commit.

Checkpoint local gần nhất: 65 tests qua; số cuối và artifacts sẽ ghi trong verification report. Mock transport dùng cho test cache/quota không phải dịch live. HTTP fixture nội bộ không phải bằng chứng tải YouTube/Facebook.

Các mục đang tiếp tục rà soát trước khi đóng bản phát triển: độ chính xác các control inspector/timeline, job concurrency/recovery, readiness khi tool/module được gói, frozen worker, và ghi nhận blocker thay vì báo thành công giả. Giọng AI/ASR/OCR/tracking vẫn nằm ngoài phạm vi bản hiện tại.
