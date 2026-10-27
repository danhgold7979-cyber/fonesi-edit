# Fonesi Edit — Đặc tả sản phẩm

Trạng thái: đặc tả để lập kế hoạch và triển khai, chưa phải chức năng đã được code hoặc kiểm chứng. Cập nhật: 27/10/2026.

## 1. Mục tiêu và các quyết định đã thống nhất

- Ứng dụng desktop dùng cá nhân, Windows 10/11 trước, xử lý và lưu dữ liệu trên máy người dùng.
- Bốn nhóm chức năng: tải kênh; tải/dịch/chèn phụ đề; edit hàng loạt; ghép theo cảnh và ma trận.
- Ưu tiên tự động hóa theo preset, khả năng phục hồi và giao diện vẫn phản hồi khi chạy việc nặng.
- Tận dụng công cụ mã nguồn mở phù hợp; kiểm chứng từng thành phần trước khi chốt kiến trúc.
- Có phụ đề rời thì tải, dịch sang ngôn ngữ chọn và chèn vào video. Ngôn ngữ đích mặc định: tiếng Việt.
- Lồng tiếng AI, nhận diện giọng nói, OCR và tự bám chữ bằng tracking để tích hợp sau.
- Ảnh được tải và tổ chức thư mục; slideshow và edit ảnh hàng loạt nằm ngoài phạm vi bản đầu.
- Thao tác kéo thả trực tiếp trong preview và timeline là yêu cầu bắt buộc cho các đối tượng được hỗ trợ.
- Cài đặt có quét/trỏ đường dẫn/tải-cài/cập nhật công cụ; quản lý Google Chrome thật và phiên đăng nhập mọi nền tảng. Chi tiết ở [SETTINGS_AND_BROWSER_SPEC.md](SETTINGS_AND_BROWSER_SPEC.md).
- Mỗi yêu cầu dưới đây là phạm vi cần triển khai. Chỉ đánh dấu hoàn thành sau khi có bằng chứng nghiệm thu.

## 2. Giao diện và luồng công việc

Các khu vực: Tổng quan; Tải nội dung; Phụ đề; Edit hàng loạt; Ghép theo cảnh; Hàng đợi/Lịch sử; Preset/Cài đặt.

Luồng tự động: nguồn → quét → tải → kiểm tra tệp → chọn/tải sub → dịch nếu cần → áp dụng edit → render → kiểm tra đầu ra.

Hai cách chạy:

- Theo lô, mặc định: hoàn tất các mục tải của một kênh/lô, kể cả những mục đã kết thúc với lỗi, rồi xử lý các tệp hợp lệ.
- Cuốn chiếu: mỗi tệp tải xong và hợp lệ được đưa sang công đoạn tiếp theo, có giới hạn tài nguyên dùng chung.

Giao diện có chế độ Cơ bản/Nâng cao, tìm kiếm thiết lập, tooltip tiếng Việt, đơn vị rõ ràng, đặt lại từng nhóm và xem trước thay đổi. Tùy chọn không khả dụng phải ghi lý do.

## 3. Tải nội dung

### 3.1. Nguồn và bộ kết nối

Phạm vi mong muốn: YouTube (video/Shorts/playlist/kênh); TikTok; Facebook (page/profile/video/Reels/ảnh/album); Instagram; Threads; X; Bilibili; Douyin; Xiaohongshu; Kuaishou. Nền tảng Trung Quốc khác được thêm theo bộ kết nối riêng.

Không coi một website được thư viện liệt kê là đã đáp ứng tải toàn bộ kênh. Mỗi bộ kết nối phải có bảng khả năng riêng: quét profile, phân trang, video, ảnh, album, phụ đề, yêu cầu đăng nhập, đồng bộ và ngày kiểm chứng. Trạng thái: chưa kiểm chứng / có điều kiện / đã kiểm chứng / tạm lỗi.

### 3.2. Lựa chọn tải

- Nhập nhiều URL, nhập danh sách từ tệp, nhận diện nền tảng, kiểm tra URL trùng.
- Chọn ảnh/video/cả hai; video dài/Shorts/Reels nếu nguồn phân biệt được.
- Lọc ngày, số lượng, thời lượng, chất lượng tối đa; chọn thứ tự cũ trước/mới trước.
- Chọn độ phân giải/chất lượng có sẵn, giới hạn tốc độ, số tệp và số kênh đồng thời.
- Tải phụ đề, thumbnail và metadata nếu có; ghi rõ phần nào nguồn không cung cấp.
- Quét trước rồi chọn hoặc chạy theo preset; đặt lịch đồng bộ chỉ lấy nội dung mới.
- Tiếp tục tải khi nguồn hỗ trợ; thử lại có giới hạn và thời gian chờ tăng dần.
- Mọi nền tảng có mục đăng nhập qua Google Chrome thật; một hồ sơ chứa nhiều nền tảng, nhiều tài khoản cùng nền tảng dùng hồ sơ độc lập. Tái sử dụng phiên đã gán khi connector dùng được; hiển thị hết hạn/thiếu quyền/bridge lỗi riêng theo tài khoản.

### 3.3. Thư mục và tính toàn vẹn

```text
ThuMucDaChon/
  NenTang/
    TenKenh__source_id/
      videos/
      images/
      subtitles/
      metadata/
    TenKenh__source_id edit/
      videos/
      subtitles/
```

Có mẫu thay thế gom kết quả vào `Videos edit/TenKenh__source_id/`. Tên thư mục có thể tùy chỉnh, bao gồm tên tiếng Việt.

- Tên kênh có ID ổn định, không ghép nhầm kênh trùng tên hoặc kênh đổi tên.
- Tên tệp có ngày, tiêu đề rút gọn và ID; làm sạch ký tự và giới hạn đường dẫn trên Windows.
- Bài nhiều ảnh có số thứ tự; album giữ quan hệ với bài/album nguồn.
- Chống tải trùng bằng ID nguồn, kiểm tra tệp; hash bổ sung khi cần.
- Có thể chỉ tải bổ sung sub khi video đã có. Nâng chất lượng là yêu cầu tải mới được ghi nhận.
- Tệp đang tải dùng tên tạm, kiểm tra media trước khi công nhận hoàn thành.
- Giữ nguồn; không ghi đè đầu ra mặc định; bỏ qua output/cache/tệp tạm khi quét đệ quy.
- Báo riêng quét chưa hết, tải lỗi, thiếu quyền và hoàn tất. Không suy ra đã tải toàn bộ kênh từ một danh sách quét dở.

## 4. Tải, dịch và chèn phụ đề

### 4.1. Chọn và dịch

- Chọn ngôn ngữ nguồn tự động hoặc thủ công, ngôn ngữ đích, danh sách ngôn ngữ ưu tiên và biến thể vùng nếu bộ dịch hỗ trợ.
- Ưu tiên sub đúng ngôn ngữ đích; trong các bản phù hợp ưu tiên bản do người đăng cung cấp. Phụ đề tự động được gắn nhãn.
- Nếu chỉ có sub khác ngôn ngữ: dịch khi đã cấu hình bộ dịch; không tự chèn ngôn ngữ ngoài danh sách thay thế đã được cho phép.
- Nguồn/đích lựa chọn theo khả năng bộ dịch; dự kiến gồm Việt, Trung giản thể/phồn thể, Anh, Nhật, Hàn và các ngôn ngữ khác được hỗ trợ.
- Chọn mức dịch sát nghĩa/tự nhiên/ngắn gọn khi bộ dịch hỗ trợ; từ điển thuật ngữ, tên riêng, từ cần giữ nguyên, quy tắc xưng hô.
- Dịch có ngữ cảnh, giữ ánh xạ về câu và thời gian gốc; không hứa mọi câu dịch vừa thời lượng mà không kiểm tra.
- Xem bản gốc/bản dịch song song, sửa từng câu, tìm/thay thế, dịch lại câu chọn, khóa câu đã sửa.
- Cache theo nội dung, ngôn ngữ, bộ dịch/phiên bản và cấu hình; chỉ đổi font không dịch lại.
- Bộ dịch thay thế được; hỗ trợ xử lý giới hạn tốc độ, retry và lỗi từng lô. Không lưu khóa API trong project hoặc log.
- Nếu có dịch vụ tính phí: ước tính, đặt hạn mức, ngừng nhận việc dịch mới khi đạt hạn mức. Không tự gọi API khi chưa được cấu hình.

### 4.2. Tệp và thời gian

- Nhập SRT/VTT/ASS; chuyển về mô hình cue chung, giữ thông tin định dạng được hỗ trợ; báo rõ thuộc tính không hỗ trợ khi nhập.
- Ghép sub với video bằng ID nguồn, ngôn ngữ hoặc quy tắc tên tệp; trường hợp mơ hồ phải cho chọn.
- Sửa bắt đầu/kết thúc, kéo cue trên timeline, tách/gộp, dịch thời gian toàn bộ hoặc đoạn chọn.
- Kiểm tra chồng thời gian, thời lượng ngắn, câu dài và cue vượt cuối video; không tự sửa mất nội dung.
- Nếu video bị trim/đổi tốc độ, thời gian cue phải biến đổi theo cùng ánh xạ thời gian và bỏ phần ngoài đoạn xuất.
- Xuất sub rời SRT/ASS; mặc định đồng thời giữ sub và ghi sub vào hình khi xuất video.
- Không có sub phù hợp: mặc định tiếp tục edit và đánh dấu thiếu sub; tùy chọn bỏ video hoặc chờ bổ sung.
- Chữ đã nằm trong hình không được coi là file sub; không có tự ASR/OCR trong phạm vi này.

### 4.3. Trình bày phụ đề

Font và ngôn ngữ dùng chung bộ thuộc tính trong [EDITOR_SPEC.md](EDITOR_SPEC.md). Thêm lựa chọn một/hai ngôn ngữ; thứ tự hai dòng/khối; màu và cỡ riêng mỗi ngôn ngữ; tối đa dòng; chiều rộng; lề; tự ngắt dòng; vị trí trên/giữa/dưới; nền khối/nền theo dòng; xuất hiện/biến mất nhẹ.

Song ngữ và phụ đề dịch dùng các track liên kết, có thể bật/tắt riêng. Cảnh báo quá nhiều chữ. Hiệu ứng tô theo từng từ chỉ đưa vào sau khi có dữ liệu thời gian từng từ đáng tin cậy; không suy đoán thời gian rồi coi là khớp lời.

## 5. Edit hàng loạt

- Chọn một/nhiều thư mục; quét đệ quy; cây checkbox, tìm kiếm, lọc theo định dạng/thời lượng/độ phân giải; loại thư mục khỏi lô.
- Bỏ khỏi danh sách không xóa dữ liệu. Đổi tên tệp thật là công cụ riêng với xem trước, phát hiện xung đột và ánh xạ hoàn tác.
- Mỗi video một đầu ra là chế độ mặc định. Ghép nhiều clip theo âm thanh là chế độ riêng, không tự bật khi một clip quá ngắn.
- Thư mục đầu ra theo kênh, giữ quan hệ nguồn; xem trước tên/đường dẫn trước khi chạy.
- Áp dụng preset chung, chọn nhiều clip để áp dụng, hoặc ghi đè riêng từng clip. Tác vụ giữ bản cấu hình tại lúc thêm vào hàng đợi.
- Chọn tỷ lệ 9:16, 16:9, 1:1, 4:5 hoặc tùy chỉnh; fit/crop/nền mờ; xem vùng bị cắt.
- Cắt đầu/cuối, chọn đoạn, tốc độ cố định hoặc ngẫu nhiên trong khoảng cho phép; lật, xoay, zoom và dịch chuyển.
- Logo, chữ, vùng che và chuyển động theo đặc tả editor; xem thử trên nhiều video đại diện trước khi chạy lô.
- Điều chỉnh sáng, tương phản, bão hòa, gamma, nhiệt độ màu và preset màu với xem trước; không tự áp hiệu chỉnh ngoài preset.
- Ngẫu nhiên có khoảng giá trị, xác suất, giới hạn vùng và seed; cho chọn độc lập theo video hoặc dùng chung toàn lô.

## 6. Âm thanh và thời lượng

- Track riêng: tiếng gốc, âm thanh chính, nhạc nền, sound effect. Chưa có giọng AI.
- Tắt/giảm tiếng gốc; âm lượng, fade, trim, điểm bắt đầu, độ trễ và nghe solo/mute từng track.
- Một âm thanh cho cả lô, ghép theo tên, theo danh sách hoặc ngẫu nhiên từ danh sách; mặc định một âm thanh cho cả lô.
- Chọn nguồn quyết định thời lượng: video, âm thanh chính hoặc thời lượng nhập tay.
- Nhạc nền có lặp và chuyển tiếp, fade, mức âm lượng; giảm nhạc theo đoạn lời được đánh dấu hoặc bộ phát hiện tín hiệu âm thanh khi có hỗ trợ.
- Sound effect ở thời điểm tuyệt đối, đầu/cuối video, đầu/cuối cảnh hoặc tỷ lệ thời lượng; đặt nhiều lần trên timeline.
- Bảo vệ mức âm tổng, hiển thị clipping; tùy chọn chuẩn hóa âm lượng với mục tiêu được ghi rõ.
- Đổi tốc độ âm thanh có lựa chọn giữ cao độ. Không ngầm kéo giọng vượt giới hạn đã đặt.
- Một video quá ngắn: chọn tăng/giảm tốc trong giới hạn, lặp, giữ khung hình cuối, hoặc báo thiếu. Không tự lấy clip khác trong chế độ mỗi video một đầu ra.
- Nhiều clip: thứ tự tên/thời gian/ngẫu nhiên, thời lượng min/max mỗi đoạn, trim phần dư, giới hạn tốc độ, tính cả thời lượng chồng của chuyển cảnh.
- Đầu ra kiểm tra track cần thiết, thời lượng và đồng bộ theo dung sai được xác định ở bước thử nghiệm kỹ thuật.

## 7. Ghép cảnh và ma trận

- Quét thư mục cha chứa cảnh C1…Cn; mỗi cảnh có nhiều góc G1…Gm. Sắp xếp số tự nhiên; cho kéo đổi thứ tự và khóa cảnh/góc.
- C1 là cảnh 1, G1 là góc 1. Mặc định đặt tên logic, ánh xạ bằng ID tệp ổn định; giữ nguyên tên thật.
- Mỗi đầu ra lấy một góc hợp lệ từ mỗi cảnh, giữ đủ cảnh và đúng thứ tự trừ khi người dùng chọn quy tắc khác rõ ràng.
- Số tổ hợp lý thuyết là tích số góc hợp lệ từng cảnh; số khả thi còn phụ thuộc thời lượng và ràng buộc chống lặp.
- Chống trùng tổ hợp, cân bằng lượt sử dụng, cửa sổ W không lặp góc ở cùng cảnh, khác tối thiểu K cảnh.
- K có lựa chọn so với đầu ra liền trước hoặc mọi đầu ra trong cửa sổ W; ghi rõ điều kiện đang áp dụng.
- Chống trùng mặc định theo lịch sử cùng dự án; có lựa chọn lịch sử rộng hơn. Lịch sử phân biệt đã lên kế hoạch, đang chạy, thành công và thất bại.
- Không nới ràng buộc ngầm. Nếu mọi cảnh đều áp dụng cửa sổ W nghiêm ngặt thì mỗi cảnh cần ít nhất W+1 góc để sinh được một chuỗi dài hơn W; đây chưa phải điều kiện đủ khi còn ràng buộc khác.
- Sinh theo số lượng yêu cầu, không cấp phát toàn bộ tích tổ hợp lớn. Giới hạn thời gian tìm, cho hủy; phân biệt chưa tìm đủ với đã chứng minh không có nghiệm.
- Bảng ma trận: mã đầu ra, góc từng cảnh, chuỗi C1G1+C2G2+…, thời lượng, cấu hình âm thanh, seed, trạng thái, lỗi và đường dẫn.
- Sửa một ô/góc, khóa ô, tạo lại hàng chưa chạy, xem thử hàng, xuất CSV, thống kê tần suất dùng góc.
- Hash phát hiện tệp giống hệt; so sánh tương đồng nội dung là nâng cấp riêng. Biến đổi hình không bảo đảm nội dung hoàn toàn khác.
- Khớp âm thanh: chia đều, theo tỷ lệ, theo trọng số hoặc thời lượng cảnh nhập tay; ưu tiên giữ đủ cảnh, giới hạn tốc độ/cắt. Không khả thi phải báo, không tự bỏ cảnh.

## 8. Tự động hóa và tài nguyên

Chi tiết auto và thao tác ở [EDITOR_SPEC.md](EDITOR_SPEC.md). Quy tắc chung:

- Các bước auto là lựa chọn trong preset; có xem trước kế hoạch và chạy thử một đầu ra trước cả lô.
- Tôn trọng chỉnh sửa thủ công và khóa thuộc tính/câu/cảnh; không chạy auto ghi đè ngầm.
- Auto framing bản đầu theo tỷ lệ, điểm neo và vùng crop đã đặt; tự nhận diện chủ thể/khuôn mặt là phần mở rộng.
- Có CPU/GPU/Auto; kiểm tra khả năng decode, filter và encode riêng. GPU bắt buộc thì báo nếu không đáp ứng; Auto có thể fallback và ghi lý do.
- Giới hạn riêng số nguồn quét, tệp tải, tác vụ dịch, render và luồng mỗi render.
- Profile Êm máy/Cân bằng/Tối đa; gợi ý dựa trên benchmark và tải hiện tại.
- Theo dõi CPU, RAM, GPU/VRAM khi hỗ trợ, dung lượng ổ đĩa, tốc độ và nhiệt độ nếu đọc được.
- Giữ tài nguyên dự phòng, hạn chế việc đồng thời khi thiếu RAM/VRAM, ngừng nhận việc mới khi thiếu ổ đĩa.
- Tải/render/đọc metadata chạy ngoài luồng UI; lỗi một worker không làm mất hàng đợi.

## 9. Hàng đợi, trạng thái và phục hồi

- Trạng thái: chờ, đang quét, tải, dịch, render, kiểm tra, tạm dừng, chờ cấu hình, thành công, thành công có cảnh báo, lỗi, hủy, bỏ qua.
- Có tiến độ từng bước và toàn tác vụ, thời gian đã chạy, ETA, tốc độ, số xong/lỗi/bỏ qua. Chưa biết tổng thì hiển thị số đã tìm được, không dựng phần trăm giả.
- Tạm dừng hàng đợi ngừng nhận việc mới. Hủy tác vụ xử lý riêng tệp dang dở. Render có thể phải chạy lại công đoạn từ đầu.
- Lưu trạng thái bền vững; khởi động lại giữ việc đã xong và chỉ lên lịch phần cần làm. Thử lại lỗi không làm lại toàn bộ lô.
- Chọn ưu tiên, di chuyển tác vụ chưa chạy, lọc/tìm lỗi, mở nguồn/kết quả, sao chép thông báo lỗi.
- Khi cấu hình thay đổi, lưu phiên bản mới; cập nhật các tác vụ đang chờ là thao tác riêng.
- Lưu bản cấu hình, seed, phiên bản công cụ, nguồn và danh sách clip cho mỗi đầu ra; không chứa bí mật.
- Tự lưu project, bản phục hồi, liên kết lại media bị di chuyển, sao lưu preset và project.
- Cache thumbnail/waveform/proxy/dịch có dung lượng giới hạn và dọn theo chính sách; không xóa nguồn hoặc đầu ra người dùng.

## 10. Mặc định vận hành

| Thiết lập | Mặc định |
| --- | --- |
| Giao diện | Tiếng Việt, cho phép mở rộng ngôn ngữ giao diện riêng với ngôn ngữ sub |
| Phụ đề đích | Tiếng Việt |
| Thiếu sub | Tiếp tục edit, ghi cảnh báo |
| Đầu ra | MP4 H.264/AAC tương thích rộng; codec/chất lượng/FPS có thể đổi |
| Video gốc | Giữ nguyên |
| Đầu ra trùng | Không ghi đè; so cấu hình để bỏ qua hoặc tạo phiên bản |
| Edit hàng loạt | Mỗi video một đầu ra |
| Ma trận | Không trùng tổ hợp, cân bằng lượt dùng, lưu lịch sử dự án |
| Phần cứng | Auto, profile Cân bằng; số việc được đo trước khi gợi ý |
| Tự động hóa | Chỉ các bước bật trong preset; giữ ghi đè thủ công |

## 11. Điều kiện hoàn thành

- Tải được các loại nội dung đã ghi là hỗ trợ trên nguồn kiểm chứng; báo đúng mục thiếu/lỗi và quét chưa hết.
- Tải/dịch/chèn sub đúng video và ngôn ngữ; thời gian khớp sau trim/đổi tốc độ.
- Preview và export thống nhất vị trí, thời gian, font, chuyển động và âm thanh trong dung sai đã đo.
- Edit hàng loạt đúng phạm vi; kết quả không bị quét vào lại; dữ liệu nguồn được giữ nguyên.
- Ma trận đúng thứ tự, đủ cảnh và đúng điều kiện chống trùng; không ngầm thay điều kiện.
- Tác vụ có progress/thời gian, UI phản hồi, lỗi riêng lẻ không làm mất lô, mở lại tiếp tục được.
- Thử với video dọc/ngang, nhiều FPS/codec, có/không audio, Unicode Việt/Trung, tệp lỗi, tên trùng và thư mục lớn.
- Windows là hệ điều hành mục tiêu: kết quả chạy trong cloud/Linux không thay thế nghiệm thu trên Windows.

## 12. Những quyết định kỹ thuật cần thực nghiệm

- Bộ kết nối và mức hỗ trợ thực tế của từng nền tảng.
- Bộ dịch, chất lượng Trung–Việt, chi phí/giới hạn và cấu hình cần thiết.
- Engine preview/timeline/render, font shaping, codec và encoder phần cứng.
- Cấu hình máy mục tiêu, giới hạn song song và dung sai nghiệm thu.

Các mục này được giải quyết trong giai đoạn kiểm chứng đầu tiên của [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), không coi là đã hoạt động khi mới có đặc tả.

## 13. Cài đặt công cụ và tài khoản Chrome

- Bảng công cụ có vai trò, bắt buộc/tùy chọn, đường dẫn, version, trạng thái, nguồn bản cài, nút quét/chọn đường dẫn/kiểm tra/tải-cài/cập nhật/sửa/rollback.
- Quét công cụ gói kèm, app quản lý, PATH và vị trí phổ biến; không chỉ kiểm tra tồn tại file. FFmpeg/ffprobe, downloader và dependency theo workflow được kiểm tra capability.
- Thiếu thành phần có nút tải/cài từ nguồn tin cậy, xác minh, progress và kiểm tra lại; ưu tiên cài per-user, không đè bản hệ thống hoặc đổi binary đang dùng.
- Google Chrome chính thức được tìm/trỏ/tải-cài tương tự. Một bản Chrome có nhiều hồ sơ user-data-dir độc lập; mặc định app quản lý hồ sơ riêng, không chiếm hồ sơ cá nhân.
- Mỗi nền tảng đều có nút đăng nhập, chọn hồ sơ/tài khoản mặc định, kiểm tra, đăng nhập lại; người dùng thao tác mật khẩu/OTP/QR/xác minh trong Chrome.
- Một hồ sơ có thể dùng Facebook A + TikTok A + YouTube A; Facebook B dùng hồ sơ khác. Nhiều page/kênh dưới cùng danh tính không bắt tạo Chrome mới.
- Nguồn/job nhớ account binding; đăng nhập lại cùng nick rồi tiếp tục. Đổi nick trong hồ sơ phải phát hiện mismatch, không tự dùng nick mới cho job cũ.
- Tải công khai vẫn được nếu chưa gán tài khoản và nguồn cho phép. Job đã chọn tài khoản hết hạn thì chờ đúng tài khoản, không tự giảm sang quét công khai.
- Đăng nhập website, connector dùng phiên và quyền xem nguồn là ba kiểm tra riêng. Không cam kết đọc được cookie Chrome chỉ vì đã đăng nhập, không tắt bảo vệ mã hóa để làm cho chạy.
- Chi tiết schema, nút và nghiệm thu: [SETTINGS_AND_BROWSER_SPEC.md](SETTINGS_AND_BROWSER_SPEC.md). Phần này thuộc bản hiện tại, không đẩy sang danh sách AI tích hợp sau.
