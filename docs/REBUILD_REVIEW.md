# Rà soát và quyết định làm lại — 2026-10-30

## Phạm vi và bằng chứng

Yêu cầu mới: làm lại code từ đầu, sửa toàn bộ plan trước khi triển khai; giữ đầy đủ phạm vi sản phẩm. Nhánh làm việc `rebuild`, baseline `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`. Đã phát hiện và fast-forward nhánh local tới `edbb47189b0e864c74623d0a4db5b5f169f2103c` của `develop/fonesi-full` (616 commit mới hơn main). Bundle đã giữ cả nhánh này. Lịch sử baseline là bằng chứng lịch sử, không phải kết quả nghiệm thu bản làm lại. Bản Git bundle đầy đủ đã được kiểm tra và fetch vào repository trống, khôi phục đúng baseline; không rewrite history.

## Vấn đề và cách xử lý được chọn

| ID | Bằng chứng/vấn đề | Quyết định và tiêu chí kiểm tra |
|---|---|---|
| R01 | Main cũ có plan 9–12 dòng; develop mới có 3182 dòng plan và nhiều plan sửa lỗi rời, cần chuẩn hóa thành thứ tự thực thi thay vì kết luận thiếu toàn bộ | Viết mỗi task riêng: đầu vào, đầu ra, phụ thuộc, trường hợp lỗi và test; kiểm tra coverage mọi ID master |
| R02 | Mâu thuẫn trạng thái của main đã được sửa trên develop; vẫn cần phân biệt trạng thái lịch sử với rebuild | Reset trạng thái bản làm lại; giữ số liệu cũ trong lịch sử, không tái dùng 92 tests của main hay 892 tests được dẫn trên develop như chứng nhận code mới |
| R03 | PRODUCT_REQUIREMENTS có 7 khu vực, README nói 8 tab, P01 ghi bảy | Chốt 8 khu vực: Tổng quan, Tải nội dung, Phụ đề, Editor, Edit hàng loạt, Ghép theo cảnh, Hàng đợi/Lịch sử, Preset/Cài đặt; Editor riêng là nơi thao tác trực tiếp, không bỏ tính năng |
| R04 | Hợp đồng kiến trúc chỉ mô tả trường, chưa có schema thực thi/version cho rebuild | P03 tạo domain độc lập Qt, schema có validation, snapshot bất biến và migration có backup; input lỗi không được sửa ngầm |
| R05 | P02 là prerequisite nhưng nhiều gate live còn mở | Tách quyền triển khai độc lập khỏi nghiệm thu. Logic thuần và local media tiếp tục; Windows/auth/GPU/dịch trả phí chưa có bằng chứng phải giữ BLOCKED |
| R06 | Preview/export dung sai chưa khóa, không thể nghiệm thu chỉ bằng “trông giống” | P02 lập corpus và metric; logic time-map kiểm thử rational chính xác; pixel/audio/performance giới hạn phải đo trên target trước release |
| R07 | Tải 10 nền tảng và auth có nguy cơ được hiểu là cam kết sẵn sàng | Capability theo từng URL/media/auth/tool version/test date; không dùng mock hay login web để báo connector đạt |
| R08 | Dịch có timeout tính phí chưa rõ và thiếu config | Adapter báo unavailable khi chưa cấu hình; giữ cue ID/manual lock; reservation budget và UNKNOWN billing, không retry mù |
| R09 | Cơ chế Chrome bridge cần quyền riêng và thực nghiệm Windows | Không copy/decrypt kho cookie hoặc tắt bảo vệ. Binding tách project, no silent account fallback, permission/setup do người dùng thực hiện |
| R10 | Có bằng chứng CI Windows trên develop; Windows 10/11 dùng thật, Chrome/GPU vẫn chưa được nghiệm thu | Ma trận target có build/architecture/tool versions; chỉ công bố support trên cấu hình đã test; không suy từ Linux |
| R11 | Source/tool/installer có version và quyền phân phối riêng | Lock dependency tái lập, provenance và notices; xác minh nguồn/hash/signature trước activation, không nâng cấp tool đang lease |
| R12 | Old implementation/prototype/tests lẫn với rebuild dễ tạo pass giả | Xóa implementation cũ trong commit riêng sau bảo toàn baseline. Không copy lại code cũ để gọi “viết mới”; requirements và edge cases dùng làm đầu vào thiết kế mới |
| R13 | Các nhóm traceability quá rộng có thể che thiếu từng tùy chọn | Giữ 95 nhóm, mỗi task liên kết đầy đủ các tiêu chí thuộc phạm vi; chỉ accept nhóm khi mọi tiêu chí con được xác minh |
| R14 | Tool hoàn thiện phụ thuộc tài khoản, API, Windows/GPU thật | Báo code/local test/target acceptance riêng. Không dùng việc thiếu credential làm lý do ngừng phần độc lập, không gọi 100% khi gate còn mở |

## Ngoài phạm vi giữ nguyên

Không thêm TTS/ASR/OCR/tracking, slideshow hay editor ảnh vào bản đầu. Không xóa nguồn media, không bypass CAPTCHA/rate limits/Chrome/OS protections. Không gửi khóa, cookie, profile hay media riêng vào Git.

## Quy trình triển khai mới

1. P01: đồng bộ đặc tả, master, chi tiết từng phase và kiểm tra traceability.
2. P02: feasibility tái lập; thực hiện local checks khả dụng, ghi target blockers.
3. P03–P10: từng vertical slice có model/use case/UI/test và kết quả, không tạo nút “thành công” giả.
4. P11: regression toàn diện và ma trận requirement-to-test.
5. P12: đóng gói Windows, trải nghiệm máy thật, acceptance cuối. Không tự publish release công khai khi còn thiếu kiểm chứng.

Tỷ lệ = task đã nghiệm thu / tổng task đã khóa; code viết xong và test local không thay nghiệm thu bên ngoài.
