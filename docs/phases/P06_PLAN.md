# P06 — Kế hoạch thực thi bản làm lại

Revision: rebuild-2026-10-30. Các kết quả bên dưới phần lịch sử thuộc code cũ; không chuyển PASS sang bản mới.

## Điều kiện bắt đầu và kết thúc

- Đọc master, PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC, TECHNICAL_DESIGN và REBUILD_REVIEW trước khi thực hiện.
- Mỗi đầu việc cần input hợp lệ, output đọc lại được, test lỗi và kiểm tra không mất dữ liệu nguồn.
- Có thể triển khai phần độc lập trong khi gate live/Windows/GPU bị chặn; không nhận công nghệ phụ thuộc là đã kiểm chứng.
- Sau mỗi task: ghi commit, file thay đổi, lệnh test, version/toolchain, PASS/FAIL/NOT_RUN và giới hạn. Chỉ nghiệm thu khi toàn bộ tiêu chí bắt buộc đạt.
- Không sử dụng phần trăm dòng code. Tiến độ nghiệm thu = số task đạt / tổng task của phase.

## Danh mục 6 đầu việc

### P06-01

**Phạm vi:** SRT/VTT/ASS về cue chung, báo style chưa hỗ trợ; ghép bằng ID/ngôn ngữ/tên, báo mơ hồ.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SUB-02 (PR 4.2): ID/tên mơ hồ không bị ghép nhầm; báo style thiếu

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. UTF8 SRT parser/exporter, diagnostics. Còn mở: VTT/ASS/style/sidecar matching và ambiguity. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P06-02

**Phạm vi:** nguồn/đích/ưu tiên, sub người đăng/tự động, chính sách thiếu sub và khác ngôn ngữ.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SUB-01 (PR 4.1): Chọn đúng ngôn ngữ và gắn nhãn sub tự động
- SUB-08 (PR 4.2): Báo đúng, không mất chữ, không chặn cả lô
- ED-10 (ED 3.3): Đổi ngôn ngữ không giả font/provider có hỗ trợ

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P06-03

**Phạm vi:** adapter dịch thật, thuật ngữ/xưng hô/tên riêng/ngữ cảnh, cache, chi phí/rate limit/retry.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SUB-03 (PR 4.1): Provider thật, ánh xạ cue đầy đủ, mẫu được đọc soát
- SUB-04 (PR 4.1): Cache hit không gọi mới, giới hạn hoạt động, timeout không rõ được ghi

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P06-04

**Phạm vi:** gốc/dịch song song, sửa/tìm/thay/tách/gộp, dịch lại câu chọn, khóa câu đã sửa, lịch sử.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SUB-05 (PR 4): Sửa đúng cue, undo/save/open giữ nội dung
- SUB-06 (PR 4.1): Auto không đổi câu khóa; chỉ câu chọn được dịch lại

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. SRT table edit/manual lock/undo-redo/literal find-replace/explicit split-merge. Còn mở: Bilingual/translation integration/persistent history. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P06-05

**Phạm vi:** thời gian qua timeline/ô số, offset, kiểm tra chồng/tràn, time map sau trim/speed.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SUB-07 (PR 4.2): Cue theo đúng nguồn sau mọi phép biến đổi thời gian
- SUB-08 (PR 4.2): Báo đúng, không mất chữ, không chặn cả lô

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Rational cue map/trim/speed/overlap diagnostics. Còn mở: Timeline/offset UI và đầy đủ source/render integration. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P06-06

**Phạm vi:** đơn/song ngữ, style cơ bản liên kết P07, xuất SRT/ASS và burn-in qua pipeline chung.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SUB-09 (PR 4.3; ED 3.3): Hai khối đúng thứ tự và có bật/tắt riêng
- SUB-10 (PR 4.2): Tệp sub mở được, video phát ngoài vẫn thấy sub

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Xuất SRT mới không overwrite. Còn mở: ASS/bilingual/style/burn-in pipeline. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

## Hồ sơ thực hiện trước rebuild (chỉ tham khảo)

# P06 — Kế hoạch chi tiết: xuất phụ đề an toàn và cache dịch không gọi phí lại

**Ngày kiểm tra:** 28/10/2026. **Nhánh duy nhất:** `develop/fonesi-full`. **Trạng thái:** lập kế hoạch trước khi sửa P06.

## 1. Rà soát master plan

Đã đối chiếu `docs/IMPLEMENTATION_PLAN.md` P06-01…P06-06 với `docs/PRODUCT_REQUIREMENTS.md`, `docs/EDITOR_SPEC.md`, traceability, `docs/IMPLEMENTATION_COVERAGE.md`, P06_RESULTS và code `src/fonesi_edit/subtitles.py`/test. P06 đã có SRT/VTT/ASS, cue locks, dịch có provider adapters/cache/quota/glossary, song ngữ và time map. Nguồn provider live, chất lượng/chi phí chưa nghiệm thu.

## 2. Lát cắt sửa lỗi và hoàn thiện

- **P06-04/P06-06 (bảo toàn sửa tay):** hàm `write_captions(overwrite=True)` đang mở trực tiếp đường dẫn bằng `wb`, có nguy cơ làm mất file sub cũ nếu ghi lỗi. Chuyển sang tệp tạm cùng filesystem + flush/fsync + `os.replace` sau khi serialization hoàn chỉnh; `overwrite=False` vẫn sử dụng tạo độc quyền, không ghi đè.
- **P06-03 (cache/quota):** cache hash hiện dùng toàn bộ `config`, khiến đổi `daily_limit` (chỉ là ràng buộc chi phí) tạo key khác và dịch lại nội dung y hệt. Tách các trường giới hạn vận hành khỏi fingerprint dịch nhưng giữ provider, endpoint, glossary và các tham số chất lượng/ngữ cảnh.
- Không thay đổi thời gian cue, source_text, khóa sửa tay hay cơ chế quota reserve trước request. Không phát sinh request trả phí trong test.
- Thêm regression test cho tệp sub gốc khi serialization/replace lỗi, không để temp bị kẹt, và reuse cache sau khi chỉ đổi hạn mức ngày.

## 3. Thứ tự và điều kiện nghiệm thu

1. Viết thay đổi hẹp cho `subtitles.py`, bổ sung test với synthetic captions/transport.
2. Chạy `uv run python scripts/check_plan.py`, `uv run pytest -q` và packaged proof qua CI Linux/Windows.
3. Chỉ khi đạt mới ghi P06_RESULTS, CURRENT_STATUS và coverage theo evidence; không đánh dấu full phase khi live provider chưa được kiểm chứng.
4. Giữ `main` không đổi, không commit API key, cookie, media tải, dữ liệu thực hoặc runtime artifacts.

**Điều kiện:** không mất file thủ công, cache hit không gọi dịch lần nữa khi chỉ đổi `daily_limit`, toàn bộ source/packaged regression pass, lỗi rõ ràng khi provider thiếu cấu hình.

## 4. Cổng còn mở

Chất lượng/chi phí dịch Trung–Việt live, dịch ngữ cảnh/xưng hô, danh sách ngôn ngữ thực của provider, UI undo toàn lịch sử cue/timeline kéo từng cue và test corpus lớn vẫn phải giữ trong `IMPLEMENTATION_COVERAGE.md`. Các phần này không tự coi hoàn tất hoặc loại khỏi yêu cầu chỉ vì test offline đã đạt.
