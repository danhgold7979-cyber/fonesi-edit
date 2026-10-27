# Fonesi Edit — Đối chiếu yêu cầu với đầu việc và nghiệm thu

Bảng dưới lưu tiêu chí nghiệm thu và mapping của 95 nhóm yêu cầu, không phải bảng tất cả đã đạt. Code, bằng chứng local và các phần còn mở được cập nhật tại [đối chiếu triển khai](IMPLEMENTATION_COVERAGE.md) và [trạng thái](CURRENT_STATUS.md).

Nguồn: PR = [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md); ED = [EDITOR_SPEC.md](EDITOR_SPEC.md); SB = [SETTINGS_AND_BROWSER_SPEC.md](SETTINGS_AND_BROWSER_SPEC.md). Mã Pxx-yy tham chiếu [kế hoạch](IMPLEMENTATION_PLAN.md). Các hàng nhóm phải kiểm tra đủ thuộc tính trong section nguồn, không lấy một ví dụ qua là cả nhóm xong.

## 1. Nguồn tải và thư mục

| ID | Yêu cầu | Nguồn | Đầu việc | Bằng chứng đạt |
| --- | --- | --- | --- | --- |
| SRC-01 | Nhiều URL, nhận diện bài/kênh/playlist, loại trùng | PR 3.2 | P05-01 | URL cùng nguồn chuẩn hóa đúng ID, không coi bài là kênh |
| SRC-02 | Mọi nền tảng đã nêu, capabilities riêng | PR 3.1 | P02-02, P05-07 | Mỗi loại nguồn có trạng thái/evidence theo bảng nền tảng |
| SRC-03 | Quét kênh nhiều trang, checkpoint, dở/đủ/unknown | PR 3.2–3.3 | P05-02, P05-03 | Quét ngắt không bị báo toàn kênh xong |
| SRC-04 | Ảnh/video/cả hai, Shorts/Reels/album | PR 3 | P05-02 | Loại tải đúng checkbox, thứ tự bài nhiều ảnh đúng |
| SRC-05 | Ngày/số lượng/thời lượng/chất lượng/thứ tự | PR 3.2 | P05-02 | Dữ liệu biên được lọc đúng, tùy chọn nguồn thiếu được báo |
| SRC-06 | Đăng nhập, hết hạn, rate limit, retry/resume | PR 3.2 | P05-04 | Lỗi auth chờ đúng nguồn, retry giới hạn, không log bí mật |
| SRC-07 | Folder kênh có ID, Unicode, album và tên dài | PR 3.3 | P05-05 | Hai kênh trùng tên không nhập chung hoặc ghi đè |
| SRC-08 | Tệp tạm, validation, thiếu quyền/đĩa | PR 3.3 | P03-06, P05-04 | Tệp dở/hỏng không thành công, nguồn giữ nguyên |
| SRC-09 | Chống tải trùng, bổ sung sub, nâng chất lượng | PR 3.3 | P05-06 | Quét lại không tải dư; thiếu sub chỉ lấy sub khi phù hợp |
| SRC-10 | Đồng bộ mới, thumbnail/metadata nếu nguồn có | PR 3.2 | P05-02, P05-06 | Nội dung mới được thêm và phần không có ghi đúng |

## 2. Phụ đề và dịch

| ID | Yêu cầu | Nguồn | Đầu việc | Bằng chứng đạt |
| --- | --- | --- | --- | --- |
| SUB-01 | Chọn ngôn ngữ nguồn/đích/ưu tiên, nguồn sub | PR 4.1 | P06-02 | Chọn đúng ngôn ngữ và gắn nhãn sub tự động |
| SUB-02 | SRT/VTT/ASS và ghép đúng video | PR 4.2 | P06-01 | ID/tên mơ hồ không bị ghép nhầm; báo style thiếu |
| SUB-03 | Dịch Trung–Việt, ngữ cảnh/thuật ngữ/tên riêng | PR 4.1 | P02-03, P06-03 | Provider thật, ánh xạ cue đầy đủ, mẫu được đọc soát |
| SUB-04 | Bộ dịch thay được, quota/chi phí/retry/cache | PR 4.1 | P06-03 | Cache hit không gọi mới, giới hạn hoạt động, timeout không rõ được ghi |
| SUB-05 | Gốc/dịch song song, tìm/sửa/tách/gộp | PR 4 | P06-04 | Sửa đúng cue, undo/save/open giữ nội dung |
| SUB-06 | Khóa câu, dịch lại chọn lọc | PR 4.1 | P06-04 | Auto không đổi câu khóa; chỉ câu chọn được dịch lại |
| SUB-07 | Offset/time map theo trim/speed/ghép | PR 4.2 | P06-05, P08-06 | Cue theo đúng nguồn sau mọi phép biến đổi thời gian |
| SUB-08 | Tràn/chồng/ngắn/quá cuối, thiếu sub | PR 4.2 | P06-02, P06-05 | Báo đúng, không mất chữ, không chặn cả lô |
| SUB-09 | Đơn/song ngữ, màu/cỡ/vị trí riêng | PR 4.3; ED 3.3 | P06-06, P07-02 | Hai khối đúng thứ tự và có bật/tắt riêng |
| SUB-10 | Sub rời và burn-in cùng pipeline | PR 4.2 | P06-06, P07-08 | Tệp sub mở được, video phát ngoài vẫn thấy sub |

## 3. Editor, thuộc tính và preview

| ID | Yêu cầu | Nguồn | Đầu việc | Bằng chứng đạt |
| --- | --- | --- | --- | --- |
| ED-01 | Panel/Cơ bản–Nâng cao/tìm thiết lập/tooltip/reset | PR 2; ED 1 | P01-02, P04-01 | Mọi nhóm có nơi thao tác, đơn vị và lý do disabled |
| ED-02 | Kéo/resize/xoay/crop/neo/nhập số | ED 2 | P04-02 | Canvas/inspector cùng model, export cùng vị trí |
| ED-03 | Đa chọn/nhóm/khóa/ẩn/z-order | ED 2 | P04-03 | Đối tượng khóa không kéo nhầm, thứ tự layer đúng |
| ED-04 | Lưới/safe area/snap/Alt/căn/phân bố | ED 2.2 | P04-02, P04-03 | Căn theo canvas, zoom không đổi giá trị project |
| ED-05 | Undo/redo, double-click chữ, keyframe tại playhead | ED 1–2 | P04-04, P07-04 | Một drag một undo, nhập chữ không kích hoạt player |
| ED-06 | Font hệ thống/TTF/OTF/tìm/yêu thích/mẫu | ED 3.1 | P07-01 | Font chọn đọc đúng, có mẫu, không bắt cài toàn hệ thống |
| ED-07 | Font glyph/fallback/thiếu font và Unicode | ED 3.1 | P02-04, P07-01 | Việt/Trung đúng; thiếu font có cảnh báo/thay hàng loạt |
| ED-08 | Mọi thuộc tính chữ/viền/bóng/nền/khoảng cách | ED 3.2 | P07-02 | Đủ thuộc tính section, preview-export layout nhất quán |
| ED-09 | Chữ động, nhiều lớp, tràn và giới hạn cỡ | ED 3.2 | P07-02 | Placeholder thay đúng, không cắt chữ ngầm |
| ED-10 | Ngôn ngữ UI/sub/font tách riêng | ED 3.3 | P04-01, P06-02, P07-01 | Đổi ngôn ngữ không giả font/provider có hỗ trợ |
| ED-11 | Nhiều logo, alpha/size/opacity/lề/time/replace | ED 4 | P07-02 | Thay logo giữ biến đổi khi chọn, không mất alpha |
| ED-12 | Chuyển động và toàn bộ tham số speed/delay/repeat | ED 5 | P07-04, P07-05 | Chạy các preset/biên, speed không đổi vì FPS/zoom |
| ED-13 | Keyframe/easing/copy/timing tuyệt đối–tương đối | ED 5 | P07-04 | Giá trị tại mốc khớp export, undo/copy đúng |
| ED-14 | Random seed/khoảng/vùng/khóa/chống che nhau | ED 5.2 | P07-06 | Tái tạo với đủ snapshot, xung đột được báo |
| ED-15 | Nhiều blur/mosaic/màu, time và keyframe vùng che | ED 6 | P07-03, P07-04 | Vùng dưới sub mới, đúng thời gian và cường độ |
| ED-16 | Tỷ lệ/fit/crop/nền/màu/flip/rotate/speed | PR 5 | P07-07 | Dọc/ngang/rotation metadata không sai khung/time map |
| ED-17 | Track/trim/split/gap/ripple/marker/in-out/loop | ED 7 | P04-05 | Gap/ripple khác nhau, timeline save/open đúng |
| ED-18 | Proxy/waveform/thumbnail/seek/quality | ED 7 | P04-06 | Tạo nền/cancel được, đổi proxy không lệch thời gian |
| ED-19 | Phím tắt remap/xung đột/focus/IME | ED 9 | P04-07 | Đủ bảng phím, nhập chữ không kích hoạt lệnh khác |
| ED-20 | Preview-export và CPU/GPU capability | PR 8; ED 7 | P02-04, P02-05, P07-08 | Frame/time/audio trong dung sai, unsupported báo đúng |

## 4. Âm thanh và batch

| ID | Yêu cầu | Nguồn | Đầu việc | Bằng chứng đạt |
| --- | --- | --- | --- | --- |
| BAT-01 | Folder đệ quy/chọn/loại/tìm/lọc/đảo chọn | PR 5 | P08-01 | Không xóa folder, output/cache không bị nhận lại |
| BAT-02 | Một clip/nhiều clip/cả lô, preset/snapshot/khóa | PR 5; ED 10 | P01-04, P08-02 | Không thay job đang chạy hoặc sửa tay đã khóa |
| BAT-03 | Folder/tên output theo kênh, không đè | PR 3.3, 5 | P03-06, P08-02 | Đúng cây folder, input trùng tên không mất kết quả |
| BAT-04 | Chạy thử/dry-run/ước tính/tác vụ lỗi riêng | PR 5, 9 | P08-07, P10-03 | Xem tác động trước lô, retry riêng không làm lại việc xong |
| AUD-01 | Track gốc/chính/nền/SFX, gain/mute/solo | PR 6 | P08-03 | Track đúng vai trò, nghe solo/mute đúng |
| AUD-02 | Fade/trim/delay/meter/clipping/normalize | PR 6 | P08-03 | Mức âm và điểm vào/ra đúng, không clipping ngoài dự kiến |
| AUD-03 | Ghép audio cả lô/tên/list/random | PR 6 | P08-04 | Ánh xạ xác định, mơ hồ/thiếu audio được báo |
| AUD-04 | Lặp nhạc/crossfade/SFX theo cảnh/giây/tỷ lệ | PR 6 | P08-04, P08-06 | Đúng mốc và tổng duration, không lỗi ở biên cảnh |
| AUD-05 | Video/audio/nhập tay quyết định thời lượng | PR 6 | P08-05 | Đủ trường hợp ngắn/dài/không audio, không tự đổi mode |
| AUD-06 | Min/max speed/đoạn, loop/freeze/cut/giữ cao độ | PR 6 | P08-05 | Theo giới hạn hoặc báo bất khả thi, không kéo giọng quá mức |

## 5. Cảnh và ma trận

| ID | Yêu cầu | Nguồn | Đầu việc | Bằng chứng đạt |
| --- | --- | --- | --- | --- |
| MAT-01 | Cảnh/góc, natural sort, tên logic, ID ổn định | PR 7 | P09-01 | C2 trước C10, đổi tên không thành góc mới |
| MAT-02 | Đổi tên thật có preview/rollback, không tự đổi | PR 5, 7 | P09-01 | Xung đột được chặn, hoàn tác về tên cũ |
| MAT-03 | Tích tổ hợp và sinh lazy theo số lượng | PR 7 | P09-02, P09-03 | Tập nhỏ đúng số, tập lớn không cấp phát cả tích |
| MAT-04 | Không trùng/W/K/cân bằng/history | PR 7 | P09-02, P09-03 | Ràng buộc đúng, không nới ngầm, timeout khác vô nghiệm |
| MAT-05 | Sửa/khóa ô, tạo lại hàng, CSV/thống kê/preview | PR 7 | P09-04 | Sửa ô revalidate cửa sổ ảnh hưởng, chuỗi đúng asset |
| MAT-06 | Đủ/thứ tự cảnh, chia thời lượng nhiều cách | PR 7 | P09-05 | Đủ cảnh và audio fit hoặc báo lý do không khả thi |
| MAT-07 | Reservation/commit history, retry và seed | PR 7, 9 | P09-06 | Không hai worker dùng cùng tổ hợp bị cấm, failed không thành công giả |

## 6. Tự động hóa, độ bền và bàn giao

| ID | Yêu cầu | Nguồn | Đầu việc | Bằng chứng đạt |
| --- | --- | --- | --- | --- |
| AUTO-01 | Chuỗi theo lô/cuốn chiếu, chính sách lỗi | PR 2, 8 | P10-01 | Tệp hợp lệ tiếp tục, lỗi riêng không treo cả chuỗi |
| AUTO-02 | Lịch/watcher/file ổn định/chống vòng | ED 10 | P10-02 | Không đọc tệp còn copy, không nhận output, lịch không chạy chồng |
| AUTO-03 | Kênh→logo/preset, layout và chạy lại nhóm | ED 10 | P10-03 | Khóa/sửa tay giữ nguyên, có dry-run và lý do |
| AUTO-04 | CPU/GPU/Auto và metrics khả dụng | PR 8 | P02-05, P10-04 | Encode thật, unknown hiển thị đúng, fallback có log |
| AUTO-05 | Profile/gợi ý/giới hạn riêng/RAM-VRAM-đĩa | PR 8 | P10-04, P10-05 | Admission/backpressure đo được, không hứa số luồng chung |
| AUTO-06 | Cache/dọn an toàn/hành động sau xong | ED 8, 10 | P10-06 | Không dọn tệp đang dùng/nguồn, tắt máy chỉ khi chủ động bật |
| OPS-01 | Progress/ETA/tốc độ/công đoạn/thống kê | PR 9 | P03-04, P10-06 | Không biết tổng không dựng phần trăm, ETA có trạng thái ước tính |
| OPS-02 | Pause/cancel/retry/ưu tiên/đổi job chờ | PR 9 | P03-04, P10-06 | Ý nghĩa đúng, không hứa resume frame render |
| OPS-03 | Save/autosave/recovery/relink/migration | PR 9 | P03-02, P03-07 | Crash/mở lại giữ việc xong, thiếu asset relink được |
| OPS-04 | Snapshot/seed/version/provenance | PR 9 | P03-05, P09-06 | Truy vết được từng đầu ra, preset đổi không thay job cũ |
| OPS-05 | Worker ngoài UI, lỗi tách biệt, log chẩn đoán | PR 8–9 | P03-04, P11-02 | FFmpeg/worker lỗi không sập UI hoặc mất lô |
| OPS-06 | Output validation/atomic finalize/không đè | PR 3, 9 | P03-06, P07-08 | Exit lỗi/tệp hỏng/duration sai không báo thành công |
| OPS-07 | Preset import/export/copy nhóm/tài nguyên thiếu | ED 8 | P01-04, P08-02, P11-05 | Đủ công cụ phụ, version/thiếu tài nguyên được báo |
| OPS-08 | Menu/search/folder gần dùng/theme/HiDPI | ED 1, 8 | P04-01, P11-05 | Thao tác chuột/phím, ngữ cảnh và tỉ lệ màn hình dùng được |
| WIN-01 | Build tái lập, user data tách, không bộ dev | PR 11 | P02-06, P12-01 | App đóng gói chạy trên Windows mục tiêu |
| WIN-02 | Unicode/CPU-only/GPU/font/codec | PR 11 | P12-02, P12-03 | Workflow từ binary thật, không chỉ từ source |
| WIN-03 | Hướng dẫn/preset mẫu/version/giới hạn | PR 11 | P12-04, P12-06 | Người dùng chạy quy trình theo tài liệu, giới hạn rõ |
| WIN-04 | Update có xác minh/version/rollback | Kế hoạch | P12-05 | Cập nhật lỗi khôi phục được, project backup trước migration |

## 7. Các tình huống tích hợp phải kiểm tra

| ID | Tình huống | Phase kiểm tra chính |
| --- | --- | --- |
| FLOW-01 | Kênh có video+sub Việt → tải → chèn → edit → output | P05–P08, P11 |
| FLOW-02 | Bilibili có sub Trung → dịch Việt → che chữ → logo chuyển động → xuất | P06–P08, P11 |
| FLOW-03 | Kênh có video thiếu sub, sub lỗi và video hợp lệ trong cùng lô | P06, P10–P11 |
| FLOW-04 | Quét lại kênh đổi tên, tệp bị xóa/hỏng, thiếu sub cần bổ sung | P05, P11 |
| FLOW-05 | Nhiều folder kênh → loại vài folder → mỗi clip một đầu ra | P08, P11 |
| FLOW-06 | Âm thanh dài/ngắn hơn clip → đúng lựa chọn speed/cut/loop/freeze | P08, P11 |
| FLOW-07 | C1…Cn nhiều góc → W/K → đổi một ô → audio fit → render | P09, P11 |
| FLOW-08 | Quá số tổ hợp, W/K mâu thuẫn, solver timeout/cancel | P09, P11 |
| FLOW-09 | Kéo logo/chữ, keyframe, đổi zoom, nhập Việt/Trung, undo/save/open | P04, P07, P11 |
| FLOW-10 | Tác vụ đang chạy, sửa preset, khóa cue, chạy lại auto | P08–P11 |
| FLOW-11 | Crash app/worker giữa tải/dịch/render và mở lại | P03, P10–P11 |
| FLOW-12 | Provider timeout sau gửi, quota/rate limit/auth hết hạn | P06, P11 |
| FLOW-13 | Thiếu RAM/VRAM/đĩa/quyền ghi, watcher nhận tệp còn copy | P10–P11 |
| FLOW-14 | VFR/rotation/mixed FPS/no audio → phụ đề/keyframe/âm thanh khớp | P07–P08, P11 |
| FLOW-15 | Binary Windows, HiDPI/Unicode, không dev tools, nâng/rollback | P12 |
| FLOW-16 | Máy thiếu FFmpeg/downloader: scan→download/install→verify→chạy thật | P02–P04, P12 |
| FLOW-17 | Tool có sẵn, đường dẫn Unicode, sai version/capability hoặc đang dùng khi update | P03–P04, P11 |
| FLOW-18 | Tải installer ngắt/checksum lỗi/thiếu đĩa/quyền ghi; giữ bản cũ và rollback | P03, P11–P12 |
| FLOW-19 | Chrome A: Facebook A + TikTok A; Chrome B: Facebook B, tải bằng đúng ba binding | P02, P05, P11 |
| FLOW-20 | Đổi nick trong hồ sơ, mở lại app/máy, kiểm tra mismatch và phiên còn hợp lệ | P05, P11 |
| FLOW-21 | Chrome đang mở/bị khóa hoặc cookie bảo vệ khiến bridge không dùng được | P02, P05, P11 |
| FLOW-22 | Phiên hết hạn/OTP/CAPTCHA: chờ đúng nick, login thật, kiểm tra và resume | P05, P10–P11 |
| FLOW-23 | Export project/preset/log và dọn cache không lộ hoặc xóa dữ liệu phiên Chrome | P03, P10–P12 |

Bằng chứng hiện tại dùng media synthetic và HTTP localhost: xem [báo cáo local](LOCAL_VERIFICATION.md). FLOW có nguồn live/API/Chrome/GPU/Windows chỉ được đánh đạt sau thử đúng môi trường; test transport giả không thay bằng chứng dịch thật.

## 8. Tích hợp sau, không tính là thiếu của bản hiện tại

- Lồng tiếng AI/TTS, nhiều giọng và tách giọng/nhạc.
- ASR khi không có file sub; OCR chữ trong hình; tracking chữ/người/vật.
- Xóa chữ tái tạo nền bằng AI; nhận diện chủ thể để auto crop.
- Slideshow từ ảnh, edit ảnh hàng loạt, phát hành đa hệ điều hành.
- Tô karaoke từng từ khi chưa có word timestamps đáng tin cậy.

Mỗi mục sau này cần đặc tả và kiểm chứng riêng. Không gắn nút giả thành tính năng đã sẵn sàng.

## 9. Công cụ cần thiết và tài khoản Chrome — bổ sung 27/10/2026

Phần này thuộc phạm vi hiện tại, không phải phần tích hợp sau ở mục 8.

| ID | Yêu cầu | Nguồn | Đầu việc | Bằng chứng đạt |
| --- | --- | --- | --- | --- |
| TOL-01 | Bảng tool và quét nguồn phổ biến/tùy chỉnh | PR 13; SB 2.1 | P01-08, P04-08 | Hiện đường dẫn/version/vai trò/trạng thái, không chỉ tìm tên exe |
| TOL-02 | Trỏ đường dẫn, chọn bản, kiểm tra hoạt động | SB 2.1 | P02-09, P03-08 | Unicode/timeout/sai version/capability báo đúng, không sửa tool ngoài |
| TOL-03 | FFmpeg/ffprobe/downloader và dependency theo workflow | SB 2.2 | P02-09, P03-08 | Manifest đúng kiến trúc/phiên bản/capability, không bắt cài dev tools vô cớ |
| TOL-04 | Tải-cài thiếu, install-all, progress/cancel | SB 2 | P03-08, P04-08 | Nút chạy thật qua tải/xác minh/cài/kiểm tra; chưa xong không báo ready |
| TOL-05 | Trusted artifacts, TLS/checksum/chữ ký | SB 2.3 | P02-09, P03-08 | Artifact lỗi bị chặn, bản cũ và cấu hình được giữ |
| TOL-06 | Staging/repair/update/rollback và tool lease | SB 2.3 | P03-08, P10-07 | Job cũ giữ binary cũ, bản mới kích hoạt an toàn, rollback chạy được |
| TOL-07 | Chrome chính thức quét/trỏ/tải-cài | SB 2.2, 3 | P02-10, P04-08, P12-07 | Google Chrome thật, không WebView/Chromium giả thay thế |
| TOL-08 | Runtime/font/model/driver có điều kiện | SB 2.2 | P03-08, P12-07 | Chỉ thành phần cần được yêu cầu, driver không tự thay, API không tự tải model |
| TOL-09 | Readiness tool/phiên/quyền nguồn, nút sửa đúng lỗi | SB 7 | P04-08, P10-07 | Thiếu tool/login/nguồn có hành động khác nhau, media cục bộ không bị chặn vô cớ |
| AUTH-01 | Mọi nền tảng có trang đăng nhập và chọn binding | PR 13; SB 4.2 | P01-08, P04-08, P05-09 | Đủ nền tảng đã nêu, capability/auth chưa thử được ghi đúng |
| AUTH-02 | Chrome thật với user-data-dir riêng, nhiều nền tảng/một hồ sơ | SB 3 | P02-10, P05-08 | Profile A lưu nhiều phiên website, đóng/mở vẫn đúng khi còn hợp lệ |
| AUTH-03 | Nhiều nick cùng nền tảng ở hồ sơ khác nhau | SB 3 | P03-09, P05-08 | Facebook A/B không chia cookie, không nhầm nhiều cửa sổ là nhiều profile |
| AUTH-04 | Tạo/đặt tên/mở/gán/default/profile bận-khóa | SB 4.1 | P04-08, P05-08 | Mở đúng hồ sơ, không xóa lock/chiếm profile cá nhân |
| AUTH-05 | Login/kiểm tra/relogin qua Chrome, người dùng xử lý xác minh | SB 4.2 | P05-09 | Mật khẩu/OTP không lưu trong app, kiểm tra sau login thật |
| AUTH-06 | Session handoff tương thích Chrome/OS/connector | SB 6 | P02-10, P05-09 | Bộ tải dùng phiên thật; không tắt mã hóa hoặc coi web login là đã đạt |
| AUTH-07 | Job gán đúng account/profile, snapshot chỉ ref | SB 5 | P03-09, P05-10 | Nick chọn được giữ, project/job không chứa cookie/token |
| AUTH-08 | Expired/challenge/bridge lỗi/quyền nguồn tách biệt | SB 4.3–5 | P05-09, P10-07 | Dừng đúng job, relogin rồi resume, không tải trùng/đổi public ngầm |
| AUTH-09 | Đổi nick/mismatch, không xoay tài khoản tự động | SB 5 | P05-10, P11-08 | Job cũ không chạy bằng nick mới; rate limit không tự coi hết hạn |
| AUTH-10 | Account-scoped cache và profile concurrency | SB 5 | P03-09, P10-07 | Cache/quyền A không dùng cho B, không giành user-data-dir |
| AUTH-11 | Browser data riêng, export/dọn/xóa liên kết khác xóa profile | SB 4–5, 8 | P03-09, P10-07, P11-08 | Export không lộ session, cache cleanup không xóa profile, xóa dữ liệu có thao tác riêng |
