# P05-06 — Nâng chất lượng video đã tải mà không ghi đè

**Ngày:** 29/10/2026  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Nhánh:** `develop/fonesi-full`  
**Trạng thái:** kế hoạch trước sửa code; chưa nghiệm thu.

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

- [ ] Đã thực hiện nâng cấp từ video nguồn đã probe, kiểm tra snapshot account và chọn target lớn hơn.
- [ ] Không sửa video/sub gốc, biến thể riêng/no-overwrite, reject output không thực sự nâng chất lượng.
- [ ] Tests unit/Qt + full source CI và frozen packaged proof Linux/Windows PASS.
- [ ] Cổng live và full P05 còn OPEN, bằng chứng và giới hạn được ghi nhận riêng.

**Lưu ý:** chiều cao là trần chọn định dạng, không phải bảo đảm source có đủ 720p/1080p/4K. Chỉ so chiều cao thực của video nguồn/đích qua FFprobe sau khi tải. Không tự xoá file lỗi sau khi fail vì có thể là file người dùng.
