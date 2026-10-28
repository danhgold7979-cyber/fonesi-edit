# P09 — Ma trận triển khai

Đã có scan/hash/natural sort/tên logic, generator lazy seed/W/K/history/locks, capacity và timeout không nới điều kiện, row composition/audio fit và reservation+job transaction. Worker commit history chỉ sau artifact hợp lệ, fail/cancel/retry có trạng thái riêng. Test tập nhỏ đầy đủ, W/K/locks và render row thật qua scheduler đã được thêm; kết quả tích hợp ghi ở P11.

Vòng tích hợp thêm W/K recheck nguyên tử theo lịch sử mới nhất, snapshot tool, tên output thứ tự hàng; preview đổi tên C/G + sidecar, no-overwrite hai bước, journal/undo/rollback/recovery và relink project hiện tại. Test giữ bytes/timestamp, xung đột, hủy, crash giữa move và save journal, vòng tên. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).
