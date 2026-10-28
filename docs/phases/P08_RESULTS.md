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
