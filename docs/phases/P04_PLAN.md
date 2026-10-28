# P04 — Kế hoạch chi tiết editor/timeline: vòng hoàn thiện tương tác

**Cập nhật:** 28/10/2026. **Nhánh duy nhất:** `develop/fonesi-full`. **Tình trạng:** kế hoạch trước khi sửa mã P04; P03 đã có code và chạy CI, cổng máy Windows thật vẫn tách riêng.

## 1. Đối chiếu master plan

Đã đọc `docs/IMPLEMENTATION_PLAN.md` (P04-01 đến P04-08), `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, P03_RESULTS và P04_RESULTS. Kiểm tra mã hiện có trong `ui/canvas.py`, `ui/editor.py`, `ui/timeline.py` và `tests/test_editor.py`.

Nền hiện có: Qt/PySide6, canvas/inspector, lựa chọn nhiều layer, undo/redo, timeline clip/audio, in/out, split, waveforms và playback. **Không viết lại app, không đổi định dạng project**; tất cả chỉnh sửa đều trên một nhánh chung và một binary Windows.

## 2. Những sai lệch được xác định

- P04-02: snap hiện tại so `x/y` góc trên trái với 0.5, không phải tâm hình; kéo các layer chọn cùng nhau có thể làm hỏng khoảng cách tương đối khi chạm ranh giới vì mỗi layer bị clamp độc lập.
- P04-02/P04-04: thao tác kéo/resize có thể cho khung chạy khỏi canvas, phụ thuộc tọa độ không chuẩn; cần kiểm thử nhóm và undo.
- P04-01/P04-02: hiển thị safe-area có sẵn nhưng chưa có lưới căn chỉnh tùy chọn/lưu trạng thái trong project.
- P04-05: timeline cần bảo vệ chống trim âm và kiểm chứng tương tác khi zoom; hiện tại UI layer kéo/thay đổi đã có.
- P04-06: proxy đa mức, thumbnail strip, playback loop đoạn, HiDPI/seek parity còn mở; **không giả làm đã đạt** nếu lát cắt chưa thực hiện.

## 3. Lát cắt triển khai trước mắt

1. Tạo hàm tọa độ độc lập kiểm thử được: snap **trung tâm lớp** vào trung tâm canvas, snap rìa vào safe area khi gần, tắt snap tạm bằng Alt; giới hạn vị trí theo kích thước layer.
2. Với multi-select/nhóm, tính delta chung và clamp theo bounding box tập lựa chọn để giữ khoảng cách giữa các layer; giữ đúng một undo cho một cử chỉ kéo.
3. Thêm bật/tắt lưới hình học trên canvas, dùng `Composition.adjustments` để giữ trạng thái khi save/open, không đưa đường lưới vào FFmpeg export. Bật/tắt có undo.
4. Tạo regression tests cho tọa độ trung tâm/rìa, Alt tắt snap, group bounds, thao tác undo, serialization trạng thái lưới và invariant không thay file nguồn.
5. Chạy `scripts/check_plan.py`, full `pytest`, build và packaged proof Linux/Windows qua CI; đọc kết quả thực, sửa lỗi chứ không bỏ test.

## 4. Cổng đóng lát cắt

- [ ] Snap đến **tâm** canvas (tính cả width/height), không nhầm góc trên trái.
- [ ] Nhiều layer giữ khoảng cách khi kéo sát mép; không lệch nhóm; undo khôi phục nguyên vị trí.
- [ ] Alt tạm tắt snap; grid on/off hiển thị đúng và lưu/khôi phục qua project.
- [ ] Test regression tự động qua Linux/Windows.
- [ ] Proof binary thực tế vẫn đạt trên CI hai hệ; giữ bản Windows review.
- [ ] P04_RESULTS và CURRENT_STATUS ghi đúng phần đạt/chưa đạt.

## 5. Phạm vi còn mở, không tự đổi thành PASS

Crop bằng tay nắm và tương tác đủ chín điểm neo, proxy chất lượng, timeline thumbnail strip, preview loop đoạn, mọi phím tắt, benchmark trên Windows/HiDPI và đối chiếu từng hiệu ứng với exporter còn phải theo dõi trong `IMPLEMENTATION_COVERAGE.md`. Tiếp tục mã P05–P12 theo master plan sau khi phần P04 có test mà không chờ live platform/API/GPU không liên quan.
