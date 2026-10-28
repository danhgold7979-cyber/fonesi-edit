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

## 6. Vòng triển khai tiếp — ED-17/18: thumbnail timeline và loop đoạn (28/10/2026)

Đã đối chiếu lại master `IMPLEMENTATION_PLAN.md` P04-05/P04-06, `EDITOR_SPEC.md` mục timeline/preview, `REQUIREMENTS_TRACEABILITY.md`, `ui/editor.py`, `ui/timeline.py`, `app.py` (playback preview dựng qua compositor), `prototypes/media.py`, `waveform.py` và tests. `P04_RESULTS`/coverage xác nhận thumbnail strip và preview loop đoạn vẫn mở.

**Lát cắt triển khai:**

1. Loop In–Out có bật/tắt trong Editor, chỉ thực hiện seek vòng khi player đang phát **bản preview đã render bằng chính compositor** của composition hiện tại. Không đưa người dùng tới thời điểm sai của file nguồn nếu clip đã trim/speed/transition. Kiểm tra In/Out dương, `out > in`, nằm trong độ dài composition; không thay đổi nguồn, project hay output. Preview sau chỉnh sửa được đánh dấu stale; yêu cầu dựng lại, không chạy loop âm thầm trên bản cũ.
2. Timeline thumbnail là tính năng tùy chọn, checkbox menu bật/tắt lưu trong `Composition.adjustments`. Khi bật, tạo tối đa một số frame/clip (3) qua FFmpeg, theo `clip.start/end`, chỉ với file nguồn local; scale nhỏ, cache theo path/stat/trim/speed, publish atomic, kiểm tra đầu ra, cancel/time budget. Tạo trong task nền, chỉ xếp tối đa số clip đang hiển thị để tránh queue vô hạn; không thay đổi input media hoặc FFmpeg output graph.
3. Timeline vẽ các thumbnail lên clip row từ cache; không truy cập FFmpeg trên UI thread. Khi trim/nguồn thay đổi, cache identity thay đổi. Làm rõ đây là source thumbnail trước transform/compositor, **không** gọi là preview/export parity.
4. Test unit giới hạn loop, thumbnail time-map/identity, PNG thật/không đổi nguồn, Qt offscreen thumbnail tiles/toggle undo và không tạo thumbnail khi tắt. CI full regressions + frozen proof Linux/Windows, chỉ ghi PASS phần có evidence.

**Cổng còn mở:** proxy Nhanh/Cân bằng/Cao và cancellation/invalidation đủ chiến lược, long timeline 4K/HiDPI trên máy người dùng, audio/video sync trong các trường hợp VFR và crop handles/safe areas chưa đủ.

## 7. P04-06 — Proxy phát nguồn local có ba mức (cùng đợt)

Tách rõ **proxy nguồn** và **rendered composition preview**: proxy chỉ tăng tốc phát media gốc ở tab Playback, không thay thế compositor/FFmpeg export hoặc được công bố đã có hiệu ứng đầy đủ. Ba mức Nhanh (cạnh dài ≤640), Cân bằng (≤1280), Cao (≤1920), ngoài chế độ Tắt. FFmpeg transcode h264/aac bảo toàn thứ tự thời gian, không sửa nguồn. Cache trên user workspace, key path/stat/quality, viết tệp tạm + probe/kiểm tra duration + atomic publish, hủy/timeout, giữ bản cũ khi không hợp lệ. UI menu chọn mức, lưu trong project; khi switching clips chỉ tạo một proxy cần thiết qua background và không lạm dụng queue; dùng đúng bản proxy khi người dùng chọn, không áp dụng trên rendered preview. Test cache/invalidations/no source mutation, UI picker, actual media decode. Cổng Windows real-time performance và proxy long media vẫn cần nghiệm thu riêng.
