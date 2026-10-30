# Fonesi Edit — rebuild

Đang xây lại theo yêu cầu ngày 30/10/2026. **Chưa có bản app hoàn thiện để sử dụng.**

- [Trạng thái bản làm lại](docs/REBUILD_STATUS.md)
- [Vấn đề và quyết định sửa plan](docs/REBUILD_REVIEW.md)
- [Kế hoạch 12 phase](docs/IMPLEMENTATION_PLAN.md)
- [Đặc tả sản phẩm](docs/PRODUCT_REQUIREMENTS.md)
- [Truy vết 95 nhóm yêu cầu](docs/REQUIREMENTS_TRACEABILITY.md)

Code cũ đã được loại khỏi nhánh rebuild trong commit riêng, không xóa lịch sử. Baseline mới nhất được giữ tại commit `edbb47189b0e864c74623d0a4db5b5f169f2103c` và full Git bundle đã kiểm tra khôi phục. Các báo cáo CURRENT_STATUS, Pxx_RESULTS và evidence cũ là lịch sử, không chứng nhận code mới.

Mục tiêu vẫn là ứng dụng Windows: tải nội dung có quyền truy cập, phụ đề, editor, batch và ma trận. Không suy từ test Linux sang nghiệm thu Windows/Chrome/GPU/nền tảng thật. Không thêm tính năng giả để báo hoàn thiện.

## Chạy bản phát triển mới

Cần Python3.12/3.13, uv, FFmpeg/ffprobe đã cài từ nguồn đáng tin:

```bash
uv sync --locked
uv run fonesi-edit
```

Đây là đường chạy cho nhà phát triển, chưa phải installer người dùng cuối. Nút Chọn công cụ cho phép trỏ tới FFmpeg/ffprobe đã cài trong phiên hiện tại, không cần sửa PATH; CLI check không xác minh chữ ký/nguồn binary và không tự cài. UI mới có import/probe/khung nguồn, CPU MP4 trim/speed, project save-as/open công cụ SRT riêng (sửa/tìm/thay literal, bỏ qua câu khóa, undo) và hộp thoại batch CPU cục bộ. Batch hiện chỉ một cặp thư mục, cho chọn ứng viên/xem tên đầu ra; không áp preset của Editor và chưa có hàng đợi phục hồi. Save-as không ghi đè tệp; project cũ không được migrate bằng suy đoán. Preview nguồn chưa phản ánh hiệu ứng xuất. Preview/export Editor dùng bản sao input riêng; nguồn đổi sau kiểm tra sẽ chặn xuất và cần kiểm tra lại. Batch chốt bytes khi bắt đầu từng mục, không phải lúc quét; việc copy thêm cần dung lượng tạm và có giới hạn thời gian hợp tác. Download/auth/dịch/ma trận/editor layer đầy đủ còn chưa nối.

```bash
QT_QPA_PLATFORM=offscreen uv run python -m unittest discover -s tests -v
uv run python scripts/check_rebuild_plan.py
```

Windows: đặt biến QT_QPA_PLATFORM=offscreen theo cú pháp shell Windows khi chạy test. Chạy GUI bình thường không cần biến đó. Các phép thử codec cần FFmpeg/ffprobe; không coi test bị skip là đã kiểm chứng media.


## Kiểm chứng đóng gói đang phát triển

`uv run fonesi-edit --smoke-test` chỉ kiểm tra mở UI và thoát, không phải nghiệm thu tính năng. CI có build one-folder Windows/Python3.12 và chạy executable riêng với PATH công cụ trống. Không có installer/release hoặc FFmpeg bundled trong lát cắt này; chỉ công nhận Windows proof sau khi job đúng commit PASS. Mọi output build nằm trong `.local/`, không phải source cần commit.

Phạm vi demuxer của lát cắt hiện tại: MOV/MP4-family, Matroska/WebM, AVI, WAV/MP3. Playlist (HLS/concat/DASH), raw và format khác chưa hỗ trợ; không suy định dạng từ đuôi file để cấp quyền. Allowlist không phải sandbox hoặc cam kết mọi codec trong container đều chạy được.
