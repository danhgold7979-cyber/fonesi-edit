# P10 — Kế hoạch chi tiết: độ an toàn automation và điều tiết tài nguyên

**Ngày:** 28/10/2026. **Nhánh:** `develop/fonesi-full`. **Trạng thái:** plan trước khi code.

## 1. Đối chiếu master

Đã đối chiếu `docs/IMPLEMENTATION_PLAN.md` P10-01…P10-07, PRODUCT_REQUIREMENTS, P10_RESULTS, IMPLEMENTATION_COVERAGE, `automation.py`, `jobs.py` và `tests/test_automation_dependencies.py`.

Hiện có watcher, lịch chạy persist, workflow tải→dịch→render, admission CPU/RAM/đĩa, công cụ versioned install và rollback. Cổng Windows Task Scheduler, máy người dùng, Chrome/driver/GPU, action sau hoàn tất, cache cleanup theo quota còn mở.

## 2. Lát cắt code độc lập

- **P10-04/P10-05:** `recommended_parallel` đang mặc nhiên dùng cấu hình `max` cho mọi profile không phải `quiet`/`balanced`. Từ chối profile sai, không ngầm tăng số worker khi cài đặt hỏng.
- **P10-04:** `update_gpu` phải đặt GPU về `unknown` khi nvidia-smi bị xóa/không chạy được; không hiển thị dữ liệu GPU thành công đã lỗi thời như trạng thái hiện tại.
- **P10-06:** vòng Automation currently ghi `str(exc)` trực tiếp vào `self.errors`; dùng bộ lọc bí mật đã kiểm chứng ở worker trước khi hiển thị/log.
- Test profile không hợp lệ, telemetry GPU bị lỗi/mất công cụ và thông báo lỗi chứa ký tự giả token/URL, giữ thông tin chẩn đoán không nhạy cảm.
- Chạy suite và packaged Linux/Windows, không kết luận GPU thật hay scheduler khi app đóng đã đạt.

## 3. Nghiệm thu

- [ ] Không tự suy diễn profile tài nguyên sai thành `max`.
- [ ] Khi mất telemetry, GPU trạng thái unknown chứ không giữ snapshot cũ.
- [ ] Lỗi automation không rò cookie/token/URL query vào giao diện hoặc log.
- [ ] Đủ test CI và không làm hồi quy các workflow hiện có.

**Ngoài phạm vi:** live Chrome/auth/installer, Windows Task Scheduler do người dùng bật, GPU/VRAM thực, soak dài hạn và mọi cổng release chưa có evidence. Giữ nguyên trong master plan.
