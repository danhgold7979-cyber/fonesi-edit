# P05 — Kế hoạch lọc metadata cho kết quả quét

**Ngày:** 29/10/2026  
**Repository:** `danhgold7979-cyber/fonesi-edit`  
**Nhánh tích hợp:** `develop/fonesi-full`  
**Trạng thái:** lát cắt đã triển khai và kiểm thử qua [CI 40837035435](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40837035435); P05 tổng thể vẫn chưa nghiệm thu.

## 1. Rà soát trước khi triển khai

Đã đọc `AGENTS.md`, `docs/IMPLEMENTATION_PLAN.md` (P05-02/P05-03), `PRODUCT_REQUIREMENTS.md` mục 3.2, `PLATFORM_SUPPORT_MATRIX.md`, `REQUIREMENTS_TRACEABILITY.md`, `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `P05_PLAN.md`/`P05_RESULTS.md` và code scan UI/adapter hiện tại.

Kết quả quét hiện đã có tìm kiếm tiêu đề/ID, lọc ảnh/video/trạng thái URL, sắp xếp ổn định và phân trang hiển thị. Metadata date/duration/height chưa được dùng để lọc danh sách scan, dù adapter yt-dlp đã có một phần metadata và đặc tả yêu cầu lọc ngày/thời lượng/chất lượng.

## 2. Phạm vi lát cắt

1. Chuẩn hóa và bảo toàn các trường metadata an toàn có sẵn từ yt-dlp/gallery-dl: `upload_date`, `duration`, `width`, `height`. Không suy đoán metadata bị thiếu; không đưa URL media có chữ ký vào UI/log.
2. Bổ sung bộ lọc cục bộ trong DownloadsPage: ngày đăng từ/đến (`YYYYMMDD`), thời lượng tối thiểu/tối đa (giây), chiều cao tối đa (pixel).
3. Metadata thiếu hoặc không hợp lệ phải được xử lý tường minh. Mặc định giữ mục thiếu metadata để tránh âm thầm loại bỏ nội dung; checkbox cho phép loại mục thiếu trường đang được lọc.
4. Kết hợp bộ lọc mới với search/kind/selectable/sort/pagination mà không đổi chỉ số gốc của scan, không xóa lựa chọn đang bị ẩn và không thay snapshot account/output.
5. Xác thực đầu vào trước khi lọc: ngày lịch hợp lệ, số hữu hạn không âm, min ≤ max, max height là số nguyên dương. Không được làm crash UI khi người dùng nhập tạm một giá trị chưa hoàn chỉnh.
6. Bổ sung unit/integration regression cho metadata hợp lệ/thiếu/sai, lọc nhiều điều kiện, selection giữ nguyên qua filter và phân trang, gallery metadata; không gọi mạng ngoài hay API dịch.

## 3. Các bước

1. Viết kế hoạch này trước khi thay đổi source.
2. Thêm helper thuần để chuẩn hóa ngày và đánh giá điều kiện metadata; kiểm thử helper.
3. Bổ sung metadata có sẵn vào kết quả scan mà không tuyên bố provider trả trường không tồn tại.
4. Nối controls vào DownloadsPage; áp dụng metadata filter trước pagination và giữ selection theo chỉ số gốc.
5. Chạy `uv run python scripts/check_plan.py`, toàn bộ `uv run pytest -q`, build/frozen proof qua CI Linux/Windows.
6. Chỉ ghi kết quả PASS sau khi CI trả kết quả thực tế; cập nhật coverage/status và giữ cổng live provider/Chrome/Windows user-machine ở trạng thái mở.

## 4. Tiêu chí nghiệm thu lát cắt

- [x] Ngày ISO/compact được chuẩn hóa đúng; ngày vô hiệu không bị chấp nhận.
- [x] Date range, duration range và maximum height áp dụng đúng; giá trị biên được kiểm tra.
- [x] Metadata thiếu được giữ mặc định và chỉ bị loại khi người dùng bỏ chọn giữ metadata thiếu.
- [x] Search, loại media, trạng thái selectable, sort và pagination phối hợp đúng.
- [x] Lựa chọn ẩn bởi bộ lọc vẫn tồn tại; chỉ số gốc và account snapshot không thay đổi.
- [x] Không có yêu cầu mạng ngoài; source suite, validator và frozen CI Linux/Windows đều PASS.

## 5. Cổng chưa được đóng bởi lát cắt này

Đây chỉ là lọc metadata **cục bộ trên các trường adapter đã trả về**. Không phải provider-side pagination/checkpoint, không xác nhận quét hết kênh, không xác nhận đủ 10 nền tảng, không chứng minh chất lượng metadata live, Chrome/session handoff, quyền/region, installer hoặc nghiệm thu trên máy Windows người dùng. Những cổng này tiếp tục được theo dõi trong P05_RESULTS và IMPLEMENTATION_COVERAGE.
