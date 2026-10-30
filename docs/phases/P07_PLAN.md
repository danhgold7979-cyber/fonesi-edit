# P07 — Kế hoạch thực thi bản làm lại

Revision: rebuild-2026-10-30. Các kết quả bên dưới phần lịch sử thuộc code cũ; không chuyển PASS sang bản mới.

## Điều kiện bắt đầu và kết thúc

- Đọc master, PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC, TECHNICAL_DESIGN và REBUILD_REVIEW trước khi thực hiện.
- Mỗi đầu việc cần input hợp lệ, output đọc lại được, test lỗi và kiểm tra không mất dữ liệu nguồn.
- Có thể triển khai phần độc lập trong khi gate live/Windows/GPU bị chặn; không nhận công nghệ phụ thuộc là đã kiểm chứng.
- Sau mỗi task: ghi commit, file thay đổi, lệnh test, version/toolchain, PASS/FAIL/NOT_RUN và giới hạn. Chỉ nghiệm thu khi toàn bộ tiêu chí bắt buộc đạt.
- Không sử dụng phần trăm dòng code. Tiến độ nghiệm thu = số task đạt / tổng task của phase.

## Danh mục 8 đầu việc

### P07-01

**Phạm vi:** font hệ thống/TTF/OTF riêng, tìm/yêu thích/mẫu/fallback/glyph/thiếu font; cùng font/layout preview-render.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- ED-06 (ED 3.1): Font chọn đọc đúng, có mẫu, không bắt cài toàn hệ thống
- ED-07 (ED 3.1): Việt/Trung đúng; thiếu font có cảnh báo/thay hàng loạt
- ED-10 (ED 3.3): Đổi ngôn ngữ không giả font/provider có hỗ trợ

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P07-02

**Phạm vi:** chữ/viền/bóng/nền/padding/căn/giãn dòng/giãn chữ/ngắt dòng/nội dung động; nhiều logo, vị trí/lề/opacity/thời gian.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SUB-09 (PR 4.3; ED 3.3): Hai khối đúng thứ tự và có bật/tắt riêng
- ED-08 (ED 3.2): Đủ thuộc tính section, preview-export layout nhất quán
- ED-09 (ED 3.2): Placeholder thay đúng, không cắt chữ ngầm
- ED-11 (ED 4): Thay logo giữ biến đổi khi chọn, không mất alpha

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P07-03

**Phạm vi:** nhiều vùng blur/mosaic/màu, bo góc/cường độ/feather theo khả năng engine đã chứng minh; cảnh báo thuộc tính không khả dụng.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- ED-15 (ED 6): Vùng dưới sub mới, đúng thời gian và cường độ

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P07-04

**Phạm vi:** keyframe X/Y/scale/rotation/opacity, linear/easing, copy/paste, thời gian tuyệt đối/tương đối, playhead và undo.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- ED-05 (ED 1–2): Một drag một undo, nhập chữ không kích hoạt player
- ED-12 (ED 5): Chạy các preset/biên, speed không đổi vì FPS/zoom
- ED-13 (ED 5): Giá trị tại mốc khớp export, undo/copy đúng
- ED-15 (ED 6): Vùng dưới sub mới, đúng thời gian và cường độ

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P07-05

**Phạm vi:** chạy thẳng/chéo/A→B/nhiều điểm/qua góc/lặp/đi-về/nảy/zoom/xoay/fade; speed/duration/delay/hold/repeat/vùng.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- ED-12 (ED 5): Chạy các preset/biên, speed không đổi vì FPS/zoom

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P07-06

**Phạm vi:** random có seed/khoảng/xác suất, biến thể mỗi clip, vùng tránh/cảnh báo xung đột, giữ khóa tay.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- ED-14 (ED 5.2): Tái tạo với đủ snapshot, xung đột được báo

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P07-07

**Phạm vi:** fit/crop/nền/tỷ lệ/màu/flip/rotate/speed; thứ tự filter, time map sub, capability CPU/GPU.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- ED-16 (PR 5): Dọc/ngang/rotation metadata không sai khung/time map

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P07-08

**Phạm vi:** compiler từ model chung, đối chiếu frame, progress FFmpeg/cancel/validation; tối ưu một lần encode khi có thể, ghi lý do cần intermediate.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SUB-10 (PR 4.2): Tệp sub mở được, video phát ngoài vẫn thấy sub
- ED-20 (PR 8; ED 7): Frame/time/audio trong dung sai, unsupported báo đúng
- OPS-06 (PR 3, 9): Exit lỗi/tệp hỏng/duration sai không báo thành công

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

## Hồ sơ thực hiện trước rebuild (chỉ tham khảo)

# P07 — Kế hoạch chi tiết: xác thực đầu vào render và ổn định compositor

**Ngày kiểm tra:** 28/10/2026. **Nhánh duy nhất:** `develop/fonesi-full`. **Trạng thái:** lập kế hoạch trước khi sửa.

## 1. Đối chiếu master plan

Đã kiểm tra `docs/IMPLEMENTATION_PLAN.md` P07-01…P07-08, `docs/EDITOR_SPEC.md` (font/logo/layer/motion/render), `docs/TECHNICAL_DESIGN.md`, P07_RESULTS, coverage và source `domain.py`, `motion.py`, `render.py`, `tests/test_render_composition.py`.

Hiện có CPU compositor/FFmpeg thực, song ngữ, keyframes, alpha/masks, motion, audio, output validation và kiểm chứng Linux/Windows với media synthetic. Chưa thể công bố đầy đủ parity trên mọi style/fonts/OS/GPU.

## 2. Lát cắt mã hóa/kiểm thử

- **P07-07/P07-08:** kiểm tra đầu vào `Clip.volume` đang dùng phép so sánh khoảng mà không kiểm tra `NaN`. Với NaN, hai phép so sánh đều false và một giá trị âm lượng không hợp lệ có thể đi vào graph FFmpeg. Bổ sung `math.isfinite(volume)`.
- Ràng buộc kích thước output và FPS thực sự là số nguyên theo schema đã công bố; không để `True` hoặc float lọt qua validate để báo lỗi muộn trong FFmpeg.
- Tạo regression tests cho numeric edge cases, nhất là NaN, Infinity, FPS/canvas sai type; đảm bảo giá trị hợp lệ và các sample render hiện có không hồi quy.
- Không thay đổi công thức random motion, filter/encoder, output manifest hoặc đồ thị công việc khi chưa có test parity.

## 3. Nghiệm thu lát cắt

- [ ] Numeric validation từ chối NaN/Infinity và giá trị không hợp lệ trước khi gọi FFmpeg.
- [ ] Dữ liệu project hợp lệ round-trip giữ nguyên; không thay schema.
- [ ] Full source suite và packaged proof Windows/Linux PASS; cập nhật P07_RESULTS và trạng thái.
- [ ] Không gắn GPU/driver thực, font CJK thực/HiDPI, parity mọi tổ hợp keyframe, corpus dài là PASS vì CI synthetic.

## 4. Cổng còn mở

Font favorites/fallback per glyph, auto-fit text/nội dung động, copy motion, vùng tránh, random kiểu khóa nâng cao, crop có tay nắm, preview/export parity đầy đủ, 60fps/4K/long-form benchmark và GPU Windows thực cần tiếp tục theo traceability/coverage. Không chuyển bất kỳ yêu cầu đã thống nhất nào sang nhóm “sau” chỉ vì chưa code.
