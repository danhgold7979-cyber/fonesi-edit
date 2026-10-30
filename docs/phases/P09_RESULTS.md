# P09 — Ma trận triển khai

Đã có scan/hash/natural sort/tên logic, generator lazy seed/W/K/history/locks, capacity và timeout không nới điều kiện, row composition/audio fit và reservation+job transaction. Worker commit history chỉ sau artifact hợp lệ, fail/cancel/retry có trạng thái riêng. Test tập nhỏ đầy đủ, W/K/locks và render row thật qua scheduler đã được thêm; kết quả tích hợp ghi ở P11.

Vòng tích hợp thêm W/K recheck nguyên tử theo lịch sử mới nhất, snapshot tool, tên output thứ tự hàng; preview đổi tên C/G + sidecar, no-overwrite hai bước, journal/undo/rollback/recovery và relink project hiện tại. Test giữ bytes/timestamp, xung đột, hủy, crash giữa move và save journal, vòng tên. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).

## Tạo lại hàng, thống kê góc và chia thời lượng — 28/10/2026

Tất cả thay đổi đã code trong **một ứng dụng** trên nhánh `develop/fonesi-full`:

- **MAT-04/MAT-05 — Tạo lại riêng một hàng:** thêm `regenerate_row` chỉ thay một hàng, giữ các ô đã khóa và mọi hàng khác, không tái sử dụng tổ hợp lịch sử/đã lên kế hoạch. Kiểm tra lại cả W/K của **những hàng sau**; seed ổn định trên cùng snapshot. Với không gian nhỏ (≤10.000) duyệt ứng viên đầy đủ; với không gian lớn, thử tối đa trong time/attempt budget và báo “chưa tìm được” thay vì “vô nghiệm”. Cancel không chỉnh dữ liệu.
- **UI ma trận:** nút `Tạo lại hàng chọn` chạy background (không chặn Qt), recheck lịch sử đặt chỗ, thay đổi scenes/rows/locks/seed/W/K trước khi nhận kết quả. Worker trả kết quả cũ sẽ bị bỏ, không ghi đè thao tác của người dùng. Cải thiện sửa ô chỉ cho scene columns, khóa không dính cột tên/formula; sửa góc revalidate lịch sử W/K và cập nhật công thức C1G… cùng lần.
- **Thống kê sử dụng góc:** nút `Thống kê góc` đếm từng góc trong ma trận đang lập, bao gồm góc chưa sử dụng = 0. Đây là số **được lên kế hoạch**, không coi là video đã xuất thành công.
- **MAT-06/P09-05 — Thời lượng cảnh:** chế độ proportional/equal hiện có được bổ sung `weights` (trọng số số dương mỗi cảnh) và `manual` (số giây mỗi cảnh), cùng speed min/max tại tab ma trận. `row_composition`, `enqueue_rows` và solver dùng một snapshot/thời lượng. Nếu có audio chính, tổng thời lượng clip trừ overlap phải khớp duration audio, nếu không báo không khả thi; không có audio thì tổng thời lượng thủ công quyết định target. Bảo vệ min/max speed/trim, không tự bỏ cảnh hoặc chuyển sang freeze/loop.
- **Test:** deterministic/exhaustive small space, khóa ô/W/K ảnh hưởng về sau, lịch sử bị đổi khi thread chạy, cancel và input bất biến, Qt điều khiển thao tác/đổi góc/số góc, weights và manual vector, FFprobe và **render FFmpeg output thật** từ clip có duration đã chỉ định. Old production jobs and source media unaffected.

**Bằng chứng CI:** [run 40645339209](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40645339209) **PASS** — Linux **180 tests**, Windows **179 tests + 1 skipped** (fixture POSIX-only), kèm build production/native-host và frozen proof video/ảnh localhost, render batch/ma trận và Qt frame decode trên hai hệ.

**Cổng P09 vẫn mở:** reorder cảnh bằng drag ở UI, tìm nghiệm/tối ưu & cân bằng frequency trên tập lớn với mọi W/K, stress/history lớn, Windows/exFAT/drive thực, mở project và thử vòng rename sau mất điện. Tập test runner không thay thế nghiệm thu máy Windows người dùng; không đánh dấu toàn phase hoàn tất.

## P09-01 — Đổi thứ tự cảnh trong UI, giữ history/W/K/lock (30/10/2026)

[Plan](P09_SCENE_REORDER_PLAN.md) được commit trước code. MatrixPage có danh sách cảnh kéo/thả, nút Cảnh lên/xuống, hiển thị folder nguồn và số góc, lưu thứ tự theo folder gốc và chỉ khôi phục khi tập scene khớp hoàn toàn. Không tự đổi tên/xóa source. Backend hoán vị các cột hàng, lịch sử đã căn đúng cảnh, ô khóa, các vector weights/manual seconds; `Angle.scene` chỉ là chỉ số logic mới, `hash/index/path` giữ nguyên. Worker sinh ma trận/preview cũ không thể ghi đè nếu thao tác mới hơn hoặc thiết lập thay đổi; hàng đang chọn được khôi phục sau đổi thứ tự.

Lịch sử SQLite cũ chỉ có content hash, nên khi cần căn theo thứ tự mới, app chỉ gán hash vào một cảnh nếu xác định duy nhất. Content giống nhau ở nhiều scene hoặc nguồn lịch sử biến mất → lỗi rõ ràng, không suy đoán. `enqueue_rows` đối chiếu history ngay trong transaction trước khi tạo job, chặn cả tổ hợp đã đặt chỗ trước đó nhưng lưu với thứ tự cũ; không có partial jobs. Qt và backend tests có FFmpeg render thật, kiểm tra W/K/lock/path/hash, cấu hình hỏng, worker concurrent và nguồn không thay đổi.

**[CI https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41016748802](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41016748802) SUCCESS exact code/test SHA `3ff0e31b28d6c12caeaaf4ae60d7f79eb28818b8`: Linux 701 PASS; Windows 700 PASS + 1 intentional POSIX skip; plan check, benchmark 128 synthetic MP4, desktop/native host và frozen packaged proof hai OS PASS.** Chỉ nghiệm thu lát cắt scene reorder trên synthetic/runner CI. P09-01 còn cổng scene-level exclusion/lock nâng cao và người dùng Windows kéo thả thực tế; P09/P11/P12 còn solver corpus lớn, live Chrome/provider, GPU, filesystem/SQLite issue #6, installer, power loss. Không merge `main`.

## P09-01/P09-03 — Chọn/loại cảnh và góc, khóa G cho toàn cảnh (30/10/2026)

[Plan](P09_SCENE_SELECTION_LOCK_PLAN.md) → [code/test 7d1f928a798b8cb50997a25e8f8947dfc0f83999](https://github.com/danhgold7979-cyber/fonesi-edit/commit/7d1f928a798b8cb50997a25e8f8947dfc0f83999) → [CI 41021003352](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41021003352) **SUCCESS đúng SHA**: Linux **728 PASS**, Windows **727 PASS + 1 skip fixture POSIX**; plan check, benchmark FFprobe 128 video synthetic, app/native-host và frozen packaged render/Batch/Matrix/localhost/UI proof trên hai runner.

Qt MatrixPage quét nguồn C/G nền, checkbox loại scene/góc tường minh, pin/unpin một góc G cho toàn bộ hàng *mới*; giữ path/hash/G gốc, chỉ đánh số C theo lựa chọn. Pin được áp cho mọi row; nếu W>0 với nhiều hàng hoặc capacity không đủ sẽ báo lỗi chứ không tự nới ràng buộc. Sau đổi thứ tự cảnh, cột khóa tiếp tục theo đúng scene. Đổi checkbox làm vô hiệu kế hoạch cũ và kết quả worker tới muộn, không tác động media nguồn/job đã enqueue. Chỉ khôi phục lựa chọn đã lưu khi nguồn có manifest đầy đủ trùng khớp; không cho đổi tên thực khi nguồn bị lọc.

Lịch sử SQLite chỉ lưu hash theo thứ tự: dự án đầy đủ trước đó được chiếu bảo thủ về tập cảnh được chọn để ngăn reuse; bản cũ có *ít/khác* cảnh nhưng hash đều xác định được không bị coi là tổ hợp mới đủ cảnh, còn hash không rõ/trùng nhiều scene bị từ chối. Transaction enqueue kiểm lại history/W/K, không ghi đè database/source. Có unit/Qt/SQLite và FFmpeg render synthetic thật, kiểm tra khôi phục lựa chọn, xử lý stale và bảo toàn byte nguồn.

**Mở:** stress ma trận lớn và tối ưu W/K, Windows người dùng/HiDPI/installer, hash trùng giữa các scene, NTFS/exFAT/power-loss, [SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) unknown root cause, Chrome/live provider, GPU và nghiệm thu 95 nhóm. Chưa đóng toàn P09/P11/P12, không merge main.


## P09-03 / P09-06 — Solver benchmark and cancel-safe Matrix queue (30/10/2026)

- Generator validates typed N/W/K/seed and finite positive budget; logical `scripts/benchmark_matrix.py` measures elapsed/tracemalloc on 14 scenes × 6 angles (capacity 6^14), validates 100 unique W=1/K=2 rows without full Cartesian media expansion, and explicitly reports incomplete rather than claiming UNSAT. No physical 100k-corpus proof.
- `enqueue_rows` supports cooperative Task cancel and progress, with all-new SQLite jobs/history rolled back if revoked before commit. SQL upsert now uses valid `excluded.job_id`; failed reservation retry explicitly tests new job ID. MatrixPage cancels obsolete pre-publication work on C/G filter/order, cell/locks, seed/W/K/output/audio/editor options, and global cancel; duplicate clicks blocked; successful prior-snapshot commits reported truthfully. Backend synthetic-media/SQLite and real Qt offscreen regressions included.
- [CI 41025266091](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41025266091) SUCCESS, exact code/test SHA `7d2d74a7173184d1e752e508ff83aa8971f72321`: 764 Linux PASS; 763 Windows PASS + one intentional POSIX skip; 128-source synthetic FFprobe benchmark, production desktop/native-host builds, frozen packaged render/Batch/Matrix/localhost/Qt proof PASS both runners. Windows development artifact 197,335,201 bytes, expires 2026-11-06. Synthetic/localhost evidence only; NOT physical Windows/HiDPI/installer, full 100k-real-media throughput/solver optimality, NTFS/exFAT/power loss, SQLite issue #6 root cause, live Chrome/provider or GPU acceptance.
- Full P09/P11 and all release gates remain OPEN; do not merge main.


## P09-03 / MAT-04 — Bounded per-scene balance on large spaces (30/10/2026)

Implemented bounded candidate competition for spaces above 10,000 combinations: default pool 8 (1–64 validated), seeded tie-break, projected per-scene squared-use score, and frequency identity keyed by (scene index, content hash). No Cartesian materialization; time budget and cooperative cancel remain active. Per-scene/per-angle counts are included in benchmark JSON. CLI supports --output and --require-complete; CI stores .local/matrix-benchmark.json. Duplicate content hashes in different scene folders retain separate frequency counters.

Regression compares pool 1 vs pool 8, checks same-seed behavior, per-row locks/W/K, cancellation, strict parameter types, shared hashes across scenes and a 10-billion-combination logical space with 2,000 outputs. Test and CI benchmark use a 45-second cap because the first 10-second run correctly returned incomplete under tracemalloc; no timeout is treated as UNSAT.

[CI 41030170331](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41030170331) SUCCESS on exact code/test SHA [4e759cdbaaa738b3df60a577e0a4cd6091cf6ed5](https://github.com/danhgold7979-cyber/fonesi-edit/commit/4e759cdbaaa738b3df60a577e0a4cd6091cf6ed5). Linux: 781 PASS; 10^10 theoretical combinations, 2,000 generated, 9.302552 s, Python tracemalloc peak 1,379,048 bytes, max per-scene spread 5. Windows: 780 PASS + 1 intentional POSIX-only skip; 10^10 theoretical combinations, 2,000 generated, 19.737411 s, Python tracemalloc peak 1,379,264 bytes, max per-scene spread 5. Both passed 128-source FFprobe synthetic Batch benchmark, phase-reference check, production desktop/native-host build and frozen packaged render/Batch/Matrix/localhost-download/Qt proof. Artifacts: Linux evidence 390,000 bytes (expires 2026-11-02); Windows evidence 322,514 bytes (expires 2026-11-02); Windows development build 197,343,856 bytes (expires 2026-11-06). Logical-ID and synthetic/localhost CI proof only; not 10 billion real videos, 100k real-media corpus, physical Windows, GPU or live provider acceptance.

**Still OPEN:** 100k real-media corpus and global solver optimality; Windows physical GUI/HiDPI/installer; NTFS/exFAT/power-loss; SQLite issue #6 root cause; live Chrome/providers/GPU. This closes only the bounded logical balance slice, not all P09 or release acceptance.
