# P12 — Kế hoạch chi tiết: CI đóng gói Windows có thể tái lập

**Ngày rà soát:** 28/10/2026. **Nhánh tích hợp:** `develop/fonesi-full`. **Trạng thái:** plan trước khi sửa pipeline.

## 1. Kiểm tra master và mã

Đã đối chiếu `docs/IMPLEMENTATION_PLAN.md` P12-01…P12-07, P11_RESULTS, P12_RESULTS, `docs/LOCAL_VERIFICATION.md`, `.github/workflows/phase2.yml`, `scripts/build_desktop.py` và `scripts/verify_packaged.py`. CI Linux/Windows từng đạt full source/frozen proof; chưa nghiệm thu app updater, hệ Windows của người dùng, Chrome login, GPU và audio vật lý.

## 2. Lát cắt độ tin cậy pipeline

GitHub Actions run `40638812868` thất bại ở bước Chocolatey prerequisite vì Chocolatey API trả **504 Gateway Timeout** trước khi chạy code/test; đây là lỗi mạng của dependency provisioning, không phải bằng chứng lỗi ứng dụng. Lệnh hiện chạy một lần rồi throw.

1. Thêm số lần retry hữu hạn cho Chocolatey khi cài FFmpeg phiên bản **7.1.1**, log số lần thử và giữ nguyên pin phiên bản.
2. Sau số lần thử, nếu vẫn không cài được thì fail chính xác thay vì bỏ kiểm tra hoặc dựa vào FFmpeg hệ thống chưa xác minh.
3. Giữ nguyên test source, check_plan, build app/native host và proof binary; không tạo public release nếu thiếu nghiệm thu.
4. Chạy Actions trên Linux/Windows, phân biệt lỗi provisioning và lỗi code/test.

## 3. Tiêu chí/cổng còn mở

- [ ] Bước cài FFmpeg có retry hữu hạn và không bỏ qua lỗi sau cùng.
- [ ] CI giữ bản development cho Windows khi toàn bộ test/proof đạt.
- [ ] Version FFmpeg, lock SHA, source hash, media validation và native host không thay.
- [ ] Chrome/session, driver/GPU, quyền cài đặt, HiDPI/audio, antivirus và người dùng chạy trên PC thật vẫn PENDING; CI runner không thay thế.
