# Fonesi Edit rebuild — hướng dẫn checkpoint phát triển

**Chưa phải bản hoàn tất.** Xem [trạng thái](CURRENT_STATUS.md) và [coverage 95 nhóm](rebuild/coverage.json); không suy toàn bộ tính năng đã xong từ số tab hoặc số test.

## 1. Dự án và nguồn
- Thêm video bằng **＋ Media** hoặc kéo tệp/thư mục. Probe chạy nền; file gốc không bị sửa.
- **Lưu/Mở** project giữ đường dẫn, thời gian, layer, cue, audio; bản tự lưu nằm trong user-data, tách khỏi thư mục cài.
- **Preset: nhập/xuất/copy nhóm** cho nhập riêng layer/audio, báo asset thiếu; relink tìm media bằng hash, không đoán chỉ theo tên.

## 2. Editor và playback
- Chọn layer, kéo vị trí; tay nắm góc phải dưới resize; tay nắm trên xoay. Shift chọn nhiều, Alt tạm bỏ snap; Delete bỏ layer, không xóa nguồn. Một gesture là một undo.
- Có chữ, logo, mask blur/mosaic/color ở model; UI mask mặc định blur. Inspector chỉnh số, khóa/ẩn, z-order, font và keyframe tại playhead. Preset motion dùng seed project, thời gian thực không phụ thuộc zoom/FPS.
- **Phát/dừng** dùng proxy video/audio được tạo nền và kiểm tra. Waveform là envelope âm thanh thật. Preview layer chạy compositor CPU; **Frame xuất chuẩn** chạy canonical reference để đối chiếu.
- **Clip/Audio** chỉnh trim, speed, fit/crop/blur, flip/rotation/màu; mỗi clip có chính sách cut/speed/loop/freeze rõ. Không tự lấy clip khác khi clip ngắn.
- **＋ Audio** probe ở nền. Trong Clip/Audio chọn vai trò main/music/SFX, gain, trim, điểm vào, loop, fade, mute/solo; mixer có limiter. SFX event theo cảnh/ducking/crossfade đầy đủ vẫn còn mở.
- Canvas/format hỗ trợ hiện tại không có nghĩa đủ mọi thuộc tính đặc tả. Crop trực tiếp, anchors, mọi shortcut/remap, font fallback/shaping, motion tránh vùng và một số thao tác timeline đang tiếp tục.

## 3. Phụ đề và dịch
- Nhập SRT/VTT/ASS. ASS được giữ text/timing và báo rõ mất thuộc tính chưa hỗ trợ; file gốc vẫn nguyên.
- Bảng có gốc/bản dịch/thời gian/khóa. Chỉnh tay khóa cue; bật song ngữ khi muốn. Kiểm tra overlap, ngắn, dài và vượt cuối video.
- Mặc định burn vào video và giữ SRT rời. Không có sub vẫn có thể edit; không có ASR/OCR tự tạo giả.
- Dịch chỉ chạy với endpoint LibreTranslate người dùng cấu hình, consent và hạn mức ký tự. Key từ `FONESI_TRANSLATION_KEY`, không ghi project/log. Timeout không được retry vô điều kiện vì có thể đã tính phí.
- Chất lượng Trung–Việt, glossary/context và khả năng live provider chưa được nghiệm thu.

## 4. Batch và ma trận
- Batch: thêm nhiều folder → chọn folder → quét/dry-run → chạy thử mục đầu hoặc chạy các mục hợp lệ. Output/cache/symlink bị loại; sub ghép theo file cụ thể, mơ hồ phải xử lý.
- Ma trận: thư mục cha chứa các cảnh, mỗi cảnh chứa góc. Natural sort, content ID; không tự đổi tên nguồn.
- Chọn N/W/K/seed/phạm vi K; sinh có giới hạn thời gian. Sửa ô phải revalidate; timeout khác chứng minh vô nghiệm. CSV ghi góc/chuỗi.
- Hệ thống có reservation/history primitives; lịch sử đầy đủ và UI khóa/cân bằng/rename vẫn còn được tích hợp. Không coi các đường này là hoàn tất toàn đặc tả.

## 5. Download, Chrome và tools
- URL mỗi dòng → quét → chọn item → hàng đợi. Tổng/quét đầy đủ không được giả định từ playlist trả về.
- Video dùng yt-dlp, ảnh dùng gallery-dl; hiện có bằng chứng localhost thật, chưa chứng nhận nguyên kênh mạng xã hội.
- 10 nền tảng có cấu hình hồ sơ/tài khoản. Chrome riêng dùng user-data-dir độc lập; mật khẩu/OTP/QR nhập trong Chrome thật. Không copy cookie DB/tắt bảo vệ. Account đã chọn mà bridge chưa xác minh thì bị chặn, không tự chuyển public.
- Tool scan cho biết path/version/capability. Path chọn sai không tự đổi bản khác. Windows x64 có nút cài FFmpeg/ffprobe từ manifest pin/checksum; vẫn cần workflow proof Windows. Chrome mở trang tải chính thức, không tự báo cài xong.

## 6. Hàng đợi, automation và phục hồi
- Pause chỉ ngừng nhận job mới; cancel xử lý công đoạn đang chạy, render có thể phải chạy lại từ đầu. Retry chỉ job lỗi, giữ snapshot. Ưu tiên chỉ đổi job đang chờ.
- Job chạy subprocess, lưu trạng thái SQLite. Thành công cần probe/decode/duration/track validation, không chỉ file tồn tại.
- Tự động/tài nguyên trong Settings: watcher tắt mặc định, bật rõ mới chạy khi app mở; chờ file ổn định rồi probe. Không có dịch vụ nền khi app đóng. Render/download/probe có giới hạn riêng và RAM/disk reserve.
- GPU/VRAM/nhiệt độ chưa đo được là unknown; GPU bắt buộc mà chưa có renderer kiểm chứng thì chặn, không báo tăng tốc giả.

## 7. Chạy và kiểm tra
```sh
uv sync --locked
uv run fonesi-edit
uv run python scripts/check_plan.py
QT_QPA_PLATFORM=offscreen uv run pytest -q
uv run fonesi-edit --verify .local/proof-new-empty-directory
uv run python scripts/build_desktop.py
uv run python scripts/verify_packaged.py
```
Windows developer: `scripts/build_windows.ps1` sau khi có FFmpeg/ffprobe trong PATH. GitHub CI dùng manifest pinned để cài trong runner cô lập. Bản frozen không cần Python/pip để chạy; nghiệm thu máy người dùng, Chrome, HiDPI, âm thanh thực và GPU vẫn riêng.
