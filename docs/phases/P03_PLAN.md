# P03 — Kế hoạch chi tiết: độ bền dữ liệu và bảo vệ bí mật

**Phiên bản kế hoạch:** 2.0 — 28/10/2026  
**Trạng thái trước khi code:** đã rà soát master, kết quả P03, coverage và mã nguồn hiện có; chưa sửa source trong phase plan này.  
**Nhánh:** phase/p03-storage-durability-secrets

## 1. Đối chiếu master plan và trạng thái hiện tại

Đã đọc lại docs/IMPLEMENTATION_PLAN.md, docs/CURRENT_STATUS.md, docs/phases/P03_RESULTS.md, docs/IMPLEMENTATION_COVERAGE.md và docs/TECHNICAL_DESIGN.md; rà soát storage.py, domain.py, worker.py, jobs.py và tests/test_storage_jobs.py.

- Master P03 có 9 task, tập trung schema/migration, project/job snapshot, scheduler/worker, recovery, output validation và bảo vệ dữ liệu.
- Nền code P03 đã tồn tại; không scaffold lại, không xóa code và không tăng schema version nếu không cần thiết.
- Suite gần nhất có 92 test. Các kiểm chứng trước đây không thay thế soak/crash/power-loss hoặc nghiệm thu máy Windows người dùng.
- Coverage vẫn mở về độ bền dài hạn, lỗi đĩa/quyền/mạng và log chẩn đoán đầy đủ. Lát cắt này xử lý các vấn đề có thể kiểm chứng tự động trước.

## 2. Phạm vi code

### P03-02 / P03-07 — Backup và migration an toàn

1. Tạo helper backup dùng file tạm trong cùng thư mục đích, hoàn tất SQLite backup, chạy integrity_check và chỉ công bố file sau khi kiểm tra thành công.
2. Tạo thư mục cha nếu chưa có; không ghi đè file backup đã tồn tại; dọn file tạm khi có exception.
3. Dùng cùng cơ chế backup cho migration schema v1→v2 trước khi thay đổi schema.
4. Bổ sung test backup vào thư mục lồng chưa tồn tại, integrity_check, dữ liệu mở lại được, từ chối ghi đè và giữ nguyên backup có sẵn khi thao tác bị từ chối.

### P03-05 — Ngăn bí mật lọt vào project/job/settings và lỗi worker

1. Chuẩn hóa tên key trước khi kiểm tra: phân biệt chữ hoa/thường và bỏ dấu gạch dưới/gạch ngang/ký tự phân cách.
2. Chặn các trường bí mật phổ biến như password/passwd, cookie/cookies, API key, access/refresh/session/bearer token, client secret và authorization header; không lưu giá trị bí mật vào project/job.
3. Chuẩn hóa thông báo lỗi worker: che cặp key/value nhạy cảm, Bearer token và query string của URL ký; giữ phần thông tin lỗi hữu ích như loại lỗi, host/path và mã trạng thái.
4. Thêm test cho các biến thể key và thông báo lỗi chứa authorization/token/URL có query nhạy cảm. Không ghi giá trị bí mật vào log hoặc assertion output.

### P03-04 / P03-06 — Không làm suy yếu hàng đợi hoặc output

- Giữ nguyên snapshot bất biến, transaction claim, heartbeat, cancel/retry, no-overwrite và validation hiện có.
- Không đổi logic recovery từ “orphan → pending” thành “succeeded” chỉ vì file tồn tại.
- Không tuyên bố đã giải quyết toàn bộ artifact reconciliation sau crash; phần reconcile render/download sau power loss tiếp tục là cổng riêng nếu chưa có validator/manifest đủ tin cậy.
- Không thêm network access, API trả phí, browser credential access hoặc dữ liệu người dùng vào test.

## 3. Thứ tự triển khai

1. Thêm test cho alias secret keys và sanitize error trước khi thay đổi implementation.
2. Sửa domain validation và worker error sanitization.
3. Thêm backup helper và dùng nó cho backup thủ công/migration.
4. Chạy test tập trung storage/security, sau đó toàn bộ suite.
5. Chạy check_plan và packaged proof Linux/Windows qua GitHub Actions.
6. Ghi P03_RESULTS, cập nhật coverage/status theo đúng kết quả; chỉ đánh dấu task hoàn thành khi test tương ứng có bằng chứng.

## 4. Tiêu chí nghiệm thu

- [ ] Backup vào thư mục mới tạo được; integrity_check trả về ok và database mở lại đọc được.
- [ ] Backup không ghi đè file đích có sẵn; thao tác lỗi không để file tạm như bản backup hợp lệ.
- [ ] Migration v1 tạo bản backup trước khi đổi schema; test migration hiện tại vẫn qua.
- [ ] Các alias như api-key, Authorization, session_cookie, clientSecret, refresh-token và bearerToken bị chặn khi nằm trong payload được kiểm tra.
- [ ] Thông báo lỗi che Bearer token, các trường token/password/cookie/API key và query URL nhạy cảm; vẫn giữ được thông tin hữu ích cho chẩn đoán.
- [ ] Toàn bộ test source pass; packaged proof Linux/Windows không hồi quy.
- [ ] Không thay đổi schema hoặc định dạng project ngoài nhu cầu; không ghi bí mật, browser profiles, downloaded media hay runtime artifacts vào Git.

## 5. Rủi ro, rollback và giới hạn

- Backup nguyên tử có thể không hỗ trợ trên một số filesystem nếu hard link bị cấm; trong trường hợp đó phải fail rõ, không âm thầm chuyển sang thao tác có nguy cơ ghi đè.
- Redaction phải ưu tiên an toàn nhưng không xóa hết thông tin chẩn đoán; test dùng chuỗi synthetic, không dùng bí mật thật.
- Nếu test hoặc CI fail, sửa nguyên nhân trên nhánh phase; không force-push, không thay main và không giảm tiêu chí kiểm tra.
- Crash/kill/power-loss soak dài hạn, lỗi đĩa/quyền/mạng trên máy thật và installer Windows vẫn mở sau lát cắt này.

## 6. Điều kiện tiếp tục

P03 có thể được đóng khi các cổng code/test của phase đạt và kết quả được ghi lại. Cổng bên ngoài như Chrome/session, nguồn live, GPU hoặc nghiệm thu máy Windows người dùng không được gắn PASS nhờ test storage. Sau P03, tiếp tục P04 theo master plan và lập phase plan riêng trước khi code.
