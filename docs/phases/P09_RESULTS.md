# P09 — Ma trận triển khai

Đã có scan/hash/natural sort/tên logic, generator lazy seed/W/K/history/locks, capacity và timeout không nới điều kiện, row composition/audio fit và reservation+job transaction. Worker commit history chỉ sau artifact hợp lệ, fail/cancel/retry có trạng thái riêng. Test tập nhỏ đầy đủ, W/K/locks và render row thật qua scheduler đã được thêm; kết quả tích hợp ghi ở P11.

Vòng tích hợp thêm W/K recheck nguyên tử theo lịch sử mới nhất, snapshot tool, tên output thứ tự hàng; preview đổi tên C/G + sidecar, no-overwrite hai bước, journal/undo/rollback/recovery và relink project hiện tại. Test giữ bytes/timestamp, xung đột, hủy, crash giữa move và save journal, vòng tên. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).

## Tạo lại hàng, thống kê góc và chia thời lượng — 28/10/2026

Tất cả thay đổi đã code trong **một ứng dụng** trên nhánh `develop/fonesi-full`:

- **MAT-04/MAT-05 — Tạo lại riêng một hàng:** thêm `regenerate_row` chỉ thay một hàng, giữ các ô đã khóa và mọi hàng khác, không tái sử dụng tổ hợp lịch sử/đã lên kế hoạch. Kiểm tra lại cả W/K của **những hàng sau**; seed ổn định trên cùng snapshot. Với không gian nhỏ (≤10.000) duyệt ứng viên đầy đủ; với không gian lớn, thử tối đa trong time/attempt budget và báo “chưa tìm được” thay vì “vô nghiệm”. Cancel không chỉnh dữ liệu.
- **UI ma trận:** nút `Tạo lại hàng chọn` chạy background (không chặn Qt), recheck lịch sử đặt chỗ, thay đổi scenes/rows/locks/seed/W/K trước khi nhận kết quả. Worker trả kết quả cũ sẽ bị bỏ, không ghi đè thao tác của người dùng. Cải thiện sửa ô chỉ cho scene columns, khóa không dính cột tên/formula; sửa góc revalidate lịch sử W/K và cập nhật công thức C1G… cùng lần.
- **Thống kê sử dụng góc:** nút `Thống kê góc` đếm từng góc trong ma trận đang lập, bao gồm góc chưa sử dụng = 0. Đây là số **được lên kế hoạch**, không coi là video đã xuất thành công.
- **MAT-06/P09-05 — Thời lượng cảnh:** chế độ proportional/equal hiện có được bổ sung `weights` (trọng số số dương mỗi cảnh) và `manual` (số giây mỗi cảnh), cùng speed min/max tại tab ma trận. `row_composition`, `enqueue_rows` và solver dùng một snapshot/thời lượng. Nếu có audio chính, tổng thời lượng clip trừ overlap phải khớp duration audio, nếu không báo không khả thi; không có audio thì tổng thời lượng thủ công quyết định target. Bảo vệ min/max speed/trim, không tự bỏ cảnh hoặc chuyển sang freeze/loop.
- **Test:** deterministic/exhaustive small space, khóa ô/W/K ảnh hưởng về sau, lịch sử bị đổi khi thread chạy, cancel và input bất biến, Qt điều khiển thao tác/đổi góc/số góc, weights và manual vector, FFprobe và **render FFmpeg output thật** từ clip có duration đã chỉ định. Old production jobs and source media unaffected.

**Bằng chứng CI:** [run 40645339209](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40645339209) **PASS** — Linux **180 tests**, Windows **179 tests + 1 skipped** (fixture POSIX-only), kèm build production/native-host và frozen proof video/ảnh localhost, render batch/ma trận và Qt frame decode trên hai hệ.

**Cổng P09 vẫn mở:** reorder cảnh bằng drag ở UI, tìm nghiệm/tối ưu & cân bằng frequency trên tập lớn với mọi W/K, stress/history lớn, Windows/exFAT/drive thực, mở project và thử vòng rename sau mất điện. Tập test runner không thay thế nghiệm thu máy Windows người dùng; không đánh dấu toàn phase hoàn tất.
