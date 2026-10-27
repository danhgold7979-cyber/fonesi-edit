# Fonesi Edit — Kế hoạch kiểm chứng nền tảng

Trạng thái: chưa thử trên ứng dụng, chưa có connector được công bố đã hoạt động. Bảng này xác định phép thử cần thực hiện ở P02/P05, không khẳng định thư viện hiện hỗ trợ đủ.

## 1. Phạm vi và đợt triển khai

| Nền tảng | Đợt dự kiến | Nội dung cần kiểm chứng | Điểm phải xác minh | Trạng thái |
| --- | --- | --- | --- | --- |
| YouTube | A | Kênh/video/Shorts/playlist, sub, thumbnail | Phân trang, sub người đăng/tự động, giới hạn truy cập | Chưa thử |
| Bilibili | A | Profile/video/nhiều phần, sub nếu có | Trang hồ sơ, chất lượng/auth/vùng, sub từng phần | Chưa thử |
| TikTok | B | Profile/video/bài nhiều ảnh | Phân trang, album ảnh, rate limit/auth/sub có sẵn | Chưa thử |
| Facebook | B | Page/profile, video/Reels/ảnh/album | Quyền xem, tab khác nhau, quét lịch sử, phiên đăng nhập | Chưa thử |
| Instagram | B | Profile/Reels/video/ảnh/carousel | Quyền xem, phân trang, rate limit, nội dung hỗn hợp | Chưa thử |
| Threads | C | Profile/bài ảnh/video | Quét toàn profile khác với tải một URL bài | Chưa thử |
| X | C | Profile/bài ảnh/video/nhiều media | Phân trang, quyền truy cập, lịch sử đầy đủ hay giới hạn | Chưa thử |
| Douyin | C | Profile/video/bài ảnh | Auth/phân trang/giới hạn vùng và khả năng có sub rời | Chưa thử |
| Xiaohongshu | C | Profile/bài ảnh/video | Xác thực, album, liên kết nguồn và giới hạn quét | Chưa thử |
| Kuaishou | C | Profile/video/media khác thực sự có | Auth, phân trang, bộ kết nối và giới hạn thực tế | Chưa thử |

Đợt là thứ tự kỹ thuật đề xuất, thay đổi theo quyền truy cập và kết quả thử. Không loại nguồn đợt C khỏi phạm vi. “Các nền tảng Trung Quốc khác” là điểm mở rộng theo tên cụ thể, không phải cam kết vô hạn mọi website.

## 2. Bản ghi capabilities bắt buộc cho từng connector

- Nhận dạng URL: bài, kênh/profile, playlist, album; canonical ID.
- Enumerate từng loại nguồn, cursor/checkpoint, phân trang, complete/partial/unknown.
- Loại nội dung: video dài, ngắn, ảnh, album/carousel, nhiều phần; ghi N/A chỉ khi có lý do rõ.
- Tải đơn so với quét toàn kênh là hai khả năng khác nhau.
- Chất lượng/media tracks, phụ đề rời, loại/ngôn ngữ sub, thumbnail/metadata.
- Auth: không cần / cần phiên đăng nhập / có điều kiện; chỉ ghi trạng thái, không ghi credential.
- Mọi nền tảng đều có mục đăng nhập/kiểm tra/đăng nhập lại theo [SETTINGS_AND_BROWSER_SPEC.md](SETTINGS_AND_BROWSER_SPEC.md). Nguồn công khai không bắt login trước, còn phiên đã gán phải dùng đúng account/profile.
- Evidence auth gồm Google Chrome chính thức/version/Windows/profile isolation, đăng nhập web, connector dùng phiên và quyền xem nguồn; bốn trạng thái không gộp làm một.
- Retry/resume, rate limit, bộ lọc được áp tại nguồn hay sau quét, đồng bộ nội dung mới.
- Tool/adapter version, ngày thử, source/item IDs đã làm sạch, điều kiện mạng và quyền truy cập.
- Kết quả quét/tải/sub/validation riêng, lỗi/blocker và phép thử lại sau thay đổi.

## 3. Bộ phép thử cho mỗi khả năng được công bố

1. Tải một item có quyền truy cập, kiểm tra artifact thật.
2. Quét nguồn có nhiều trang, đối chiếu danh sách mẫu, xác nhận checkpoint và thông báo chưa biết tổng.
3. Tải lô có loại media hỗn hợp nếu nền tảng có; ảnh đúng thứ tự, video đúng ID.
4. Quét lại, thêm nội dung mới hoặc bỏ một tệp cục bộ, kiểm tra chống trùng/phục hồi.
5. Kiểm tra sub có/không có; không coi chữ trong hình là phụ đề rời.
6. Ngắt mạng/cancel/auth hết hạn hoặc mô phỏng lỗi lớp adapter có gắn nhãn; tách phép thử live và mô phỏng.
7. Tên kênh trùng/đổi tên/Unicode, folder output và metadata không nhập nhầm nguồn.
8. Chrome A đăng nhập nhiều nền tảng, Chrome B tài khoản thứ hai cùng nền tảng; kiểm tra đúng danh tính, không lẫn session/cache.
9. Hết hạn/cần xác minh/profile đang mở hoặc bridge không nhận phiên: dừng đúng nguồn/tài khoản, login lại rồi resume; không tắt bảo vệ Chrome hoặc đổi tài khoản ngầm.

## 4. Quy tắc công bố hỗ trợ

- Chưa thử: chỉ có kế hoạch hoặc thư viện liệt kê website.
- Đã kiểm chứng: phép thử loại URL/nội dung tương ứng thành công và có evidence.
- Có điều kiện: ghi rõ auth, loại URL, chất lượng, vùng hoặc phạm vi quét đáp ứng được.
- Tạm lỗi: capability từng đạt nay thất bại, có phiên bản/ngày và lỗi.
- Bị chặn: thiếu quyền/cấu hình/hạ tầng; chưa thể kết luận hỗ trợ hay không hỗ trợ.
- Không hỗ trợ: đã có chẩn đoán và quyết định rõ, ghi hạn chế và công việc còn lại; không tự thay đổi phạm vi đã thống nhất.

UI và release notes dùng chính dữ liệu này. Không gộp một item tải được thành “tải toàn bộ kênh được”, không hứa mọi nền tảng đều có file sub hoặc thời gian sửa lỗi cố định khi website đổi.

## 5. Đăng nhập cho tất cả nền tảng

YouTube, Bilibili, TikTok, Facebook, Instagram, Threads, X, Douyin, Xiaohongshu và Kuaishou đều cần UI quản lý đăng nhập. Tất cả đường auth/bridge hiện chưa thử; yêu cầu có nút không đồng nghĩa đã kiểm chứng dùng phiên được.

Mỗi nền tảng có account binding, hồ sơ được gán, tài khoản mặc định, lần kiểm tra, trạng thái website/bridge/quyền nguồn và phép thử tải cần auth. Facebook page/Google channel có thể thuộc chung danh tính; Instagram/Threads liên kết phải kiểm tra riêng. Không tự suy ra cùng hệ sinh thái là dùng chung phiên được.
