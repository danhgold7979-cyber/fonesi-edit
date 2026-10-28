# P10 — Auto và tools triển khai

Đã có idempotent job IDs, dependency workflow download→translate→render, watcher ổn định/loại output, schedule persisted và chống overlap, resource metrics/admission/profile/giới hạn từng loại, heartbeat worker. Tool manager có TLS/hash/staging/archive guard/versioned install/rollback, Chrome installer kiểm tra Authenticode, không đè bản hệ thống. 4 test chuyên biệt qua cho idempotence/watcher, thiếu tài nguyên, archive/hash và repeatable fixture installation.

Installer/live Windows/Chrome và GPU còn cổng thực tế. Module downloader mặc định gói cùng ứng dụng; external downloader binary chỉ được chẩn đoán cho đến khi có adapter được kiểm chứng, không báo đang dùng bản khác thực tế.

Vòng tích hợp thêm giới hạn riêng scan/download/render/translate và gợi ý trong Settings, admission ngừng nhận việc khi CPU/RAM/đĩa căng, giữ nguồn/song ngữ trong auto translate, repair cạnh bản hỏng. Installer/Chrome/driver Windows còn chưa thử thật. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).


## P10 — Cache quota cho proxy và an toàn file đang phát (28/10/2026)

Settings có quota cache proxy **128–65536 MiB** (mặc định 4096 MiB) lưu SQLite và nút dọn nền; app kiểm tra định kỳ khi không có proxy/thumbnail đang tạo. Cache janitor chỉ xóa file proxy **hoàn chỉnh, tên SHA256 64 ký tự .mp4** trong đúng thư mục `app-data/cache/proxies`, oldest-first. Không theo symlink/thư mục con, không xóa media gốc, output, file đang phát, Chrome profile, tool installer hoặc file tạm. Quá quota nhưng file được bảo vệ còn lớn thì trả over_budget, không xóa lén.

Regression tests kiểm tra quota/path, file cũ/mới, symlink/partial/foreign/active, Settings persistence và background callback trên Qt. [CI 40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) **PASS 195 Linux, 194 Windows + 1 skip**, packaged proof hai hệ thành công. Cổng còn mở: quota của các loại cache khác, chạy nền/Task Scheduler thực, NTFS/ACL/disk-full/soak Windows user, GPU/VRAM/driver và installer thật.
