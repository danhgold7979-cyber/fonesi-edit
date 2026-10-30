# P02 — Kế hoạch thực thi bản làm lại

Revision: rebuild-2026-10-30. Các kết quả bên dưới phần lịch sử thuộc code cũ; không chuyển PASS sang bản mới.

## Điều kiện bắt đầu và kết thúc

- Đọc master, PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC, TECHNICAL_DESIGN và REBUILD_REVIEW trước khi thực hiện.
- Mỗi đầu việc cần input hợp lệ, output đọc lại được, test lỗi và kiểm tra không mất dữ liệu nguồn.
- Có thể triển khai phần độc lập trong khi gate live/Windows/GPU bị chặn; không nhận công nghệ phụ thuộc là đã kiểm chứng.
- Sau mỗi task: ghi commit, file thay đổi, lệnh test, version/toolchain, PASS/FAIL/NOT_RUN và giới hạn. Chỉ nghiệm thu khi toàn bộ tiêu chí bắt buộc đạt.
- Không sử dụng phần trăm dòng code. Tiến độ nghiệm thu = số task đạt / tổng task của phase.

## Danh mục 10 đầu việc

### P02-01

**Phạm vi:** ghi toolchain/máy/OS/codec/filter/encoder/font; lấy công cụ từ nguồn tin cậy, giữ TLS/checksum/chữ ký, pin sau kiểm chứng.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Khóa Python/Qt/Ruff/PyInstaller và CI tool versions. Còn mở: Corpus/codec/filter/font/target inventory đầy đủ. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P02-02

**Phạm vi:** thử yt-dlp/gallery-dl trên nguồn công khai và nguồn có cấu hình đăng nhập; quét nhiều trang, tải video/ảnh/sub theo bảng nền tảng.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SRC-02 (PR 3.1): Mỗi loại nguồn có trạng thái/evidence theo bảng nền tảng

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P02-03

**Phạm vi:** thử dịch Trung–Việt với thuật ngữ/tên riêng/câu dài; so chất lượng, tốc độ, chi phí, cache và quota.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SUB-03 (PR 4.1): Provider thật, ánh xạ cue đầy đủ, mẫu được đọc soát

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P02-04

**Phạm vi:** so engine preview cho Qt; mẫu alpha logo, chữ Việt/Trung, blur, seek, waveform, keyframe, audio; so mốc với FFmpeg export.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- ED-07 (ED 3.1): Việt/Trung đúng; thiếu font có cảnh báo/thay hàng loạt
- ED-20 (PR 8; ED 7): Frame/time/audio trong dung sai, unsupported báo đúng

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Qt khung đầu nguồn và mở UI thật. Còn mở: Preview layer/audio/seek và parity với export. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P02-05

**Phạm vi:** thử CPU/encoder GPU thật, phân biệt encode GPU và filter CPU; đo RAM/VRAM và fallback.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- ED-20 (PR 8; ED 7): Frame/time/audio trong dung sai, unsupported báo đúng
- AUTO-04 (PR 8): Encode thật, unknown hiển thị đúng, fallback có log

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Render CPU synthetic có decode/probe/hash. Còn mở: GPU/RAM/VRAM/fallback benchmark trên target. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P02-06

**Phạm vi:** bản đóng gói Windows thử: mở UI, media/font/sub, FFmpeg, Unicode, startup.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- WIN-01 (PR 11): App đóng gói chạy trên Windows mục tiêu

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. EXE Windows khởi động Editor/SRT/batch, 6 checks PASS. Còn mở: Installer/signing/media/font/Unicode/target-PC acceptance. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P02-07

**Phạm vi:** benchmark có máy/mẫu; chốt ngân sách UI/proxy/seek, sai số hình/thời gian và mức song song ban đầu trước P04/P07.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P02-08

**Phạm vi:** ghi quyết định provider dịch, preview, FFmpeg build, packaging; blocker cho Windows/nguồn chưa truy cập được.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Ghi candidate Qt/FFmpeg/PyInstaller và giới hạn proof. Còn mở: Provider/preview/full packaging decisions. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P02-09

**Phạm vi:** thử discovery/tool manifest, nguồn Windows đáng tin, đường dẫn tùy chỉnh/version/capability, tải-cài-verify và rollback khi job đang dùng bản cũ.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- TOL-02 (SB 2.1): Unicode/timeout/sai version/capability báo đúng, không sửa tool ngoài
- TOL-03 (SB 2.2): Manifest đúng kiến trúc/phiên bản/capability, không bắt cài dev tools vô cớ
- TOL-05 (SB 2.3): Artifact lỗi bị chặn, bản cũ và cấu hình được giữ

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P02-10

**Phạm vi:** Google Chrome chính thức trên Windows, hồ sơ độc lập, nhiều nền tảng/một hồ sơ và nhiều nick cùng nền tảng khác hồ sơ; kiểm chứng session handoff vào downloader với Chrome đang mở, mã hóa hiện tại và account mismatch.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- TOL-07 (SB 2.2, 3): Google Chrome thật, không WebView/Chromium giả thay thế
- AUTH-02 (SB 3): Profile A lưu nhiều phiên website, đóng/mở vẫn đúng khi còn hợp lệ
- AUTH-06 (SB 6): Bộ tải dùng phiên thật; không tắt mã hóa hoặc coi web login là đã đạt

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

## Hồ sơ thực hiện trước rebuild (chỉ tham khảo)

# P02 — Kế hoạch chi tiết kiểm chứng kỹ thuật và đóng gói

**Phiên bản kế hoạch:** 2.0 — 28/10/2026  
**Trạng thái trước khi code:** lập kế hoạch; chưa có thay đổi code trong phase này.  
**Nhánh làm việc:** `phase/p02-windows-packaged-proof`  
**Cơ sở:** `docs/IMPLEMENTATION_PLAN.md` v1.1, `docs/CURRENT_STATUS.md`, `docs/LOCAL_VERIFICATION.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/phases/P02_RESULTS.md`, và log/artifact GitHub Actions mới nhất.

## 1. Đối chiếu master plan và tình trạng thật

- Master plan xác định P02 là cổng kiểm chứng rủi ro về media, preview/render, nguồn tải, dịch, GPU và đóng gói Windows.
- P01 đã hoàn tất thiết kế (8/8 task được đánh dấu hoàn thành).
- Repository hiện đã có code và kết quả local cho các lát cắt P03–P12. Vì vậy, câu trong bản P02 plan cũ cho rằng P03 chưa được scaffold là giả định lịch sử, không còn phản ánh trạng thái repository hiện tại.
- Không xóa hoặc viết lại code P03–P12. P02 tiếp tục là cổng kỹ thuật độc lập; các cổng bên ngoài chưa thử được phải tiếp tục ghi BLOCKED/PENDING.
- Traceability có 95 nhóm yêu cầu, 95 ID duy nhất, mapping tới task và tiêu chí nghiệm thu. Master plan có 12 phase và 94 task ID duy nhất.
- Bằng chứng local hiện ghi 92 test pass và frozen proof Linux pass. CI gần nhất trên commit `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`: Linux pass; Windows build và test nguồn pass, nhưng `scripts/verify_packaged.py` fail vì job tải ảnh `gallery-dl` trong packaged proof kết thúc với `Gallery extractor could not complete; check source/session`. Hai job render và job tải video trong cùng proof thành công. Hiện chưa có log nguyên nhân đủ chi tiết để kết luận root cause.

## 2. Phạm vi triển khai của lát cắt này

### P02-06 — Sửa và kiểm chứng packaged proof trên Windows

1. Thêm chẩn đoán có kiểm soát cho lỗi extractor trong proof synthetic: ghi status và log lỗi liên quan vào `proof.json`, giới hạn số dòng/kích thước, không ghi cookie/token/API key hoặc dữ liệu hồ sơ.
2. Xác định nguyên nhân thực từ bằng chứng packaged Windows: extractor discovery/import, request tới loopback, tải file, validate ảnh hoặc đường dẫn đầu ra. Không đoán nguyên nhân và không vô hiệu hóa proxy/TLS hay kiểm tra an toàn toàn cục.
3. Sửa đúng lớp gây lỗi, giữ luồng download production và chính sách no-overwrite/validation. Không đổi bài proof để bỏ qua `gallery-dl`.
4. Bổ sung regression test phù hợp để lỗi có thông báo rõ ràng và proof không báo pass nếu thiếu ảnh hợp lệ.

### P02-08 — Quyết định kỹ thuật và bằng chứng

1. Cập nhật kết quả phase với commit SHA, workflow run, trạng thái từng hệ điều hành, test count và nguyên nhân lỗi.
2. Phân biệt rõ source tests, frozen Linux proof, frozen Windows proof, live platform, live translation, Chrome handoff và GPU.
3. Không đánh dấu toàn bộ P02 hoàn thành nếu cổng nguồn live, provider thật, Chrome/session handoff hoặc phần cứng vẫn thiếu bằng chứng theo acceptance criteria của master plan.

### P02-02 / P02-09 / P02-10 — Chỉ làm các nhánh độc lập có thể kiểm chứng

- Dùng localhost fixture để kiểm tra transport/adapters; không gọi nó là bằng chứng hỗ trợ mạng xã hội thật.
- Kiểm tra dependency được bundle và tool được phát hiện đúng; không dựa vào công cụ ngẫu nhiên trên PATH để tuyên bố ứng dụng đã tự chứa đầy đủ.
- Chrome thật, session handoff, nguồn live bị proxy chặn và GPU thật vẫn giữ BLOCKED nếu môi trường không cung cấp bằng chứng tương ứng.

## 3. Quy trình làm việc bắt buộc

1. Ghi kế hoạch này trước khi sửa source.
2. Chụp trạng thái ban đầu: main SHA, test/CI hiện có, blob SHA của file dự định sửa.
3. Thay đổi hẹp, có regression test; không sửa cùng một file song song.
4. Chạy `uv run python scripts/check_plan.py`, `uv run pytest -q` và packaged proof trên môi trường khả dụng.
5. Đẩy commit lên nhánh phase, mở PR để CI Linux/Windows chạy; đọc log/artifact, không coi build thành công là proof thành công.
6. Cập nhật `P02_RESULTS.md`, `CURRENT_STATUS.md` và master plan chỉ sau khi có kết quả thật. Không tự đánh dấu cổng bên ngoài là PASS.
7. Commit theo phase; giữ `main` nguyên trạng cho đến khi người dùng quyết định hợp nhất.

## 4. Tiêu chí nghiệm thu của lát cắt

- [ ] Lỗi packaged gallery download được tái hiện hoặc có chẩn đoán đủ rõ trong artifact.
- [ ] Regression test chứng minh ảnh tải qua loopback được tạo và validate; không làm yếu test.
- [ ] Toàn bộ source test pass trên CI.
- [ ] Frozen proof Linux pass.
- [ ] Frozen proof Windows pass; nếu vẫn fail, nguyên nhân và blocker phải được nêu bằng log cụ thể.
- [ ] `proof.json` phân biệt job pass/fail và không báo `passed=true` khi bất kỳ job bắt buộc nào thất bại.
- [ ] Master plan, phase results và status đồng nhất với bằng chứng.
- [ ] Live platform, live translation, Chrome authentication, GPU và nghiệm thu máy Windows người dùng không được đánh dấu pass chỉ nhờ fixture/CI.

## 5. Rủi ro và rollback

- **Rủi ro:** PyInstaller có thể xử lý dynamic imports khác source run; Windows có proxy/environment khác Linux; lỗi extractor bị che bởi packaged GUI không có stderr.
- **Giảm thiểu:** lưu diagnostic trong artifact synthetic, thêm test, so sánh source/frozen cùng fixture và không mở rộng bypass mạng.
- **Rollback:** revert commit của nhánh phase nếu regression; không force-push, không xóa code hiện hữu, không thay đổi main trong giai đoạn xác minh.

## 6. Ngoài phạm vi đóng P02

P02 không chứng minh mọi 95 nhóm yêu cầu đã hoàn tất. Chất lượng dịch live, quét nguyên kênh từng nền tảng, session handoff bằng Chrome thật, GPU/VRAM/driver, audio/HiDPI trên máy Windows, soak/crash/power-loss và các tương tác nâng cao tiếp tục cần bằng chứng riêng. Các phần độc lập trong P03–P12 vẫn được hoàn thiện theo phase plan của chúng, không được bỏ khỏi phạm vi chỉ vì P02 có blocker.
