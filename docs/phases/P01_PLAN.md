# P01 — Kế hoạch thực thi bản làm lại

Revision: rebuild-2026-10-30. Các kết quả bên dưới phần lịch sử thuộc code cũ; không chuyển PASS sang bản mới.

## Điều kiện bắt đầu và kết thúc

- Đọc master, PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC, TECHNICAL_DESIGN và REBUILD_REVIEW trước khi thực hiện.
- Mỗi đầu việc cần input hợp lệ, output đọc lại được, test lỗi và kiểm tra không mất dữ liệu nguồn.
- Có thể triển khai phần độc lập trong khi gate live/Windows/GPU bị chặn; không nhận công nghệ phụ thuộc là đã kiểm chứng.
- Sau mỗi task: ghi commit, file thay đổi, lệnh test, version/toolchain, PASS/FAIL/NOT_RUN và giới hạn. Chỉ nghiệm thu khi toàn bộ tiêu chí bắt buộc đạt.
- Không sử dụng phần trăm dòng code. Tiến độ nghiệm thu = số task đạt / tổng task của phase.

## Danh mục 8 đầu việc

### P01-01

**Phạm vi:** đánh mã yêu cầu, tách phạm vi hiện tại/tích hợp sau; ghi mặc định và trường hợp lỗi.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P01-02

**Phạm vi:** wireframe bảy khu vực, media/preview/inspector/timeline, Cơ bản/Nâng cao, trạng thái rỗng/đang làm/lỗi.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- ED-01 (PR 2; ED 1): Mọi nhóm có nơi thao tác, đơn vị và lý do disabled

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P01-03

**Phạm vi:** luồng thêm kênh, folder, âm thanh, chỉnh sub/logo, ma trận và hàng đợi; đếm thao tác đường dùng thường xuyên.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P01-04

**Phạm vi:** preset từng nhóm, một clip/nhiều clip/cả lô; thuộc tính khóa và ghi đè tay.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- BAT-02 (PR 5; ED 10): Không thay job đang chạy hoặc sửa tay đã khóa
- OPS-07 (ED 8): Đủ công cụ phụ, version/thiếu tài nguyên được báo

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P01-05

**Phạm vi:** định nghĩa W/K, ưu tiên khớp âm thanh, thiếu sub, tên logic, trùng tên và tệp đã xử lý.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P01-06

**Phạm vi:** corpus media, nguồn thử, quyền truy cập/cấu hình cần, tiêu chí và phép đo preview/export.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P01-07

**Phạm vi:** hợp đồng project/preset/job, module và sổ quyết định cần thực nghiệm ở P02.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P01-08

**Phạm vi:** wireframe Cài đặt công cụ/hồ sơ Chrome/tài khoản mọi nền tảng, luồng scan→download/install→check, login→verify→use; readiness ba trục.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- TOL-01 (PR 13; SB 2.1): Hiện đường dẫn/version/vai trò/trạng thái, không chỉ tìm tên exe
- AUTH-01 (PR 13; SB 4.2): Đủ nền tảng đã nêu, capability/auth chưa thử được ghi đúng

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

## Hồ sơ thực hiện trước rebuild (chỉ tham khảo)

# P01 — Kế hoạch chi tiết trước triển khai

Đã đối chiếu `docs/IMPLEMENTATION_PLAN.md` v1.1, toàn bộ PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC và bảng truy vết. Đây là phase thiết kế; chưa xây scheduler/editor hoàn chỉnh trước cổng P02.

## Phạm vi và thứ tự

1. P01-01: dùng 95 mã yêu cầu hiện có làm baseline; ghi phạm vi hiện tại/tích hợp sau, quy tắc mặc định và xử lý lỗi.
2. P01-02/P01-03: thiết kế bảy màn hình, luồng thường dùng và trạng thái rỗng/loading/lỗi; wireframe editor có đối tượng kéo thả và phạm vi áp dụng luôn thấy.
3. P01-04/P01-05: chốt preset/override/lock, W/K/history, duration planner, missing sub/output collision.
4. P01-06: lập corpus tổng hợp có nhãn, nguồn công khai cần thử, phép đo và prerequisites chưa có.
5. P01-07: hợp đồng project/preset/job và quy tắc dữ liệu chung, đối chiếu TECHNICAL_DESIGN.
6. P01-08: luồng scan/install tool và browser/account binding có readiness ba trục.

## Bàn giao và kiểm tra

- `P01_DESIGN.md`: màn hình, wireframe, field/state, luồng, rules và data contracts.
- `SOURCE_CORPUS.md`: đầu vào, cách tạo/đối chiếu, phân biệt synthetic/live, Windows/credential prerequisites.
- `P01_RESULTS.md`: từng task với hiện vật và kết luận thiết kế.
- Kiểm tra toàn bộ link, ID đầu việc, 95 yêu cầu có vị trí/phase/tiêu chí; không đánh dấu khả năng nguồn đã hoạt động.

## Cổng hoàn tất

Tất cả task thiết kế có hiện vật, các màn hình không có quy tắc mâu thuẫn. Chưa cần API key hoặc Windows để hoàn tất thiết kế; những thứ đó là cổng thực nghiệm P02, được ghi nguyên trạng.
