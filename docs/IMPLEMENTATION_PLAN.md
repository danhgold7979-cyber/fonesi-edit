# Fonesi Edit — Master clean rebuild

Revision: clean-2026-11-01. **P01 IN_PROGRESS; P02–P12 NOT_STARTED. Không kế thừa PASS cũ.**

## Baseline và quy tắc

Nguồn chuẩn: PRODUCT_REQUIREMENTS.md, EDITOR_SPEC.md, SETTINGS_AND_BROWSER_SPEC.md; 95 ID trong REQUIREMENTS_TRACEABILITY.md. 94 task dưới đây giữ ID và phạm vi gốc. Không bỏ tùy chọn qua cách đổi tên scope. TTS/ASR/OCR/tracking/slideshow/photo-edit không thuộc bản đầu; Chrome/tool distribution và cả mười nền tảng thuộc bản đầu. Dấu nhận diện hội thoại Edit: **vòng tròn đỏ**, không tự đổi branding app.

- Mỗi phase dùng đúng nhánh ngắn `phase-01` … `phase-12`, khởi từ checkpoint đã review; không force push, không xóa lịch sử main. Parent quản lý publish/reset/remote branches.
- Kế hoạch phải tồn tại trước code. Mỗi task có input/output/interface/errors/cancel/dependencies/tests/acceptance riêng; task chỉ READY khi đầy đủ. Scope catalog không phải executable plan.
- Trạng thái: NOT_STARTED, PLANNED, IN_PROGRESS, LOCAL_VERIFIED, BLOCKED_EXTERNAL, ACCEPTED, NEEDS_FIX. ACCEPTED cần tất cả tiêu chí, không chỉ test unit. Phase không qua gate khi requirement bắt buộc còn chặn.
- Có thể triển khai phần độc lập khi live/provider/Windows/GPU bị chặn, ghi chính xác dependency có thể tiến hành; không biến blocker thành feature removal.
- Sau thay đổi chạy affected tests; một aggregate owner tại checkpoint. Independent review trước nhận gate. Ghi SHA, command, OS/tool versions, corpus, kết quả PASS/FAIL/NOT_RUN/BLOCKED. Không chạy lại PASS không đổi chỉ để báo tiến độ.
- Không gọi API tính phí/login/đổi bảo vệ Chrome; chỉ cấu hình đã được cấp phép. Fixture không phải live evidence. Không mang code/test/package cũ vào source tree mới.

## Phase và dependency gates

| Phase | Kết quả | Phụ thuộc | Gate |
|---|---|---|---|
| P01 | Đặc tả, UX và hợp đồng | Yêu cầu gốc | 95 nhóm / 94 task được bảo toàn, đủ contract và tiêu chí trước code |
| P02 | Thực nghiệm và quyết định | P01 | Bằng chứng engine, nguồn, dịch, Chrome, GPU, Windows riêng theo môi trường |
| P03 | Nền ứng dụng và dữ liệu | P01; quyết định P02 liên quan | Migration, queue, publication, recovery, project và tool/profile registry |
| P04 | Workspace, preview, timeline | P03; preview P02 | Một model, undo, focus/IME, drag/cancel, save/open, tám vùng |
| P05 | Tải đa nền tảng | P03; connector/Chrome P02 | Mỗi capability được ghi hỗ trợ có live evidence và account identity |
| P06 | Phụ đề và dịch | P03; P05 khi tải sub | Cue import/export/time-map; provider thật và giữ sửa tay |
| P07 | Composition và render | P04/P06; parity P02 | Toàn bộ thuộc tính render được đối chiếu preview và lỗi unsupported rõ |
| P08 | Batch và audio | P06/P07 | Nhiều folder, audio playlist, duration, retry theo item; giữ nguồn |
| P09 | Ma trận | P08; storage P03 | W/K/history đúng, solver bounded và snapshot/retry không đổi hàng |
| P10 | Automation | P05–P09 | DAG, watcher/schedule, admission, backpressure, không loop/trùng |
| P11 | Độ bền và đủ phạm vi | P04–P10 | Từng subcriterion có evidence; crash/fault/scale/parity/resource gates |
| P12 | Windows và bàn giao | P11 và mọi release gate | Bản frozen trên Windows thật; tool/Chrome/source và tài liệu được kiểm chứng |

## Task catalog (94, unchanged IDs/scope)

### P01
- [ ] **P01-01**: đánh mã yêu cầu, tách phạm vi hiện tại/tích hợp sau; ghi mặc định và trường hợp lỗi.
- [ ] **P01-02**: wireframe tám khu vực, media/preview/inspector/timeline, Cơ bản/Nâng cao, trạng thái rỗng/đang làm/lỗi.
- [ ] **P01-03**: luồng thêm kênh, folder, âm thanh, chỉnh sub/logo, ma trận và hàng đợi; đếm thao tác đường dùng thường xuyên.
- [ ] **P01-04**: preset từng nhóm, một clip/nhiều clip/cả lô; thuộc tính khóa và ghi đè tay.
- [ ] **P01-05**: định nghĩa W/K, ưu tiên khớp âm thanh, thiếu sub, tên logic, trùng tên và tệp đã xử lý.
- [ ] **P01-06**: corpus media, nguồn thử, quyền truy cập/cấu hình cần, tiêu chí và phép đo preview/export.
- [ ] **P01-07**: hợp đồng project/preset/job, module và sổ quyết định cần thực nghiệm ở P02.
- [ ] **P01-08**: wireframe Cài đặt công cụ/hồ sơ Chrome/tài khoản mọi nền tảng, luồng scan→download/install→check, login→verify→use; readiness ba trục.

### P02
- [ ] **P02-01**: ghi toolchain/máy/OS/codec/filter/encoder/font; lấy công cụ từ nguồn tin cậy, giữ TLS/checksum/chữ ký, pin sau kiểm chứng.
- [ ] **P02-02**: thử yt-dlp/gallery-dl trên nguồn công khai và nguồn có cấu hình đăng nhập; quét nhiều trang, tải video/ảnh/sub theo bảng nền tảng.
- [ ] **P02-03**: thử dịch Trung–Việt với thuật ngữ/tên riêng/câu dài; so chất lượng, tốc độ, chi phí, cache và quota.
- [ ] **P02-04**: so engine preview cho Qt; mẫu alpha logo, chữ Việt/Trung, blur, seek, waveform, keyframe, audio; so mốc với FFmpeg export.
- [ ] **P02-05**: thử CPU/encoder GPU thật, phân biệt encode GPU và filter CPU; đo RAM/VRAM và fallback.
- [ ] **P02-06**: bản đóng gói Windows thử: mở UI, media/font/sub, FFmpeg, Unicode, startup.
- [ ] **P02-07**: benchmark có máy/mẫu; chốt ngân sách UI/proxy/seek, sai số hình/thời gian và mức song song ban đầu trước P04/P07.
- [ ] **P02-08**: ghi quyết định provider dịch, preview, FFmpeg build, packaging; blocker cho Windows/nguồn chưa truy cập được.
- [ ] **P02-09**: thử discovery/tool manifest, nguồn Windows đáng tin, đường dẫn tùy chỉnh/version/capability, tải-cài-verify và rollback khi job đang dùng bản cũ.
- [ ] **P02-10**: Google Chrome chính thức trên Windows, hồ sơ độc lập, nhiều nền tảng/một hồ sơ và nhiều nick cùng nền tảng khác hồ sơ; kiểm chứng session handoff vào downloader với Chrome đang mở, mã hóa hiện tại và account mismatch.

### P03
- [ ] **P03-01**: scaffold module, môi trường tái lập, dependency lock, config và user data tách khỏi thư mục chương trình.
- [ ] **P03-02**: schema/version/migration cho project/media/preset/job/artifact/history/cache; backup và phục hồi khi migration lỗi.
- [ ] **P03-03**: probe, ID/fingerprint, rational timestamp/time map; media không audio hoặc metadata lỗi.
- [ ] **P03-04**: scheduler/worker process, công đoạn/progress/cancel/pause/retry, quản lý tiến trình con trên Windows và lease phục hồi sau crash.
- [ ] **P03-05**: snapshot cấu hình/seed, log lọc bí mật, phân loại lỗi và UI hàng đợi đầu tiên.
- [ ] **P03-06**: output tạm → kiểm tra → tên cuối an toàn, không đè; truy vết nguồn; bỏ output/cache khi quét.
- [ ] **P03-07**: save/autosave/recovery, relink media, cache theo fingerprint/phiên bản; thử đóng bất thường có kiểm soát.
- [ ] **P03-08**: dependency registry/resolver, tool ownership/version/path/capabilities, trusted manifests, cài per-user, staging/self-test/activation/lease/rollback, không đè tool ngoài.
- [ ] **P03-09**: schema BrowserProfile/PlatformAccountBinding, profile ownership/browser state/auth state, credential refs và account-scoped cache; không lưu cookie/mật khẩu trong project.

### P04
- [ ] **P04-01**: panel/theme/HiDPI/cỡ chữ UI, drag từ Explorer, media/inspector, slider/ô số/reset.
- [ ] **P04-02**: chọn/kéo/resize/xoay logo/chữ/vùng che, crop; neo/tọa độ tương đối, lưới/safe area/snap/Alt và đưa về khung.
- [ ] **P04-03**: đa chọn/nhóm/khóa/ẩn/thứ tự layer; tránh kéo nhầm; menu ngữ cảnh.
- [ ] **P04-04**: undo/redo, một drag một lệnh; inspector và canvas dùng cùng model, save/open giữ đúng.
- [ ] **P04-05**: timeline/playhead/trim/split/in-out/gap/ripple/marker, thumbnail/waveform, zoom/scroll/loop.
- [ ] **P04-06**: proxy/cache tạo nền, đổi chất lượng/cancel/invalidation, seek đồng bộ audio/video.
- [ ] **P04-07**: shortcut theo focus, remap/xung đột/trợ giúp; nhập Việt/Trung không kích hoạt player/canvas.
- [ ] **P04-08**: UI Cài đặt tool scan/path/check/download/install-all/update/repair/rollback có progress; Chrome/profile/account tables, Ctrl+, và readiness với nút khắc phục đúng lỗi.

### P05
- [ ] **P05-01**: registry/capabilities, nhiều URL, bài/kênh/playlist, ID chuẩn và loại trùng.
- [ ] **P05-02**: phân trang/checkpoint, ảnh/video/Reels/Shorts/album khi nguồn hỗ trợ, lọc ngày/thời lượng/số lượng/chất lượng.
- [ ] **P05-03**: cây nội dung, chọn mục, tổng chưa biết/quét ngắt, cancel và tiếp tục khi hỗ trợ.
- [ ] **P05-04**: downloader/tệp tạm/validation, tốc độ/retry/rate limit/auth; không log cookie/token.
- [ ] **P05-05**: folder/kênh/album Unicode có ID, video/images/subtitles/metadata, thiếu đĩa/quyền ghi/tên dài/xung đột.
- [ ] **P05-06**: chống trùng theo ID/chất lượng/tệp hợp lệ; bổ sung sub riêng, tải lại tệp lỗi, đồng bộ lần hai và kênh đổi tên.
- [ ] **P05-07**: kiểm chứng nguồn/loại media/auth, lưu ngày/phiên bản/evidence. Thiếu quyền ghi blocker, không dùng mock để báo hỗ trợ.
- [ ] **P05-08**: profile manager mở Chrome thật vào đúng user-data-dir/nền tảng, tạo/đặt tên/gán nhiều nền tảng, tách nick cùng nền tảng, xử lý khóa/bận mà không phá profile.
- [ ] **P05-09**: session broker theo cơ chế đạt P02, đăng nhập/kiểm tra/đăng nhập lại cho mọi nền tảng, nhận diện nick, trạng thái website khác khả năng connector dùng phiên và quyền nguồn.
- [ ] **P05-10**: chọn account theo nguồn/job, nhớ mặc định, refresh cùng danh tính/resume, mismatch chặn đúng job; không silent fallback sang công khai hoặc tự xoay nick; auth cache không lẫn tài khoản.

### P06
- [ ] **P06-01**: SRT/VTT/ASS về cue chung, báo style chưa hỗ trợ; ghép bằng ID/ngôn ngữ/tên, báo mơ hồ.
- [ ] **P06-02**: nguồn/đích/ưu tiên, sub người đăng/tự động, chính sách thiếu sub và khác ngôn ngữ.
- [ ] **P06-03**: adapter dịch thật, thuật ngữ/xưng hô/tên riêng/ngữ cảnh, cache, chi phí/rate limit/retry.
- [ ] **P06-04**: gốc/dịch song song, sửa/tìm/thay/tách/gộp, dịch lại câu chọn, khóa câu đã sửa, lịch sử.
- [ ] **P06-05**: thời gian qua timeline/ô số, offset, kiểm tra chồng/tràn, time map sau trim/speed.
- [ ] **P06-06**: đơn/song ngữ, style cơ bản liên kết P07, xuất SRT/ASS và burn-in qua pipeline chung.

### P07
- [ ] **P07-01**: font hệ thống/TTF/OTF riêng, tìm/yêu thích/mẫu/fallback/glyph/thiếu font; cùng font/layout preview-render.
- [ ] **P07-02**: chữ/viền/bóng/nền/padding/căn/giãn dòng/giãn chữ/ngắt dòng/nội dung động; nhiều logo, vị trí/lề/opacity/thời gian.
- [ ] **P07-03**: nhiều vùng blur/mosaic/màu, bo góc/cường độ/feather theo khả năng engine đã chứng minh; cảnh báo thuộc tính không khả dụng.
- [ ] **P07-04**: keyframe X/Y/scale/rotation/opacity, linear/easing, copy/paste, thời gian tuyệt đối/tương đối, playhead và undo.
- [ ] **P07-05**: chạy thẳng/chéo/A→B/nhiều điểm/qua góc/lặp/đi-về/nảy/zoom/xoay/fade; speed/duration/delay/hold/repeat/vùng.
- [ ] **P07-06**: random có seed/khoảng/xác suất, biến thể mỗi clip, vùng tránh/cảnh báo xung đột, giữ khóa tay.
- [ ] **P07-07**: fit/crop/nền/tỷ lệ/màu/flip/rotate/speed; thứ tự filter, time map sub, capability CPU/GPU.
- [ ] **P07-08**: compiler từ model chung, đối chiếu frame, progress FFmpeg/cancel/validation; tối ưu một lần encode khi có thể, ghi lý do cần intermediate.

### P08
- [ ] **P08-01**: nhiều folder/đệ quy/checkbox/loại/đảo chọn/tìm/lọc, không xóa nguồn, không nhận output/cache.
- [ ] **P08-02**: preset/ghi đè clip/xem tác động/snapshot, output theo kênh/mẫu tên/phiên bản không đè.
- [ ] **P08-03**: tiếng gốc/âm chính/nhạc/SFX, mute/solo/gain/fade/trim/delay, meter/clipping/chuẩn hóa.
- [ ] **P08-04**: audio cả lô/theo tên/danh sách/random và playlist thủ công đa thư mục có preflight/snapshot/render verification; nhạc lặp chuyển tiếp; SFX theo giây/cảnh/tỷ lệ và trigger không đều; ducking theo chính sách hỗ trợ.
- [ ] **P08-05**: duration planner một hoặc nhiều clip; đích video/audio/nhập tay, min/max speed/đoạn, giữ cao độ, lặp/freeze/cắt theo lựa chọn.
- [ ] **P08-06**: tính chuyển cảnh/audio crossfade vào thời lượng, time map sub; báo bất khả thi, không tự bỏ cảnh/ghép clip ngoài chế độ.
- [ ] **P08-07**: chạy thử một video/đoạn, ước tính dung lượng/ETA, render lô/resume, kiểm tra duration/tracks/media.

### P09
- [ ] **P09-01**: quét C1…Cn/G1…Gm, natural sort/đổi thứ tự/khóa/loại, ID ổn định/tên logic; đổi tên thật có ánh xạ hoàn tác riêng.
- [ ] **P09-02**: tích tổ hợp/lọc/history dự án/hash góc/tổ hợp; phân biệt reservation và đầu ra thành công.
- [ ] **P09-03**: generator seed/không trùng/cân bằng/W/K, phạm vi so sánh, timeout/cancel, chưa tìm đủ khác bất khả thi.
- [ ] **P09-04**: bảng sửa/khóa ô/tạo lại hàng/preview/chuỗi C1G1+C2G2+…/thống kê/CSV; sửa hàng phải kiểm tra lại ràng buộc.
- [ ] **P09-05**: chia đều/tỷ lệ/trọng số/nhập tay, dùng duration planner P08, tính chuyển cảnh, giữ đủ/thứ tự.
- [ ] **P09-06**: render/validation theo hàng, snapshot nguồn/góc/preset/seed, commit lịch sử sau output hợp lệ, retry không sinh tổ hợp mới ngầm.

### P10
- [ ] **P10-01**: DAG tải→sub→dịch→edit→render→validation theo lô/cuốn chiếu, công đoạn idempotent/trạng thái riêng.
- [ ] **P10-02**: lịch đồng bộ/watcher đợi tệp ổn định/loại output, chống job trùng/chạy chồng, chính sách lịch bỏ lỡ; chạy khi app đóng cần chế độ nền/Windows Task Scheduler được bật rõ.
- [ ] **P10-03**: kênh→logo/preset/output, auto layout có giới hạn, chạy lại riêng nhóm/giữ sửa tay/dry-run.
- [ ] **P10-04**: CPU/RAM/GPU/VRAM/đĩa, Êm/Cân bằng/Tối đa, giới hạn riêng quét/tải/dịch/render/luồng mỗi việc.
- [ ] **P10-05**: benchmark gợi ý, giữ tài nguyên dự phòng/backpressure/giảm nhận việc, phục hồi có ngưỡng tránh dao động; encode khác filter GPU.
- [ ] **P10-06**: ETA/tốc độ/công đoạn/lô, ưu tiên/đổi job chờ/thông báo, hành động sau xong do người dùng bật, dọn cache an toàn.
- [ ] **P10-07**: preflight tool/Chrome/session/quyền nguồn, lease tool/profile và giới hạn theo account/domain; login lại đúng nick rồi resume, cập nhật tool không đụng job đang chạy, không dọn browser data như cache.

### P11
- [ ] **P11-01**: end-to-end các workflow/nguồn hỗ trợ; dọc/ngang/CFR/VFR/rotation/audio lệch hoặc không audio/sub sau speed-trim.
- [ ] **P11-02**: crash worker/app/mạng/auth/rate limit/quota/tệp hỏng/thiếu font-media/quyền ghi-đĩa đầy; retry/resume.
- [ ] **P11-03**: lô lớn/nhiều layer/ma trận lớn/tải+render; đo UI/proxy/seek/RAM/VRAM/rò tài nguyên trên máy tham chiếu.
- [ ] **P11-04**: đối chiếu frame/sub/audio/duration theo dung sai; sửa nguyên nhân, không tắt kiểm tra để đạt.
- [ ] **P11-05**: rà mọi hàng truy vết, mọi tùy chọn/phím tắt/focus/HiDPI/theme/persistence/preset migration.
- [ ] **P11-06**: nguồn có phiên bản/ngày/evidence, tách lỗi app/hạn chế nguồn/blocker cấu hình; không đóng mục chưa chạy thành công.
- [ ] **P11-07**: log/backup/cache/dependency, lỗi còn lại theo mức ảnh hưởng và cách khắc phục.
- [ ] **P11-08**: missing/wrong tools, installer ngắt/verify lỗi/quyền ghi/update bận; Chrome A nhiều nền tảng, Chrome B nick khác, phiên hết hạn/challenge/mismatch/lock/bridge không dùng được, export không chứa session.

### P12
- [ ] **P12-01**: đóng gói tái lập theo P02, FFmpeg/thư viện/font hợp lệ; chạy không cần bộ dev/admin nếu không thiết yếu.
- [ ] **P12-02**: phân biệt install/user data, Unicode/quyền ghi/antivirus thực tế, CPU-only và GPU phù hợp khi có.
- [ ] **P12-03**: chạy workflow từ bản đóng gói, save/open/crash/restart/migration/cấu hình thiếu, mở kết quả bằng player ngoài.
- [ ] **P12-04**: hướng dẫn Việt, preset mẫu, cấu hình dịch/phiên nguồn an toàn, phím tắt/chẩn đoán/báo lỗi.
- [ ] **P12-05**: cập nhật tool/adapter có version/xác minh/tương thích/rollback, backup trước đổi schema.
- [ ] **P12-06**: manifest, capabilities, máy thật, release notes/giới hạn, lưu bản phục hồi.
- [ ] **P12-07**: Windows mới thiếu dependency/Chrome: từ Cài đặt tải-cài-kiểm tra, mở Chrome thật/login, dùng phiên tải mẫu; tool ngoại không bị sửa, offline vẫn dùng media cục bộ, giới hạn auth được ghi đúng.

## Acceptance records

`requirements/tasks.json` is the task inventory, not acceptance evidence. `requirements/criteria.json` will expand the 95 groups into independently checkable source-backed subcriteria before P01 acceptance. `CURRENT_STATUS.md` is the sole current status. Old CI/reports remain only in external recovery archive. P01 contract/design acceptance does not certify application behavior.

## Release policy

No full-release claim until all mandatory requirement subcriteria pass on the claimed platform/provider. A limited internal build must explicitly list missing capabilities. Windows/GPU/Chrome/provider evidence cannot be replaced by Linux, mocked executables, screenshots, documentation, or import-only tests. Performance numbers are measured gates on declared hardware/corpus, never an invented universal promise. See contracts/VERIFICATION.md and decisions/ADR-0001.md.
