# Fonesi Edit

Ứng dụng desktop dùng cá nhân để tải ảnh/video theo kênh, tải và dịch phụ đề, edit hàng loạt và ghép video theo ma trận cảnh/góc quay.

Repository có master plan 12 phase và ứng dụng Python/Qt/FFmpeg đang phát triển: 8 tab, project, phụ đề, editor, batch, ma trận, hàng đợi, tự động hóa và cài đặt. [Trạng thái hiện tại](docs/CURRENT_STATUS.md) phân biệt code đã có, kiểm tra local và nghiệm thu còn mở; chưa coi mọi nền tảng/Windows/GPU đã được xác nhận.

## Chạy ứng dụng

Máy phát triển cần Python 3.12, uv, FFmpeg và ffprobe:

```bash
uv sync --locked
uv run fonesi-edit
```

Đọc [hướng dẫn sử dụng](docs/USER_GUIDE.md). Bộ tải yt-dlp/gallery-dl được khóa và gói cùng app. Google Chrome thật và Node tùy quy trình; Settings quét, chọn đường dẫn, tải/cài bản có xác minh và rollback công cụ app quản lý. Không lưu cookie/API key vào Git hay project.

## Kiểm tra và đóng gói

```bash
uv run python scripts/check_plan.py
uv run pytest -q
uv run fonesi-edit --verify .local/proof-new-run
uv run python scripts/build_desktop.py --native-host
uv run python scripts/verify_packaged.py
```

Trên Linux không có display, thêm `QT_QPA_PLATFORM=offscreen` trước lệnh GUI/test. `--verify` chạy batch/ma trận/render và tải video/ảnh qua HTTP localhost bằng dữ liệu synthetic, không cần tài khoản hay API trả phí. Mỗi lần dùng thư mục mới; kết quả nằm trong `proof.json`.

Windows: `scripts/build_windows.ps1` tạo `dist/FonesiEdit/FonesiEdit.exe` và native host. CI chạy trên Linux/Windows, kiểm tra cả binary và giữ artifact Windows để review khi các bước thành công. Chưa có bằng chứng CI thành công trong phiên cloud nếu chưa đọc được kết quả Actions. Các bản thử P02 và script kiểm chứng cũ vẫn giữ cho hồi quy kỹ thuật.

Ảnh/video thử, database, bản đóng gói và browser profiles không commit. Nền tảng mục tiêu đầu tiên là Windows; cần kiểm tra Chrome thật, quyền tài khoản, encoder GPU và trải nghiệm trực tiếp trên máy mục tiêu.

## Kế hoạch và trạng thái

- [Đặc tả sản phẩm](docs/PRODUCT_REQUIREMENTS.md)
- [Preview, tùy chọn editor, phím tắt và tự động hóa](docs/EDITOR_SPEC.md)
- [Kế hoạch 12 phase, đầu việc và điều kiện hoàn thành](docs/IMPLEMENTATION_PLAN.md)
- [Thiết kế kỹ thuật, dữ liệu và các quyết định cần kiểm chứng](docs/TECHNICAL_DESIGN.md)
- [Đối chiếu yêu cầu với phase và tình huống nghiệm thu](docs/REQUIREMENTS_TRACEABILITY.md)
- [Ma trận kiểm chứng từng nền tảng tải](docs/PLATFORM_SUPPORT_MATRIX.md)
- [Cài đặt công cụ, hồ sơ Chrome thật và tài khoản nền tảng](docs/SETTINGS_AND_BROWSER_SPEC.md)
- [Kế hoạch chi tiết P01](docs/phases/P01_PLAN.md), [kết quả P01](docs/phases/P01_RESULTS.md)
- [Kế hoạch chi tiết P02](docs/phases/P02_PLAN.md), [kết quả/blocker P02](docs/phases/P02_RESULTS.md)
- [Screenshot và frame kiểm chứng local](docs/evidence/README.md)

Nền tảng mục tiêu đầu tiên là Windows. Giọng AI, ASR, OCR và tracking tự động được tích hợp ở giai đoạn sau.

Theo yêu cầu người dùng: trước mỗi phase đọc master plan, lập phase plan, triển khai và ghi kết quả; không đánh dấu phase hoàn tất khi cổng bắt buộc còn bị chặn. Quy trình lưu ở AGENTS.md.

## Sổ thực hiện và nghiệm thu

Xem [nhật ký thực hiện tích hợp](docs/PHASE_EXECUTION_LEDGER.md) để theo dõi từng phase, commit/CI proof và các cổng bắt buộc vẫn còn mở; các bản build/fixture không chứng minh 95 nhóm đã được nghiệm thu.

Để xem bản build Windows thử nghiệm từ CI: [Desktop verification run 40655116611](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40655116611) → Artifacts → `FonesiEdit-Windows-development` (có hạn lưu); xem [trạng thái nghiệm thu](docs/PHASE_EXECUTION_LEDGER.md) trước khi dùng.
