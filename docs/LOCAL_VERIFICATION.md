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

## GitHub Actions — P02 frozen-app verification

Lần chạy mới nhất trên nhánh phase/p02-windows-packaged-proof: [Desktop verification #40634117095](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40634117095), commit ff3254ea8619bff5aefd4c2dac6e36bda637ac37.

- Linux: 92 tests, 0 fail/error/skip; build app/native host và frozen proof đạt. Proof gồm hai job render, tải video và ảnh qua localhost, phụ đề song ngữ, rename/undo và UI smoke/frame decode.
- Windows Server 2025: 92 tests, 0 fail/error, 1 skip có chủ đích cho fixture installer POSIX; build app/native host và frozen proof đạt. Hai job render, tải video/ảnh localhost, phụ đề song ngữ, rename/undo và UI smoke/frame decode. Frozen proof hoàn thành trong 8.781 giây.
- Cả hai proof đều dùng synthetic media và localhost; không chứng minh tải nguyên kênh mạng xã hội, dịch live, Chrome session handoff hoặc GPU. Một test installer POSIX được skip trên Windows và không được coi là nghiệm thu installer Windows.

Root cause lỗi gallery-dl trước đó là worker in đường dẫn Unicode vào stdout Windows cp1252. Đã đặt gallery-dl output mode thành null trong worker GUI và thêm regression test dùng stdout cp1252 nghiêm ngặt.


## GitHub Actions — P03 storage/security hardening

Latest run: [Desktop verification #40635978628](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40635978628), commit 989368b9560b059c27c131c36ed12955f98c6602.

- Linux: 108 tests pass; plan validation, build production/native host và frozen proof pass.
- Windows runner: 107 tests pass, 1 POSIX installer-fixture test được skip có chủ đích; plan validation, build production/native host và frozen proof pass.
- Proof trên cả hai OS gồm render batch/ma trận, tải video/ảnh synthetic qua localhost, phụ đề song ngữ, rename/undo, UI smoke và frame decode. Windows proof đánh dấu passed=true, frozen=true.
- Regression test ban đầu phát hiện file backup tạm còn bị khóa trên Windows vì SQLite connection context manager không tự đóng connection. Đã đóng connection tường minh và chạy lại xanh trên cả hai OS.
- Backup giờ kiểm tra integrity, không ghi đè, dọn file tạm; payload validator chặn alias credential; worker error sanitizer lọc credential và query URL. Không có bí mật hay runtime media được commit.

Kết quả này không thay thế live source/translation, Chrome session handoff, GPU, installer trên máy người dùng hoặc soak/crash/power-loss.

## Cổng còn mở

Không có bằng chứng trong môi trường này cho tải nguyên kênh trên từng mạng xã hội, API dịch thật, phiên Chrome→connector Windows, GPU/VRAM/driver, HiDPI/âm thanh Windows, soak/crash/mất điện dài hạn và toàn bộ tương tác nâng cao. Proxy live đã chặn YouTube/Bilibili ở kiểm chứng P02; draft network chưa phải runtime đã áp dụng.

Bản phát triển hiện có đường chạy thật cho các workflow chính. Các tùy chọn nâng cao còn phải code/kiểm chứng được liệt kê tại [đối chiếu triển khai](IMPLEMENTATION_COVERAGE.md), giữ nguyên trong [master plan](IMPLEMENTATION_PLAN.md). Không đánh dấu toàn bộ phase/95 nhóm đã nghiệm thu.
