# P02 — Kết quả thực nghiệm hiện tại

Trạng thái: **chưa hoàn tất phase**, đã có prototype chạy thật và kiểm chứng CPU/Linux. Giữ nguyên cổng tổng thể; **P03 chưa bắt đầu**. Ngày: 27/10/2026.

## 1. Mã đã triển khai

- Package Python có `pyproject.toml` và `uv.lock`; Qt/PySide6 6.8.3, yt-dlp 2026.10.26, gallery-dl 1.32.18, PyInstaller 6.22.3 được resolve từ nguồn package tin cậy.
- Prototype Qt: mở media cục bộ, bố trí/kéo vị trí chữ, X/Y/cỡ/tốc độ, chọn sub/logo/font, render/cancel/progress, playback và tool scan/path override.
- Renderer CPU thật: text Unicode không chèn vào shell/filter expression, logo RGBA, blur vùng cố định, SRT burn-in, giữ audio, no-overwrite, validate probe/duration/tracks/full-decode rồi publish.
- SRT parser/time map: BOM/CRLF, nhiều dòng, cue không hợp lệ, giao với đoạn trim, speed rational và offset.
- Official Google Translation v2 adapter: chỉ gửi khi có cấu hình; báo thiếu key, không mock dịch. Chưa chứng minh chất lượng/billing live.
- Chrome profile proof: tạo hồ sơ app-owned độc lập, mở URL nền tảng bằng Google Chrome chính thức khi tìm thấy; không đọc cookie, không tuyên bố auth/bridge đã dùng được.
- Script Windows verify/build và GitHub Actions Linux/Windows đã chuẩn bị; kết quả remote cần kiểm tra riêng, không suy ra đã pass vì có YAML.

## 2. Bằng chứng local đã đạt

Lệnh chính: `uv run pytest -q`, `uv run python scripts/run_p02_local.py`, `QT_QPA_PLATFORM=offscreen uv run fonesi-prototype ui --smoke --source <fixture> --screenshot <path>`.

| Kiểm tra | Kết quả |
| --- | --- |
| Test suite | 24 bài qua, không có bài skip trong lần local được ghi nhận |
| FFmpeg/ffprobe | 7.1.5 Debian, CPU libx264/AAC; artifact decode đầy đủ |
| Dọc/ngang | 360×640 và 640×360, 25 FPS, synthetic 3 giây; output 3.008 giây |
| Sample render | 0.454s ngang, 0.478s dọc trong lần đo; chỉ là fixture nhỏ trên cloud hiện tại |
| Unicode/path/filter | Tên Việt/Trung, dấu nháy/ký tự filter trong title/path được xử lý, không overwrite |
| Logo alpha | Fixture có alpha=0 và alpha>100; logo nhìn thấy trên frame output |
| Qt UI | Khởi tạo, nạp frame thật, screenshot và đóng sạch offscreen |
| Package Linux | PyInstaller 6.22.3 build onedir có FFmpeg/ffprobe, binary mở media/chụp screenshot/đóng sạch exit 0; không thay kết quả Windows |
| Qt video decode | Nhận ít nhất hai QVideoFrame thật của video đã render |
| Decode parity | Qt frame so với FFmpeg tại startTime của frame, mean RGB error <3/255 |
| Cancel/error | Không publish output khi hủy/nguồn lỗi, không thay nguồn/output cũ; UI smoke trả exit 1 nếu media yêu cầu không nạp được |
| Tool scan | FFmpeg, ffprobe, yt-dlp, gallery-dl khởi chạy/version được; Google Chrome chính thức thiếu |
| Plan validation | 12 phase, 94 task, 95 nhóm yêu cầu; link/task references hợp lệ |

Corpus là **synthetic lavfi**, không phải nội dung đã tải từ mạng xã hội. Decode parity của video đã composited không thay nghiệm thu toàn bộ thao tác/keyframe/font preview của P04/P07. Cloud có 5 vCPU và RAM khoảng 33 GiB; không suy ra tốc độ máy Windows khác.

Screenshot/frame tham khảo ở [evidence](../evidence/README.md); media/log/runtime giữ trong `.local/` bị loại khỏi Git.

## 3. Lỗi đã chẩn đoán và sửa

- PySide6 6.12.0 được resolver chọn ban đầu gây native segfault khi khởi tạo QAudioOutput trong Linux thiếu PipeWire config. Reproducer tối thiểu xác nhận, không nuốt lỗi bằng try/except Python. Khóa PySide6 6.8.3, chạy lại UI/audio init và tests thành công. Không coi đây là kiểm tra loa vật lý.
- Logo synthetic tạo bằng drawbox trên nền alpha=0 ban đầu vẫn trong suốt. Thay fixture bằng PNG RGBA có alpha rõ và thêm kiểm tra pixel alpha; kiểm tra frame đã thấy logo thật.

## 4. Blocker và phép thử đã thực hiện

| Task | Trạng thái hiện tại | Prerequisite còn thiếu |
| --- | --- | --- |
| P02-01 | Linux toolchain/dependency lock đã kiểm chứng; Windows còn mở | Máy/runner Windows cho phần mục tiêu |
| P02-02 | YouTube test item và Bilibili test item đều bị proxy từ chối CONNECT HTTP 403 | Áp dụng quyền egress; sau đó mới đánh giá extractor/auth |
| P02-03 | Parser/adapter/báo thiếu config có test, chưa dịch live | Provider/key hợp lệ và quyền tới translation.googleapis.com |
| P02-04 | Qt 6.8.3 + FFmpeg reference/decode đã chạy local | Interactive Windows, đầy đủ UI parity và benchmark seek |
| P02-05 | CPU encode pass; thử NVENC thất bại vì không có libcuda.so.1, không có /dev/dri | GPU/driver/máy có khả năng thật |
| P02-06 | Có script và CI build Windows, kết quả remote chưa xác nhận | Runner Windows và chạy bản đóng gói thực tế |
| P02-07 | Có số đo fixture CPU nhỏ; chưa có ngân sách Windows/UI hoàn chỉnh | Máy tham chiếu/mẫu đủ lớn và đo tương tác |
| P02-08 | Qt/FFmpeg có ứng viên bằng evidence; provider và auth còn mở | Hoàn tất các phép thử phụ thuộc |
| P02-09 | Discovery/path/version và dependency package lock có proof; Windows installer/rollback chưa đạt | Phép thử installer/lease trên Windows |
| P02-10 | Profile isolation có test; không thay Chromium cho Chrome | Google Chrome Windows và người dùng đăng nhập để thử bridge |

URL thử live: `https://www.youtube.com/watch?v=BaW_jenozKc`, `https://www.bilibili.com/video/BV13x41117TL` (mẫu công khai từ upstream extractor). Proxy trả 403 trước khi có response của website; chưa thể kết luận website chặn tài khoản hay yt-dlp lỗi.

Không có GH_TOKEN vẫn push Git thành công qua HTTPS proxy hiện có; không yêu cầu token GitHub mới.

## 5. Cấu hình cloud đã lưu nháp

- `install_script`: `bash scripts/bootstrap.sh` trong checkout.
- `start_skill`: đọc master/phase plan, refresh lock, local proof, test, headless UI và giới hạn nghiệm thu.
- Custom egress: youtube.com, *.youtube.com, youtubei.googleapis.com, *.googlevideo.com, *.ytimg.com, www.bilibili.com, api.bilibili.com, *.bilivideo.com, *.hdslb.com.
- Optional personal binding `FONESI_GOOGLE_TRANSLATE_API_KEY`, destination `translation.googleapis.com`; domain này được tool tự thêm. Chỉ khai báo tên, không có giá trị.
- Tool đã xác nhận draft saved và yêu cầu Review/Save trong Environment settings rồi Publish. Việc lưu draft **chưa áp dụng mạng, chưa tạo key, chưa publish**; không lặp lại request bị chặn khi runtime chưa đổi.

## 6. Điều kiện tiếp tục

Áp dụng egress rồi retry live nguồn; cấu hình provider qua nơi nhập an toàn nếu muốn dùng adapter Google; kiểm tra kết quả Windows CI và chạy Chrome/account/GPU trên máy tương ứng. Theo chỉ đạo mới của người dùng, tiếp tục code các phần độc lập sau khi đọc master/lập phase plan. P02 vẫn chưa được đánh dấu hoàn tất nghiệm thu bên ngoài.
