# Fonesi Edit — Hướng dẫn bản phát triển

Đây là bản phát triển desktop, không phải lời cam kết mọi mạng xã hội đã tải nguyên kênh được. Xem CURRENT_STATUS và bảng nền tảng cho phần đã thử/chưa thử.

## Chạy

Developer: `uv sync --locked` rồi `uv run fonesi-edit`. Bản đóng gói: mở FonesiEdit.exe (Windows) hoặc FonesiEdit (Linux proof). Dữ liệu app ở LocalAppData/FonesiEdit trên Windows; biến FONESI_DATA_DIR đổi vị trí khi kiểm thử. Không để dữ liệu runtime trong Git.

## Quy trình

1. Cài đặt → Công cụ: quét, chọn đường dẫn, cài thành phần thiếu hoặc rollback bản app quản lý. Nếu bản đã cài bị hỏng, nút cài tải bản sửa vào thư mục mới, giữ bản cũ. Tool thiếu không ngăn mở editor.
2. Editor: thêm video, chữ/logo/vùng che; kéo/resize/xoay, chỉnh inspector và keyframes. Ctrl/Shift và hộp chọn để chọn nhiều, menu Thao tác thêm có nhóm/căn/phân bố/ẩn/khóa/copy kiểu; double-click chữ để sửa. Double-click clip mở trim/speed/flip/rotation/âm gốc. Scope clip/chọn/cả lô được lưu vào layer. Đầu ra chọn tỷ lệ/FPS/CPU-GPU/màu; Âm thanh thêm main/music/SFX, mute/solo/trim/fade/loop và khớp duration. Đầu ra có thiết lập riêng cho clip tạo trong batch/ma trận, gồm trim đầu/đuôi, speed/flip/rotation/gain và random flip/rotation/zoom có seed.
3. Preview chất lượng xuất dùng compositor thật. Bấm Esc hoặc sửa thuộc tính để quay lại bố cục kéo thả; không chồng overlay lần hai lên frame đã composited. Thao tác thêm → Preview có âm thanh dựng bản phát từ cùng compositor. Playback nguồn vừa mở chưa bao gồm mọi thay đổi; sau khi sửa cần tạo lại bản dựng. Waveform tạo nền, không chặn UI.
4. Sub: mở SRT/VTT/ASS, sửa gốc/dịch/time/lock, dịch qua hàng đợi khi provider được cấu hình. Nạp kết quả là thao tác rõ ràng để giữ sửa tay; gắn sub vào clip hoặc xuất riêng. Bật Song ngữ để tạo riêng layer gốc và bản dịch khi hai nội dung đã có. Sub đã gắn thành layer kéo được trên preview, lưu bố cục vào preset; batch/ma trận tự ghép lại file sub của từng nguồn. Bảng sub có draft tự lưu, tìm/thay/offset và dịch câu chọn; nạp bản dịch giữ câu đã sửa hoặc khóa sau khi gửi.
5. Batch: chọn folder, quét, tick bỏ folder/tệp, lập kế hoạch, preview rồi enqueue. Không xóa nguồn; output nằm ở folder tên kênh kèm edit.
6. Ma trận: C1…Cn mỗi folder chứa góc, quét/sinh N/W/K/seed, sửa G1/G2 trong ô, khóa ô, preview/CSV/render. Không nới điều kiện ngầm; timeout khác vô nghiệm. Preview đổi tên C/G cho xem ánh xạ video/sub trước khi đổi thật, giữ bytes nguồn và lưu journal trong `.fonesi-renames` để hoàn tác/phục hồi. Queue còn dùng nguồn phải hoàn tất/hủy trước; liên kết project đang mở được cập nhật.
7. Tải: một URL mỗi dòng, folder, account/engine/media/limit/sub; 0 là không giới hạn ở adapter hỗ trợ. Kết quả quét không đồng nghĩa đã tải hết kênh. Có thể bật workflow edit/dịch sau tải hoặc đặt lịch scan-first chỉ tải media mới. Trong cây quét có thể tải media, bổ sung phụ đề, nâng chất lượng hoặc bấm **Đồng bộ mục mới (kết quả lọc)**.
8. Cài đặt → Tự động / máy: giới hạn tổng và riêng scan/download/render/translate; nút gợi ý theo CPU/RAM/đĩa hiện tại. Gợi ý không thay benchmark. Tài nguyên thấp chỉ dừng nhận thêm việc.
9. Hàng đợi: pause ngừng nhận việc mới; cancel dừng đúng job; retry riêng việc lỗi. Job dùng snapshot, sửa preset sau đó không đổi việc đang chạy.

## Đồng bộ mục mới và lịch chạy (bản phát triển)

Tab **Tải** → **Quét danh sách** → **Xem kết quả quét** → lọc/tìm → **Đồng bộ mục mới (kết quả lọc)**. Hệ thống xét tối đa **500 URL an toàn** trên mọi trang của bộ lọc, kiểm tra job cũ theo đúng URL/folder/adapter/tài khoản và kiểm tra lại file bằng FFprobe/QImageReader. File cũ mất/hỏng, job failed/canceled/blocked hoặc khác account sẽ **chặn toàn nhóm**; không xóa file, không tự chuyển về tài khoản public, và không ghi đè. Enqueue nguyên nhóm trong một transaction SQLite. Checkbox đang ẩn vẫn được giữ.

**Đặt lịch** quét trước với tối đa **200 item/cửa sổ**, hoặc 100 item mặc định nếu chọn limit 0; sau khi scan thành công mới kiểm tra lịch sử và xếp media mới. Kết quả chưa rõ/partial không đồng nghĩa hết kênh. Lịch cũ thiếu chế độ cũng được xử lý scan-first thay vì tải toàn kênh mỗi chu kỳ. Scan lỗi cần mở **Hàng đợi → Retry**; không tự chuyển tài khoản. App phải đang chạy/bật nền; chưa có Windows Task Scheduler khi app đã tắt. Quét nhiều trang provider thực và Chrome tài khoản thật vẫn chưa nghiệm thu.

## Chrome thật

Một profile dùng nhiều nền tảng; nhiều nick cùng nền tảng dùng profile khác. Tạo hồ sơ trong Cài đặt, mở login trong Google Chrome, người dùng tự nhập mật khẩu/OTP/QR/CAPTCHA. Đăng ký native host và load extension theo extension/README.md, ghép bằng mã 5 phút. Gửi phiên hoặc bật đồng bộ riêng từng nền tảng. Quên phiên chỉ xóa snapshot trong app; Thu hồi ghép extension ngăn extension gửi tiếp đến khi ghép mã mới. Windows DPAPI bảo vệ dữ liệu; không có plaintext fallback Linux.

Đăng nhập website, có snapshot cookie, danh tính và khả năng connector dùng phiên là các kiểm tra khác nhau. Không tắt Chrome protection hoặc coi HTTP 403 luôn là hết hạn. Tài khoản đổi nick bị phát hiện khi có danh tính đáng tin cậy; nền tảng khác vẫn hiển thị identity_unverified.

## Dịch và chi phí

Google hoặc LibreTranslate do bạn cấu hình. API key nhập ở Settings, không nằm trong project/preset; Windows lưu bằng DPAPI, Linux chỉ giữ trong bộ nhớ phiên. Có quota ký tự theo ngày và cache. Request timeout có thể chưa biết đã tính phí: không tự retry trả phí vô điều kiện. Giọng AI/ASR/OCR/tracking chưa thuộc bản này.

## Giới hạn và phục hồi

Thiếu sub mặc định tiếp tục có cảnh báo. Font thiếu glyph phải chọn font phù hợp. GPU phải encode thật được; Auto không có nghĩa mọi filter chạy GPU. Đóng app có thể hủy việc đang làm để lưu phục hồi; bật nền chỉ có tác dụng khi có system tray. Lịch chỉ chạy khi app/process đang hoạt động; không tự có Windows service.

Project tự lưu, có recovery và liên kết lại media. Menu Thao tác có nhập/xuất preset `.fonesipreset` theo schema; tài nguyên logo/font/audio tham chiếu đường dẫn, cần sao chép riêng nếu chuyển máy. Giữ nguồn, không overwrite output khác cấu hình; output hợp lệ cùng hash/config có thể tái sử dụng. Không xuất cookie/API key hoặc gửi dữ liệu hồ sơ Chrome vào báo lỗi.

## Phím tắt và kiểm chứng

Ctrl+S lưu project; Ctrl+Z/Ctrl+Shift+Z undo/redo; Ctrl+B chia clip; I/O đặt In/Out; Ctrl+G/Ctrl+Shift+G nhóm/bỏ nhóm; Ctrl+L khóa layer; M đặt marker; Space phát/dừng; Ctrl+, cài đặt; F5 quét công cụ; F1 hướng dẫn. Menu Thao tác cho đổi phím và kiểm tra trùng. Mũi tên/Shift+mũi tên trên canvas dịch 1/10 pixel; trên timeline đi 1 frame/1 giây. Alt tắt snap tạm, Ctrl+con lăn zoom. Delete chỉ bỏ layer khỏi project.

Developer có thể chạy `uv run fonesi-edit --verify .local/proof-new` và `uv run python scripts/verify_packaged.py` sau build. Chỉ dùng dữ liệu synthetic/localhost, không xác nhận tải mạng xã hội hay dịch live. Xem [đối chiếu triển khai](IMPLEMENTATION_COVERAGE.md) cho các tùy chọn còn mở.


## Preview In–Out, thumbnail và proxy (bản development)

Trong **Editor / preset**, đặt In bằng **I** và Out bằng **O**, rồi vào **Thao tác thêm → Lặp đoạn In–Out (preview đã render)**. Loop chỉ seek trong video dựng bằng compositor đúng composition hiện tại, không lặp trực tiếp theo timestamp file gốc khi clip có trim/speed. Sau khi chỉnh layer/clip cần dựng lại preview.

**Thao tác thêm → Thumbnail video trên timeline (tạo nền)**: bật/tắt bằng undo/save project; app tạo 3 PNG nguồn/clip đang nhìn thấy, dùng FFmpeg/cache background, không thay media. Đây là ảnh của video *nguồn*, không phải frame chứa hiệu ứng final.

**Thao tác thêm → Proxy nguồn**: chọn Không dùng / Nhanh (640px) / Cân bằng (1280px) / Cao (1920px). FFmpeg tạo MP4 H.264/AAC theo nguồn đang chọn trong cache per-user, validate trước khi dùng; video gốc và export final luôn giữ nguyên. Proxy chỉ tăng tốc phát **nguồn**, không phản ánh toàn bộ text/logo/sub; dùng nút **Preview có âm thanh** để kiểm tra composition đã dựng.

Trong **Cài đặt → Tự động / máy**, đặt **Giới hạn cache proxy (MiB)** (128–65536, mặc định 4096) và bấm **Dọn cache proxy an toàn** nếu muốn quét ngay. App dọn file proxy cũ chỉ có filename hash khi vượt quota; không xóa thư mục tải, nguồn, render output, media đang phát, hồ sơ Chrome hoặc tool. Cache downloader/dịch có phạm vi quản lý khác.

## Nâng chất lượng video đã tải (P05 development)

Trong tab **Tải**, quét video và tải bản gốc trước. Bản gốc phải có job tải **thành công**, thuộc adapter video yt-dlp, có file thực đọc được bằng FFprobe và còn nằm trong thư mục `NenTang/TenKenh__id/videos/`. Chọn lại đúng lần quét, đánh dấu video đã tải, chọn **Chất lượng tối đa** mong muốn (144–4320 pixel, cao hơn bản gốc) rồi bấm **Nâng chất lượng video đã tải**.

Ứng dụng xếp **job mới** vào Queue, giữ URL, folder, tài khoản và danh tính gốc. Không tự chuyển account, không tự sửa project, không tải lại phụ đề và không ghi đè video đã có. Video nâng cấp nằm ở `NenTang/TenKenh__id/quality-upgrades/<target>p/videos/`. Mỗi target/job nguồn được enqueue một lần cho cùng lần quét; muốn chạy lại job lỗi dùng Queue → Retry.

**Quan trọng:** mức trong UI là *chiều cao tối đa được yêu cầu*, không bảo đảm nguồn có đúng 720p/1080p/4K. Sau tải, FFprobe phải xác nhận chiều cao thực **cao hơn** video gốc và **không vượt** target; không đạt thì job báo lỗi, không công bố nâng cấp thành công. Không tự xóa file biến thể bị hỏng/không đủ chất lượng; kiểm tra thủ công trước khi xử lý. Các job có chất lượng live, mạng xã hội, tài khoản Chrome chưa có bằng chứng nghiệm thu đầy đủ.

Quét Batch hoặc watch tự động từ thư mục kênh sẽ **bỏ qua** thư mục `quality-upgrades` để không xử lý lặp. Nếu muốn edit bản nâng cấp, chủ động chọn chính tệp hoặc thư mục biến thể. Có thể nâng tiếp từ một biến thể đã được job và FFprobe xác minh nếu mức target mới lớn hơn trần biến thể nguồn; không ghi đè phiên bản trước. Chưa kiểm chứng live chất lượng trên toàn bộ 10 nền tảng và tài khoản thật.

## An toàn khi lưu và chỉnh phụ đề

Khi chọn **Thêm câu / Tách câu / Gộp câu chọn** trong tab **Phụ đề**, việc tách sẽ giữ nguyên mọi ký tự của cả **Bản gốc** lẫn **Bản dịch**, giữ khóa câu và chia mốc thời gian thành hai khoảng dương. Một cue quá ngắn hoặc không thể tách thành hai phần có chữ sẽ báo lỗi, không tự sinh dấu `…`. Khi gộp các cue liền nhau, cả hai ngôn ngữ được ghép theo đúng thứ tự; các câu được khóa vẫn giữ trạng thái khóa. Tab Phụ đề hiện có nút **Hoàn tác câu / Làm lại câu** và **Ctrl+Z / Ctrl+Shift+Z**: lưu tối đa 100 trạng thái chỉnh cue trong phiên, bao gồm text gốc/dịch, mốc thời gian nhập dở, khóa, thêm/tách/gộp/offset và nạp kết quả dịch. Hoàn tác không làm thay đổi lịch sử Undo của tab Editor; khi đang nhập văn bản vào QLineEdit hoặc combobox có thể nhập, phím tắt ưu tiên hoàn tác văn bản của ô đó. Sau Undo, bản nháp khôi phục cũng được lưu; sửa tiếp sẽ xóa nhánh Redo. **Lịch sử Undo không lưu xuyên lần đóng/mở ứng dụng**, mặc dù nội dung bản nháp vẫn được giữ; mở file sub khác sẽ bắt đầu lịch sử mới. Tab Phụ đề hiện có một thước thời gian cho **cue đang chọn**: kéo giữa để dịch toàn bộ câu, kéo mép để sửa điểm bắt đầu/kết thúc, nhấn **Esc** để hủy trước khi thả chuột. Một lần thả là một bước Hoàn tác câu; mốc thời gian ở đây là tuyệt đối theo file sub, không thay thế việc đối chiếu trim/speed trong bản render. Kéo nhiều cue cùng lúc vẫn chưa hỗ trợ.

Tệp phụ đề mới được ghi vào tên tạm rồi công bố nguyên tử: nếu lỗi ghi/đầy đĩa, sẽ không có tệp đích ghi dở. Không ghi đè tệp đã có khi tạo tự động; khi gắn sub vào clip, app kiểm tra lại **nội dung và thời gian từng câu** của các tệp source/target đã sinh trước đó. Nếu file đã được sửa ngoài app, không tự thay thế hoặc coi là đúng. Trên filesystem không hỗ trợ hard link cần thiết cho việc công bố không ghi đè, thao tác sẽ báo lỗi rõ ràng; chọn một thư mục phù hợp thay vì kỳ vọng app ghi tệp từng phần.

## Nhập ASS và cảnh báo định dạng

Khi dùng **Mở SRT/VTT/ASS** với phụ đề **ASS/SSA**, Fonesi Edit đọc văn bản/thời gian cue để chỉnh sửa, nhưng **không bảo đảm giữ nguyên style/font/vị trí/hiệu ứng/karaoke** của ASS trong bảng cue hoặc khi xuất lại. Cảnh báo hiển thị ở dưới bảng, giữ qua sửa câu/Undo và khi mở lại bản nháp; mở một file SRT thuần mới sẽ xóa cảnh báo cũ. Tệp ASS ban đầu không bị sửa khi chỉ nhập. Nếu cần giữ nguyên trình bày ASS gốc, hãy giữ và sử dụng tệp gốc hoặc kiểm tra kỹ bản xuất trước khi dùng.

## Đồng bộ phụ đề sau trim và thay đổi tốc độ

Khi render, cue từ tệp sub được cắt theo khoảng source đã chọn rồi ánh xạ sang thời gian output theo speed và vị trí clip (bao gồm vùng chồng khi chuyển cảnh). Cue **hoàn toàn ngoài** đoạn trim bị loại theo lựa chọn cắt; nếu một cue vẫn giao với đoạn giữ lại nhưng bị nén ngắn đến mức **không thể biểu diễn bằng 1 ms**, ứng dụng báo lỗi số cue thay vì xuất video thành công mà mất chữ. Hãy điều chỉnh thời điểm cue hoặc tốc độ của clip đó rồi chạy lại.

Phụ đề ASS ở bước ghép vào video có mốc thời gian **10 ms**, có thể làm tròn tối đa khoảng **5 ms** mỗi biên cue. Kiểm thử synthetic với hai clip/transition đã xác nhận logic này, không thay thế kiểm tra đồng bộ hình/âm thanh trên media VFR, rotation, dài hoặc máy Windows thực.
