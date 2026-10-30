# Fonesi Edit — rebuild

Đang xây lại theo yêu cầu ngày 30/10/2026. **Chưa có bản app hoàn thiện để sử dụng.**

- [Trạng thái bản làm lại](docs/REBUILD_STATUS.md)
- [Vấn đề và quyết định sửa plan](docs/REBUILD_REVIEW.md)
- [Kế hoạch 12 phase](docs/IMPLEMENTATION_PLAN.md)
- [Đặc tả sản phẩm](docs/PRODUCT_REQUIREMENTS.md)
- [Truy vết 95 nhóm yêu cầu](docs/REQUIREMENTS_TRACEABILITY.md)

Code cũ đã được loại khỏi nhánh rebuild trong commit riêng, không xóa lịch sử. Baseline mới nhất được giữ tại commit `edbb47189b0e864c74623d0a4db5b5f169f2103c` và full Git bundle đã kiểm tra khôi phục. Các báo cáo CURRENT_STATUS, Pxx_RESULTS và evidence cũ là lịch sử, không chứng nhận code mới.

Mục tiêu vẫn là ứng dụng Windows: tải nội dung có quyền truy cập, phụ đề, editor, batch và ma trận. Không suy từ test Linux sang nghiệm thu Windows/Chrome/GPU/nền tảng thật. Không thêm tính năng giả để báo hoàn thiện.
