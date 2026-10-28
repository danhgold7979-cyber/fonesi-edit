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

- [x] Chế độ không hỗ trợ hoặc sai cấu hình phải bị từ chối trước khi tạo job.
- [x] Tùy chọn nguyên vẹn, không auto fallback khác chính sách đã chọn.
- [x] Test offline CPU/Windows/Linux đạt, không làm ảnh hưởng render/batch/ma trận hiện tại.
- [ ] Mapping audio theo tên/list/random đã có riêng ở lát cắt P08-04; SFX %, crossfade nhạc, meter realtime, thời lượng nhập tay toàn bộ UI và benchmark batch lớn vẫn giữ mở trong coverage.

## 4. Vòng P08-04 — Ánh xạ âm thanh chính theo tên/danh sách/random (28/10/2026)

Đọc lại `IMPLEMENTATION_PLAN.md` P08-03/P08-04/P08-05/P08-07, `PRODUCT_REQUIREMENTS.md` mục 6, P08_RESULTS và source `batch.py`, `ui/pages.py` (BatchPage), test `test_batch.py`. Hiện tại BatchPage chỉ nhận **một audio_path chung**. Triển khai mở rộng có thể chạy offline:

1. Giữ mặc định `shared` cho một audio chung hoặc không có audio; bổ sung `by_name` (stem trùng tên video), `ordered` (danh sách audio sort tự nhiên và video theo thứ tự đã chọn), `random` (mỗi video chọn trong thư mục theo seed ổn định).
2. Có trường chọn thư mục âm thanh và chế độ trong BatchPage; chỉ nhận media có audio track thực bằng ffprobe; báo tên thiếu/2 file trùng tên/count không khớp rõ, không tự fallback qua audio khác hoặc bỏ tiếng.
3. Giữ main audio snapshot riêng từng composition, không biến đổi preset đầu vào; tính duration theo âm thanh đã gán, giữ các music/SFX khác; render vẫn qua compositor chung.
4. Test ánh xạ 2 video/2 audio với fixture ffmpeg thực, missing/duplicate/mismatched count, seed reproducible, thử render + audio codec và hồi quy all existing P08/ma trận.
5. Chạy `check_plan` + source suite + packaged proof Linux/Windows. Lát cắt đạt khi mapping đúng và verified; không coi meter realtime, SFX trigger hoặc crossfade music đã xong.

### Bằng chứng P08-04

- [x] Mặc định shared/no-audio giữ tương thích; 3 chế độ by_name/ordered/random có từ Backend đến BatchPage.
- [x] Dry-run mapping/snapshot đúng, kiểm tra ffprobe audio track và lỗi ambiguous/missing, output FFmpeg có âm thanh; không tự thay preset.
- [x] Test CPU/Qt/Windows qua CI full-suite và frozen proof: [run 40642781347](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40642781347) — Linux 166 pass, Windows 165 pass + 1 skip.
- [ ] Mapping nhạc/SFX cao cấp, meters, kiểm chứng output audio trên hệ Windows người dùng và benchmark corpus lớn vẫn mở.

## P08/P09 tích hợp — duration manual per-scene (28/10/2026)

Theo P09-05, thêm `allocation='manual'` và `manual_durations` tùy chọn vào solver chung `fit_duration`. Chỉ thay đổi khi caller chọn chế độ thủ công; mặc định speed/proportional/equal/weights không đổi. Validate dương/hữu hạn/số scene, tổng cảnh kể cả transition khớp target, tốc độ theo min/max hoặc trim không vượt nguồn; không fallback sang thuật toán chia tỉ lệ. Bổ sung unit regression và CI packaged. UI cung cấp vector thời lượng giây trong ma trận, không tự sinh độ dài không có nguồn. Chưa coi là đánh giá performance/loudness Windows.
