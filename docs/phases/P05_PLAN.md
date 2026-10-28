# P05 — Kế hoạch hoàn thiện adapter tải và phiên đăng nhập

**Ngày kiểm tra:** 28/10/2026. **Nhánh:** `develop/fonesi-full`. **Trạng thái:** chuẩn bị lát cắt code P05, nghiệm thu live riêng.

## 1. Đối chiếu kế hoạch tổng thể

Đã đọc master `docs/IMPLEMENTATION_PLAN.md` (P05-01…P05-10), `docs/PRODUCT_REQUIREMENTS.md`, `docs/SETTINGS_AND_BROWSER_SPEC.md`, `docs/PLATFORM_SUPPORT_MATRIX.md`, traceability, P05_RESULTS và coverage. Đã đối chiếu mã `src/fonesi_edit/downloads.py`, `browser.py`, `ui/pages.py` và test `test_downloads_sessions.py`.

Ứng dụng đã có yt-dlp/gallery-dl trong worker, nhận diện URL, profile/binding Chrome và extension/nativemessaging opt-in. Chưa có bằng chứng live trên từng nền tảng, quét nguyên kênh hoặc phiên Chrome dùng được vào downloader trên máy Windows người dùng. Không được tự đánh dấu P05 hoàn tất toàn bộ.

## 2. Các lỗi/thiếu sót có thể khắc phục độc lập

- **P05-09/P05-10:** khi gallery-dl dùng session `CookieJar`, nhánh `_gallery` truy cập `instance.extractor.session.cookies` trước khi extractor được initialize. Theo lifecycle gallery-dl, session thường là None cho tới `initialize()`; gây lỗi trước khi thử nguồn.
- **P05-04/P05-05:** cần từ chối `engine`, `media` và `limit` không hợp lệ thay vì âm thầm chọn engine/video hoặc giới hạn âm.
- **P05-04:** bất kỳ warning từ nhánh thử hai engine phải được lọc khi trả về artifact/result, không để URL có query nhạy cảm lọt vào SQLite.
- **P05-07:** test authentication transport chỉ dùng localhost synthetic/cookie giả, **không coi là bằng chứng Chrome→connector live**.

## 3. Thứ tự code/check

1. Bổ sung bộ test cho CookieJar đã gán, bảo đảm extractor session được khởi tạo trước khi inject cookie; kiểm tra idempotence với fixture localhost.
2. Chặn tùy chọn engine/media/limit bất hợp lệ và test lỗi rõ ràng trước khi tạo folder/job.
3. Cập nhật đường session gallery-dl, giữ nguyên quyền nguồn, không lấy cookie từ Chrome DB hoặc bypass mã hóa DPAPI.
4. Không in/sao chép cookie/token trong diagnostics, log và lỗi trả về UI; giữ nguyên kiểm tra output decode/no-overwrite.
5. Chạy check_plan, full source suite và frozen packaged proof CI Linux/Windows.
6. Cập nhật P05_RESULTS, coverage và trạng thái theo bằng chứng, không đánh dấu 10 nền tảng đã hoạt động.

## 4. Điều kiện nghiệm thu lát cắt

- [ ] Gallery-dl khởi tạo session trước khi gán CookieJar; fixture kiểm tra không crash.
- [ ] URL/source và payload sai loại hoặc giới hạn bị chặn có thông báo dễ hiểu, không âm thầm hạ cấp.
- [ ] Download localhost ảnh/video vẫn qua hai lần không ghi đè output tốt.
- [ ] CI Linux/Windows source + binary proof không hồi quy.
- [ ] Những cổng live phụ thuộc nguồn, trình duyệt, tài khoản và môi trường vẫn ghi PENDING/BLOCKED.

## 5. Cổng còn mở trong P05

Quét nhiều trang nguyên kênh và checkpoint, cây chọn từng bài, ảnh album/carousel theo đúng thứ tự, nâng chất lượng/bổ sung sub chỉ thiếu, account mismatch/OTP khi session live, giới hạn rate/region, mạng/Chrome Windows và bảng capability cho 10 nền tảng đều chưa đủ bằng chứng. Các yêu cầu này phải được giữ nguyên trong traceability và các vòng triển khai tiếp, không tự chuyển sang “giai đoạn sau”. Không tạo public release khi cổng bắt buộc chưa qua.
