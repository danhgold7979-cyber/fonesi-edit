# P10 — Auto và tools triển khai

Đã có idempotent job IDs, dependency workflow download→translate→render, watcher ổn định/loại output, schedule persisted và chống overlap, resource metrics/admission/profile/giới hạn từng loại, heartbeat worker. Tool manager có TLS/hash/staging/archive guard/versioned install/rollback, Chrome installer kiểm tra Authenticode, không đè bản hệ thống. 4 test chuyên biệt qua cho idempotence/watcher, thiếu tài nguyên, archive/hash và repeatable fixture installation.

Installer/live Windows/Chrome và GPU còn cổng thực tế. Module downloader mặc định gói cùng ứng dụng; external downloader binary chỉ được chẩn đoán cho đến khi có adapter được kiểm chứng, không báo đang dùng bản khác thực tế.

Vòng tích hợp thêm giới hạn riêng scan/download/render/translate và gợi ý trong Settings, admission ngừng nhận việc khi CPU/RAM/đĩa căng, giữ nguồn/song ngữ trong auto translate, repair cạnh bản hỏng. Installer/Chrome/driver Windows còn chưa thử thật. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).
