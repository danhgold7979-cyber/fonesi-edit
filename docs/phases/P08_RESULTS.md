# P08 — Batch/duration triển khai

Đã có scan folder loại output/cache/symlink, batch dry-run/snapshot/output theo kênh và duration water-filling với bounds, equal/proportional/weights, trim/loop/freeze rõ lựa chọn. Audio main/music/SFX qua compositor có volume/fade/delay/loop và giới hạn thời lượng. Test mới đối chiếu số cảnh, tốc độ, bất khả thi, folder exclusions và render loop/freeze thực; kết quả được cập nhật ở báo cáo tích hợp cuối.

Vòng tích hợp thêm video defaults riêng cho lô/ma trận (trim/speed/flip/rotation/gain/random), bind sub mới cho từng video/loop, IDs/tên kế hoạch deterministic, hai track song ngữ và output hợp lệ thật. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).

## P08-04 — Ghép âm thanh chính có chính sách (28/10/2026)

Đã triển khai trong **cùng mã nguồn/binary** Fonesi Edit:

- `batch_audio_assignments` chuẩn hóa 4 chế độ: `shared` (mặc định hiện tại), `by_name` (stem media trùng tên, mỗi video đúng 1 audio), `ordered` (video giữ thứ tự đã chọn, audio sort tự nhiên, kiểm tra đủ số tệp), và `random` (hash từ seed dự án + đường dẫn nguồn, chọn ổn định khi dry-run lại). Không tự đổi chế độ hoặc bỏ qua audio thiếu/mơ hồ.
- Chỉ nhận tệp có extension audio/media hỗ trợ, **loại symlink**, dùng FFprobe xác minh audio track + duration thực trước khi tạo toàn bộ batch plan; file không có audio/độ dài hợp lệ báo lỗi. Kết quả trả `audio_source` để UI cho xem trước mapping; thông tin main audio đóng gói trong Composition snapshot riêng từng video. Preset gốc và những track music/SFX không được sửa.
- BatchPage có dropdown chế độ và thư mục nhiều audio riêng bên cạnh audio chung. Dry-run liệt kê tên audio được gán; render vẫn qua compositor P07 và duration solver P08.
- Regression tests: tên trùng + 2 video/2 audio thực, phát hiện thiếu/trùng tên/sai số lượng/file không có track, mapping ordered/random tái lập với seed, sample FFmpeg render video có audio và UI radio/combo modes.

**Bằng chứng:** [GitHub Actions run 40642781347](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40642781347) PASS: **Linux 166 tests**, **Windows 165 tests + 1 skip** (fixture POSIX-only), packaged application/native-host/frozen proof Linux và Windows đều PASS. Đây là test offline có tạo media synthetic và chạy FFmpeg thật; không phải nghiệm thu loa/audio realtime trên máy sử dụng.

**Còn mở P08:** ghép audio theo playlist nhập tay nhiều nguồn hơn một folder, SFX placement theo cảnh/% thời lượng, meter/clipping realtime, music loop crossfade, nghe solo độc lập, ước lượng dung lượng/ETA với corpus lớn, benchmark và trải nghiệm Windows máy người dùng. Không đánh dấu toàn bộ P08 hoàn tất.

## P08/P09 — duration solver: số giây cảnh nhập tay

Bổ sung `allocation='manual'` và `manual_durations` vào `fit_duration` dùng chung: số giây từng cảnh dương/hữu hạn, tổng sau transition đúng target, giới hạn speed/trim được kiểm trước render; lệnh thiếu hoặc không khả thi báo lỗi, không rơi vào proportional. Vừa có option `weights` vừa có `manual` ở Matrix UI, không thay Batch mặc định. [CI 40645339209](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40645339209) PASS Linux/Windows và frozen proof. SFX theo cảnh/audio timeline nâng cao vẫn mở.

## P08-01/P08-04 — SFX mốc tương đối và Batch search/filter (28/10/2026)

Triển khai vào **cùng mã nguồn/compositor** Fonesi Edit:

- **Sound effect placement:** `Composition.audio` SFX nhận các mốc `absolute`, `percent` (0–100% thời lượng video đã render), `video_end` (số giây trước cuối video), `scene_start` và `scene_end` (scene index 1-based, sau đầu/trước cuối cảnh). `offset` theo nghĩa sau/trước mốc đã ghi trong AudioDialog. Mọi mode không áp dụng cho main/music; domain validate index/type/finite và compiler chặn SFX bắt đầu trước 0 hoặc tại/sau cuối video. FFmpeg đặt đúng `adelay` sau trim/speed/transition, duy trì fade/gain/mute/solo/limiter.
- **AudioDialog** có UI mốc SFX, % và cảnh, round-trip từ preset hiện có. Cấu hình sai được báo lỗi; track không có `placement` tiếp tục có offset tuyệt đối như trước. Test PCM xuất thật xác minh đầu video im lặng, SFX phát ở nửa sau, cùng test scene/transition, domain invalid input, Qt UI.
- **BatchPage** có tìm video/kênh, lọc đuôi video; chọn/bỏ/đảo **mục đang hiển thị**, các tệp bị ẩn giữ checkbox. Mọi thay đổi checkbox/folder/audio/mode/speed/preset đều làm vô hiệu hóa dry-run cũ. Worker lập kế hoạch có revision token, không áp kết quả async cũ sau khi người dùng sửa nguồn/preset. Preview/Chạy cần lập kế hoạch lại.
- **Kiểm thử hồi quy:** synthetic Qt, FFmpeg audio/video thật và multi-video SFX % source-dependent. Ban đầu CI bắt một assertion sai do MP4 fixture dài 0,52 giây theo FFprobe thay vì hint 0,50 giây; test đã sửa đối chiếu chính xác duration probe, **không hạ ngưỡng hoặc bỏ assertion**.

**Bằng chứng:** [CI 40655116611](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40655116611) PASS **219 test Linux / 218 test Windows + 1 skipped POSIX-only**, build app/native host và frozen packaged proof trên hai hệ. Artifact `FonesiEdit-Windows-development` là binary nội bộ, không phải installer đã ký/Release.

**Còn mở:** music loop crossfade, sound effect nhiều mốc một lần trong UI, meter/clipping nghe realtime, duration/resolution filter từ metadata và corpus lớn, ước tính dung lượng/ETA, áp dụng toàn diện trên Windows máy người dùng. P08 chưa đủ cổng nghiệm thu cuối.

## P08-01 — Quét nhiều folder gốc, loại trùng và hủy kết quả quét cũ (28/10/2026)

Đã code `scan_multiple_folders` hợp nhất các root được chọn bằng path đã resolve, giữ nhóm channel đúng thư mục, tự bỏ file trùng khi root trùng hoặc chồng cha/con; vẫn bỏ thư mục ` edit`, cache, symlink và file không phải video theo `scan_folders`. BatchPage có ô thư mục gốc + danh sách folder bổ sung mỗi dòng, nút chọn folder, chạy cùng worker. Khi sửa danh sách folder, các checkbox/nhóm cũ bị xóa và phải quét lại; khi quét mới bắt đầu, xóa lựa chọn cũ trước khi chạy; kết quả callback từ lần quét cũ bị bỏ theo scan revision, không ghi đè danh sách mới. Các thay đổi này không chạm/xóa media gốc.

**Kiểm thử:** multi-root + nested overlap/duplicate + bỏ output/cache + Qt GUI quét 2 nguồn + invalidation và callback đến sai thứ tự. [CI 40656796768](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40656796768) **PASS 222 tests Linux, 221 tests Windows +1 skip POSIX-only**, packaged/native-host/frozen proof hai hệ PASS. Đây là quét thư mục **local**, không chứng minh kết nối mạng xã hội đã scan đủ kênh. P08-01 vẫn mở filter duration/resolution, hàng trăm nghìn file và sức chịu tải thực.

## P08-01 — Metadata duration/resolution có kiểm soát (28/10/2026)

`probe_batch_metadata` đọc FFprobe bằng worker nền sau khi quét nhiều folder; mỗi video resolve chỉ đọc một lần. Kết quả có duration/width/height, tệp lỗi được báo riêng và không tự coi là khớp bộ lọc. Trong BatchPage có thời lượng tối thiểu/tối đa (0 = không giới hạn), độ phân giải theo **cạnh ngắn** ≥720/1080/2160 px phù hợp ảnh/video ngang và dọc. Kết quả quét cũ bị loại bởi revision; bộ lọc chỉ ẩn mục, không sửa checkbox của video ẩn. Không cho tạo dry-run khi đang đợi FFprobe hoặc khoảng thời lượng đảo ngược. Không sửa file nguồn.

**Bằng chứng:** [CI 40658101720](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40658101720) PASS: **225 tests Linux**, **224 tests Windows +1 skip** (fixture POSIX). Build app/native-host và kiểm chứng frozen binary trên cả hai hệ PASS. Test FFprobe nguồn thật/file hỏng, khử trùng, cancel và Qt offscreen (vị trí ngang/dọc, chọn ẩn, callback stale, khoảng không hợp lệ). Chưa có kiểm chứng corpus rất lớn/metadata codec/FPS/bitrate.

## P08-04 — Crossfade nhạc lặp, đã sửa tương thích Windows (28/10/2026)

Track `mode=music, loop=true` hỗ trợ thêm `loop_crossfade` (giây); 0 mặc định giữ behavior cũ. Domain yêu cầu số hữu hạn từ 0 đến 10 và chỉ cho nhạc lặp, graph chặn thời gian crossfade từ nửa mẫu nguồn trở lên và giới hạn tối đa 128 vòng để giữ tài nguyên. FFmpeg tạo các đầu vào âm nhạc độc lập cho từng vòng và nối `acrossfade` giữa các đoạn; volume/fade/delay chỉ áp sau khi nối. AudioDialog có ô Crossfade lặp, lưu/khôi phục đúng, không cho main/SFX dùng crossfade.

**Quá trình kiểm lỗi thực:** Bản đầu [CI 40658721822](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40658721822) FAILED Windows 1 test export: FFmpeg 7.1.1 báo assertion `best_input >= 0` với nhánh `asplit`. Đã sửa nguyên nhân bằng input riêng, không skip/bỏ test. **[CI 40659216526](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40659216526) PASS:** **233 tests Linux**, **232 tests Windows +1 skip**; source regressions và frozen app/native-host proof cả hai hệ PASS, có FFmpeg render audio/video thật.

**Còn mở P08:** chất lượng âm khi nghe trên thiết bị Windows thực, meter/clipping realtime, SFX nhiều mốc lặp, import playlist, stress/soak batch lớn, ước tính dung lượng/ETA, installer/ký số/release và provider live. P08 chưa được đánh dấu nghiệm thu toàn diện.

## P08-04 — SFX repeat theo khoảng cách trên timeline render (28/10/2026)

SFX `repeat_count` (mặc định 1, tối đa 32) và `repeat_interval` (giây) cho phép một track phát nhiều lần với khoảng cách đều từ mốc `absolute/percent/video_end/scene_start/scene_end` đã resolve theo video đầu ra. Domain chặn kiểu/giới hạn không hợp lệ, role khác SFX, hoặc kết hợp loop; compositor chặn trigger cuối tại/sau cuối video. Mỗi sự kiện dùng FFmpeg audio input riêng, trim/gain/fade/delay, mix thành một track trước limiter; track cũ phát một lần vẫn giữ pipeline. AudioDialog bổ sung hai cột số lần và giây/khoảng cách, sửa/round-trip.

**Bằng chứng:** [CI 40660385646](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40660385646) PASS **246 tests Linux**, **245 tests Windows +1 skip POSIX-only**; packaged app/native host/localhost frozen verification PASS cả hai hệ. Test kiểm domain invalid, FFmpeg graph hai adelay 200/600ms, video có hai khoảng SFX nghe được và khoảng im lặng ở giữa bằng PCM, GUI lưu giá trị và báo lỗi. Chưa có arbitrary trigger list, nhiều trigger không theo chu kỳ, live loudness meter/loa thực hoặc benchmark corpus lớn.
