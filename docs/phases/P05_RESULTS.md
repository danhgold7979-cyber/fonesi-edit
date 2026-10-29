# P05 — Kết quả adapter và session

Đã code nhận diện nền tảng/URL, yt-dlp và gallery-dl scan/download trong worker, template folder, no-overwrite, lọc/ngôn ngữ sub, cookie jar theo binding và profile store. Có extension MV3 với thao tác gửi phiên rõ ràng, native messaging pairing mã hết hạn, Windows DPAPI và account mismatch cho danh tính xác định được; không đọc Chrome cookie DB.

Kiểm tra local gồm URL chống nhầm host, Windows filename, profile/binding isolation, pairing single-use và không có plaintext fallback. Download HTTP media từ server fixture nội bộ được test riêng, không thay kiểm chứng YouTube/Facebook/kênh nhiều trang. Live network/auth/Chrome thật vẫn mở.

## P05-03 — Quét → chọn mục → tải; phân trang hiển thị (28/10/2026)

Triển khai trên **một nhánh tích hợp** `develop/fonesi-full`, không tách riêng bộ tải:

- `downloads.py`: scan từ yt-dlp/gallery-dl trả metadata từng item có ID/kiểu media/adapter/URL tải lại (nếu đủ an toàn). URL có tài khoản trong authority, signed query/token/CDN query hoặc fragment không được đưa vào URL selectable; item không đủ URL bị gắn trạng thái không chọn được. Flat playlist của YouTube/Bilibili được chuẩn hóa từ **đúng loại extractor và ID đã được xác thực cú pháp**, không suy ra cho nền tảng không rõ. Không coi item scan xong là scan toàn kênh.
- `DownloadsPage`: danh sách scan chọn lại được sau mở app, cây Qt checkbox có trạng thái URL, nút chọn/bỏ chọn, tạo job tải riêng từ scan snapshot, phân trang tối đa 200 hàng hiển thị, checkbox giữ lại qua nhiều trang, không chọn URL trùng trong một scan.
- `selected_download_payloads`: giữ snapshot thư mục/tài khoản/identity/sub/lang/chất lượng/auto-edit, khóa cross-platform account binding, giữ engine video/gallery đúng theo chính item gốc kể cả nguồn mixed-media, chỉ đưa URL hợp lệ vào job. `submit_once` tránh enqueue lặp khi bấm nút hai lần; job cũ cần Retry trong hàng đợi, không tự đổi account.
- Test nguồn thật **chỉ trên localhost**: gallery scan ảnh → item được chọn → download file PNG hợp lệ. Test synthetic: URL ký bị từ chối, YouTube/Bilibili flat ID, adapter mixed, lựa chọn trùng, stale/mismatch account, Qt tree và đa chọn qua nhiều trang, reopen/history.

**Bằng chứng CI:** [run 40641870092](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40641870092) — **Linux 162 passed; Windows 161 passed + 1 skipped** (fixture lệnh shell chỉ chạy POSIX). Cả hai runner cũng build production app/native-host và chạy frozen packaged proof qua FFmpeg, batch/ma trận, tải video/ảnh từ localhost và Qt smoke/frame decode. Development binary cho Windows được lưu dưới artifact `FonesiEdit-Windows-development` có ngày hết hạn.

**Không tuyên bố P05 đã hoàn tất toàn bộ.** Phân trang checkbox chỉ là phân trang **hiển thị**, không phải phân trang/checkpoint API nguồn. Chưa có live corpus quét nguyên kênh ở 10 nền tảng, Chrome→connector qua tài khoản thực, quyền nguồn/region, album ở mọi adapter, nâng chất lượng/bổ sung sub đơn lẻ, filter/sort đầy đủ, kiểm thử click chọn cực lớn, và test mạng/xác thực trên Windows người dùng.

## P05-04/05 — strict payload validation, CookieJar transport and repeat-image safety (28/10/2026)

- `execute_download_job` now rejects malformed job/payload/URL, engine and media types, booleans/floats/non-integer limits, negative limits and non-HTTP(S) URLs before creating the destination folder.
- The gallery CookieJar fixture now requires the synthetic cookie on the localhost image endpoint, proving the initialized gallery session actually sends the selected cookie; it remains a synthetic transport test, not Chrome/live-account acceptance.
- Added scan → select → download → repeat-download coverage for gallery images in a Unicode folder. The existing file path, bytes and modification time must remain unchanged; the file is checked as a readable PNG.
- CI [run 40736655575](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40736655575) **PASS**: 421 Linux tests; 420 Windows tests + 1 intentional POSIX-fixture skip. Production desktop/native host and frozen proof passed on both runners.
- The dedicated repeat-image slice [run 40735733292](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40735733292) also passed: 413 Linux / 412 Windows + 1 intentional skip, packaged proof both systems.
- Still open: provider pagination/checkpoint, live platform corpus, Chrome/session handoff on a real account, region/permission behavior and Windows user-machine acceptance. P05 is not fully closed.

## P05-03 — Scan result search/filter/sort (28/10/2026)

- Added case-insensitive title/ID search (never URL), media-kind and selectable-state filters, and stable source/title/kind sorting.
- The 200-row page is now based on the filtered view; selection remains keyed to original scan indices and persists when selected items are temporarily hidden by a filter. Download-selected still validates original URLs, duplicate state, adapter and account snapshot.
- CI [run 40738678506](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40738678506) **PASS**: 422 Linux / 421 Windows + 1 intentional POSIX-fixture skip; packaged proof passed on both runners.
- Provider pagination/checkpoint, advanced metadata filters, huge bulk-selection UX, live platform corpus and real Chrome/session acceptance remain open.


## P05-02/03 — Lọc metadata kết quả quét (29/10/2026)

- \`downloads.py\` chỉ lấy metadata hợp lệ từ extractor (\`upload_date\`, \`duration\`, \`width\`, \`height\`); hỗ trợ ngày \`YYYYMMDD\`/\`YYYY-MM-DD\` và ngày dạng \`date/datetime\` từ gallery-dl, không suy đoán metadata bị thiếu và không sao chép URL/CDN query hoặc cookie từ metadata thô.
- DownloadsPage lọc ngày đăng từ/đến, thời lượng giây tối thiểu/tối đa, chiều cao pixel tối đa. Bộ lọc chạy cục bộ sau scan, kết hợp tìm kiếm/loại media/trạng thái URL/sắp xếp/phân trang. Mặc định giữ mục thiếu metadata; có lựa chọn loại mục thiếu. Ngày sai, số không hữu hạn, giới hạn nghịch hoặc giá trị nhập dở được báo lỗi ở UI mà không làm hỏng chọn mục.
- Chọn/tải tiếp tục dùng **chỉ số scan gốc**, kiểm tra URL an toàn, account/adapter/output snapshot. Các mục bị ẩn khi lọc vẫn được chọn nếu đã chọn trước đó; bulk chọn/bỏ chọn chỉ tác động những mục khớp bộ lọc trong giới hạn 500.
- Thêm \`tests/test_scan_metadata.py\` cho biên ngày, metadata gallery-style, bộ lọc nhiều điều kiện, thiếu/sai metadata và đầu vào không hợp lệ; \`tests/test_app_integration.py\` cho điều kiện kết hợp, UI Qt, phân trang và selection xuyên lọc. Không cần nguồn live hoặc tài khoản thực.
- **Bằng chứng:** [CI 40837035435](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40837035435) **SUCCESS đúng commit [a73a1dc](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a73a1dc41840ff981047f2d8aadf4fa313e70d4d)**: 449 Linux PASS; 448 Windows PASS + 1 POSIX-only skip; plan validator, production desktop/native-host build và frozen packaged proof đạt trên cả hai runner.
- **Chưa đóng P05 tổng thể:** metadata từng nguồn thực chưa đủ xác nhận; provider-side pagination/checkpoint, 10-platform live corpus, Chrome/session handoff tài khoản thực, quyền/region, chất lượng/sub-only upgrade, album và kiểm thử Windows máy người dùng vẫn mở. Đây là lọc metadata đã quét, không phải kiểm chứng quét hết kênh.

## P05-02 — Stable oldest/newest scan sorting (29/10/2026)

- UI thêm hai chế độ "Ngày cũ trước"/"Ngày mới trước" sau các lựa chọn sắp có, mặc định vẫn giữ "Thứ tự nguồn". Date được chuẩn hóa theo `normalize_scan_metadata`; bản ghi thiếu hoặc có ngày vô hiệu luôn đứng cuối ở cả hai chiều, ngày bằng nhau giữ original source index.
- Sắp xếp thực hiện trên tập đã được tìm kiếm/lọc, trước phân trang. Checkbox theo chỉ số scan gốc không bị đổi khi chuyển sort, lọc hoặc trang; selected download vẫn giữ account/adapter snapshot và kiểm tra URL an toàn.
- Bổ sung integration regression `test_scan_chronological_sort_keeps_unknown_last_ties_stable_and_selection` với 5 mục synthetic: ngày ISO/compact/trùng/thiếu/sai, trang có mục ẩn, date filter và enqueue theo index.
- **Evidence:** [CI 40838160968](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40838160968) **SUCCESS trên commit [b1d5df0](https://github.com/danhgold7979-cyber/fonesi-edit/commit/b1d5df00b0295bf307f3814e8be820833399f895)**: 450 Linux PASS; 449 Windows PASS + 1 POSIX-only skip; check_plan, production build/native-host và frozen packaged proof PASS hai hệ.
- Chỉ xác nhận sort **cục bộ trong kết quả quét hiện có**. Provider pagination/checkpoint, live channel/account/region, metadata thực, Chrome session, chất lượng/sub-only upgrade và Windows máy người dùng vẫn mở; không đánh dấu full P05 đã nghiệm thu.

## P05-02/03 — Bounded yt-dlp index-window continuation (29/10/2026)

- Added `continuation_scan_payload` for successful, **explicit video-engine** yt-dlp playlist scans with 1–200 items per window and at most 2,000 accumulated items. Generates immutable next-window snapshot (parent scan ID, absolute 1-based `playliststart/playlistend`), verifies origin URL/platform, engine, media, folder, limit, account/expected identity and options **again inside worker, before transport**. No gallery/mixed continuation claim.
- Each continuation creates a new scan job, preserving prior result and original scan indices. Repeated URLs become unselectable and all-repeat windows stop; unknown/short/unsupported provider returns do not set `complete=True`. `selected_download_payloads` strips scan-cursor fields before enqueueing download.
- `DownloadsPage.continue_scan` enqueues idempotently by parent/window via `submit_once`; UI retains prior in-memory checkbox indices only when parent items are an exact prefix, including across filter/pagination, without switching account. Existing unbounded scans and older scan results remain readable but cannot claim resumable checkpoint.
- Synthetic tests use fake yt-dlp (no live provider) for 3 windows, cumulative/dedup, tamper rejection before source IO, missing/corrupt cursor, old results, total cap, and Qt idempotence/selection/download regression.
- **Evidence:** [CI 40840732733](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40840732733) attempt 2 **SUCCESS** on [a140d9b](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a140d9b517d71976ec64b4a098e0d91394349c37): Linux **455 passed**; Windows **454 passed + 1 intentionally skipped**. Validator, production desktop/native-host build and frozen packaged proof passed on both runners.
- **Caveat:** attempt 1 Windows had a separate proxy UI close/autosave test failure `sqlite3.DatabaseError: database disk image is malformed` (453 passed/1 failed/1 skipped); Windows rerun on the same commit passed with no code/assertion changes. Root cause of intermittent SQLite failure remains **unknown**, tracked as P03/P04 QA risk.
- **Not full P05 acceptance:** yt-dlp playlist index windows are not verified provider pagination/checkpoints; source ordering may change. Live full-channel/10-platform corpus, gallery continuation, albums, Chrome/session/permissions/region, Windows user device and installer remain open.
