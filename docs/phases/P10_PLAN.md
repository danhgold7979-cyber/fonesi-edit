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

## 4. Vòng P10-04/05 — Dọn cache theo hạn mức, bảo vệ file đang dùng

Rà master P10-04/P10-05, `REQUIREMENTS_TRACEABILITY.md` AUTO-04…AUTO-06, `PRODUCT_REQUIREMENTS.md` phần tài nguyên và `IMPLEMENTATION_COVERAGE.md`. Proxy local P04 được lưu tại `<app-data>/cache/proxies`. Hiện chưa có giới hạn dung lượng hoặc cơ chế dọn dẹp.

1. Lập chính sách FIFO/LRU đơn giản theo `mtime_ns` cho **file proxy hoàn chỉnh** trong đúng thư mục cache app, giới hạn bytes từ Settings (mặc định 4 GiB); không theo symlink, không quét subdirectories, không dọn media nguồn, output render, browser profile hay cache tool installer.
2. Dùng danh sách `protected` bảo vệ source QMediaPlayer đang phát. Nếu tổng protected > quota, ghi `over_budget` thay vì xóa file đang dùng; không xóa `.fonesi-proxy-*.` chưa publish.
3. UI Settings có `Giới hạn cache proxy (MiB)` và nút dọn bằng background; app định kỳ trigger khi rảnh và không có proxy/thumbnail đang tạo. Không thực hiện quét thư mục trên UI thread.
4. Test tmp cache (file cũ/mới, protected file, suffix khác, symlink, root symlink, quota quá nhỏ, idempotence), Settings/store, callback và lỗi quyền nếu có. CI Linux/Windows full suite, frozen proof. Ghi P10_RESULTS, coverage/status chỉ với evidence.
5. Chưa bao gồm quota cache downloader/translation, eviction đa máy hoặc Windows ACL/fault injection thật; giữ các cổng này mở.


### Kết quả lát cắt cache quota P10-04/05 (28/10/2026)

- [x] Eviction trong đúng cache proxy app, chỉ filename hash, không theo symlink/partial/foreign media.
- [x] Dọn old-first theo quota; active playback protected, báo quá quota nếu cần.
- [x] Settings persistent quota và manual/periodic background task, không khóa UI.
- [x] Full Linux/Windows CI + packaged proof [40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) PASS.
- [ ] GPU/VRAM thật, Task Scheduler, cache downloader/tool, Windows soak/installer/ACL còn mở.
