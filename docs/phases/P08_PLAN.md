# P08 — Kế hoạch thực thi bản làm lại

Revision: rebuild-2026-10-30. Các kết quả bên dưới phần lịch sử thuộc code cũ; không chuyển PASS sang bản mới.

## Điều kiện bắt đầu và kết thúc

- Đọc master, PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC, TECHNICAL_DESIGN và REBUILD_REVIEW trước khi thực hiện.
- Mỗi đầu việc cần input hợp lệ, output đọc lại được, test lỗi và kiểm tra không mất dữ liệu nguồn.
- Có thể triển khai phần độc lập trong khi gate live/Windows/GPU bị chặn; không nhận công nghệ phụ thuộc là đã kiểm chứng.
- Sau mỗi task: ghi commit, file thay đổi, lệnh test, version/toolchain, PASS/FAIL/NOT_RUN và giới hạn. Chỉ nghiệm thu khi toàn bộ tiêu chí bắt buộc đạt.
- Không sử dụng phần trăm dòng code. Tiến độ nghiệm thu = số task đạt / tổng task của phase.

## Danh mục 7 đầu việc

### P08-01

**Phạm vi:** nhiều folder/đệ quy/checkbox/loại/đảo chọn/tìm/lọc, không xóa nguồn, không nhận output/cache.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- BAT-01 (PR 5): Không xóa folder, output/cache không bị nhận lại

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Bounded scan/no-follow, multi-folder UI và checkbox. Còn mở: Filter/search/tree/exclusion controls. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P08-02

**Phạm vi:** preset/ghi đè clip/xem tác động/snapshot, output theo kênh/mẫu tên/phiên bản không đè.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- BAT-02 (PR 5; ED 10): Không thay job đang chạy hoặc sửa tay đã khóa
- BAT-03 (PR 3.3, 5): Đúng cây folder, input trùng tên không mất kết quả
- OPS-07 (ED 8): Đủ công cụ phụ, version/thiếu tài nguyên được báo

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Selected tuple snapshot và tên output preview/no-overwrite. Còn mở: Presets/clip override/source-content snapshot/versioning. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P08-03

**Phạm vi:** tiếng gốc/âm chính/nhạc/SFX, mute/solo/gain/fade/trim/delay, meter/clipping/chuẩn hóa.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUD-01 (PR 6): Track đúng vai trò, nghe solo/mute đúng
- AUD-02 (PR 6): Mức âm và điểm vào/ra đúng, không clipping ngoài dự kiến

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P08-04

**Phạm vi:** audio cả lô/theo tên/danh sách/random và playlist thủ công đa thư mục có preflight/snapshot/render verification; nhạc lặp chuyển tiếp; SFX theo giây/cảnh/tỷ lệ và trigger không đều; ducking theo chính sách hỗ trợ.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUD-03 (PR 6): Ánh xạ xác định, mơ hồ/thiếu audio được báo
- AUD-04 (PR 6): Đúng mốc và tổng duration, không lỗi ở biên cảnh

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P08-05

**Phạm vi:** duration planner một hoặc nhiều clip; đích video/audio/nhập tay, min/max speed/đoạn, giữ cao độ, lặp/freeze/cắt theo lựa chọn.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUD-05 (PR 6): Đủ trường hợp ngắn/dài/không audio, không tự đổi mode
- AUD-06 (PR 6): Theo giới hạn hoặc báo bất khả thi, không kéo giọng quá mức

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P08-06

**Phạm vi:** tính chuyển cảnh/audio crossfade vào thời lượng, time map sub; báo bất khả thi, không tự bỏ cảnh/ghép clip ngoài chế độ.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SUB-07 (PR 4.2): Cue theo đúng nguồn sau mọi phép biến đổi thời gian
- AUD-04 (PR 6): Đúng mốc và tổng duration, không lỗi ở biên cảnh

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P08-07

**Phạm vi:** chạy thử một video/đoạn, ước tính dung lượng/ETA, render lô/resume, kiểm tra duration/tracks/media.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- BAT-04 (PR 5, 9): Xem tác động trước lô, retry riêng không làm lại việc xong

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Actual CPU batch/decode/probe, per-item progress và isolated failures. Còn mở: ETA/resume/durable queue/full duration-tracks corpus. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

## Hồ sơ thực hiện trước rebuild (chỉ tham khảo)

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

## P08-04 — Nhạc nền lặp có crossfade thực trong FFmpeg (28/10/2026)

**Đối chiếu master:** P08-03 (track/gain/fade/loop), P08-04 (nhạc lặp chuyển tiếp), P08-06 (audio crossfade và time map), `PRODUCT_REQUIREMENTS.md` §6; render hiện đang `-stream_loop` hoặc `aloop`, có thể sinh điểm nối cứng không mượt. Không nhầm với `acrossfade` giữa các clip video vốn đã có.

1. Trường tùy chọn `loop_crossfade` (giây, mặc định 0) **chỉ** cho track `mode=music` + `loop=true`; validate hữu hạn, khoảng 0–10, và độ dài mẫu phải đủ để xfade; 0 giữ hành vi cũ.
2. FFmpeg compositor tạo số lần lặp hữu hạn theo timeline đầu ra/offset và chiều dài mẫu, dùng **input FFmpeg riêng cho mỗi vòng lặp** và nối `acrossfade` tại mỗi điểm lặp (không dùng `asplit` do phát hiện assertion trên FFmpeg Windows 7.1.1). Không tự đổi sang lặp cứng nếu cấu hình vượt giới hạn; chỉ apply volume/gain/fade/delay **sau** khi nối để không tạo fade ở mọi bản sao.
3. AudioDialog thêm ô crossfade ở cuối bảng, giữ nguyên chỉ số/cấu trúc các ô cũ; round-trip đúng preset, hiển thị lỗi nếu nhập vào main/SFX hoặc không bật loop.
4. Regression: domain rejects NaN/negative/nonmusic/bounds, compile_graph chứa xfade, render FFmpeg video+audio thật và GUI round-trip; full CI Linux/Windows/frozen proof.
5. Cổng chưa khép: metre/clipping realtime, SFX nhiều-trigger trong UI, playlist dài, benchmark nhạc dài/corpus, loa thực trên Windows/installer. Không ghi PASS trước khi CI hoàn tất.

### Đối chiếu nghiệm thu P08-01/P08-04 lần này

- [x] Metadata FFprobe bất đồng bộ, duration min/max và cạnh ngắn 720/1080/2160 px, xử lý video lỗi và giữ lựa chọn ẩn. Cấu hình khoảng thời lượng sai hoặc chưa quét xong bị chặn trước dry-run. [CI 40658101720](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40658101720) PASS 225 Linux, 224 Windows + 1 skip, packaged proof hai hệ.
- [x] Crossfade loop nhạc chỉ áp dụng music+loop, có validation/giới hạn, AudioDialog round-trip, FFmpeg render thật. Vòng đầu dùng `asplit` làm Windows FFmpeg 7.1.1 báo assertion `best_input >= 0`; thay bằng đầu vào độc lập ở commit `54ab4398`, giữ test render, không tắt assertion. [CI 40659216526](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40659216526) PASS 233 Linux, 232 Windows +1 skip, binary/native-host/frozen proof hai hệ.
- [x] Bộ lọc codec/FPS/bitrate; SFX đa trigger; decoded playback PCM Peak/RMS meter pre-device; Batch manual playlist absolute đa thư mục đã có code, regression, render FFmpeg/PCM và [CI 41000959481](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41000959481) PASS.
- [ ] Profile/corpus rất lớn, render ETA/output size, per-track meter/solo/true-peak/EBU loudness, loa/driver/installer Windows máy thực vẫn mở. Không kết luận toàn phase P08 đạt nghiệm thu người dùng.

## P08-04 — SFX phát lặp theo số lần/khoảng cách, không vượt cuối video (28/10/2026)

**Đối chiếu master:** P08-03/P08-04/P08-06 yêu cầu hiệu ứng âm thanh đặt theo giây/cảnh/% và mix đúng timeline, `PRODUCT_REQUIREMENTS.md` §6; SFX hiện có `placement`, `scene_index`, `position_pct`, `offset` nhưng mỗi track chỉ phát một lần. `IMPLEMENTATION_COVERAGE.md` còn mở SFX repeat và multiple trigger.

1. Mở rộng track SFX với `repeat_count` (1..32, mặc định 1) và `repeat_interval` (s, >0 nếu count>1, mặc định 0). Nếu count>1, yêu cầu role SFX, không bật `loop`, không tự fallback. `domain.validate` chặn kiểu sai, NaN/infinity/âm/vượt giới hạn, trạng thái bất nhất.
2. Sau khi `audio_timeline_offset` resolve mốc video/cảnh/% trên timeline đầu ra, xác định mỗi onset = base + k×interval. Chặn nếu onset cuối nằm tại/sau cuối video. Mỗi trigger dùng FFmpeg input độc lập (tránh bug FFmpeg Windows khi chia nhánh), cùng trim/gain/fade và delay rồi mix thành một track SFX; track có mặc định 1 vẫn giữ pipeline cũ.
3. AudioDialog thêm hai cột 'SFX số lần' và 'SFX khoảng cách s', không đổi chỉ số field cũ; đọc/ghi round-trip và báo lỗi trạng thái không hợp lệ.
4. Tests domain invalid/edge, compile_graph onset/fade, FFmpeg render thật hai mốc, Qt offscreen round-trip, regression các audio music crossfade; CI Linux/Windows và frozen proof. Cổng còn mở: danh sách trigger không đều/playlist, realtime meter, stress rất dài và loa Windows máy thật.
5. Chỉ ghi DONE khi full CI cả hai hệ đạt; khối SFX này không đồng nghĩa P08 hay 95 nhóm đã nghiệm thu toàn diện.

### Bằng chứng P08-04 SFX repeat

- [x] Count 1–32 và interval được validate; count >1 yêu cầu SFX không loop, không tự fallback; onset cuối không được nằm tại/sau cuối timeline render. Track cũ mặc định phát một lần.
- [x] FFmpeg mỗi trigger là đầu vào riêng (không asplit), áp cùng trim/gain/fade và adelay theo timeline đã resolve, mix về track SFX. AudioDialog có count/interval và round-trip.
- [x] Regression kiểm tra sai kiểu/giới hạn, kiểm vị trí và PCM hai trigger có vùng yên lặng tách biệt, Qt UI. [CI 40660385646](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40660385646) PASS **246 Linux /245 Windows +1 skip**, frozen app/native-host proof hai hệ PASS.
- [x] SFX trigger không đều 2–32 mốc và Batch manual playlist cross-folder; [CI 41000959481](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41000959481) PASS (682 Linux / 681 Windows + 1 skip, packaged proof hai OS).
- [x] Playback PCM Peak/RMS meter pre-device đã có regression và packaged proof.
- [ ] Per-track meter/solo, true-peak/EBU loudness, real audio hardware/Windows device và release acceptance vẫn mở; không gắn P08 đạt toàn phase.


## P08-04 update — SFX trigger không đều (30/10/2026)

Lát cắt đã lập kế hoạch tại [P08_SFX_TRIGGER_LIST_PLAN.md](P08_SFX_TRIGGER_LIST_PLAN.md), triển khai trong [commit f6d90e4](https://github.com/danhgold7979-cyber/fonesi-edit/commit/f6d90e4470cdca3e98f23e48f4f0983521540a80), và xác minh bằng [CI 40988695667](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40988695667) attempt 2 SUCCESS. Danh sách 2–32 thời điểm không đều tính bằng giây từ timeline xuất; chi tiết test và cổng còn mở nằm trong P08_RESULTS. Đây không phải nghiệm thu toàn P08.


## P08-03 update — Decoded playback Peak/RMS meter (30/10/2026)

Detailed [plan](P08_AUDIO_PLAYBACK_METER_PLAN.md) preceded [implementation](https://github.com/danhgold7979-cyber/fonesi-edit/commit/c706930e2c5e8a5026e37fb5fd856901585330b5) and [Python 3.12 fix](https://github.com/danhgold7979-cyber/fonesi-edit/commit/743e68b3e4c262fa4bc824f9ccca4f1ec67361c2). [CI 40996183826](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40996183826) **SUCCESS exact SHA 743e68b**: 676 Linux/675 Windows passed +1 intentional POSIX-only skip, desktop/native-host and frozen synthetic proof both systems. Meter displays source/proxy or rendered-preview decoded PCM before the audio device, not true-peak, speaker volume, EBU loudness or per-track pre-mix levels; full P08 remains open.


## P08-04 update — Batch manual playlist across folders (30/10/2026)

[Plan](P08_MANUAL_AUDIO_PLAYLIST_PLAN.md) → [implementation](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a4ea6a851ac912503ce4db6fb08841b9dae8257a) → [backend tests](https://github.com/danhgold7979-cyber/fonesi-edit/commit/d4fd7e5a3b559fb415c00e54fcc711cdb9f754a6) → [Qt tests](https://github.com/danhgold7979-cyber/fonesi-edit/commit/3acf0b56a2b5f96c450d15076984d4e037c47282) → [final fixes](https://github.com/danhgold7979-cyber/fonesi-edit/commit/cfd2c4cf6a7c7a96e5619631d83c13ff2e2039c0) → [CI 41000959481](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41000959481) **SUCCESS exact SHA cfd2c4c** (682 Linux / 681 Windows + 1 intentional skip; frozen proof both OS).

The new `playlist` mode is distinct from folder-based `ordered`: it accepts an editable, explicit list of absolute audio file paths across multiple directories, permits same basenames and duplicate entries, preserves line order, maps one entry to one selected video, and never falls back silently. Full-path mapping is visible in dry-run. Complete FFprobe preflight (distinct-path cache, stream/duration, symlink/extension checks and cancellation) happens before any video snapshot. Existing shared/by-name/ordered/random behavior and project schema remain unchanged. Actual FFmpeg/PCM render verifies the assigned 660 Hz audio source.

**Still OPEN:** render ETA/output size, real large corpus, per-track meter/solo/true-peak/loudness, physical Windows audio/installer/user machine, live providers and SQLite #6. P08 is not complete as a whole.
