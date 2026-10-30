# P10 — Kế hoạch thực thi bản làm lại

Revision: rebuild-2026-10-30. Các kết quả bên dưới phần lịch sử thuộc code cũ; không chuyển PASS sang bản mới.

## Điều kiện bắt đầu và kết thúc

- Đọc master, PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC, TECHNICAL_DESIGN và REBUILD_REVIEW trước khi thực hiện.
- Mỗi đầu việc cần input hợp lệ, output đọc lại được, test lỗi và kiểm tra không mất dữ liệu nguồn.
- Có thể triển khai phần độc lập trong khi gate live/Windows/GPU bị chặn; không nhận công nghệ phụ thuộc là đã kiểm chứng.
- Sau mỗi task: ghi commit, file thay đổi, lệnh test, version/toolchain, PASS/FAIL/NOT_RUN và giới hạn. Chỉ nghiệm thu khi toàn bộ tiêu chí bắt buộc đạt.
- Không sử dụng phần trăm dòng code. Tiến độ nghiệm thu = số task đạt / tổng task của phase.

## Danh mục 7 đầu việc

### P10-01

**Phạm vi:** DAG tải→sub→dịch→edit→render→validation theo lô/cuốn chiếu, công đoạn idempotent/trạng thái riêng.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUTO-01 (PR 2, 8): Tệp hợp lệ tiếp tục, lỗi riêng không treo cả chuỗi

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P10-02

**Phạm vi:** lịch đồng bộ/watcher đợi tệp ổn định/loại output, chống job trùng/chạy chồng, chính sách lịch bỏ lỡ; chạy khi app đóng cần chế độ nền/Windows Task Scheduler được bật rõ.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUTO-02 (ED 10): Không đọc tệp còn copy, không nhận output, lịch không chạy chồng

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P10-03

**Phạm vi:** kênh→logo/preset/output, auto layout có giới hạn, chạy lại riêng nhóm/giữ sửa tay/dry-run.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- BAT-04 (PR 5, 9): Xem tác động trước lô, retry riêng không làm lại việc xong
- AUTO-03 (ED 10): Khóa/sửa tay giữ nguyên, có dry-run và lý do

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P10-04

**Phạm vi:** CPU/RAM/GPU/VRAM/đĩa, Êm/Cân bằng/Tối đa, giới hạn riêng quét/tải/dịch/render/luồng mỗi việc.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUTO-04 (PR 8): Encode thật, unknown hiển thị đúng, fallback có log
- AUTO-05 (PR 8): Admission/backpressure đo được, không hứa số luồng chung

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P10-05

**Phạm vi:** benchmark gợi ý, giữ tài nguyên dự phòng/backpressure/giảm nhận việc, phục hồi có ngưỡng tránh dao động; encode khác filter GPU.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUTO-05 (PR 8): Admission/backpressure đo được, không hứa số luồng chung

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P10-06

**Phạm vi:** ETA/tốc độ/công đoạn/lô, ưu tiên/đổi job chờ/thông báo, hành động sau xong do người dùng bật, dọn cache an toàn.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUTO-06 (ED 8, 10): Không dọn tệp đang dùng/nguồn, tắt máy chỉ khi chủ động bật
- OPS-01 (PR 9): Không biết tổng không dựng phần trăm, ETA có trạng thái ước tính
- OPS-02 (PR 9): Ý nghĩa đúng, không hứa resume frame render

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P10-07

**Phạm vi:** preflight tool/Chrome/session/quyền nguồn, lease tool/profile và giới hạn theo account/domain; login lại đúng nick rồi resume, cập nhật tool không đụng job đang chạy, không dọn browser data như cache.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- TOL-06 (SB 2.3): Job cũ giữ binary cũ; activation xác thực receipt identity/managed path/hash/companion; rollback chặn executable ngoài root và ffprobe symlink; Settings cleanup chỉ gỡ bản không còn lease; per-tool busy guard chặn cập nhật trùng và thao tác xung đột. [CI 41080729485](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41080729485) PASS synthetic Linux/Windows; máy Windows người dùng, cross-process mutex và live install/update vẫn mở
- TOL-09 (SB 7): Thiếu tool/login/nguồn có hành động khác nhau, media cục bộ không bị chặn vô cớ
- AUTH-08 (SB 4.3–5): Dừng đúng job, relogin rồi resume, không tải trùng/đổi public ngầm
- AUTH-10 (SB 5): Cache/quyền A không dùng cho B, không giành user-data-dir
- AUTH-11 (SB 4–5, 8): Export không lộ session, cache cleanup không xóa profile, xóa dữ liệu có thao tác riêng

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

## Hồ sơ thực hiện trước rebuild (chỉ tham khảo)

# P10 — Kế hoạch chi tiết: độ an toàn automation và điều tiết tài nguyên

**Ngày:** 28/10/2026. **Nhánh:** `develop/fonesi-full`. **Trạng thái:** plan trước khi code.

## 1. Đối chiếu master

Đã đối chiếu `docs/IMPLEMENTATION_PLAN.md` P10-01…P10-07, PRODUCT_REQUIREMENTS, P10_RESULTS, IMPLEMENTATION_COVERAGE, `automation.py`, `jobs.py` và `tests/test_automation_dependencies.py`.

Hiện có watcher, lịch chạy persist, workflow tải→dịch→render, admission CPU/RAM/đĩa, công cụ versioned install và rollback. Cổng Windows Task Scheduler, máy người dùng, Chrome/driver/GPU, action sau hoàn tất, cache cleanup theo quota còn mở.

## 2. Lát cắt code độc lập

- **P10-04/P10-05:** `recommended_parallel` đang mặc nhiên dùng cấu hình `max` cho mọi profile không phải `quiet`/`balanced`. Từ chối profile sai, không ngầm tăng số worker khi cài đặt hỏng.
- **P10-04:** `update_gpu` phải đặt GPU về `unknown` khi nvidia-smi bị xóa/không chạy được; không hiển thị dữ liệu GPU thành công đã lỗi thời như trạng thái hiện tại.
- **P10-06:** vòng Automation currently ghi `str(exc)` trực tiếp vào `self.errors`; dùng bộ lọc bí mật đã kiểm chứng ở worker trước khi hiển thị/log.
- Test profile không hợp lệ, telemetry GPU bị lỗi/mất công cụ và thông báo lỗi chứa ký tự giả token/URL, giữ thông tin chẩn đoán không nhạy cảm.
- Chạy suite và packaged Linux/Windows, không kết luận GPU thật hay scheduler khi app đóng đã đạt.

## 3. Nghiệm thu

- [ ] Không tự suy diễn profile tài nguyên sai thành `max`.
- [ ] Khi mất telemetry, GPU trạng thái unknown chứ không giữ snapshot cũ.
- [ ] Lỗi automation không rò cookie/token/URL query vào giao diện hoặc log.
- [ ] Đủ test CI và không làm hồi quy các workflow hiện có.

**Ngoài phạm vi:** live Chrome/auth/installer, Windows Task Scheduler do người dùng bật, GPU/VRAM thực, soak dài hạn và mọi cổng release chưa có evidence. Giữ nguyên trong master plan.

## 4. Vòng P10-04/05 — Dọn cache theo hạn mức, bảo vệ file đang dùng

Rà master P10-04/P10-05, `REQUIREMENTS_TRACEABILITY.md` AUTO-04…AUTO-06, `PRODUCT_REQUIREMENTS.md` phần tài nguyên và `IMPLEMENTATION_COVERAGE.md`. Proxy local P04 được lưu tại `<app-data>/cache/proxies`. Hiện chưa có giới hạn dung lượng hoặc cơ chế dọn dẹp.

1. Lập chính sách FIFO/LRU đơn giản theo `mtime_ns` cho **file proxy hoàn chỉnh** trong đúng thư mục cache app, giới hạn bytes từ Settings (mặc định 4 GiB); không theo symlink, không quét subdirectories, không dọn media nguồn, output render, browser profile hay cache tool installer.
2. Dùng danh sách `protected` bảo vệ source QMediaPlayer đang phát. Nếu tổng protected > quota, ghi `over_budget` thay vì xóa file đang dùng; không xóa `.fonesi-proxy-*.` chưa publish.
3. UI Settings có `Giới hạn cache proxy (MiB)` và nút dọn bằng background; app định kỳ trigger khi rảnh và không có proxy/thumbnail đang tạo. Không thực hiện quét thư mục trên UI thread.
4. Test tmp cache (file cũ/mới, protected file, suffix khác, symlink, root symlink, quota quá nhỏ, idempotence), Settings/store, callback và lỗi quyền nếu có. CI Linux/Windows full suite, frozen proof. Ghi P10_RESULTS, coverage/status chỉ với evidence.
5. Chưa bao gồm quota cache downloader/translation, eviction đa máy hoặc Windows ACL/fault injection thật; giữ các cổng này mở.


### Kết quả lát cắt cache quota P10-04/05 (28/10/2026)

- [x] Eviction trong đúng cache proxy app, chỉ filename hash, không theo symlink/partial/foreign media.
- [x] Dọn old-first theo quota; active playback protected, báo quá quota nếu cần.
- [x] Settings persistent quota và manual/periodic background task, không khóa UI.
- [x] Full Linux/Windows CI + packaged proof [40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) PASS.
- [ ] GPU/VRAM thật, Task Scheduler, cache downloader/tool, Windows soak/installer/ACL còn mở.
