# P03 — Kế hoạch thực thi bản làm lại

Revision: rebuild-2026-10-30. Các kết quả bên dưới phần lịch sử thuộc code cũ; không chuyển PASS sang bản mới.

## Điều kiện bắt đầu và kết thúc

- Đọc master, PRODUCT_REQUIREMENTS, EDITOR_SPEC, SETTINGS_AND_BROWSER_SPEC, TECHNICAL_DESIGN và REBUILD_REVIEW trước khi thực hiện.
- Mỗi đầu việc cần input hợp lệ, output đọc lại được, test lỗi và kiểm tra không mất dữ liệu nguồn.
- Có thể triển khai phần độc lập trong khi gate live/Windows/GPU bị chặn; không nhận công nghệ phụ thuộc là đã kiểm chứng.
- Sau mỗi task: ghi commit, file thay đổi, lệnh test, version/toolchain, PASS/FAIL/NOT_RUN và giới hạn. Chỉ nghiệm thu khi toàn bộ tiêu chí bắt buộc đạt.
- Không sử dụng phần trăm dòng code. Tiến độ nghiệm thu = số task đạt / tổng task của phase.

## Danh mục 9 đầu việc

### P03-01

**Phạm vi:** scaffold module, môi trường tái lập, dependency lock, config và user data tách khỏi thư mục chương trình.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Scaffold, dependency lock, Windows/Linux CI. Còn mở: Config/user-data ownership và nền ứng dụng đầy đủ. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P03-02

**Phạm vi:** schema/version/migration cho project/media/preset/job/artifact/history/cache; backup và phục hồi khi migration lỗi.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- OPS-03 (PR 9): Crash/mở lại giữ việc xong, thiếu asset relink được

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Project/job schema1, reject drift, online backup validated. Còn mở: Các schema preset/artifact/history/cache; migrations/restore faults. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P03-03

**Phạm vi:** probe, ID/fingerprint, rational timestamp/time map; media không audio hoặc metadata lỗi.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- Tiêu chí từ phạm vi task và cổng phase trong master; phải có kết quả kiểm tra trực tiếp, không chỉ tệp tồn tại.

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. ffprobe thật, rational interval/time mapping. Còn mở: Strong source fingerprint/VFR corpus và provenance đầy đủ. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P03-04

**Phạm vi:** scheduler/worker process, công đoạn/progress/cancel/pause/retry, quản lý tiến trình con trên Windows và lease phục hồi sau crash.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- OPS-01 (PR 9): Không biết tổng không dựng phần trăm, ETA có trạng thái ước tính
- OPS-02 (PR 9): Ý nghĩa đúng, không hứa resume frame render
- OPS-05 (PR 8–9): FFmpeg/worker lỗi không sập UI hoặc mất lô

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Qt worker, bounded direct child, SQLite lease primitive. Còn mở: Durable scheduler/descendant containment/pause/crash recovery integration. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P03-05

**Phạm vi:** snapshot cấu hình/seed, log lọc bí mật, phân loại lỗi và UI hàng đợi đầu tiên.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- OPS-04 (PR 9): Truy vết được từng đầu ra, preset đổi không thay job cũ

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Immutable intent/seed/hash, lỗi UI được lọc. Còn mở: Queue UI, typed error taxonomy và worker snapshot integration. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P03-06

**Phạm vi:** output tạm → kiểm tra → tên cuối an toàn, không đè; truy vết nguồn; bỏ output/cache khi quét.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- SRC-08 (PR 3.3): Tệp dở/hỏng không thành công, nguồn giữ nguyên
- BAT-03 (PR 3.3, 5): Đúng cây folder, input trùng tên không mất kết quả
- OPS-06 (PR 3, 9): Exit lỗi/tệp hỏng/duration sai không báo thành công

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Staging/decode/probe/hash/atomic no-overwrite; scan exclude output. Còn mở: Artifact/job provenance transaction và toàn ma trận filesystem. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P03-07

**Phạm vi:** save/autosave/recovery, relink media, cache theo fingerprint/phiên bản; thử đóng bất thường có kiểm soát.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- OPS-03 (PR 9): Crash/mở lại giữ việc xong, thiếu asset relink được

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** IN_PROGRESS / chưa nghiệm thu. Project save-as/open, exact edits, manual relink/undo, ledger backup. Còn mở: Autosave/cache recovery và abrupt-close fault corpus. Xem [đối chiếu hiện tại](../REBUILD_TASK_PROGRESS.md); dẫn chứng lịch sử không chứng nhận code mới.

### P03-08

**Phạm vi:** dependency registry/resolver, tool ownership/version/path/capabilities, trusted manifests, cài per-user, staging/self-test/activation/lease/rollback, không đè tool ngoài.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- TOL-02 (SB 2.1): Unicode/timeout/sai version/capability báo đúng, không sửa tool ngoài
- TOL-03 (SB 2.2): Manifest đúng kiến trúc/phiên bản/capability, không bắt cài dev tools vô cớ
- TOL-04 (SB 2, 2.3): Nút chạy thật qua tải/xác minh/cài/kiểm tra; chưa xong không báo ready; FFmpeg/ffprobe chung busy key, công cụ độc lập vẫn xếp hàng, install-missing bỏ qua thành phần đang bận. Qt regressions + [CI 41080729485](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41080729485) PASS synthetic Linux/Windows
- TOL-05 (SB 2.3): Artifact lỗi bị chặn, bản cũ và cấu hình được giữ
- TOL-06 (SB 2.3): Job cũ giữ binary cũ; activation xác thực receipt identity/managed path/hash/companion; rollback chặn executable ngoài root và ffprobe symlink; Settings cleanup chỉ gỡ bản không còn lease; per-tool busy guard chặn cập nhật trùng và thao tác xung đột. [CI 41080729485](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41080729485) PASS synthetic Linux/Windows; máy Windows người dùng, cross-process mutex và live install/update vẫn mở
- TOL-08 (SB 2.2): Chỉ thành phần cần được yêu cầu, driver không tự thay, API không tự tải model

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

### P03-09

**Phạm vi:** schema BrowserProfile/PlatformAccountBinding, profile ownership/browser state/auth state, credential refs và account-scoped cache; không lưu cookie/mật khẩu trong project.

**Đầu vào:** phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa; fixture có quyền sử dụng. Dữ liệu live không đủ thì ghi BLOCKED riêng, không thay bằng mock.

**Đầu ra:** implementation hoặc tài liệu đúng phạm vi trên, test hồi quy và bản ghi kết quả có thể tái lập; UI chỉ gắn hành động thành công sau readback/validation.

**Truy vết và tiêu chí cụ thể:**
- AUTH-03 (SB 3): Facebook A/B không chia cookie, không nhầm nhiều cửa sổ là nhiều profile
- AUTH-07 (SB 5): Nick chọn được giữ, project/job không chứa cookie/token
- AUTH-10 (SB 5): Cache/quyền A không dùng cho B, không giành user-data-dir
- AUTH-11 (SB 4–5, 8): Export không lộ session, cache cleanup không xóa profile, xóa dữ liệu có thao tác riêng

**Ca lỗi bắt buộc:** input thiếu/sai/biên; hủy hoặc lặp thao tác; lỗi dependency/quyền ghi/tiến trình khi có tác động; không thay nguồn, không mất sửa tay và không báo thành công giả.

**Phụ thuộc:** thực hiện sau task tạo contract/nguồn dữ liệu của chức năng; xem đồ thị master. Adapter/live/Windows/GPU phải được kiểm chứng riêng trước công bố khả dụng.

**Trạng thái rebuild:** NOT_STARTED. Bằng chứng cũ bên dưới chỉ dùng để thiết kế regression.

## Hồ sơ thực hiện trước rebuild (chỉ tham khảo)

# P03 — Kế hoạch chi tiết: độ bền dữ liệu và bảo vệ bí mật

**Phiên bản kế hoạch:** 2.0 — 28/10/2026  
**Trạng thái:** lát cắt hardening đã code; CI Linux/Windows pass trên commit 989368b9560b059c27c131c36ed12955f98c6602. Cổng soak/crash/power-loss và nghiệm thu máy Windows người dùng vẫn mở.  
**Nhánh:** phase/p03-storage-durability-secrets

## 1. Đối chiếu master plan và trạng thái hiện tại

Đã đọc lại docs/IMPLEMENTATION_PLAN.md, docs/CURRENT_STATUS.md, docs/phases/P03_RESULTS.md, docs/IMPLEMENTATION_COVERAGE.md và docs/TECHNICAL_DESIGN.md; rà soát storage.py, domain.py, worker.py, jobs.py và tests/test_storage_jobs.py.

- Master P03 có 9 task, tập trung schema/migration, project/job snapshot, scheduler/worker, recovery, output validation và bảo vệ dữ liệu.
- Nền code P03 đã tồn tại; không scaffold lại, không xóa code và không tăng schema version nếu không cần thiết.
- CI xác nhận 108 test pass trên Linux và 107 pass + 1 skip có chủ đích trên Windows. Các kiểm chứng này không thay thế soak/crash/power-loss hoặc nghiệm thu máy Windows người dùng.
- Coverage vẫn mở về độ bền dài hạn, lỗi đĩa/quyền/mạng và log chẩn đoán đầy đủ. Lát cắt này xử lý các vấn đề có thể kiểm chứng tự động trước.

## 2. Phạm vi code

### P03-02 / P03-07 — Backup và migration an toàn

1. Tạo helper backup dùng file tạm trong cùng thư mục đích, hoàn tất SQLite backup, chạy integrity_check và chỉ công bố file sau khi kiểm tra thành công.
2. Tạo thư mục cha nếu chưa có; không ghi đè file backup đã tồn tại; dọn file tạm khi có exception.
3. Dùng cùng cơ chế backup cho migration schema v1→v2 trước khi thay đổi schema.
4. Bổ sung test backup vào thư mục lồng chưa tồn tại, integrity_check, dữ liệu mở lại được, từ chối ghi đè và giữ nguyên backup có sẵn khi thao tác bị từ chối.

### P03-05 — Ngăn bí mật lọt vào project/job/settings và lỗi worker

1. Chuẩn hóa tên key trước khi kiểm tra: phân biệt chữ hoa/thường và bỏ dấu gạch dưới/gạch ngang/ký tự phân cách.
2. Chặn các trường bí mật phổ biến như password/passwd, cookie/cookies, API key, access/refresh/session/bearer token, client secret và authorization header; không lưu giá trị bí mật vào project/job.
3. Chuẩn hóa thông báo lỗi worker: che cặp key/value nhạy cảm, Bearer token và query string của URL ký; giữ phần thông tin lỗi hữu ích như loại lỗi, host/path và mã trạng thái.
4. Thêm test cho các biến thể key và thông báo lỗi chứa authorization/token/URL có query nhạy cảm. Không ghi giá trị bí mật vào log hoặc assertion output.

### P03-04 / P03-06 — Không làm suy yếu hàng đợi hoặc output

- Giữ nguyên snapshot bất biến, transaction claim, heartbeat, cancel/retry, no-overwrite và validation hiện có.
- Không đổi logic recovery từ “orphan → pending” thành “succeeded” chỉ vì file tồn tại.
- Không tuyên bố đã giải quyết toàn bộ artifact reconciliation sau crash; phần reconcile render/download sau power loss tiếp tục là cổng riêng nếu chưa có validator/manifest đủ tin cậy.
- Không thêm network access, API trả phí, browser credential access hoặc dữ liệu người dùng vào test.

## 3. Thứ tự triển khai

1. Thêm test cho alias secret keys và sanitize error trước khi thay đổi implementation.
2. Sửa domain validation và worker error sanitization.
3. Thêm backup helper và dùng nó cho backup thủ công/migration.
4. Chạy test tập trung storage/security, sau đó toàn bộ suite.
5. Chạy check_plan và packaged proof Linux/Windows qua GitHub Actions.
6. Ghi P03_RESULTS, cập nhật coverage/status theo đúng kết quả; chỉ đánh dấu task hoàn thành khi test tương ứng có bằng chứng.

## 4. Tiêu chí nghiệm thu

- [x] Backup vào thư mục mới tạo được; integrity_check trả về ok và database mở lại đọc được.
- [x] Backup không ghi đè file đích có sẵn; thao tác lỗi không để file tạm như bản backup hợp lệ.
- [x] Migration v1 tạo bản backup trước khi đổi schema; test migration hiện tại vẫn qua.
- [x] Các alias như api-key, Authorization, session_cookie, clientSecret, refresh-token và bearerToken bị chặn khi nằm trong payload được kiểm tra.
- [x] Thông báo lỗi che Bearer token, các trường token/password/cookie/API key và query URL nhạy cảm; vẫn giữ được thông tin hữu ích cho chẩn đoán.
- [x] Toàn bộ test source pass; packaged proof Linux/Windows không hồi quy.
- [x] Không thay đổi schema hoặc định dạng project ngoài nhu cầu; không ghi bí mật, browser profiles, downloaded media hay runtime artifacts vào Git.

## 5. Rủi ro, rollback và giới hạn

- Backup nguyên tử có thể không hỗ trợ trên một số filesystem nếu hard link bị cấm; trong trường hợp đó phải fail rõ, không âm thầm chuyển sang thao tác có nguy cơ ghi đè.
- Redaction phải ưu tiên an toàn nhưng không xóa hết thông tin chẩn đoán; test dùng chuỗi synthetic, không dùng bí mật thật.
- Nếu test hoặc CI fail, sửa nguyên nhân trên nhánh phase; không force-push, không thay main và không giảm tiêu chí kiểm tra.
- Crash/kill/power-loss soak dài hạn, lỗi đĩa/quyền/mạng trên máy thật và installer Windows vẫn mở sau lát cắt này.

## 6. Điều kiện tiếp tục

P03 có thể được đóng khi các cổng code/test của phase đạt và kết quả được ghi lại. Cổng bên ngoài như Chrome/session, nguồn live, GPU hoặc nghiệm thu máy Windows người dùng không được gắn PASS nhờ test storage. Sau P03, tiếp tục P04 theo master plan và lập phase plan riêng trước khi code.

## Vòng bảo mật bổ sung 28/10/2026 — P03-05/P11

Đối chiếu lại master P03-05 (log lọc bí mật), P11 (đường lỗi tích hợp) và `storage.Store.fail`: worker đã lọc error nhưng những caller khác có thể gọi Store.fail trực tiếp, khiến thông báo chứa token/URL query được ghi nguyên vào SQLite. Sửa tại **ranh giới ghi database**, dùng cùng sanitizer chuẩn của worker (import local để tránh vòng module) với giới hạn 3000 ký tự. Test synthetic kiểm chứng nội dung SQLite và `Store.job`, trạng thái failed/blocked không đổi; chạy suite/packaged proof hai hệ. Không đánh dấu nghiệm thu mạng/Windows máy thật.
