# Fonesi Edit — Công cụ cần thiết và đăng nhập bằng Chrome thật

Trạng thái: bổ sung yêu cầu ngày 27/10/2026, chưa có mã ứng dụng hoặc phép thử Chrome/cookie trên Windows. Tài liệu đi cùng [đặc tả sản phẩm](PRODUCT_REQUIREMENTS.md), [thiết kế kỹ thuật](TECHNICAL_DESIGN.md) và [kế hoạch 12 phase](IMPLEMENTATION_PLAN.md).

## 1. Phân khu trong Cài đặt

1. Công cụ cần thiết: quét, đường dẫn, phiên bản, kiểm tra hoạt động, tải/cài/cập nhật/sửa.
2. Hồ sơ Chrome: Chrome thật, thư mục dữ liệu độc lập, mở/đổi tên/gán tài khoản/trạng thái.
3. Tài khoản nền tảng: mọi nền tảng đều có mục đăng nhập, hồ sơ được gán, tài khoản mặc định, kiểm tra phiên và đăng nhập lại.
4. Chẩn đoán: readiness theo chức năng, lỗi dependency/session/nguồn, lịch sử kiểm tra đã loại thông tin nhạy cảm.

Thiết lập có tìm kiếm, tooltip tiếng Việt, nút reset theo nhóm. Phím Ctrl+, mở Cài đặt; F5 trong bảng công cụ quét lại, không chiếm F5 của cửa sổ Chrome thật.

## 2. Quét và trỏ đường dẫn công cụ

### 2.1. Nội dung bảng

Mỗi dòng có tên, vai trò, chức năng cần nó, bắt buộc/tùy chọn/theo tính năng, nguồn bản gói kèm/app quản lý/hệ thống/người chọn, đường dẫn đang dùng, kiến trúc/phiên bản, lần kiểm tra và trạng thái.

Trạng thái: chưa quét / sẵn sàng / thiếu / sai đường dẫn / không tương thích / thiếu capability / lỗi khởi chạy / đang tải-cài / đang dùng / có cập nhật / cần thao tác hệ điều hành.

Các nút:

- Quét lại; chọn tệp/thư mục; dùng bản phát hiện được; khôi phục đường dẫn mặc định.
- Kiểm tra hoạt động; mở thư mục; xem lỗi và bản build/capability.
- Tải và cài; tải/cài tất cả thành phần bắt buộc còn thiếu theo workflow đang chọn.
- Cập nhật, sửa cài đặt, quay lại phiên bản đã hoạt động; gỡ riêng bản do app quản lý và không còn được dùng.
- Nếu thành phần chỉ tải được installer hoặc cần UAC/thao tác trình duyệt: tải từ nguồn tin cậy, mở installer và ghi rõ bước còn lại; không báo cài xong trước khi kiểm tra lại.

Quét nền theo đường dẫn đã cấu hình, công cụ gói kèm/app quản lý, PATH và vị trí cài phổ biến trên Windows; cho thêm thư mục quét. Không quét toàn bộ ổ đĩa mặc định. Giới hạn thời gian, cho hủy, xử lý quyền truy cập và Unicode.

Lần đầu mở tự quét nền; các lần sau dùng kết quả gần nhất để hiển thị nhanh và xác minh lại công cụ trước workflow, khi đường dẫn/phiên bản đổi hoặc khi bấm Quét. Thiếu dependency không ngăn mở app/Cài đặt.

Đường dẫn được người dùng chọn rõ có ưu tiên; nếu hỏng phải báo và cho đổi, không âm thầm chuyển bản khác. Chế độ Auto chọn bản app quản lý/bản gói kèm đã kiểm chứng trước, rồi bản hệ thống tương thích; UI và job ghi đúng bản thực sự được dùng.

Tệp tồn tại chưa đủ: kiểm tra version/capability và phép thử chức năng tối thiểu trong tiến trình có timeout. Bộ FFmpeg/ffprobe phải tương thích; GPU phải thử encode nhỏ thật khi cần.

### 2.2. Danh sách thành phần

| Thành phần | Vai trò | Chính sách |
| --- | --- | --- |
| FFmpeg và ffprobe | Probe, ghép, sub, audio, encode | Bắt buộc cho workflow media; bản gói kèm hoặc tải bản Windows đã chọn và kiểm chứng |
| yt-dlp | Bộ tải video chính | App quản lý binary/module đã pin; có trạng thái phiên bản/cập nhật riêng |
| gallery-dl | Ảnh/album và nguồn bổ sung | Cài theo connector cần dùng; không hứa mọi nền tảng được hỗ trợ |
| Google Chrome chính thức | Đăng nhập bằng trình duyệt thật | Tìm bản đã cài, cho trỏ tệp, tải/cài từ nguồn chính thức nếu thiếu |
| JavaScript runtime/thành phần extractor bổ sung | Phụ thuộc của phiên bản downloader nếu cần | Xác định ở P02; chỉ cài khi connector/tool được chọn thực sự yêu cầu |
| Thư viện playback/runtime hệ thống | Preview/codec/UI | Ưu tiên gói kèm hợp lệ; VC++ runtime hoặc thành phần khác chỉ yêu cầu nếu build cần |
| Font bổ sung | Hiển thị các hệ chữ | Chọn font sẵn có hoặc thư mục font riêng; chỉ tải font có nguồn/giấy phép phù hợp |
| Model dịch cục bộ | Chỉ cho phương án dịch local được chọn | Không tải model khi dùng API; hiển thị dung lượng và yêu cầu máy trước khi tải |
| Driver GPU | Tăng tốc phần cứng | Phát hiện/kiểm tra, hướng dẫn tới hãng; không âm thầm cài/thay driver |

Bản người dùng cuối không mặc định phải tự cài Python, pip, Git, Visual Studio hoặc CUDA toolkit. Nếu engine đã chọn cần thêm thành phần, dependency manifest phải khai báo rõ và chứng minh cần thiết.

### 2.3. Tải, cài và cập nhật

- Hiển thị tiến độ, dung lượng, tốc độ, thời gian, nguồn và bước tải/xác minh/cài/kiểm tra; chưa biết tổng thì hiển thị đúng.
- Manifest có OS/architecture/version/artifact/dependencies/nguồn/checksum hoặc chữ ký được xác thực. Giữ TLS và xác minh; không bỏ kiểm tra khi tải lỗi.
- Staging riêng, kiểm tra archive/đường dẫn giải nén, kiểm tra binary trước khi kích hoạt; lỗi giữ bản cũ và có rollback.
- App-managed tools lưu trong user data theo version; không đè công cụ hệ thống/người dùng, không tự sửa PATH toàn máy.
- Job giữ tool version/path đã resolve và lease. Không thay binary đang render/tải; kích hoạt bản mới cho job sau khi điều kiện an toàn đạt.
- Bản bên ngoài chỉ được quét/chọn/kiểm tra; cập nhật bằng cách cài bản app quản lý hoặc để người dùng cập nhật ngoài, không tự xóa bản của người dùng.
- Hủy/mất mạng/quyền ghi/đĩa đầy có thông báo và cleanup staging; cài lại không tạo bản rác hoặc mất cấu hình.
- Tải-cài tất cả giữ trạng thái từng thành phần, không coi cả nhóm thành công vì một tool đã cài; cài lại chỉ làm phần thiếu/lỗi và giữ phần đã đạt.
- Phát hiện có bản mới không tự đổi môi trường đang chạy. Tự động tải/cài trong phạm vi nút người dùng đã bấm hoặc lựa chọn auto-update được bật rõ.

## 3. Mô hình Chrome thật và nhiều tài khoản

Một bản cài Google Chrome có thể mở nhiều hồ sơ độc lập, hiển thị là Chrome A, Chrome B… Không cần cài lại một Chrome cho mỗi tài khoản.

Mặc định mỗi hồ sơ do app tạo có thư mục user-data-dir riêng, không chỉ là hai cửa sổ ẩn danh hay hai tab chung cookie. Đây là lựa chọn để tách phiên và tránh ảnh hưởng hồ sơ Chrome cá nhân đang dùng.

```text
Google Chrome chính thức
├── Chrome A — thư mục dữ liệu A
│   ├── Facebook: tài khoản FB_A
│   ├── TikTok: tài khoản TT_A
│   ├── YouTube: tài khoản YT_A
│   └── Bilibili: tài khoản BL_A
└── Chrome B — thư mục dữ liệu B
    ├── Facebook: tài khoản FB_B
    ├── TikTok: tài khoản TT_B
    └── Instagram: tài khoản IG_B
```

- Một hồ sơ chứa nhiều nền tảng. Mỗi nền tảng có một danh tính đăng nhập đang được app gán cho hồ sơ đó.
- Muốn thêm tài khoản thứ hai của cùng nền tảng thì tạo/chọn hồ sơ khác. App không coi account switcher trong cùng cookie jar là hai phiên độc lập.
- Nhiều cửa sổ chung một user-data-dir vẫn là một hồ sơ, không phải cách ly tài khoản.
- Đăng nhập Chrome Sync/Google ở cấp trình duyệt không phải điều kiện bắt buộc để tạo hồ sơ; đăng nhập từng website thực hiện trong Chrome.
- Tài khoản Facebook có nhiều page hoặc Google có nhiều kênh vẫn có thể là một tài khoản xác thực với nhiều đối tượng truy cập; không bắt tạo Chrome mới cho mỗi page/kênh.
- Nền tảng có liên kết danh tính như Instagram/Threads được kiểm tra riêng; không tự suy ra đăng nhập một bên thì connector bên kia dùng được.

## 4. Quản lý hồ sơ và đăng nhập

### 4.1. Hồ sơ Chrome

- Tạo, đổi tên/màu/nhãn, xem đường dẫn/phiên bản, mở, chọn mặc định và kiểm tra hồ sơ.
- Mở một nền tảng vào đúng Chrome/hồ sơ đã chọn; dùng trình duyệt Google Chrome có cửa sổ thật để người dùng thao tác.
- Google Chrome, Chromium tải kèm automation và WebView là các lựa chọn khác nhau; bản này yêu cầu Google Chrome thật, không âm thầm thay bằng trình duyệt khác.
- Hồ sơ có trạng thái browser: đóng/mở/bận/bị khóa/thiếu đường dẫn/không tương thích. Không xóa lock file hoặc ép đóng Chrome đang dùng để giành quyền.
- Xóa liên kết tài khoản khỏi app khác với đăng xuất website; xóa hồ sơ/dữ liệu Chrome là thao tác riêng có xác nhận rõ.
- Liên kết hồ sơ Chrome cá nhân có sẵn chỉ là tùy chọn sau khi đã kiểm chứng tương thích; không tự sao chép/migrate hồ sơ cá nhân hoặc coi là đường mặc định.
- Thư mục hồ sơ không phải cache để tự dọn và không nằm trong project export. Chuyển máy/Windows khác không được hứa giữ phiên chỉ bằng copy thư mục vì bảo vệ phiên có thể gắn với máy/OS.

### 4.2. Mọi nền tảng có mục đăng nhập

Mỗi dòng nền tảng hiển thị: hồ sơ Chrome, tên/ID tài khoản nếu kiểm tra được, trạng thái phiên, khả năng bộ tải dùng phiên, lần kiểm tra và tài khoản mặc định. Nút: Thêm tài khoản, Mở đăng nhập, Kiểm tra, Đăng nhập lại, Chọn mặc định, Bỏ liên kết.

Quy trình:

1. Chọn nền tảng, hồ sơ hiện có hoặc tạo hồ sơ mới.
2. Mở URL đăng nhập hợp lệ của nền tảng trong đúng Google Chrome/hồ sơ.
3. Người dùng nhập tài khoản/mật khẩu, OTP/QR/CAPTCHA hoặc xác minh nếu website yêu cầu.
4. Bấm kiểm tra; app xác minh trạng thái đăng nhập bằng thao tác đọc và nhận diện tài khoản khi khả dụng.
5. Kiểm tra riêng connector có dùng được phiên cho quét/tải thử hay không.
6. Lưu liên kết platform/account/profile và trạng thái. Chrome giữ cookie trong kho của chính hồ sơ; project/preset chỉ lưu ID tham chiếu.

Không có ô lưu mật khẩu mạng xã hội trong app. Phiên đăng nhập tồn tại theo Chrome/nền tảng, không cam kết vĩnh viễn hoặc né được xác minh của website.

### 4.3. Trạng thái xác thực

- Chưa cấu hình / chưa đăng nhập / chưa kiểm tra / phiên dùng được / hết hạn / cần xác minh / sai tài khoản / connector chưa dùng được phiên.
- Phân biệt đăng nhập website thành công với quyền xem nội dung, khả năng bridge và rate limit; một mục lỗi không tự đổi toàn bộ thành hết hạn.
- Tên tài khoản hiển thị khác source đang tải. Người tải có thể tải kênh khác mà tài khoản của họ có quyền xem.

## 5. Dùng phiên đăng nhập khi tải

- Mỗi nguồn/job có lựa chọn tài khoản hoặc chế độ công khai; nhớ lựa chọn theo nền tảng/nguồn.
- Mặc định dùng tài khoản đã gán nếu có; chưa gán và nguồn cho phép thì tải công khai, không bắt đăng nhập tất cả website ngay khi cài app.
- Trước lô cần auth, kiểm tra Chrome/profile/session/connector và quyền truy cập nguồn bằng thao tác đọc thích hợp; không chỉ kiểm tra có cookie file.
- Nếu job đã chọn tài khoản nhưng phiên hết hạn: chờ đúng tài khoản, mở đăng nhập lại, kiểm tra rồi tiếp tục phần còn thiếu. Không tự âm thầm chuyển sang công khai làm danh sách tải bị thiếu.
- Snapshot giữ profile ID, account binding ID và danh tính đã kiểm chứng nếu có; cookie/session token không được nhúng vào snapshot.
- Refresh phiên cùng danh tính có thể dùng lại sau kiểm tra. Nếu người dùng đổi nick trong Chrome, job cũ phải báo sai tài khoản, không tự chạy bằng nick mới.
- Không tự xoay tài khoản khi rate limit hoặc thiếu quyền; người dùng chủ động chọn tài khoản khác và xác nhận cập nhật job nếu cần.
- Session và quyền truy cập phải tách cache theo account scope để kết quả riêng tư/giới hạn của tài khoản A không bị dùng cho B.
- Điều phối truy cập hồ sơ theo khả năng thật, tránh hai tiến trình giành cùng user-data-dir. Việc không cần browser vẫn được tải song song theo giới hạn connector/tài khoản.

## 6. Điểm bắt buộc kiểm chứng ở P02

Đăng nhập trong Chrome không tự động bảo đảm yt-dlp/gallery-dl đọc được cookie. Chrome mới có mã hóa bảo vệ theo ứng dụng/OS; hồ sơ đang mở có thể bị khóa; cơ chế điều khiển trình duyệt cũng có giới hạn theo phiên bản/chính sách máy.

- Không thiết kế đường mặc định bằng copy file SQLite, giải mã cookie hoặc tắt bảo vệ Chrome/Windows.
- Chọn cơ chế session handoff mà connector và Chrome hỗ trợ, ví dụ tích hợp trình duyệt/extension/bridge hoặc cookie interface của công cụ khi hệ thống thực sự cho phép; thử trên Chrome chính thức và Windows thật.
- Nếu dùng automation/CDP: dùng hồ sơ app quản lý tách biệt, endpoint local giới hạn vòng đời/quyền, không mở cổng điều khiển ra mạng hay chiếm hồ sơ cá nhân mặc định. Không hứa native CDP có sẵn cơ chế xác thực ngoài khả năng thật.
- Nếu connector không nhận phiên qua đường đã kiểm chứng, ghi giới hạn; có thể cần đường chạy qua browser phù hợp. Không báo tài khoản sẵn sàng cho bộ tải chỉ vì trang web hiển thị đã đăng nhập.
- Nhập cookie thủ công chỉ là đường bổ sung nếu quyết định hỗ trợ; không dùng như lời giải mặc định bắt người dùng xuất lại mỗi lần.
- Không có một cơ chế đăng nhập bảo đảm mọi website đều hỗ trợ. Mỗi nền tảng vẫn có nút/quản lý đăng nhập, còn mức dùng phiên được ghi bằng evidence riêng.

## 7. Readiness trước khi chạy

Ba trục hiển thị riêng:

1. Công cụ: đúng đường dẫn/phiên bản/capability.
2. Phiên: đúng Chrome/hồ sơ/tài khoản và connector dùng được.
3. Nguồn: quét/tải loại URL và nội dung cụ thể có quyền truy cập.

Nút sửa theo nguyên nhân: Tải công cụ, Chọn đường dẫn, Mở Chrome, Đăng nhập lại, Chọn tài khoản hoặc Thử lại nguồn. Các lỗi này không chặn chức năng độc lập như edit media cục bộ.

## 8. Nghiệm thu bổ sung

- Máy Windows thiếu công cụ: quét đúng, tải/cài theo nút, xác minh, kiểm tra lại và chạy workflow thật.
- Công cụ có sẵn ở đường dẫn Unicode: chọn dùng được, không sửa bản hệ thống; sai version/capability được báo.
- Tải bị ngắt, checksum/chữ ký lỗi, đĩa đầy, không có quyền, cập nhật lúc tool bận: không phá bản đang dùng; có retry/rollback rõ.
- Chrome A đăng nhập Facebook A + TikTok A; Chrome B đăng nhập Facebook B: ba binding đúng, mở đúng hồ sơ, quét/tải dùng đúng tài khoản.
- Khởi động lại app/máy: giữ liên kết hồ sơ và dùng phiên còn hợp lệ, không yêu cầu đăng nhập lại vô cớ.
- Đổi nick cùng nền tảng trong một hồ sơ: job cũ phát hiện mismatch, không tải nhầm danh tính.
- Chrome đang mở/bị khóa hoặc bridge không nhận được phiên mã hóa: báo đúng nguyên nhân, không phá profile hoặc tắt bảo vệ.
- Hết hạn/OTP/CAPTCHA: chỉ job tài khoản bị ảnh hưởng chờ; người dùng xử lý trong Chrome, kiểm tra lại rồi resume không tải trùng.
- Mọi nền tảng có trang cấu hình đăng nhập; từng đường auth còn chưa kiểm chứng được ghi đúng, không thay bằng cam kết hỗ trợ.
- Export project/preset/log chẩn đoán không chứa mật khẩu, cookie, token, dữ liệu hồ sơ Chrome hoặc nội dung đăng nhập riêng tư.
