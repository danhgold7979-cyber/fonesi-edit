# P08 — Kế hoạch chi tiết: kiểm soát chính sách khớp thời lượng lô

**Ngày kiểm tra:** 28/10/2026. **Nhánh chung:** `develop/fonesi-full`. **Trạng thái:** kế hoạch trước khi sửa.

## 1. Đối chiếu master

Đã xem `docs/IMPLEMENTATION_PLAN.md` P08-01…P08-07, phần Batch/Audio ở PRODUCT_REQUIREMENTS, `docs/IMPLEMENTATION_COVERAGE.md`, P08_RESULTS, và source `batch.py`/test `test_batch.py`. Công cụ có quét folder loại output/cache, preset, duration solver, loop/freeze và audio. Chưa nghiệm thu mọi mapping audio/SFX, long corpus hay lỗi máy thật.

## 2. Lát cắt code độc lập

**P08-05/P08-06:** hàm `fit_duration` hiện âm thầm xử lý `policy` hoặc `allocation` không hợp lệ như chế độ speed/proportional. Việc này vi phạm nguyên tắc không tự đổi chế độ mà người dùng yêu cầu.

1. Validate `policy` chỉ thuộc `speed`, `trim`, `loop`, `freeze`; validate `allocation` chỉ thuộc `proportional`, `equal`, `weights`.
2. Nếu chọn `allocation=weights` thì bắt buộc có danh sách trọng số đầy đủ; không thay thế bằng tỷ lệ tự nhiên mà không báo.
3. Nếu chọn `loop` hoặc `freeze` khi nhiều clip/cảnh, chỉ sử dụng nếu thuật toán hỗ trợ thật; nếu chưa hỗ trợ thì báo rõ thay vì âm thầm biến thành `speed`.
4. Test mọi lựa chọn thiếu/không hợp lệ, bảo toàn input và luật giữ nguyên cảnh/nguồn, test loop/freeze hợp lệ.
5. Chạy full test suite, check_plan, packaged proof trên CI Linux/Windows; sửa lỗi phát hiện trước khi đánh dấu đạt.

## 3. Tiêu chí và cổng còn mở

- [ ] Chế độ không hỗ trợ hoặc sai cấu hình phải bị từ chối trước khi tạo job.
- [ ] Tùy chọn nguyên vẹn, không auto fallback khác chính sách đã chọn.
- [ ] Test offline CPU/Windows/Linux đạt, không làm ảnh hưởng render/batch/ma trận hiện tại.
- [ ] Mapping audio theo tên/list/random, SFX %, crossfade nhạc, meter realtime, thời lượng nhập tay toàn bộ UI và benchmark batch lớn vẫn giữ mở trong coverage.
