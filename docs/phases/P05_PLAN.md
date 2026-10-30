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

- [x] Gallery-dl khởi tạo session trước khi gán CookieJar; fixture localhost yêu cầu cookie và xác nhận header được gửi.
- [x] URL/source và payload sai loại hoặc giới hạn bị chặn có thông báo dễ hiểu, không âm thầm hạ cấp.
- [x] Download localhost ảnh/video và scan-selected gallery image lặp lại không ghi đè output tốt; kiểm tra path/bytes/mtime.
- [x] CI Linux/Windows source + binary proof không hồi quy; xem P05_RESULTS.
- [x] Những cổng live phụ thuộc nguồn, trình duyệt, tài khoản và môi trường vẫn ghi PENDING/BLOCKED; P05 chưa đóng.

## 5. Cổng còn mở trong P05

Quét nhiều trang nguyên kênh và checkpoint, cây chọn từng bài, ảnh album/carousel theo đúng thứ tự, nâng chất lượng/bổ sung sub chỉ thiếu, account mismatch/OTP khi session live, giới hạn rate/region, mạng/Chrome Windows và bảng capability cho 10 nền tảng đều chưa đủ bằng chứng. Các yêu cầu này phải được giữ nguyên trong traceability và các vòng triển khai tiếp, không tự chuyển sang “giai đoạn sau”. Không tạo public release khi cổng bắt buộc chưa qua.

## 6. Vòng triển khai kế tiếp — Scan → chọn mục → download từng mục (28/10/2026)

Đối chiếu thêm `IMPLEMENTATION_PLAN.md` P05-01/P05-02/P05-03/P05-04/P05-10, `PRODUCT_REQUIREMENTS.md` mục 3.2/3.3, `REQUIREMENTS_TRACEABILITY.md` SRC-01/SRC-03/SRC-04/SRC-06, `ui/pages.py`, `downloads.py`, `storage.py` và test integration. Hiện UI chỉ hiển thị JSON sau scan; người dùng không có cây checkbox/chọn từng mục, dù đặc tả yêu cầu.

**Phạm vi có thể kiểm thử hoàn toàn offline:**

1. Kết quả scan từ yt-dlp/gallery-dl trả thêm `url` có thể download khi metadata thực cung cấp URL HTTP(S) hợp lệ. Không ghi URL chứa userinfo, token, signed query hoặc fragment vào job result; item không thể chọn được phải có lý do cụ thể. Đừng tự suy luận quét toàn bộ nguồn hoặc tự chế ID/URL.
2. DownloadsPage có bảng/cây mục đã quét, checkbox chọn tất cả/bỏ chọn, thể hiện trạng thái scan incomplete/unknown; không tự tích mục không có URL hợp lệ, không đánh dấu scan complete nếu provider không biết tổng.
3. Nút `Tải mục đã chọn` tạo *mỗi mục một job download*, kế thừa snapshot `folder/engine/media/account_ref/expected_identity` của chính scan job; không lấy tài khoản mặc định mới hoặc URL không thuộc nền tảng source khi đã gắn account. Chặn tài khoản/URL sai trước khi enqueue; không mặc định chuyển sang public hoặc lặng lẽ tải toàn kênh.
4. Không thay đổi cơ chế no-overwrite, validation, cancel/retry; job/queue hiện có thực thi tải từng URL và output được kiểm tra. Test Qt offscreen + HTTP localhost cho scan hình/video → chọn một mục → enqueue/download → file thật, và trường hợp signed URL bị từ chối.
5. Chạy `check_plan`, full tests và frozen proof CI Linux/Windows; ghi P05_RESULTS và coverage/status sau khi có bằng chứng. Khi scan nhiều trang/live account chưa thử, vẫn ghi PENDING.

**Cổng lát cắt:** đường chọn từ scan dùng được, mỗi item chọn có một job với snapshot/account đúng; không lưu URL có query nhạy cảm từ kết quả scan; không khẳng định quét hết kênh. **Cổng mở:** multi-page checkpoint/continuation theo provider, sắp xếp và lọc nâng cao, toàn bộ nền tảng live, album tập hợp và Chrome bridge thực.

### P05-03 — Kiểm soát danh sách scan lớn trong UI

Bảng Qt ban đầu tải mọi mục cùng lúc, gây nguy cơ treo UI khi scan hàng nghìn/hàng chục nghìn mục. Triển khai phân trang hiển thị (ví dụ 200 mục/trang), lưu các chỉ số đã tick trên nhiều trang trong phiên làm việc, báo số mục đã chọn và trang; chuyển lần quét không lẫn selection. Cần test dữ liệu synthetic trên nhiều trang, chọn chéo trang và tạo đủ job đúng snapshot, không bỏ mục ngoài màn hình hoặc nạp hàng nghìn item vào cây cùng lúc. Phân trang hiển thị **không phải** checkpoint quét ở provider; checkpoint live vẫn còn mở.

### Bằng chứng nghiệm thu lát cắt

- [x] UI có cây checkbox scan và hiển thị trạng thái chưa rõ tổng, không gắn complete giả.
- [x] Download item riêng bảo toàn account/output snapshot, giữ adapter video/gallery đúng nguồn, job có idempotence.
- [x] Các item URL ký hoặc trùng bị khóa, không lưu signed-query URL từ metadata scan làm link tải lại.
- [x] UI paginated 200 item/trang, lưu lựa chọn across pages trong phiên và test Qt offscreen.
- [x] `gallery-dl` scan → selected download file PNG thực với server localhost; hồi quy config và đóng gói qua CI cả Linux/Windows.
- [ ] Quét nhiều trang từ provider thật/checkpoint resume, thử 10 nền tảng/đăng nhập Chrome live, chất lượng và chính sách tải toàn kênh, nghiệm thu PC Windows người dùng.

**CI:** [run 40641870092](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40641870092) — 162 Linux passed; 161 Windows passed + 1 skip có chủ đích. Lát cắt P05-03 đạt trong phạm vi synthetic/localhost, **phase P05 chưa đóng**.
