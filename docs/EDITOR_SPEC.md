# Fonesi Edit — Preview, tùy chọn, phím tắt và tự động hóa

Trạng thái: yêu cầu triển khai, chưa phải tính năng đã có trong phần mềm. Bổ sung cho [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md).

## 1. Bố cục và nguyên tắc

- Trái: media, thư mục, cảnh/góc và tài nguyên; giữa: preview; phải: thuộc tính; dưới: timeline.
- Hàng đợi và thông số máy thu gọn/mở rộng; đổi kích thước panel, lưu bố cục, đặt lại bố cục.
- Cơ bản hiển thị thiết lập thường dùng; Nâng cao mở thêm lựa chọn. Có tìm kiếm thuộc tính, tooltip, ô nhập số cạnh slider và reset từng thuộc tính/nhóm.
- Thay đổi hiển thị ngay khi có thể; việc cần render preview có chỉ báo, hủy được và không khóa UI.
- Tất cả chỉnh sửa tạo lệnh undo/redo. Một lần kéo là một lệnh, không chiếm hàng trăm bước undo.
- Phạm vi luôn hiển thị: clip này / các clip chọn / preset cả lô. Sửa preset không tự thay tác vụ đang chạy.

## 2. Thao tác trực tiếp trên preview

### 2.1. Đối tượng hỗ trợ

- Khung video/crop, logo ảnh, chữ do phần mềm thêm, phụ đề rời và vùng che chữ.
- Click chọn, Shift+click chọn nhiều, hộp chọn, chuyển chọn qua danh sách layer khi các đối tượng chồng nhau.
- Đối tượng đang chọn có viền, các tay nắm, tâm/điểm neo và thông số; đối tượng khóa không bị kéo nhầm.
- Chữ/logo đã nằm trong video gốc không phải layer độc lập; bản đầu không tự tách để di chuyển.

### 2.2. Biến đổi và căn chỉnh

- Kéo di chuyển; tay nắm đổi kích thước; khóa/mở tỷ lệ; tay nắm xoay; nhập số chính xác.
- Căn trái/giữa/phải, trên/giữa/dưới; chín điểm neo; phân bố đều đối tượng được chọn.
- Lưới, đường căn, vùng an toàn, snap theo tâm/cạnh/đối tượng; giữ Alt để tạm tắt snap.
- Mũi tên dịch một bước theo độ phân giải đầu ra, Shift+mũi tên dịch bước lớn khi canvas có focus.
- Nút đưa về trong khung, khớp khung, giữ tỷ lệ và đặt lại biến đổi.
- Zoom preview: fit, 25/50/100/200% và tùy chỉnh; pan khi phóng to; đổi zoom không đổi vị trí đối tượng trong video.
- Crop có lưới, tỷ lệ khóa, nền ngoài vùng xuất và nút xác nhận/hủy; không kéo nhầm clip trong lúc crop.
- Lưu vị trí/kích thước theo tỷ lệ khung và điểm neo để áp dụng được cho nhiều độ phân giải; xem trước riêng khi đổi tỷ lệ dọc/ngang.
- Hiển thị tọa độ, kích thước, góc, opacity, điểm neo và vùng thời gian của đối tượng.
- Nhân bản, nhóm/tách nhóm, khóa/mở, ẩn/hiện, đổi thứ tự trước/sau, copy/paste kiểu và copy/paste chuyển động.

### 2.3. Chỉnh nội dung và thời gian

- Double-click chữ để sửa tại chỗ; có chế độ nhập chữ riêng để phím tắt không ăn vào nội dung.
- Chọn cue sub tại con trỏ, sửa văn bản; tùy chọn áp kiểu cho cue chọn hoặc cả track.
- Bật ghi keyframe: thay đổi tại vị trí playhead tạo keyframe của thuộc tính được bật. Tắt ghi: sửa giá trị nền hoặc hỏi phạm vi khi có keyframe.
- Kéo thời điểm xuất hiện/kết thúc trên timeline, đặt in/out theo playhead; giới hạn trong thời lượng project.
- So sánh trước/sau hoặc bật/tắt từng hiệu ứng; xem frame tại kích thước xuất khi cần kiểm tra chữ.

## 3. Font, chữ và ngôn ngữ

### 3.1. Font

- Quét font hệ thống, chọn font người dùng cung cấp TTF/OTF bằng thư mục riêng; không tự cài toàn hệ thống.
- Tìm theo tên, lọc yêu thích/gần dùng, xem mẫu bằng chính nội dung đang nhập.
- Chọn family, style/weight có thật, cỡ, đậm/nghiêng khi hỗ trợ, gạch chân, gạch ngang.
- Giãn ký tự, giãn dòng, căn trái/giữa/phải, chiều rộng hộp chữ, padding, tự xuống dòng, giới hạn số dòng.
- Cỡ theo pixel đầu ra hoặc tỷ lệ khung; hiện giá trị quy đổi, không phụ thuộc mức zoom preview.
- Font fallback cho glyph thiếu, cảnh báo thiếu font/glyph khi mở project hoặc xuất; cho thay font hàng loạt.
- Hỗ trợ Unicode, dấu tiếng Việt, chữ Trung/Nhật/Hàn qua font thích hợp. Các hệ chữ RTL và shaping khác phải kiểm chứng trước khi hiển thị là hỗ trợ đầy đủ.
- Preview và render dùng cùng font đã chọn và quy tắc xuống dòng; project ghi nhận font cần dùng, không sao chép font không có sẵn quyền phân phối.

### 3.2. Kiểu chữ

- Màu chữ bằng bảng màu, HEX/RGB, màu gần dùng/yêu thích; opacity riêng.
- Viền màu/độ dày; bóng màu/độ mờ/độ lệch; nền khối/nền dòng với màu, opacity, padding và bo góc.
- Các preset dễ đọc: sáng viền tối, tối nền sáng, nền mờ, tiêu đề, chú thích, song ngữ.
- Viết hoa/thường theo lựa chọn, giữ nguyên tên riêng trong dịch; tìm/thay thế nội dung có xem trước.
- Nội dung động: tên kênh, tiêu đề rút gọn, số đầu ra, tên cảnh và ngày; cho xem giá trị sẽ thay, không chèn thông tin nhạy cảm từ metadata.
- Nhiều lớp chữ, mỗi lớp có thời gian, kiểu, vị trí và chuyển động riêng.
- Chọn xử lý tràn: tự xuống dòng, giảm cỡ trong giới hạn, hoặc cảnh báo; không cắt mất chữ ngầm.

### 3.3. Ngôn ngữ

- Tách ngôn ngữ giao diện, ngôn ngữ nguồn, ngôn ngữ dịch đích và font; đổi ngôn ngữ không đồng nghĩa font đã đủ glyph.
- Tìm ngôn ngữ theo tên/mã, nhớ gần dùng, thứ tự ưu tiên, tự nhận diện khi có dữ liệu đáng tin cậy.
- Song ngữ với vị trí, thứ tự, màu, cỡ và khoảng cách hai khối riêng; có preview mẫu.
- Danh sách ngôn ngữ dịch phản ánh bộ dịch thực tế; không hiển thị mọi ngôn ngữ là khả dụng khi provider chưa hỗ trợ.

## 4. Logo và đối tượng phủ

- Thêm nhiều logo PNG/JPEG/WebP khi decoder hỗ trợ, giữ alpha nếu nguồn có; báo nền không trong suốt khi cần.
- Kích thước theo % khung hoặc pixel, khóa tỷ lệ, crop, xoay, opacity, viền/bóng nếu được engine hỗ trợ.
- Chín vị trí nhanh, lề từng cạnh, tọa độ nhập tay, vùng giới hạn chuyển động và vùng cần tránh.
- Chọn toàn video, một đoạn hoặc các khoảng xuất hiện; fade đầu/cuối.
- Chọn logo theo từng kênh, theo tên tệp hoặc danh sách; báo thiếu logo thay vì dùng nhầm logo kênh khác.
- Kéo logo từ thư viện thả vào preview/timeline, thay ảnh nhưng giữ biến đổi/chuyển động nếu người dùng chọn.
- Không tự phóng logo vượt giới hạn chất lượng hoặc ra ngoài khung mà không cho thấy cảnh báo.

## 5. Chuyển động logo, chữ và layer

### 5.1. Preset chuyển động

| Nhóm | Lựa chọn |
| --- | --- |
| Cố định | Neo một vị trí, bật/tắt theo thời gian |
| Chạy thẳng | Trái→phải, phải→trái, trên→dưới, dưới→trên, đường chéo |
| Qua điểm | Điểm A→B, nhiều điểm do người dùng đặt, lần lượt qua các góc |
| Lặp | Lặp cùng chiều, đi-về, nảy trong vùng giới hạn |
| Nhẹ | Trôi chậm, zoom in/out, nhịp phóng nhỏ, xoay trong biên độ |
| Xuất hiện/biến mất | Fade, trượt vào/ra, zoom vào/ra |
| Ngẫu nhiên | Vị trí/đường đi/tham số trong vùng và khoảng cho phép, seed tái tạo |

### 5.2. Tham số chuyển động

- Hướng, điểm đầu/cuối, điểm neo, đường đi và phạm vi hoạt động.
- Chọn điều khiển bằng tốc độ hoặc thời gian hoàn thành; hai giá trị liên kết, không để mâu thuẫn.
- Tốc độ theo % chiều rộng/chiều cao khung mỗi giây; có giá trị pixel/giây quy đổi theo đầu ra. Không phụ thuộc FPS hoặc zoom preview.
- Trì hoãn bắt đầu, thời gian vào, thời gian giữ, thời gian ra, khoảng nghỉ giữa vòng, số lần lặp hoặc lặp đến hết đoạn.
- Linear, ease-in, ease-out, ease-in-out; hiển thị đường cong và cho xem thử.
- Độ phóng min/max, góc xoay min/max, opacity min/max; keyframe X/Y/scale/rotation/opacity.
- Giữ toàn đối tượng trong khung hoặc cho phép đi ra ngoài theo preset; tính cả kích thước/điểm neo khi nảy ở biên.
- Vùng tránh sub/logo khác; nếu không đủ không gian thì báo hoặc giữ vị trí đã đặt, không hứa tự giải mọi xung đột.
- Seed cố định/ngẫu nhiên mới; cùng chuyển động cho cả lô hoặc biến thể mỗi đầu ra.
- Keyframe có copy/paste, xóa, chuyển thời gian và undo; cho chọn thời gian tuyệt đối hoặc tỷ lệ thời lượng clip.
- Chuyển động không phải tracking chủ thể. Chưa có tự bám người/vật/chữ trong video gốc.

## 6. Vùng che chữ gốc

- Nhiều vùng độc lập: hình chữ nhật, chỉnh vị trí/kích thước trực tiếp, bo góc.
- Chọn blur, mosaic hoặc màu phủ; cường độ, màu, opacity và feather khi engine hỗ trợ.
- Thời gian bật/tắt, fade; keyframe vị trí/kích thước nếu cần di chuyển thủ công.
- Layer vùng che đặt dưới sub mới và trên video gốc theo mặc định; đổi thứ tự được.
- Vùng che có thể lưu trong preset theo tọa độ tương đối nhưng cần xem lại khi chữ gốc thay đổi vị trí.
- Là che/làm mờ, không phải xóa chữ tái tạo nền hoặc tự tracking.

## 7. Timeline và âm thanh

- Track video, vùng che, logo, chữ, sub và các track audio; đổi tên/màu/chiều cao track.
- Khóa, ẩn, mute/solo theo loại track; liên kết audio-video, nhóm đối tượng và chọn nhiều.
- Thước thời gian, playhead, thumbnail, waveform, marker, snap, zoom ngang, cuộn và fit toàn project.
- Kéo đổi vị trí/thời gian; trim mép; split tại playhead; gap và ripple-delete là hai thao tác khác nhau.
- Delete mặc định chỉ xóa đối tượng khỏi project hoặc danh sách, không xóa tệp trên ổ đĩa.
- In/out để xuất một đoạn; vòng lặp đoạn preview; nhảy đầu/cuối, từng frame và marker.
- Track sub có tìm câu và nhảy theo cue; âm thanh có nghe thử, mức âm, fade và điểm đặt sound effect.
- Hiện vùng clip thiếu media/thiếu sub, khoảng trống, cue chồng và thời điểm âm thanh bị cắt.
- Cache thumbnail/waveform theo nền; proxy Nhanh/Cân bằng/Cao; cho tạo lại proxy khi lỗi.
- Preview cùng mô hình thời gian, layer, kiểu chữ và biến đổi với export. Không dùng một hiệu ứng chỉ có trong preview rồi đánh dấu xuất được.

## 8. Công cụ phụ để giảm thao tác

- Kéo tệp/thư mục từ Explorer vào ứng dụng; drag nhiều mục; đánh dấu tệp không hỗ trợ.
- Tìm/lọc/sắp xếp media, folder, hàng đợi, cue; chọn tất cả/bỏ chọn/đảo chọn; tìm theo trạng thái.
- Menu chuột phải theo ngữ cảnh; mở thư mục chứa, mở kết quả, sao chép đường dẫn và lỗi.
- Tạo preset từ clip đang chỉnh; nhân bản preset; so sánh, nhập/xuất preset; kiểm tra phiên bản khi nhập.
- Copy/paste một nhóm thuộc tính, ví dụ chỉ font hoặc chỉ chuyển động, tránh thay cả cấu hình.
- Xem trước thay đổi hàng loạt, tên đầu ra, dung lượng ước tính, số video và cảnh báo trước khi chạy.
- Lưu project, tự lưu, khôi phục sau thoát bất thường; liên kết lại media bị di chuyển bằng thư mục gốc mới.
- Báo thiếu font, logo, nhạc, sub, codec, quyền ghi hoặc dung lượng; cho sửa liên kết thay vì tạo project lại.
- Làm thử một đầu ra hoặc một đoạn trước cả lô; mở video thử để xác nhận.
- Thông báo hoàn tất/lỗi, âm báo tùy chọn; đóng ứng dụng/tắt máy sau xong chỉ khi người dùng chủ động bật.
- HiDPI, cỡ chữ giao diện, theme sáng/tối, focus bàn phím, tên nút rõ; nhớ thư mục và bố cục gần dùng.

## 9. Phím tắt mặc định

Phím tắt tùy chỉnh được, có trang tra cứu/tìm kiếm, phát hiện xung đột và đặt lại. Phân phối theo vùng focus: lúc nhập văn bản không chạy phím điều khiển canvas/timeline. Thao tác phát toàn cục chỉ chạy khi không có ô nhập đang sửa.

| Phím | Thao tác | Phạm vi |
| --- | --- | --- |
| Ctrl+O | Mở project | Ứng dụng |
| Ctrl+, | Mở Cài đặt | Ứng dụng |
| F5 | Quét lại công cụ | Bảng công cụ, không áp sang Chrome |
| Ctrl+Shift+O | Thêm media/thư mục | Project |
| Ctrl+S / Ctrl+Shift+S | Lưu / lưu thành project mới | Project |
| Ctrl+Z / Ctrl+Shift+Z | Undo / redo | Editor, ô nhập có lịch sử riêng |
| Ctrl+C / Ctrl+V / Ctrl+X | Copy / paste / cut | Đối tượng hoặc văn bản theo focus |
| Ctrl+D | Nhân bản đối tượng | Canvas/timeline |
| Ctrl+A | Chọn tất cả trong vùng hiện tại | Danh sách/canvas/timeline/ô nhập |
| Delete | Bỏ đối tượng/mục chọn, không xóa tệp | Editor/danh sách |
| Esc | Hủy kéo/công cụ hoặc bỏ chọn | Editor |
| Space | Phát/dừng | Player, trừ lúc nhập chữ |
| Trái/phải | Lùi/tiến một frame khi dừng | Player/timeline |
| Shift+trái/phải | Lùi/tiến một giây | Player/timeline |
| Mũi tên | Dịch đối tượng một pixel đầu ra | Canvas khi đang chọn đối tượng |
| Shift+mũi tên | Dịch đối tượng mười pixel đầu ra | Canvas |
| Alt trong lúc kéo | Tạm tắt snap | Canvas/timeline |
| I / O | Đặt đầu/cuối vùng chọn | Player/timeline |
| Home / End | Đầu/cuối project | Player/timeline |
| Ctrl+B | Split clip tại playhead | Timeline |
| M | Thêm marker | Timeline |
| S | Bật/tắt snap | Timeline/canvas, ngoài chế độ nhập chữ |
| + / - | Zoom timeline | Timeline |
| Ctrl+con lăn | Zoom quanh playhead/con trỏ | Timeline hoặc preview theo focus |
| F | Fit preview | Preview |
| Ctrl+F | Tìm trong vùng hiện tại | Danh sách/sub/thiết lập |
| Ctrl+Enter | Đưa cấu hình vào hàng đợi | Editor, ngoài chế độ nhập chữ |
| F1 | Trợ giúp/phím tắt theo vùng | Ứng dụng |

Không gán phím đơn cho xóa tệp thật, tắt máy hoặc hủy hàng loạt. Hệ điều hành/IME có thể giữ một số tổ hợp; cho đổi phím.

## 10. Tự động hóa theo quy tắc

| Auto | Hành vi và giới hạn |
| --- | --- |
| Nhận diện link | Xác định bộ kết nối, loại URL, loại trùng; không coi mọi URL là kênh |
| Đồng bộ kênh | Tải nội dung mới theo lịch, lưu mốc và lịch sử quét |
| Nhận file mới | Theo dõi folder, chỉ nhận khi tệp đã ổn định/sao chép xong |
| Ghép sub | ID/ngôn ngữ/quy tắc tên; mơ hồ thì yêu cầu chọn, không đoán ngầm |
| Dịch sub | Theo ngôn ngữ đích, cache, thuật ngữ, khóa câu đã sửa và hạn mức |
| Bố trí chữ | Tự ngắt dòng/giảm cỡ trong giới hạn/vùng an toàn; cảnh báo khi không đủ chỗ |
| Đổi tỷ lệ | Fit/crop/nền theo preset và điểm neo; không tự nhận diện chủ thể ở bản đầu |
| Logo theo kênh | Bảng ánh xạ kênh→logo/preset; thiếu tài nguyên thì báo |
| Khớp âm thanh | Phân bổ cảnh, trim/tốc độ trong giới hạn, báo cấu hình bất khả thi |
| Chuyển động | Sinh biến thể trong khoảng/vùng, lưu seed, tôn trọng keyframe khóa |
| Tạo ma trận | Số lượng, lịch sử, chống lặp, cân bằng góc, giới hạn tìm và hủy được |
| Phần cứng | Kiểm tra encoder/filter, gợi ý số việc, quản lý RAM/VRAM/ổ đĩa |
| Chạy chuỗi | Tải→sub→dịch→edit→xuất; riêng theo lô hoặc cuốn chiếu |
| Thử lại | Chỉ lỗi tạm thời, giới hạn và backoff; lỗi tài khoản/cấu hình chờ xử lý |
| Kiểm tra đầu ra | Đọc media, đối chiếu track/thời lượng, phát hiện thiếu/hỏng; không thay bằng chỉ kiểm tra tồn tại tệp |
| Phục hồi | Giữ việc xong, tiếp tục công đoạn thiếu, ghi lý do phải render lại |
| Dọn cache | Theo tuổi/dung lượng, không xóa nguồn, đầu ra hoặc tệp đang dùng |

### Quyền ưu tiên giữa auto và thao tác tay

1. Thuộc tính khóa và chỉnh sửa riêng được giữ nguyên.
2. Auto chỉ cập nhật thuộc tính chưa bị ghi đè, trừ khi người dùng chọn đặt lại.
3. Có nút chạy lại auto theo nhóm: chỉ sub, chỉ bố cục, chỉ ma trận…
4. Xem trước danh sách tác động; tác vụ đã chạy giữ bản cấu hình riêng.
5. Mỗi quyết định tự động có thể xem lý do và tham số trong lịch sử.

## 11. Nghiệm thu editor

- Kéo/resize/xoay một logo, chữ, cue sub và vùng che; lưu/mở lại đúng; undo/redo đúng một thao tác kéo.
- Nhập tiếng Việt/Trung không kích hoạt phím tắt; thiếu font được báo và thay được.
- Cùng preset chạy trên video dọc/ngang và độ phân giải khác nhau không làm đối tượng mất khỏi khung ngoài ý muốn.
- Tốc độ chuyển động không đổi khi đổi zoom preview/FPS; vị trí tại các mốc so khớp render.
- Keyframe, lặp đi-về, fade, thứ tự layer và thời điểm xuất hiện đúng trên preview và export.
- Sửa một clip không thay cả lô; sửa cả lô không ghi đè thuộc tính đã khóa; chạy auto không mất chỉnh sửa tay.
- Phím mũi tên thực hiện đúng chức năng theo vùng focus; Delete không xóa tệp gốc.
- Preview có proxy/tải nền, UI phản hồi khi render; thao tác hủy không làm mất project.
- Các tùy chọn chưa triển khai không được gắn nhãn đã hoạt động. Phạm vi chưa hoàn tất được theo dõi trong kế hoạch, không âm thầm bỏ khỏi đặc tả.

## 12. Cài đặt công cụ và đăng nhập

Yêu cầu đầy đủ ở [SETTINGS_AND_BROWSER_SPEC.md](SETTINGS_AND_BROWSER_SPEC.md). Trong app có bảng quét/trỏ/tải-cài tool, hồ sơ Google Chrome thật và tài khoản theo nền tảng. Mỗi workflow có readiness tách công cụ/phiên/quyền nguồn và nút khắc phục đúng lỗi. Mở đăng nhập đưa người dùng sang đúng cửa sổ Chrome/hồ sơ, không thay bằng một khung WebView trong editor.
