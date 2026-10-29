# P05 — Kế hoạch quét tiếp video theo khoảng giới hạn

**Ngày:** 29/10/2026  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Nhánh:** `develop/fonesi-full`  
**Trạng thái:** kế hoạch trước code, chưa nghiệm thu.

## 1. Căn cứ

Đã đối chiếu `AGENTS.md`, `README.md`, master `IMPLEMENTATION_PLAN.md` (P05-01, P05-02, P05-03), `PRODUCT_REQUIREMENTS.md` mục 3.2–3.3, `REQUIREMENTS_TRACEABILITY.md` (SRC-03/04/05/06/10), `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, `P05_PLAN/RESULTS` và code `downloads.py`, `ui/pages.py`, `storage.py`, `automation.py`, `worker.py` cùng regression tests.

UI hiện đã phân trang **hiển thị** 200 hàng, có checkbox, lọc metadata và sort ngày. yt-dlp scan có `playlistend=limit` nhưng không có thông tin chỉ số để quét tiếp. Một lần scan hiện không chứng minh đủ toàn kênh; library có thể không hỗ trợ offset ở mọi extractor.

## 2. Phạm vi code độc lập

1. Chỉ cho phép tiếp tục với **yt-dlp playlist** đã trả kết quả `scan_window` có chứng cứ; không giả lập provider checkpoint, không hỗ trợ nối tiếp gallery-dl/mixed-auto trong lát cắt này. Scan đầu phải có giới hạn 1–200 item, cumulative snapshot tối đa 2000 item.
2. Tạo metadata `scan_window` chứa version/start/limit/next_start theo khoảng index 1-based; `playliststart` và `playlistend` là khoảng chỉ số tuyệt đối của yt-dlp. Không khẳng định `complete=True` nếu extractor không có bằng chứng hết kênh.
3. Lệnh quét tiếp sinh payload **chỉ từ job scan succeeded** cùng snapshot URL/engine/media/folder/limit/account/identity, loại trường runtime `_tools`. Worker xác minh lại cha và mọi trường bất biến trước khi khởi tạo download folder/truyền cookie; từ chối offset giả, nguồn/identity thay đổi, limit sai hoặc parent không hợp lệ.
4. Tạo **job scan mới**, giữ parent bất biến và nối prefix items theo original index; duplicate item URL giữa các khoảng sẽ bị gắn không thể chọn (không tạo tải trùng). Không tiếp tục nếu trang mới không có mục mới hoặc đạt giới hạn tổng.
5. UI có nút quét tiếp, giữ bộ lọc và sao chép checkbox cũ theo index khi prefix thực tế giống hệt. Dùng `submit_once` theo parent + next_start để chống bấm đôi/reopen. Scan cũ, download job và lịch sử không bị sửa.
6. Khi phần thư viện không hỗ trợ offset hoặc trả kết quả thiếu/không chắc, báo giới hạn và vẫn để `complete=None/False`; không tự suy ra đã tải/quét toàn kênh. Không có mạng ngoài trong unit test.

## 3. Test và cổng an toàn

- Test yt-dlp fake extractor kiểm tra khoảng [1..N], [N+1..2N], append/trùng, stop; metadata/URL an toàn; không sử dụng mạng ngoài.
- Test snapshot tamper: thay URL, account identity, engine, limit, scan_start, parent không hợp lệ phải bị chặn **trước IO nguồn**; scan không có giới hạn/scan gallery không được giả tiếp tục.
- Qt integration: nút scan tiếp submit idempotent, preserve selection/filter/pagination sau khi job mới succeeded, tải đúng URL và account snapshot. Test backward compatibility các scan cũ thiếu metadata.
- CI `scripts/check_plan.py`, `pytest -q`, PyInstaller native host và frozen proof Linux/Windows. Không hạ assertion khi CI lỗi.

## 4. Chưa nghiệm thu theo yêu cầu sản phẩm

- [ ] Code + tests xác thực đúng tính chất bounded window và bất biến snapshot.
- [ ] Test UI chọn/lọc/quét tiếp không làm thay index/account/URL.
- [ ] Linux/Windows CI source + build + packaged proof PASS trên đúng SHA.
- [ ] Provider-side pagination/checkpoint thực tế và live 10 nền tảng/Chrome/Windows máy người dùng vẫn ghi OPEN, không đóng P05 tổng thể.

Khoảng index này chỉ dùng tính năng `playliststart/playlistend` của yt-dlp và **không** xác nhận checkpoint nguyên kênh của provider. Các extractor có thể đổi thứ tự, bỏ mục hoặc không hỗ trợ offset; cần live corpus/thiết bị riêng để xác nhận.
