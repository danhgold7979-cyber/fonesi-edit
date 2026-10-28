# P09 — Ma trận

Đã đọc master P09/PR 7 và nền batch/render. Không phụ thuộc live sources.

1. Natural sort cảnh/góc, tên logic và content hash; không sửa tên/tệp nguồn mặc định.
2. Generator lazy, không trùng tổ hợp, W/K/cân bằng, seed + input/history snapshot; small space thử hết chỉ trong budget rõ.
3. History/reservation SQLite và job creation nguyên tử; failed/retry/cancel không ghi success giả.
4. Bảng ma trận edit/khóa/revalidate, preview row và CSV; cùng duration planner/render P08.
5. Test toàn bộ tập nhỏ, constraints W/K, seed, history và bất khả thi, concurrent reservation, render integration.

Vòng MAT-02: preview đổi tên thật CnGm trong folder cảnh, journal/hash/two-stage no-overwrite và hoàn tác bằng mapping; mặc định vẫn tên logic. Chặn tệp đang được queue dùng, cập nhật liên kết project đang mở, không theo symlink. Thử xung đột/rollback/undo và giữ nguyên bytes/timestamp nguồn.
