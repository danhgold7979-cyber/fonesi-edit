# P05-06 — Nâng chất lượng video đã tải mà không ghi đè

**Ngày:** 29/10/2026  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Nhánh:** `develop/fonesi-full`  
**Trạng thái:** lát cắt đã triển khai, có source/Qt regression và [CI 40849001694](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40849001694) PASS hai runner; P05 tổng thể vẫn OPEN.

## 1. Đối chiếu trước code

Đã đọc `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P05-04/05/06), `docs/PRODUCT_REQUIREMENTS.md` (3.2–3.3), `docs/REQUIREMENTS_TRACEABILITY.md` (SRC-05/08/09/10), `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, `docs/phases/P05_PLAN.md`/`P05_RESULTS.md` và code `downloads.py`, `ui/pages.py`, `storage.py`, `automation.py`, `prototypes/media.py`, `tests/test_downloads_sessions.py`, `tests/test_app_integration.py`.

Video đã tải thông thường nằm ở `platform/channel__id/videos/` với kết quả được probe qua FFprobe; `overwrites=False`. Đã có sub-only mode được kiểm chứng CI. Yêu cầu P05-06/SRC-09 đòi hỏi nâng chất lượng thành yêu cầu mới, không ghi đè video cũ, không tráo tài khoản và không báo nâng cấp nếu bản tải chỉ bằng/thấp hơn.

## 2. Lát cắt độc lập

1. Thêm `download_mode='quality_upgrade'` cho **một video yt-dlp** và `upgrade_from_job_id` tham chiếu job download **succeeded** của video nguồn. UI chỉ lấy baseline từ job đã có trong Store, không suy ra đã tải xong từ scan metadata; nếu thiếu job nguồn thì từ chối **cả nhóm** trước enqueue.
2. Snapshot URL, engine, media, folder, account_ref/expected_identity phải trùng baseline; `target_height` do người dùng chọn trong khoảng 144–4320 (pixel) và lớn hơn chiều cao nguồn đã được FFprobe xác nhận. Không hỗ trợ ảnh/gallery/auto, nguồn chưa tải, scan/playlist, `workflow`, thumbnail hoặc sub-only chung với quality upgrade.
3. Worker **xác minh lại** job nguồn, đường dẫn trong `platform/channel/videos`, loại video, ID nguồn, nội dung media có thể probe và target trước `cookie_jar`, `root.mkdir` hay IO mạng. Không dùng path do payload client tự cung cấp.
4. yt-dlp chọn định dạng video có chiều cao lớn hơn baseline và không vượt target; lưu vào `platform/channel/quality-upgrades/<target>p/videos/` (không sửa/cùng đường dẫn với video cũ). `overwrites=False`, tắt phụ đề/thumbnail/autoedit. FFprobe output thật; chỉ công nhận nếu chiều cao lớn hơn baseline, ID video trùng và path hợp lệ dưới thư mục biến thể; kết quả ghi requested/actual/baseline heights rõ ràng. Không hứa nhận đúng target khi nguồn không có định dạng đó.
5. Qt có nút nâng chất lượng từ video đã tải dùng giá trị `Chất lượng tối đa` trong form và các scan item checkbox. Enqueue idempotent theo scan+URL+baseline job ID+target, không đụng job media/sub-only; không tạo một phần khi group thiếu baseline.
6. Unit và Qt regression chống giả mạo URL/account/path/source job, target quá thấp/cao, chất lượng thực không cao hơn, path ngoại lai/symlink, no-overwrite video cũ và biến thể khi tải lặp. Test synthetic dùng FFmpeg/FFprobe thật với fixture ngắn; không gọi provider live.

## 3. Các bước và nghiệm thu

1. Commit kế hoạch trước khi thay code; triển khai helper và validation worker; thêm lựa chọn Qt; test phần thuần và Qt.
2. Chạy `uv run python scripts/check_plan.py`, `uv run pytest -q`, build desktop/native-host và frozen proof ở GitHub Actions Linux/Windows trên SHA code. Khi CI thất bại, đọc log sửa lỗi, không làm xanh giả bằng bỏ assertion.
3. Chỉ ghi nghiệm thu từng lát cắt sau khi CI thật PASS; cập nhật `P05_RESULTS.md`, `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`.
4. **Chưa đóng:** live availability/format/quality nguồn thật, quality nâng liên tiếp từ biến thể, chống file cũ hỏng, resync toàn kênh, provider checkpoint/album, Chrome/10 nền tảng/region, Windows máy người dùng, issue SQLite #6.

## 4. Checklist

- [x] Đã thực hiện nâng cấp từ video nguồn đã probe, kiểm tra snapshot account và chọn target lớn hơn.
- [x] Không sửa video/sub gốc, biến thể riêng/no-overwrite, reject output không thực sự nâng chất lượng.
- [x] Tests unit/Qt + full source CI và frozen packaged proof Linux/Windows PASS.
- [x] Cổng live và full P05 còn OPEN, bằng chứng và giới hạn được ghi nhận riêng.

**Lưu ý:** chiều cao là trần chọn định dạng, không phải bảo đảm source có đủ 720p/1080p/4K. Chỉ so chiều cao thực của video nguồn/đích qua FFprobe sau khi tải. Không tự xoá file lỗi sau khi fail vì có thể là file người dùng.

## 5. Kết quả lát cắt và giới hạn

- Code/Qt worker: `downloads.py`, `ui/pages.py`; test FFmpeg/FFprobe thực `tests/test_quality_upgrade.py` + `tests/test_app_integration.py`; regression loại trùng nguồn mặc định từ thư mục biến thể qua `batch.py`, `automation.py` + hai bộ test tương ứng. Code HEAD `0ca96d300f0c3cce323291e5ac1759daf766625d`.
- Chỉ dùng bản video nguồn từ job download thường đã thành công, cùng URL/folder/account_ref/expected_identity, nằm trong `platform/channel/videos/` và FFprobe decode được. Worker xác minh lại trước khi tạo folder hay lấy cookie, so sánh ID sau tải, yêu cầu `source_height < actual_height <= target_height`.
- Output được tách dưới `platform/channel/quality-upgrades/<target>p/videos/`, `overwrites=False` và không chạy workflow/sub/thumbnail. Kiểm tra video nguồn không đổi kích thước và mtime sau tải. Target là **độ cao tối đa**, không phải cam kết nguồn có đúng cấp đó. Video biến thể được loại khỏi Batch và watch quét đệ quy mặc định; có thể chọn chính thư mục biến thể nếu muốn dùng một cách rõ ràng.
- `CI 40849001694` **SUCCESS attempt 1 trên đúng SHA code**: Linux 510 PASS; Windows 509 PASS + 1 skip fixture POSIX có lý do; plan validator, desktop/native-host build, frozen packaged proof PASS trên cả hai hệ.
- Không tự đánh dấu đạt live provider bitrate/codec/4K, nâng tiếp từ một biến thể làm baseline, nhận diện/giải quyết tệp biến thể hỏng, đồng bộ kênh thực, 10 nền tảng, Chrome authenticated session, Windows máy người dùng, hay issue SQLite #6.
