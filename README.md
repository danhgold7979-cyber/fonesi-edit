# Fonesi Edit

Ứng dụng desktop dùng cá nhân để tải ảnh/video theo kênh, tải và dịch phụ đề, edit hàng loạt và ghép video theo ma trận cảnh/góc quay.

Repository có đặc tả, kế hoạch 12 phase và mã **prototype P02** chạy bằng Python/Qt/FFmpeg. P01 đã hoàn tất thiết kế. P02 đã kiểm chứng CPU/Linux nhưng còn các cổng live source, dịch, Windows/Chrome/GPU; chưa có bản sản phẩm hoàn chỉnh.

## Chạy prototype

Máy phát triển cần Python 3.12, uv, FFmpeg và ffprobe. Công cụ tự cài cho người dùng cuối thuộc các phase sau; prototype hiện quét/trỏ/kiểm tra bản đã có.

```bash
uv sync --locked
uv run python scripts/check_plan.py
uv run pytest -q
uv run fonesi-prototype scan
uv run python scripts/run_p02_local.py
uv run fonesi-prototype ui
```

GUI hiện có mở video cục bộ, kéo vị trí chữ và chỉnh X/Y/cỡ/tốc độ, chọn SRT/logo/font, render CPU thật có blur và giữ audio, progress/cancel, playback, tool scan/path override và Chrome profile proof. Các tab đều ghi rõ giới hạn prototype; chưa có batch/ma trận/auth session bridge hoàn chỉnh.

Trên Linux không có display:

```bash
QT_QPA_PLATFORM=offscreen uv run fonesi-prototype ui --smoke
```

Trên Windows, kiểm chứng bằng `scripts/verify_windows.ps1 -OpenUi`; build proof bằng `scripts/build_windows.ps1`. Những script này cần được chạy trên Windows để có kết quả, không thể coi build Linux là Windows đã đạt.

Ảnh, video synthetic và log được sinh trong `.local/`, không đưa vào Git. Mỗi lần `run_p02_local.py` tạo thư mục mới. Không đặt cookie/API key vào repository; adapter dịch chỉ gọi API khi cấu hình `FONESI_GOOGLE_TRANSLATE_API_KEY` hợp lệ.

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
