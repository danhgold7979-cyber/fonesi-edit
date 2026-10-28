# P09 — Kế hoạch chi tiết: lịch sử ma trận và khóa cảnh/góc

**Ngày rà soát:** 28/10/2026. **Nhánh:** `develop/fonesi-full`. **Trạng thái:** plan trước khi code.

## 1. Đối chiếu master và triển khai

Đã đọc `docs/IMPLEMENTATION_PLAN.md` P09-01…P09-06, yêu cầu ma trận ở PRODUCT_REQUIREMENTS, `docs/REQUIREMENTS_TRACEABILITY.md`, P09_RESULTS và source `matrix.py`, `tests/test_matrix.py`. Ma trận có generator lazy W/K, seed, history, lock ô, transaction reservation, validation output, journal đổi tên/rollback. Còn yêu cầu UI regenerate row/weights, cân bằng tập lớn, scale/corpus và kiểm chứng Windows/exFAT thực tế.

## 2. Lát cắt P09-02/P09-03/P09-04

- Khi history chứa cùng một tổ hợp nhiều lần, capacity hiện đếm từng bản ghi lịch sử thay vì số tổ hợp **duy nhất**, có thể báo hết khả năng trong khi vẫn còn tổ hợp hợp lệ.
- Lock row/scene ngoài phạm vi hoặc khóa không thuộc cảnh hiện tại hiện có thể rơi vào IndexError hoặc bị bỏ qua nếu key nhập chuỗi. Chuẩn hóa/kiểm tra lock theo row/scene, báo ValueError rõ ràng trước khi sinh.
- Không nới W/K, không thay thế khóa không hợp lệ bằng lựa chọn ngẫu nhiên. Giữ hạt giống, thứ tự lịch sử và xác nhận kết quả.
- Thêm test history trùng, lock index âm/vượt, chuỗi chỉ số hợp lệ, và không thay input/history.
- Chạy check_plan, test source, proof binary Linux/Windows; chỉ cập nhật trạng thái theo evidence thực.

## 3. Cổng ngoài phạm vi lát cắt

Chứng minh solver constraints với corpus lớn, GUI regenerate từng hàng/khóa mọi kiểu, cân bằng tần suất toàn cục, thiết lập trọng số thời lượng từ UI, multi-worker Windows/exFAT/rename và xử lý mất điện vẫn mở. Không coi offline fixture là nghiệm thu đủ 95 nhóm.
