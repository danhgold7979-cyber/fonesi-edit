# P12 — Kế hoạch thực thi bản làm lại

Revision: rebuild-2026-10-30. Các kết quả bên dưới phần lịch sử thuộc code cũ; không chuyển PASS sang bản mới.

## Điều kiện bắt đầu và kết thúc

- Đọc master, PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC, TECHNICAL_DESIGN và REBUILD_REVIEW trước khi thực hiện.
- Mỗi đầu việc cần input hợp lệ, output đọc lại được, test lỗi và kiểm tra không mất dữ liệu nguồn.
- Có thể triển khai phần độc lập trong khi gate live/Windows/GPU bị chặn; không nhận công nghệ phụ thuộc là đã kiểm chứng.
- Sau mỗi task: ghi commit, file thay đổi, lệnh test, version/toolchain, PASS/FAIL/NOT_RUN và giới hạn. Chỉ nghiệm thu khi toàn bộ tiêu chí bắt buộc đạt.
- Không sử dụng phần trăm dòng code. Tiến độ nghiệm thu = số task đạt / tổng task của phase.

## Danh mục 7 đầu việc

### P12-01

**Phạm vi:** đóng gói tái lập theo P02, FFmpeg/thư viện/font hợp lệ; chạy không cần bộ dev/admin nếu không thiết yếu.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- WIN-01 (PR 11): App đóng gói chạy trên Windows mục tiêu

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P12-02

**Phạm vi:** phân biệt install/user data, Unicode/quyền ghi/antivirus thực tế, CPU-only và GPU phù hợp khi có.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- WIN-02 (PR 11): Workflow từ binary thật, không chỉ từ source

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P12-03

**Phạm vi:** chạy workflow từ bản đóng gói, save/open/crash/restart/migration/cấu hình thiếu, mở kết quả bằng player ngoài.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- WIN-02 (PR 11): Workflow từ binary thật, không chỉ từ source

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P12-04

**Phạm vi:** hướng dẫn Việt, preset mẫu, cấu hình dịch/phiên nguồn an toàn, phím tắt/chẩn đoán/báo lỗi.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- WIN-03 (PR 11): Người dùng chạy quy trình theo tài liệu, giới hạn rõ

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P12-05

**Phạm vi:** cập nhật tool/adapter có version/xác minh/tương thích/rollback, backup trước đổi schema.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- WIN-04 (Kế hoạch): Cập nhật lỗi khôi phục được, project backup trước migration

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P12-06

**Phạm vi:** manifest, capabilities, máy thật, release notes/giới hạn, lưu bản phục hồi.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- WIN-03 (PR 11): Người dùng chạy quy trình theo tài liệu, giới hạn rõ

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P12-07

**Phạm vi:** Windows mới thiếu dependency/Chrome: từ Cài đặt tải-cài-kiểm tra, mở Chrome thật/login, dùng phiên tải mẫu; tool ngoại không bị sửa, offline vẫn dùng media cục bộ, giới hạn auth được ghi đúng.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- TOL-07 (SB 2.2, 3): Google Chrome thật, không WebView/Chromium giả thay thế
- TOL-08 (SB 2.2): Chỉ thành phần cần được yêu cầu, driver không tự thay, API không tự tải model

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

## Hồ sơ thực hiện trước rebuild (chỉ tham khảo)

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
