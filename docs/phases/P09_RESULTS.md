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

## P09-01 — Đổi thứ tự cảnh trong UI, giữ history/W/K/lock (30/10/2026)

[Plan](P09_SCENE_REORDER_PLAN.md) được commit trước code. MatrixPage có danh sách cảnh kéo/thả, nút Cảnh lên/xuống, hiển thị folder nguồn và số góc, lưu thứ tự theo folder gốc và chỉ khôi phục khi tập scene khớp hoàn toàn. Không tự đổi tên/xóa source. Backend hoán vị các cột hàng, lịch sử đã căn đúng cảnh, ô khóa, các vector weights/manual seconds; `Angle.scene` chỉ là chỉ số logic mới, `hash/index/path` giữ nguyên. Worker sinh ma trận/preview cũ không thể ghi đè nếu thao tác mới hơn hoặc thiết lập thay đổi; hàng đang chọn được khôi phục sau đổi thứ tự.

Lịch sử SQLite cũ chỉ có content hash, nên khi cần căn theo thứ tự mới, app chỉ gán hash vào một cảnh nếu xác định duy nhất. Content giống nhau ở nhiều scene hoặc nguồn lịch sử biến mất → lỗi rõ ràng, không suy đoán. `enqueue_rows` đối chiếu history ngay trong transaction trước khi tạo job, chặn cả tổ hợp đã đặt chỗ trước đó nhưng lưu với thứ tự cũ; không có partial jobs. Qt và backend tests có FFmpeg render thật, kiểm tra W/K/lock/path/hash, cấu hình hỏng, worker concurrent và nguồn không thay đổi.

**[CI https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41016748802](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41016748802) SUCCESS exact code/test SHA `3ff0e31b28d6c12caeaaf4ae60d7f79eb28818b8`: Linux 701 PASS; Windows 700 PASS + 1 intentional POSIX skip; plan check, benchmark 128 synthetic MP4, desktop/native host và frozen packaged proof hai OS PASS.** Chỉ nghiệm thu lát cắt scene reorder trên synthetic/runner CI. P09-01 còn cổng scene-level exclusion/lock nâng cao và người dùng Windows kéo thả thực tế; P09/P11/P12 còn solver corpus lớn, live Chrome/provider, GPU, filesystem/SQLite issue #6, installer, power loss. Không merge `main`.
