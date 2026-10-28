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

## 4. Vòng P09-04 — Tạo lại một hàng mà không phá ràng buộc (28/10/2026)

Đã rà lại master `IMPLEMENTATION_PLAN.md` P09-02/03/04/06, yêu cầu MAT-04/MAT-05 trong `REQUIREMENTS_TRACEABILITY.md`, đặc tả ma trận ở `PRODUCT_REQUIREMENTS.md`, P09_RESULTS và mã `matrix.py`/`ui/pages.py`/`tests/test_matrix.py`. Hiện đã sửa/khóa ô, preview, CSV nhưng chưa có thao tác tạo lại đúng **một hàng**.

1. Thêm hàm thuần `regenerate_row` trả ứng viên mới cho hàng chỉ định, giữ nguyên các hàng khác và các ô bị khóa. Không tái sử dụng tổ hợp lịch sử, kể cả chính hàng cũ; không nới W/K hoặc thay góc khóa.
2. Rà **toàn bộ ma trận** trong thứ tự hiện hành với history, gồm các hàng *sau* vị trí vừa tạo lại vì W/K liên quan đến tiền nhiệm. Cảnh báo lỗi nếu input ban đầu không hợp lệ; giữ nguyên rows khi không có lời giải.
3. Với tập nhỏ duyệt toàn bộ không gian cho các góc không khóa trong ngân sách, xác nhận không có nghiệm nếu hết tất cả; với tập lớn thử ứng viên bounded, phân biệt chưa tìm đủ trong budget với bất khả thi đã chứng minh. Seed tái lập được cho cùng snapshot; cancel không sửa dữ liệu.
4. MatrixPage thêm nút `Tạo lại hàng chọn`, bắt kết quả qua background worker để không treo UI; giữ nguyên khóa các ô, lựa chọn UI và kiểm tra snapshot trước khi apply để tránh worker ghi đè thao tác diễn ra đồng thời. Tham chiếu history mới nhất khi chạy và không tạo job/render cho tới khi người dùng bấm Render.
5. Unit test: W/K/history/unique các hàng trước-sau, khóa cột, tất cả ô khóa, seed deterministic, input immutability/cancel, tập lớn timeout; Qt integration test click regenerate và kiểm tra các hàng khác/lock vẫn nguyên. Không dùng nguồn live hoặc tài khoản thật.
6. Chạy source tests, check_plan, frozen build proof trên CI Linux/Windows, cập nhật P09_RESULTS/CURRENT_STATUS/COVERAGE khi có bằng chứng.

**Cổng giữ mở:** cân bằng lượt sử dụng toàn cục, weights/nhập tay UI, solver tập lớn chứng minh tối ưu, UX multi-row/drag scene và nghiệm thu máy Windows người dùng. Không đánh dấu toàn P09 là hoàn tất.

### P09-04 — Thống kê tần suất sau tạo/sửa hàng

Cùng lát cắt bổ sung bảng thống kê góc từ **những hàng hiện có**: tất cả góc hợp lệ theo từng cảnh, số lần sử dụng (kể cả góc 0 lần), không cộng một job chưa render thành lượt thành công lịch sử. UI có nút xem tóm tắt không làm thay đổi ma trận. Test định lượng với số góc khác nhau giữa các cảnh; giữ `hash` làm ID thay vì tự suy ra theo filename.

### P09-04 — Sửa một ô phải đồng bộ công thức và khóa chỉ áp dụng cho góc

Kiểm tra trực tiếp trong MatrixModel: thay G ở một ô hiện chỉ phát `dataChanged` cho ô đó nên cột công thức C1G1+… có thể hiển thị cũ; thao tác Khóa có thể gắn cờ vào cột video/công thức vốn không phải góc. Sửa để chỉ scene columns (1…N) có thể edit/lock, phát tín hiệu cập nhật ô + công thức; nếu sửa vi phạm W/K/history thì rollback nguyên giá trị và không phát tín hiệu thành công. Test Qt với bảng synthetic và history.
