# P03 — Kết quả triển khai nền

Đã có domain/version/validation, SQLite WAL với project/preset/job/cache/profile/binding/tool/history/schedule, backup và từ chối schema mới hơn. Scheduler dùng subprocess, claim transaction, cancellation, dependency và phục hồi orphan. 5 test chuyên biệt đã qua, gồm render FFmpeg thật qua worker và đọc kết quả từ Store mở lại.

P03-08 registry/install và P03-09 browser metadata là nền cho phần tool/auth tiếp theo; giao diện, installer/session bridge và kiểm chứng Windows được theo dõi tiếp, không coi đã nghiệm thu toàn bộ. Tiếp tục theo chỉ đạo không dừng vì cổng bên ngoài.

Vòng tích hợp đã thêm schema v2 có backup, thời điểm bắt đầu job, khóa một scheduler/DB, phục hồi orphan cả sau startup, unblock dependency và bảo toàn trạng thái matrix khi retry. Các bài tương ứng có trong suite cuối. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).


## 4. Lát cắt hardening — backup và bảo vệ bí mật (28/10/2026)

**CI:** [Desktop verification #40635978628](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40635978628)  
**Commit:** 989368b9560b059c27c131c36ed12955f98c6602

- Linux: 108 tests pass; check_plan, build production/native host và frozen packaged proof đều pass.
- Windows runner: 107 tests pass, 1 skip có chủ đích cho fixture installer POSIX; check_plan, build production/native host và frozen packaged proof đều pass.
- Frozen proof xác nhận hai job render, tải video và ảnh qua localhost vào thư mục Unicode, phụ đề song ngữ, rename/undo và UI smoke/frame decode. Proof đánh dấu passed=true và frozen=true.
- Backup SQLite nay được tạo trong thư mục tạm cùng filesystem, xác nhận integrity_check, flush dữ liệu và công bố bằng hard link không ghi đè. Các connection backup được đóng tường minh để Windows có thể xóa file tạm.
- CI ban đầu phát hiện lỗi Windows thật: SQLite connection context manager không tự đóng connection, làm file tạm bị khóa khi cleanup. Đã đổi sang đóng tường minh; lần chạy mới nhất pass trên cả hai hệ điều hành.
- Payload validator chuẩn hóa tên trường và chặn thêm alias credential; worker error sanitizer che Bearer/Basic, trường credential, signature và query/fragment URL nhưng giữ lại mã lỗi/host/path cần chẩn đoán.

**Giới hạn còn mở:** CI dùng media synthetic và localhost; không chứng minh mạng xã hội live, dịch API thật, Chrome session handoff, GPU/VRAM, installer trên máy người dùng hoặc soak/crash/power-loss dài hạn. P03 không được coi là nghiệm thu toàn bộ chỉ dựa trên lát cắt này.

## P03-05 — Bảo vệ lỗi ở ranh giới SQLite (28/10/2026)

`Store.fail` giờ áp dụng `sanitize_error_message` **trước khi INSERT/UPDATE lỗi vào SQLite**, kể cả caller không phải worker. Bảo vệ query URL token/signature, Bearer credentials và các alias khóa API; giữ mã lỗi/host/path phục vụ chẩn đoán. Test đọc trực tiếp SQLite cho job `failed` và `blocked`, bảo toàn trạng thái/chức năng. [CI 40652053745](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40652053745) PASS Linux/Windows và packaged proof. Chưa chứng minh mọi chuỗi credential lạ được lọc hoặc vận hành trên máy thật.
