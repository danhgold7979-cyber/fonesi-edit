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
