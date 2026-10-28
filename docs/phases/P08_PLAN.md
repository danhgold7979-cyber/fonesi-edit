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

## Vòng P08-04 tiếp theo — SFX placement trên timeline (28/10/2026)

**Rà soát master:** `docs/IMPLEMENTATION_PLAN.md` P08-03/P08-04/P08-06/P08-07; `PRODUCT_REQUIREMENTS.md` mục 6 (SFX theo thời điểm tuyệt đối/đầu/cuối video/cảnh/% thời lượng); `docs/IMPLEMENTATION_COVERAGE.md` AUD-03…AUD-06; `src/fonesi_edit/domain.py`, `render.py`, `ui/dialogs.py`, test render và app integration. Pipeline hiện nhận `offset` tuyệt đối; chưa có clip-relative/percent placement và chưa có UI cho các mode.

**Thiết kế:**

1. Bổ sung thuộc tính tùy chọn chỉ cho SFX: `placement` ∈ `absolute,percent,video_end,scene_start,scene_end`; `position_pct` 0..100 cho `percent`; `scene_index` 1-based cho scene modes. `offset` là giây sau mốc với `absolute/percent/scene_start`, hoặc số giây **trước** mốc với `video_end/scene_end` (không âm). Trường mặc định không có `placement` tiếp tục là offset tuyệt đối như bản cũ. Không áp dụng placement cho main/music.
2. Domain validate value types, finite range, clip index và required parameters. Chặn scene index sai và placement dẫn đến start trước video hoặc từ thời điểm video kết thúc trở đi. Không fallback về offset 0 khi cấu hình sai.
3. Compositor tính clip ranges sau speed/trim/freeze/transition và resolve SFX onset từ **timeline đầu ra thật**, thay vì lấy thời gian media gốc. FFmpeg adelay theo onset, cắt cuối theo total, giữ gain/fade/mute/solo/limiter hiện tại.
4. AudioDialog chọn mode + % + scene index, giữ trạng thái round-trip khi sửa track; GUI validation trong apply. Các field chỉ được ghi vào track SFX khi mode phù hợp. Không ảnh hưởng audio chính/nhạc.
5. Unit tests ranh giới và các mốc có transition, trim, duration; test FFmpeg render SFX từ audio fixture ở giây chỉ định (đo sự xuất hiện âm thanh bằng PCM); Qt offscreen dialog round-trip/invalid. Cần pass check_plan, suite Linux/Windows và frozen proof. Cổng ngoài vẫn mở: music crossfade, SFX repeat/multiple-placement UI nâng cao, kiểm chứng hệ loa Windows/HiDPI, realtime meter.

**Nghiệm thu lát cắt:** một track SFX có thể chọn mốc tuyệt đối, theo %, trước cuối video, sau đầu cảnh hoặc trước cuối cảnh; onset đúng sau thay đổi speed/transition; output thực có âm đúng vị trí, config sai báo lỗi, không thay đổi các track cũ. CI hai hệ phải đạt. Không suy ra đã hoàn tất mọi lựa chọn âm thanh P08.

## Vòng P08-01 — Lọc và chọn file hàng loạt trong BatchPage (28/10/2026)

**Rà lại phạm vi:** master P08-01/P08-02, PRODUCT_REQUIREMENTS mục 5 yêu cầu cây checkbox, tìm kiếm/lọc, chọn tất cả/bỏ chọn/đảo chọn. BatchPage đã có cây checkbox và chỉ lấy tệp được chọn để batch_plan nhưng không có tìm/lọc hoặc nút thao tác nhanh. Điểm nguy hiểm: danh sách đã chọn có thể đổi sau khi lập kế hoạch mà `self.plans` vẫn lưu kế hoạch cũ.

1. Thêm tìm theo tên file/kênh, lọc theo đuôi video, điều khiển chọn/bỏ/đảo **các mục đang hiển thị**. Lọc chỉ ẩn/hiện, tuyệt đối không xóa nguồn hoặc tự thay checkbox của file không hiển thị.
2. Sau chỉnh checkbox/scan folder mới phải hủy kế hoạch dry-run cũ và yêu cầu người dùng bấm Lập kế hoạch lại trước Preview/Chạy toàn bộ. Hiển thị số file đang được chọn / tổng; không âm thầm chạy kế hoạch stale.
3. Parent checkbox vẫn giữ Qt tristate theo con; chỉ thao tác lên leaf file khi chọn hiển thị; test Qt offscreen gồm search, extension filter, chọn/đảo, file ẩn vẫn giữ trạng thái và invalidation của plan.
4. CI Linux/Windows full suite, frozen proof và ghi kết quả P08_RESULTS/COVERAGE sau khi PASS. Bộ lọc theo metadata độ dài/độ phân giải và phân trang nguồn rất lớn vẫn còn mở, không gắn đủ P08-01.

### Kết quả P08-01/P08-04 cập nhật

- [x] SFX có mốc absolute/percent/video-end/scene-start/scene-end; giữ tương thích offset cũ, reject dữ liệu sai; FFmpeg output kiểm tra bằng PCM và graph.
- [x] AudioDialog sửa/round-trip các mốc, test Qt và cấm relative placement cho main/music.
- [x] Batch tree tìm/lọc định dạng, chọn/bỏ/đảo file đang hiển thị, giữ file bị ẩn; hủy dry-run khi lựa chọn/preset thay đổi và chống stale background result.
- [x] Regression và frozen proof Linux/Windows PASS [CI 40655116611](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40655116611) — 219 Linux; 218 Windows + 1 skip.
- [ ] Filter duration/resolution, SFX repeat/trigger phức tạp, crossfade music, meter/solo nghe trên máy thật, ước lượng/benchmark vẫn mở.

## P08-01 — Quét nhiều thư mục gốc, không trùng nguồn (28/10/2026)

Đối chiếu `IMPLEMENTATION_PLAN.md` P08-01 và PRODUCT_REQUIREMENTS §5: có yêu cầu nhiều folder/đệ quy, tự loại output/cache/symlink. `scan_folders(root)` đã hỗ trợ một thư mục gốc nhưng BatchPage hiện chỉ có một ô. Bổ sung hàm `scan_multiple_folders(roots)` hợp nhất channel chính xác theo đường dẫn đã resolve, loại file trùng khi gốc trùng/cha-con chồng nhau. Giữ nguyên thứ tự root đã chọn, trong từng root vẫn natural-sort video, không đọc/xóa/chỉnh tệp nguồn. Phải từ chối gốc rỗng/không tồn tại, không fallback sang folder mặc định. BatchPage thêm danh sách đường dẫn root mỗi dòng và nút chọn folder để chèn, rồi scan trong background như trước; đổi danh sách root làm invalidation dry-run. Test unit với folder trùng/nested và tệp trong ` edit`/cache bị bỏ, cùng Qt offscreen kiểm tra lựa chọn và không render bản kế hoạch stale. CI frozen Linux/Windows theo hợp đồng. **Đây chưa là nghiệm thu đủ lọc duration/resolution hay corpus lớn.**

### Bằng chứng P08-01 multi-root

- [x] Nhiều folder gốc và file chồng root/cha-con được quét/merge có khử trùng, giữ nhóm kênh; tệp trong output/cache bị bỏ.
- [x] GUI thêm folder và nhập nhiều đường dẫn, đổi folder/hủy scan cũ không được dùng lựa chọn/plan đã cũ; callback out-of-order bị bỏ.
- [x] Test backend + Qt offscreen + packaged CI Linux/Windows [40656796768](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40656796768) PASS: 222 Linux, 221 Windows + 1 skip.
- [ ] Filter metadata duration/resolution và corpus quy mô lớn còn mở, P08 chưa đủ điều kiện nghiệm thu toàn phase.

## P08-01 — Lọc thời lượng/độ phân giải theo metadata FFprobe (28/10/2026)

**Đối chiếu trước code:** Master `IMPLEMENTATION_PLAN.md` P08-01/P08-07; PRODUCT_REQUIREMENTS §5; COVERAGE hàng BAT-01…BAT-04; P08_RESULTS và P08 multi-root CI 40656796768. Bộ lọc hiện tại chỉ tìm tên/kênh và đuôi video. Cần tránh quét FFprobe đồng bộ trên main thread, tránh dùng kết quả cũ khi nguồn đổi và tránh thay checkbox ẩn.

1. Backend `probe_batch_metadata(groups, progress, cancel)`: đọc FFprobe theo video đã hợp nhất, trả duration/width/height; báo lỗi riêng từng file không đọc được, không chặn toàn bộ lô hay sửa file nguồn. Không tự coi file lỗi là video đạt bộ lọc.
2. BatchPage thêm giới hạn duration tối thiểu/tối đa (0 = không giới hạn) và độ phân giải theo **cạnh ngắn** (0/720/1080/2160 px; ảnh dọc không bị hiểu sai). Metadata chỉ đọc khi người dùng bật lọc; đọc trên worker và hiển thị rõ trạng thái chờ/lỗi; lọc chỉ ẩn mục, không mất checkbox hay kế hoạch đã lập.
3. Gắn revision token cho callback metadata; thay folder hoặc quét lại vô hiệu hóa metadata, callback cũ không được ghi đè. Trong lúc bộ lọc chưa áp dụng xong hoặc khoảng giây sai, không cho tạo dry-run mới như thể đã lọc xong.
4. Test media thật/corrupt qua FFprobe, Qt offscreen với duration/resolution, source đổi/callback ngoài thứ tự, checkbox và invalid interval; chạy check_plan, full suite, CI Linux/Windows + packaged proof.
5. Chỉ nghiệm thu lát cắt khi cả hai hệ PASS; nghiệm thu P08 toàn diện vẫn mở cho corpus rất lớn/hiệu năng, metadata chuyên sâu, music crossfade, meter/solo, packaging Windows và live sources.
