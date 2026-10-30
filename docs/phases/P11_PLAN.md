# P11 — Kế hoạch thực thi bản làm lại

Revision: rebuild-2026-10-30. Các kết quả bên dưới phần lịch sử thuộc code cũ; không chuyển PASS sang bản mới.

## Điều kiện bắt đầu và kết thúc

- Đọc master, PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC, TECHNICAL_DESIGN và REBUILD_REVIEW trước khi thực hiện.
- Mỗi đầu việc cần input hợp lệ, output đọc lại được, test lỗi và kiểm tra không mất dữ liệu nguồn.
- Có thể triển khai phần độc lập trong khi gate live/Windows/GPU bị chặn; không nhận công nghệ phụ thuộc là đã kiểm chứng.
- Sau mỗi task: ghi commit, file thay đổi, lệnh test, version/toolchain, PASS/FAIL/NOT_RUN và giới hạn. Chỉ nghiệm thu khi toàn bộ tiêu chí bắt buộc đạt.
- Không sử dụng phần trăm dòng code. Tiến độ nghiệm thu = số task đạt / tổng task của phase.

## Danh mục 8 đầu việc

### P11-01

**Phạm vi:** end-to-end các workflow/nguồn hỗ trợ; dọc/ngang/CFR/VFR/rotation/audio lệch hoặc không audio/sub sau speed-trim.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P11-02

**Phạm vi:** crash worker/app/mạng/auth/rate limit/quota/tệp hỏng/thiếu font-media/quyền ghi-đĩa đầy; retry/resume.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- OPS-05 (PR 8–9): FFmpeg/worker lỗi không sập UI hoặc mất lô

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P11-03

**Phạm vi:** lô lớn/nhiều layer/ma trận lớn/tải+render; đo UI/proxy/seek/RAM/VRAM/rò tài nguyên trên máy tham chiếu.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P11-04

**Phạm vi:** đối chiếu frame/sub/audio/duration theo dung sai; sửa nguyên nhân, không tắt kiểm tra để đạt.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P11-05

**Phạm vi:** rà mọi hàng truy vết, mọi tùy chọn/phím tắt/focus/HiDPI/theme/persistence/preset migration.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- OPS-07 (ED 8): Đủ công cụ phụ, version/thiếu tài nguyên được báo
- OPS-08 (ED 1, 8): Thao tác chuột/phím, ngữ cảnh và tỉ lệ màn hình dùng được

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P11-06

**Phạm vi:** nguồn có phiên bản/ngày/evidence, tách lỗi app/hạn chế nguồn/blocker cấu hình; không đóng mục chưa chạy thành công.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P11-07

**Phạm vi:** log/backup/cache/dependency, lỗi còn lại theo mức ảnh hưởng và cách khắc phục.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P11-08

**Phạm vi:** missing/wrong tools, installer ngắt/verify lỗi/quyền ghi/update bận; Chrome A nhiều nền tảng, Chrome B nick khác, phiên hết hạn/challenge/mismatch/lock/bridge không dùng được, export không chứa session.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- TOL-04 (SB 2, 2.3): Nút chạy thật qua tải/xác minh/cài/kiểm tra; chưa xong không báo ready; FFmpeg/ffprobe chung busy key, công cụ độc lập vẫn xếp hàng, install-missing bỏ qua thành phần đang bận. Qt regressions + [CI 41080729485](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41080729485) PASS synthetic Linux/Windows
- TOL-06 (SB 2.3): Job cũ giữ binary cũ; activation xác thực receipt identity/managed path/hash/companion; rollback chặn executable ngoài root và ffprobe symlink; Settings cleanup chỉ gỡ bản không còn lease; per-tool busy guard chặn cập nhật trùng và thao tác xung đột. [CI 41080729485](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41080729485) PASS synthetic Linux/Windows; máy Windows người dùng, cross-process mutex và live install/update vẫn mở
- AUTH-09 (SB 5): Job cũ không chạy bằng nick mới; rate limit không tự coi hết hạn
- AUTH-11 (SB 4–5, 8): Export không lộ session, cache cleanup không xóa profile, xóa dữ liệu có thao tác riêng

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

## Hồ sơ thực hiện trước rebuild (chỉ tham khảo)

# P11 — Tích hợp và hoàn thiện

Đã đọc master P11, tất cả phase plans/results local và 95 nhóm yêu cầu. Chỉ đạo tiếp tục không biến kiểm tra bên ngoài thành pass.

1. Chạy toàn bộ suite: Store/worker, editor, downloads/session, captions/translation, motion/render, batch/matrix/automation/tools.
2. Tạo app production thật đủ khu vực, save/autosave/preset, nguồn/job UI, sub editor, dry-run batch, matrix model virtualized, Settings tools/browser/provider/resources.
3. Integration UI→snapshot→worker→FFmpeg→artifact, mở lại project/queue; kiểm tra scope, shortcut không ăn IME, lỗi source/quota/no overwrite.
4. Rà bug time map, input hashing, cancel, app close, CLI/tool override và browser secret boundary; fix và chạy lại check bị ảnh hưởng.
5. Báo riêng implemented/local-tested/live-blocked/pending; không đánh dấu full Windows/platform/AI đã có. Lưu hiện vật/run summary và cập nhật traceability thực tế.

## Vòng rà soát tích hợp tiếp theo

Đối chiếu lại master P03–P12 trước sửa: ưu tiên đường dùng xuyên tab và kiểm chứng binary.

- P06-05/P07-08/P08-02/P09-06: sub là layer kéo được; bind lại đúng sidecar từng video trong batch/ma trận, map trim/speed/loop, chuỗi dịch cập nhật đúng tham chiếu; lưu bản nháp bảng sub.
- P03-04/P03-05/P09-03: khóa scheduler, migration có backup, kiểm tra W/K lần cuối trong transaction đặt chỗ, tên đầu ra theo thứ tự hàng và snapshot tool.
- P04-03/P04-05/P07-01: đa chọn/nhóm, căn chỉnh, clip inspector, ripple/in-out và audio timeline; giữ undo nguyên tử và font riêng trong canvas.
- P03-08/P10-04: repair cài bản mới cạnh bản hỏng, không thay tệp đang được job sử dụng; kiểm tra nguồn dịch không chứa bí mật trong URL.
- P12-01/P12-03: chạy batch + matrix thật qua worker binary; CI build production trên Linux/Windows và giữ evidence cụ thể. Cập nhật README/hướng dẫn/trạng thái theo kết quả thực.

Vòng công cụ phụ: import/export preset schema có kiểm tra, thu hồi pairing extension theo profile không xóa Chrome, giữ undo riêng của ô nhập khi phím tắt ứng dụng có focus. Đối chiếu OPS-07/AUTH-11/ED-19 trước đóng gói lại.


## Vòng P11 — Khóa tính toàn vẹn master và traceability (28/10/2026)

**Nhánh:** `develop/fonesi-full`. Đã đọc lại IMPLEMENTATION_PLAN, REQUIREMENTS_TRACEABILITY, IMPLEMENTATION_COVERAGE, CURRENT_STATUS và checklist các phase. Tổng thể có 12 phase, 94 task và 95 nhóm yêu cầu gốc.

**Lý do cần bổ sung:** `scripts/check_plan.py` hiện kiểm tra phase/order, duplicate ID và liên kết. Tuy nhiên, mất một yêu cầu khỏi traceability hoặc một hàng thiếu mapping/acceptance vẫn có thể không bị phát hiện nếu ID còn lại không trùng.

**Lát cắt P11-05/P11-07:**

1. Yêu cầu tất cả 95 nhóm có ID duy nhất và mapping ít nhất một task `Pxx-yy` có trong master.
2. Kiểm tra từng hàng có đầy đủ tên yêu cầu, nguồn, task và bằng chứng nghiệm thu; không chấp nhận ô rỗng hoặc placeholder.
3. Không ép `[x]` trên master; validator chỉ kiểm tra cấu trúc/yêu cầu, không tuyên bố 95 nhóm đã chạy pass.
4. Test kiểm tra đúng bộ tài liệu gốc và trường hợp thiếu một hàng/mapping/acceptance bằng fixture tạm.
5. Chạy source + packaged proof Linux/Windows; ghi P11_RESULTS kết quả thật và blocker ngoài fixture.

**Cổng mở:** nghiệm thu 95 nhóm theo UI/chức năng thực, Windows user/GPU/HiDPI/audio, Chrome login, live provider/nguồn, crash soak và benchmark corpus lớn vẫn chưa được xác nhận. Script validation không thay thế chúng.
