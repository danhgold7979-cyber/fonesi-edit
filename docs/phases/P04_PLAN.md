# P04 — Editor tương tác

Đã đọc master P04, ED 1–2/7–9 và P03_RESULTS. Tiếp tục bằng model production; P02 Windows còn mở.

1. Canvas layer: select/multi-select/lock/z-order, move/resize/rotate/anchor, snap, safe area và scale độc lập zoom.
2. Inspector bind vào domain, font/style/motion fields chuẩn bị cho compositor; undo transaction cho drag/sửa/nhân bản/delete, không bắt phím khi nhập chữ.
3. Timeline video/layer/audio có playhead, trim/split, gap/ripple, marker và zoom; đọc duration thật, không dùng số giả.
4. Project/preset lưu schema qua Store/atomic JSON; mở/relink/copy nhóm thuộc tính; file thiếu có trạng thái.
5. Frame/thumbnail/proxy tạo nền; playback Qt; render tham chiếu dùng backend chung P07 sau khi sẵn sàng.

Kiểm tra: Qt offscreen + thao tác layer/undo/split/save-open; no-overwrite và dữ liệu source không thay. Rich parity tương tác cần đối chiếu P07 và Windows riêng.
