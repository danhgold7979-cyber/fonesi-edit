# P05-06 — Tải phụ đề riêng cho mục video đã quét

**Ngày:** 29/10/2026  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Nhánh tích hợp:** `develop/fonesi-full`  
**Trạng thái:** kế hoạch trước khi code; chưa nghiệm thu.

## 1. Truy vết

Đối chiếu `AGENTS.md`, `README.md`, `IMPLEMENTATION_PLAN.md` P05-04/05/06, `PRODUCT_REQUIREMENTS.md` mục 3.2–3.3, `REQUIREMENTS_TRACEABILITY.md` SRC-06/07/08/09/10, `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, `P05_PLAN.md`/`P05_RESULTS.md` cùng `downloads.py`, `ui/pages.py`, `automation.py`, `storage.py`, `subtitles.py` và các test liên quan.

Tải thông thường dùng yt-dlp với `writesubtitles` nhưng sau đó bắt buộc phải có video. `P05-06` đòi hỏi bổ sung sub riêng mà không tải lại/tác động tệp video hiện có. Phạm vi này không đồng nghĩa nâng chất lượng, phát hiện video theo toàn kênh hoặc kiểm chứng provider live.

## 2. Phạm vi thực hiện

1. Thêm chế độ payload `download_mode='subtitles_only'` **chỉ** cho `kind=download`, `engine=video`, `media=videos`, `limit=1`. Chặn engine gallery/auto, ảnh, scan, cờ đầu vào không hợp lệ **trước khi tạo thư mục hoặc liên lạc mạng**. Chế độ download thông thường vẫn giữ mặc định cũ.
2. Tạo helper từ **selected scan job succeeded**, giữ nguyên URL hợp lệ, output folder, account_ref, expected_identity, languages, giới hạn và snapshot, loại bỏ `workflow` (không edit/render tự động), thumbnail và cursor. Không đổi account/engine ngầm. Chặn mục không hợp lệ trước khi enqueue.
3. Trong yt-dlp, bật `skip_download=True`, `writesubtitles=True`, `writeautomaticsub=True`, không lấy video/thumbnail/infojson. Chỉ chấp nhận sidecar do thông tin `requested_subtitles` cung cấp và nằm trong cây `subtitles/` thuộc output root; kiểm tra suffix hỗ trợ, file thường không symlink, kích thước hữu hạn/hợp lý và đọc được cue hợp lệ. Nếu không có phụ đề phù hợp thì báo không có artifact đã kiểm chứng, không báo succeeded giả.
4. Giữ `overwrites=False` và kiểm tra lần tải lại không thay đổi bytes/mtime của phụ đề hợp lệ; không xóa/sửa file người dùng hoặc video. Từ chối sidecar ngoài output root, path giả, tệp rỗng/hỏng; không đưa signed subtitle URL/cookie/token vào SQLite result/error.
5. Nút `Tải bổ sung phụ đề` cho những mục video **đã đánh dấu** trong cây scan; job idempotent và độc lập với chế độ download video. Với scan có adapter gallery/ảnh, thông báo không hỗ trợ rõ ràng; không tạo job một phần nếu selection hỗn hợp không hợp lệ.
6. Test thuần với fake yt-dlp cho option `skip_download`, output path validation, tái chạy/no-overwrite, không phụ đề/hỏng/ngoài root, các kiểu payload sai. Integration Qt kiểm tra selection/account snapshot, URL, workflow removal, chống double-click và mode idempotence. Không sử dụng tài khoản/mạng social thực.

## 3. Kiểm thử và nghiệm thu

- Chạy `uv run python scripts/check_plan.py`, toàn bộ `uv run pytest -q`, build desktop/native host và frozen proof CI Linux/Windows.
- Chỉ ghi PASS sau kết quả thật của CI trên **code SHA**. Ghi rõ skip/failure và retry; không vô hiệu hóa assertion.
- Cập nhật `P05_RESULTS.md`, `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md` và `PHASE_EXECUTION_LEDGER.md` theo bằng chứng.

## 4. Tiêu chí đóng lát cắt

- [ ] Sub-only chỉ chạy đúng engine/video, giữ account/nguồn/thư mục và không kích hoạt workflow edit.
- [ ] Không tải lại video, không ghi đè phụ đề hợp lệ, không báo success với file thiếu/hỏng/ngoài root.
- [ ] Regression unit/Qt và CI Linux/Windows source + packaged proof PASS.
- [ ] P05 vẫn OPEN cho sync toàn kênh, nâng chất lượng, gallery album, provider/Chrome/live auth và Windows máy thật.

**Giới hạn:** yt-dlp có thể không cung cấp subtitle/auto-sub cho từng nguồn; phải ghi lý do khi không có. Kiểm chứng ngôn ngữ/chất lượng trên nguồn thật và quản trị file đã hỏng là công việc riêng, không giả định đã giải quyết trong lát cắt này.
