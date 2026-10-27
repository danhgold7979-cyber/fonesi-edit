# Kiểm chứng bản phát triển desktop

Môi trường hiện tại: Linux x86_64, Python 3.12, PySide6 6.8.3, FFmpeg/ffprobe 7.1.5, CPU; không có GPU/Google Chrome thật hoặc thiết bị âm thanh. Mọi media thử được tạo synthetic. Không sử dụng tài khoản hay gọi API dịch trả phí trong kiểm thử local.

## Kiểm tra đã chạy

- Hồi quy source: `QT_QPA_PLATFORM=offscreen uv run pytest -q --junitxml=.local/desktop-tests.xml`. Kết quả cuối: **92 tests qua, 0 lỗi, 0 thất bại, 0 bỏ qua**; xem [evidence JSON](evidence/desktop-verification.json).
- Source end-to-end: `uv run fonesi-edit --verify .local/source-release` đã qua 4 job độc lập: batch, ma trận, tải video và ảnh bằng HTTP localhost. Có burn-in song ngữ và đổi tên/undo trong proof mới.
- Frozen app: các checkpoint `.local/packaged-03`, `.local/packaged-final`, `.local/packaged-resource` đã chạy app/worker, FFmpeg gói kèm, tải video/ảnh và UI; Lượt cuối `.local/packaged-handoff` đã qua đủ 4 job, burn-in song ngữ, đổi tên/undo, kiểm tra FFmpeg gói kèm và UI giải mã frame Qt. 36 file source khớp hash trong bundle.
- Smoke GUI source có source media thật đã giải mã ít nhất một frame Qt, mở giao diện và thoát sạch; không chỉ kiểm tra process hoặc file screenshot tồn tại.
- Tool repair/hash/traversal dùng fixture riêng có nhãn, không giả là installer Windows thật. Dịch cache/quota/glossary dùng transport kiểm thử, không giả là Google/Libre live.

Một lỗi chỉ xuất hiện trong binary đã được phát hiện và sửa: Qt mang bộ libavcodec riêng làm FFmpeg con mất libx264 trên Linux. Build hiện tách binary và thư viện FFmpeg ở `tools/bin`/`tools/lib`, launcher chọn thư viện riêng; tiến trình Qt giữ thư viện của Qt. Script proof từ chối dùng FFmpeg hệ thống thay cho bản gói.

## Tái lập

```bash
uv sync --locked
QT_QPA_PLATFORM=offscreen uv run pytest -q
uv run python scripts/check_plan.py
uv run fonesi-edit --verify .local/source-new
uv run python scripts/build_desktop.py --native-host
uv run python scripts/verify_packaged.py --folder .local/packaged-new
```

Mỗi proof cần folder mới. Build có `build-info.json` chứa phiên bản, hash lock/source và binary media; output có manifest/hash nguồn/cấu hình. CI Windows/Linux dùng cùng các bước, upload evidence riêng và gói Windows phát triển nếu toàn job thành công.

## Cổng còn mở

Không có bằng chứng trong môi trường này cho tải nguyên kênh trên từng mạng xã hội, API dịch thật, phiên Chrome→connector Windows, GPU/VRAM/driver, HiDPI/âm thanh Windows, soak/crash/mất điện dài hạn và toàn bộ tương tác nâng cao. Proxy live đã chặn YouTube/Bilibili ở kiểm chứng P02; draft network chưa phải runtime đã áp dụng.

Bản phát triển hiện có đường chạy thật cho các workflow chính. Các tùy chọn nâng cao còn phải code/kiểm chứng được liệt kê tại [đối chiếu triển khai](IMPLEMENTATION_COVERAGE.md), giữ nguyên trong [master plan](IMPLEMENTATION_PLAN.md). Không đánh dấu toàn bộ phase/95 nhóm đã nghiệm thu.
