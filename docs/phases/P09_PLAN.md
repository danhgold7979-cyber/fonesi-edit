# P09 — Kế hoạch chi tiết: lịch sử ma trận và khóa cảnh/góc

**Ngày rà soát:** 28/10/2026. **Nhánh:** `develop/fonesi-full`. **Trạng thái:** plan trước khi code.

## 1. Đối chiếu master và triển khai

Đã đọc `docs/IMPLEMENTATION_PLAN.md` P09-01…P09-06, yêu cầu ma trận ở PRODUCT_REQUIREMENTS, `docs/REQUIREMENTS_TRACEABILITY.md`, P09_RESULTS và source `matrix.py`, `tests/test_matrix.py`. Ma trận có generator lazy W/K, seed, history, lock ô, transaction reservation, validation output, journal đổi tên/rollback. Còn yêu cầu UI regenerate row/weights, cân bằng tập lớn, scale/corpus và kiểm chứng Windows/exFAT thực tế.

## 2. Lát cắt P09-02/P09-03/P09-04

- Khi history chứa cùng một tổ hợp nhiều lần, capacity hiện đếm từng bản ghi lịch sử thay vì số tổ hợp **duy nhất**, có thể báo hết khả năng trong khi vẫn còn tổ hợp hợp lệ.
- Lock row/scene ngoài phạm vi hoặc khóa không thuộc cảnh hiện tại hiện có thể rơi vào IndexError hoặc bị bỏ qua nếu key nhập chuỗi. Chuẩn hóa/kiểm tra lock theo row/scene, báo ValueError rõ ràng trước khi sinh.
- Không nới W/K, không thay thế khóa không hợp lệ bằng lựa chọn ngẫu nhiên. Giữ hạt giống, thứ tự lịch sử và xác nhận kết quả.
- Thêm test history trùng, lock index âm/vượt, chuỗi chỉ số hợp lệ, và không thay input/history.
- Chạy check_plan, test source, proof binary Linux/Windows; chỉ cập nhật trạng thái theo evidence thực.

## 3. Cổng ngoài phạm vi lát cắt

Chứng minh solver constraints với corpus lớn, GUI regenerate từng hàng/khóa mọi kiểu, cân bằng tần suất toàn cục, thiết lập trọng số thời lượng từ UI, multi-worker Windows/exFAT/rename và xử lý mất điện vẫn mở. Không coi offline fixture là nghiệm thu đủ 95 nhóm.

## 4. Vòng P09-04 — Tạo lại một hàng mà không phá ràng buộc (28/10/2026)

Đã rà lại master `IMPLEMENTATION_PLAN.md` P09-02/03/04/06, yêu cầu MAT-04/MAT-05 trong `REQUIREMENTS_TRACEABILITY.md`, đặc tả ma trận ở `PRODUCT_REQUIREMENTS.md`, P09_RESULTS và mã `matrix.py`/`ui/pages.py`/`tests/test_matrix.py`. Hiện đã sửa/khóa ô, preview, CSV nhưng chưa có thao tác tạo lại đúng **một hàng**.

1. Thêm hàm thuần `regenerate_row` trả ứng viên mới cho hàng chỉ định, giữ nguyên các hàng khác và các ô bị khóa. Không tái sử dụng tổ hợp lịch sử, kể cả chính hàng cũ; không nới W/K hoặc thay góc khóa.
2. Rà **toàn bộ ma trận** trong thứ tự hiện hành với history, gồm các hàng *sau* vị trí vừa tạo lại vì W/K liên quan đến tiền nhiệm. Cảnh báo lỗi nếu input ban đầu không hợp lệ; giữ nguyên rows khi không có lời giải.
3. Với tập nhỏ duyệt toàn bộ không gian cho các góc không khóa trong ngân sách, xác nhận không có nghiệm nếu hết tất cả; với tập lớn thử ứng viên bounded, phân biệt chưa tìm đủ trong budget với bất khả thi đã chứng minh. Seed tái lập được cho cùng snapshot; cancel không sửa dữ liệu.
4. MatrixPage thêm nút `Tạo lại hàng chọn`, bắt kết quả qua background worker để không treo UI; giữ nguyên khóa các ô, lựa chọn UI và kiểm tra snapshot trước khi apply để tránh worker ghi đè thao tác diễn ra đồng thời. Tham chiếu history mới nhất khi chạy và không tạo job/render cho tới khi người dùng bấm Render.
5. Unit test: W/K/history/unique các hàng trước-sau, khóa cột, tất cả ô khóa, seed deterministic, input immutability/cancel, tập lớn timeout; Qt integration test click regenerate và kiểm tra các hàng khác/lock vẫn nguyên. Không dùng nguồn live hoặc tài khoản thật.
6. Chạy source tests, check_plan, frozen build proof trên CI Linux/Windows, cập nhật P09_RESULTS/CURRENT_STATUS/COVERAGE khi có bằng chứng.

**Cổng giữ mở:** cân bằng lượt sử dụng toàn cục, weights/nhập tay UI, solver tập lớn chứng minh tối ưu, UX multi-row/drag scene và nghiệm thu máy Windows người dùng. Không đánh dấu toàn P09 là hoàn tất.

### P09-04 — Thống kê tần suất sau tạo/sửa hàng

Cùng lát cắt bổ sung bảng thống kê góc từ **những hàng hiện có**: tất cả góc hợp lệ theo từng cảnh, số lần sử dụng (kể cả góc 0 lần), không cộng một job chưa render thành lượt thành công lịch sử. UI có nút xem tóm tắt không làm thay đổi ma trận. Test định lượng với số góc khác nhau giữa các cảnh; giữ `hash` làm ID thay vì tự suy ra theo filename.

### P09-04 — Sửa một ô phải đồng bộ công thức và khóa chỉ áp dụng cho góc

Kiểm tra trực tiếp trong MatrixModel: thay G ở một ô hiện chỉ phát `dataChanged` cho ô đó nên cột công thức C1G1+… có thể hiển thị cũ; thao tác Khóa có thể gắn cờ vào cột video/công thức vốn không phải góc. Sửa để chỉ scene columns (1…N) có thể edit/lock, phát tín hiệu cập nhật ô + công thức; nếu sửa vi phạm W/K/history thì rollback nguyên giá trị và không phát tín hiệu thành công. Test Qt với bảng synthetic và history.

### P09-05 — Trọng số thời lượng theo từng cảnh trong UI

Master `P09-05`/MAT-06 yêu cầu chia đều, tỷ lệ, trọng số hoặc nhập tay. Backend `fit_duration` đã giải trọng số chuẩn, nhưng MatrixPage chỉ có 2 lựa chọn tỷ lệ/đều; `row_composition` chưa chuyển `weights` tới solver. Thêm chế độ `weights` trong UI và ô nhập vector cho từng cảnh, kiểm tra số lượng bằng số scene, số hữu hạn và dương; chuyển snapshot vào `row_composition` và `enqueue_rows` để preview và render cùng duration solver. Test offline giá trị hợp lệ/thất bại với 2 cảnh và audio fixture thật, giữ tự động phân đoạn an toàn. Bản vòng sau đã bổ sung nhập tay thời lượng giây/cảnh; tiêu chí và bằng chứng ở phần 5.

### P09-05 — Nhập thời lượng giây cho từng cảnh

Bổ sung tùy chọn `manual` riêng với `weights`: vector thời lượng (giây) từng cảnh; tổng thời lượng clip trừ overlap chuyển cảnh phải bằng target audio nếu gắn audio, sai lệch báo rõ, không ép khớp. Nếu không gắn audio, tổng thời lượng từ các cảnh sẽ quyết định mục tiêu video. Chỉ hỗ trợ chính sách speed/trim đã có và kiểm tra giới hạn tốc độ/cắt; không ngầm bỏ cảnh hoặc đổi thành freeze/loop. Cung cấp ô nhập/kiểm tra số cảnh, giá trị hữu hạn dương, test solver (có/không audio), queue snapshot và UI. Đây là phần còn thiếu của P09-05/MAT-06.

### P09-05 — Giới hạn speed cùng UI với thời lượng từng cảnh

`MatrixPage` chưa có min/max speed riêng dù solver hỗ trợ. Thêm hai spinbox 0.1–10 giống BatchPage; preview/queued render truyền cùng snapshot giới hạn vào `row_composition` và `enqueue_rows`. Kiểm tra min lớn hơn max trong worker (solver báo không khả thi). Test UI và output theo giới hạn. Mặc định 0.5–2 giữ tương thích.

## 5. Kết quả nghiệm thu lát cắt P09-04/P09-05

- [x] Chỉ thay hàng chọn; lock, W/K của toàn bộ chuỗi và history giữ đúng; nếu không tìm được trong budget không tự nới.
- [x] UI background kiểm tra cảnh/hàng/lock/setting/history thay đổi trước khi apply; test Qt offscreen và cancel.
- [x] Chỉnh sửa ô cập nhật formula, chỉ cột góc được khóa; bảng thống kê góc có cả tần suất 0.
- [x] Weighted và manual seconds per-scene, min/max speed trong UI, preview/render dùng cùng duration solver và audio target; FFmpeg output thật được test.
- [x] [CI 40645339209](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40645339209) source tests Linux/Windows và frozen proof đều PASS.
- [ ] Nghiệm thu hoàn chỉnh toàn P09 cần scene reorder UI, corpus lớn, UX nhiều tổ hợp/locks nâng cao và Windows/exFAT/power-loss trên máy người dùng.

Đây là **lát cắt đạt theo kiểm thử offline/CI**, không phải đóng toàn bộ phase. Theo `IMPLEMENTATION_PLAN.md`, không thay checklist P09-[01…06] thành hoàn tất khi vẫn thiếu cổng trên.

## 6. P09-01 scene reorder — verified bounded slice (30/10/2026)

Detailed plan: [P09_SCENE_REORDER_PLAN.md](P09_SCENE_REORDER_PLAN.md). Implemented the in-app drag-reorder and Up/Down scene controls, immutable folder/hash/path identities, transpose of rows/locked cells/history/per-scene weight and manual-duration vectors, persisted folder-specific ordering and stale-async protection. The matrix render transaction now rejects cross-order duplicate reservations without rewriting legacy SQLite history. [CI 41016748802](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41016748802) **SUCCESS exact SHA `3ff0e31b28d6c12caeaaf4ae60d7f79eb28818b8`**: Linux 701 PASS; Windows 700 PASS + one intentional skip; production/frozen packaged proof both runners. Physical Windows dragging, advanced scene exclusion/locking and other P09/P11 acceptance gates remain OPEN; **do not mark the entire phase complete**.

## 7. P09-01/P09-03 — Explicit scene/angle selection and global G pin (30/10/2026)

[Detailed plan](P09_SCENE_SELECTION_LOCK_PLAN.md) was committed before code. MatrixPage now provides asynchronous C/G source scanning and explicit scene/angle checkboxes, one globally pinned G across all new rows, source identity and hash-preserving logical C numbering, same-manifest saved selection, and stale-worker guards. The seeded solver refuses conflicting W/whole-scene pins or inadequate capacity. Hash-only SQLite history projects full past rows onto selected subsets without allowing duplicate reuse; known shorter/different rows are not equivalent to longer compositions, unknown/cross-scene ambiguous hashes are blocked. Final enqueue rechecks this in its transaction. [CI 41021003352](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41021003352) **SUCCESS exact SHA `7d1f928a798b8cb50997a25e8f8947dfc0f83999`: 728 Linux / 727 Windows + 1 skip**, production/frozen packaged proof both runners. P09 is still OPEN for Windows user-device and large-corpus/other release gates.


## P09-03 / MAT-04 — Large-space balance selection (30/10/2026)
[Plan](P09_MATRIX_BALANCE_PLAN.md). Bounded candidate pool, scene-local frequency accounting and 10-billion-space logical benchmark implemented. [CI 41030170331](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41030170331) SUCCESS on exact code/test SHA [4e759cdbaaa738b3df60a577e0a4cd6091cf6ed5](https://github.com/danhgold7979-cyber/fonesi-edit/commit/4e759cdbaaa738b3df60a577e0a4cd6091cf6ed5). Linux: 781 PASS; 10^10 theoretical combinations, 2,000 generated, 9.302552 s, Python tracemalloc peak 1,379,048 bytes, max per-scene spread 5. Windows: 780 PASS + 1 intentional POSIX-only skip; 10^10 theoretical combinations, 2,000 generated, 19.737411 s, Python tracemalloc peak 1,379,264 bytes, max per-scene spread 5. Both passed 128-source FFprobe synthetic Batch benchmark, phase-reference check, production desktop/native-host build and frozen packaged render/Batch/Matrix/localhost-download/Qt proof. Artifacts: Linux evidence 390,000 bytes (expires 2026-11-02); Windows evidence 322,514 bytes (expires 2026-11-02); Windows development build 197,343,856 bytes (expires 2026-11-06). Logical-ID and synthetic/localhost CI proof only; not 10 billion real videos, 100k real-media corpus, physical Windows, GPU or live provider acceptance.
Full P09 remains open for real-media corpus, physical Windows and external gates.
