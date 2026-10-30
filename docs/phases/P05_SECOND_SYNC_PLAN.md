# P05-06 — Đồng bộ lần hai chỉ tải mục mới trong kết quả quét

**Ngày:** 29/10/2026  
**Repository/nhánh:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`  
**Trạng thái:** manual new-only and atomic follow-up verified on synthetic Linux/Windows CI; full P05 remains OPEN.

## 1. Căn cứ

Đã đối chiếu `AGENTS.md`, `README.md`, master `IMPLEMENTATION_PLAN.md` (P05-02/03/04/05/06), `PRODUCT_REQUIREMENTS.md` mục 3.2–3.3, `REQUIREMENTS_TRACEABILITY.md` (SRC-03/06/08/09/10), `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, kế hoạch/kết quả P05 hiện có, `storage.py`, `downloads.py`, `ui/pages.py`, `automation.py`, `prototypes/media.py` và các test liên quan.

Nút `Tải mục đã chọn` dùng `submit_once` theo ID scan, do đó quét lại cùng URL có thể tạo job media thứ hai dù tệp đã có. Hiện chống URL trùng trong một lần quét, chưa đối chiếu lịch sử job xuyên scan. Commit kế hoạch chained quality `e85574d` trên cùng nhánh là công việc độc lập; lát cắt này không sửa logic quality upgrade.

## 2. Phạm vi và giới hạn

1. Tra cứu SQLite `Store.download_jobs_for_urls` theo URL từ scan (tối đa 500, query parameterized), không giới hạn lịch sử 2.000 job mới nhất.
2. Helper `plan_new_only_sync` dựa trên `selected_download_payloads` để xác nhận scan succeeded, URL an toàn và snapshot. Chỉ so sánh job `download_mode=media` với **chính xác** URL/folder/engine/media/account_ref/expected_identity; không lẫn subtitle-only hay quality-upgrade. Nếu có job khác account/adapter trong cùng URL+folder thì báo xung đột chứ không dùng lẫn.
3. Job `succeeded` chỉ được bỏ qua khi media vẫn thực sự tồn tại trong `platform/channel/videos|images`, là file thường không symlink, decode được bằng FFprobe/QImageReader. Tệp thiếu/hỏng/ngoài root => chặn **toàn nhóm**, báo cần kiểm tra, không tự xóa/ghi đè. `pending/running/blocked` được ghi riêng là đang chờ; `failed/canceled` cần Queue → Retry, không coi là đã tải.
4. UI có nút **Đồng bộ mục mới (kết quả lọc)** dùng tất cả mục selectable đang khớp filter/search/sort ở mọi trang, không thay checkbox, tối đa 500 mục. Lập kế hoạch/kiểm tra account trước khi enqueue; key idempotent theo URL/folder/engine/media/account/identity **không dùng ID scan**. Ghi số mới/đã hợp lệ/đang chờ mà không suy ra đã quét hết kênh.
5. Regression Store >2.000 job, snapshot/account conflict, output thiếu/hỏng/symlink/ngoài root, media video/ảnh thực (FFprobe/QImageReader), UI lọc/phân trang/checkbox, song song và duplicate across scan, không tự enqueue một phần khi có blocker.

## 3. Test và nghiệm thu

- Commit plan trước khi sửa source. Code riêng `src/fonesi_edit/sync.py` + `storage.py` và kết nối Qt, test unit/Qt.
- Chạy `scripts/check_plan.py`, toàn bộ `pytest -q`, build desktop/native-host và frozen packaged proof trên CI Linux/Windows **đúng SHA**. Không bỏ test để làm xanh giả.
- Sau CI có bằng chứng, cập nhật `P05_RESULTS.md`, `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, `USER_GUIDE.md`.

## 4. Checklist

- [x] Sync lại cùng URL không tạo thêm media job nếu file cũ hợp lệ.
- [x] Missing/corrupt, job failed/canceled và xung đột account/adapter không bỏ qua hoặc enqueue âm thầm; không sửa file nguồn.
- [x] Qt filter/pagination/checkbox/cap 500 và SQLite history sâu có regression.
- [x] Source/Qt, build, frozen CI Linux/Windows PASS trên code SHA.
- [ ] Provider live/full-channel, URL alias, Chrome/account thực, vùng/quyền, Windows máy người dùng, sửa tệp hỏng và issue SQLite #6 vẫn mở.

**Giới hạn:** Dùng URL HTTP(S) an toàn **chính xác**, không suy đoán provider ID/alias, không khẳng định toàn kênh hoàn thành. Khi lịch sử không chắc hoặc có tệp hỏng, yêu cầu xử lý rõ ràng. Sub-only và quality upgrade giữ các luồng riêng.

## Verified manual repeat-scan evidence (29/10/2026)

- `sync.py`, SQLite complete URL history and Qt filtered new-only action compare exact URL/account/engine/folder, use FFprobe/QImageReader for valid files, reject corrupt/foreign/failed outputs and preserve hidden checkbox selection. Synthetic tests cover >2,000 old jobs and real media.
- Atomic follow-up [c0405c4](https://github.com/danhgold7979-cyber/fonesi-edit/commit/c0405c45bb8646874bf6b1a2046a6a907b5fdc9e) uses one transaction for up to 500 new jobs, injected-second-INSERT rollback, immutable key/snapshot checks, safe duplicate scan rows and symlink-chain rejection. [CI 40855868306](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40855868306) **SUCCESS attempt 1** on the code/test SHA: **537 Linux /536 Windows +1 intentional skip**, desktop/native-host build and packaged proof both OS PASS.
- This is **not** evidence of provider-native pagination, actual full-channel completion, Chrome or real Windows user-device acceptance.
