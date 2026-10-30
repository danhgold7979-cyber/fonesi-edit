# P05 — Kế hoạch thực thi bản làm lại

Revision: rebuild-2026-10-30. Các kết quả bên dưới phần lịch sử thuộc code cũ; không chuyển PASS sang bản mới.

## Điều kiện bắt đầu và kết thúc

- Đọc master, PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC, TECHNICAL_DESIGN và REBUILD_REVIEW trước khi thực hiện.
- Mỗi đầu việc cần input hợp lệ, output đọc lại được, test lỗi và kiểm tra không mất dữ liệu nguồn.
- Có thể triển khai phần độc lập trong khi gate live/Windows/GPU bị chặn; không nhận công nghệ phụ thuộc là đã kiểm chứng.
- Sau mỗi task: ghi commit, file thay đổi, lệnh test, version/toolchain, PASS/FAIL/NOT_RUN và giới hạn. Chỉ nghiệm thu khi toàn bộ tiêu chí bắt buộc đạt.
- Không sử dụng phần trăm dòng code. Tiến độ nghiệm thu = số task đạt / tổng task của phase.

## Danh mục 10 đầu việc

### P05-01

**Phạm vi:** registry/capabilities, nhiều URL, bài/kênh/playlist, ID chuẩn và loại trùng.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SRC-01 (PR 3.2): URL cùng nguồn chuẩn hóa đúng ID, không coi bài là kênh

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P05-02

**Phạm vi:** phân trang/checkpoint, ảnh/video/Reels/Shorts/album khi nguồn hỗ trợ, lọc ngày/thời lượng/số lượng/chất lượng.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SRC-03 (PR 3.2–3.3): Quét ngắt không bị báo toàn kênh xong
- SRC-04 (PR 3): Loại tải đúng checkbox, thứ tự bài nhiều ảnh đúng
- SRC-05 (PR 3.2): Dữ liệu biên được lọc đúng, tùy chọn nguồn thiếu được báo
- SRC-10 (PR 3.2): Nội dung mới được thêm và phần không có ghi đúng

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P05-03

**Phạm vi:** cây nội dung, chọn mục, tổng chưa biết/quét ngắt, cancel và tiếp tục khi hỗ trợ.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SRC-03 (PR 3.2–3.3): Quét ngắt không bị báo toàn kênh xong

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P05-04

**Phạm vi:** downloader/tệp tạm/validation, tốc độ/retry/rate limit/auth; không log cookie/token.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SRC-06 (PR 3.2): Lỗi auth chờ đúng nguồn, retry giới hạn, không log bí mật
- SRC-08 (PR 3.3): Tệp dở/hỏng không thành công, nguồn giữ nguyên

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P05-05

**Phạm vi:** folder/kênh/album Unicode có ID, video/images/subtitles/metadata, thiếu đĩa/quyền ghi/tên dài/xung đột.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SRC-07 (PR 3.3): Hai kênh trùng tên không nhập chung hoặc ghi đè

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P05-06

**Phạm vi:** chống trùng theo ID/chất lượng/tệp hợp lệ; bổ sung sub riêng, tải lại tệp lỗi, đồng bộ lần hai và kênh đổi tên.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SRC-09 (PR 3.3): Quét lại không tải dư; thiếu sub chỉ lấy sub khi phù hợp
- SRC-10 (PR 3.2): Nội dung mới được thêm và phần không có ghi đúng

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P05-07

**Phạm vi:** kiểm chứng nguồn/loại media/auth, lưu ngày/phiên bản/evidence. Thiếu quyền ghi blocker, không dùng mock để báo hỗ trợ.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SRC-02 (PR 3.1): Mỗi loại nguồn có trạng thái/evidence theo bảng nền tảng

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P05-08

**Phạm vi:** profile manager mở Chrome thật vào đúng user-data-dir/nền tảng, tạo/đặt tên/gán nhiều nền tảng, tách nick cùng nền tảng, xử lý khóa/bận mà không phá profile.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUTH-02 (SB 3): Profile A lưu nhiều phiên website, đóng/mở vẫn đúng khi còn hợp lệ
- AUTH-03 (SB 3): Facebook A/B không chia cookie, không nhầm nhiều cửa sổ là nhiều profile
- AUTH-04 (SB 4.1): Mở đúng hồ sơ, không xóa lock/chiếm profile cá nhân

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P05-09

**Phạm vi:** session broker theo cơ chế đạt P02, đăng nhập/kiểm tra/đăng nhập lại cho mọi nền tảng, nhận diện nick, trạng thái website khác khả năng connector dùng phiên và quyền nguồn.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUTH-01 (PR 13; SB 4.2): Đủ nền tảng đã nêu, capability/auth chưa thử được ghi đúng
- AUTH-05 (SB 4.2): Mật khẩu/OTP không lưu trong app, kiểm tra sau login thật
- AUTH-06 (SB 6): Bộ tải dùng phiên thật; không tắt mã hóa hoặc coi web login là đã đạt
- AUTH-08 (SB 4.3–5): Dừng đúng job, relogin rồi resume, không tải trùng/đổi public ngầm

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P05-10

**Phạm vi:** chọn account theo nguồn/job, nhớ mặc định, refresh cùng danh tính/resume, mismatch chặn đúng job; không silent fallback sang công khai hoặc tự xoay nick; auth cache không lẫn tài khoản.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUTH-07 (SB 5): Nick chọn được giữ, project/job không chứa cookie/token
- AUTH-09 (SB 5): Job cũ không chạy bằng nick mới; rate limit không tự coi hết hạn

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

## Hồ sơ thực hiện trước rebuild (chỉ tham khảo)

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
