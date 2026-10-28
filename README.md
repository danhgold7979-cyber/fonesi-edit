# Fonesi Edit — clean rebuild

Bản desktop Python/PySide6/SQLite/FFmpeg đang viết lại từ đặc tả trên nhánh `rebuild/spec-first-2026-10-28`. **Đây là checkpoint phát triển, chưa hoàn tất 95 nhóm yêu cầu hoặc nghiệm thu Windows/live nguồn.** Main và lịch sử được giữ nguyên.

## Theo dõi
- [Trạng thái hiện tại: code / test / còn thiếu](docs/CURRENT_STATUS.md)
- [Master plan + 12 phase plans](docs/REBUILD_MASTER_PLAN.md)
- [95 nhóm yêu cầu / evidence / phần còn mở](docs/rebuild/coverage.json)
- [Screenshot editor thật](docs/rebuild/evidence/editor-checkpoint.png)

## Chạy từ source
Cần Python 3.12, uv, FFmpeg/ffprobe. Bản người dùng cuối sẽ được đóng gói, chưa yêu cầu này là nghiệm thu cuối.

```sh
uv sync --locked
uv run fonesi-edit
uv run fonesi-edit --diagnose
uv run python scripts/check_plan.py
QT_QPA_PLATFORM=offscreen uv run pytest -q
```

Nếu môi trường không cho ghi cache mặc định, đặt `UV_CACHE_DIR`/`XDG_CACHE_HOME` vào thư mục được phép. Dữ liệu người dùng tách khỏi thư mục cài; có thể đặt `FONESI_DATA_DIR` để kiểm thử cô lập.

## Checkpoint hiện tại
8 tab mở được; local media/project/subtitle/editor/batch/matrix/queue/settings đã nối đường chạy nền. CPU xuất MP4 với text/logo/mask/sub/keyframes, kiểm tra probe+decode+duration+tracks rồi mới ghi thành công; không ghi đè nguồn. Tải video/ảnh localhost đã kiểm chứng, không đồng nghĩa live mạng xã hội hoặc gallery-dl packaged đã đạt.

**59 tests pass** và frozen Linux proof4 job thật đã qua; playable proxy/audio/waveform đã có. Windows CI mới được chuẩn bị; advanced UI, history/DAG completeness và máy mục tiêu còn đang làm. Xem trạng thái sống thay vì coi số test là đủ sản phẩm.

Không commit browser profiles/cookie/API key/download media. Dịch chỉ gọi endpoint được người dùng cấu hình và cho phép; Chrome thật/user-data-dir riêng, auth chưa xác minh bị chặn, không tự đổi sang public. AI voice/ASR/OCR/tracking ngoài bản đầu.
