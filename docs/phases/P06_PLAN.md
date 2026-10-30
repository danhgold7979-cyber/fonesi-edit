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
