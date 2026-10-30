**HỒ SƠ BASELINE TRƯỚC REBUILD:** nội dung/bằng chứng dưới đây thuộc implementation trước đợt làm lại 30/10/2026, không chứng nhận code mới. Xem [trạng thái rebuild hiện hành](REBUILD_STATUS.md). Baseline tích hợp được giữ tại commit `edbb47189b0e864c74623d0a4db5b5f169f2103c`.

# Fonesi Edit — Trạng thái triển khai

Bản phát triển, chưa tuyên bố nghiệm thu toàn bộ 95 nhóm yêu cầu. Theo chỉ đạo người dùng, tiếp tục phần độc lập qua mọi phase; không dừng vì mạng/tài khoản/Windows/GPU và không gắn các mục đó là pass.

| Phase | Code/kiểm chứng hiện có | Cổng còn riêng |
| --- | --- | --- |
| P01 | Thiết kế, luồng, contracts, traceability | Cập nhật theo thay đổi đã được chấp thuận |
| P02 | Source tests và frozen packaged proof Linux/Windows CI đạt; đã sửa lỗi gallery-dl Unicode console | Live nguồn/dịch, Chrome/session handoff, GPU/VRAM, installer/rollback và nghiệm thu trên máy Windows người dùng |
| P03 | Domain/SQLite/snapshots/worker; backup có integrity/no-overwrite, credential alias checks và error redaction; CI Linux/Windows pass | Soak/crash/power-loss, filesystem không hỗ trợ hard link, installer và nghiệm thu máy Windows người dùng |
| P04 | Canvas/inspector/timeline/undo, rendered In–Out loop, async thumbnail strip, validated source proxy; peer snap + viewport guides; normalized crop + ratio-lock/anchor tests; Save As + Ctrl+Shift+S; focus-aware Ctrl+A/C/V/X layer clipboard; Escape cancels active drag; latest slices CI Linux/Windows + frozen proof PASS | Rotation metadata/VFR/mixed FPS, HiDPI/4K/seek/audio-sync/long timeline, remaining shortcut/customization cases, remaining P04 tasks and real Windows user-machine acceptance |
| P05 | yt-dlp/gallery-dl, profile/binding and bridge; scan→checkbox tree/200-row UI pagination; title/ID search, media/selectable filters and stable sorting including date oldest/newest with missing dates last; local validated upload-date/duration/height filters with explicit missing-data policy; bounded index-window yt-dlp scan continuation with separate cumulative job, snapshot validation and duplicate guards; selected download preserves adapter/account snapshot; supplemental yt-dlp subtitle-only jobs with read-back validation/no-overwrite and UI idempotence; verified chained yt-dlp quality variants, manual filtered new-only with atomic SQL batch, bounded scan-first new-only schedules and Batch/watch exclusions; signed/duplicate URL protection; strict URL/engine/media/limit validation; CookieJar transport fixture; repeated gallery-image no-overwrite | Verified provider pagination/checkpoint, live 10-platform coverage, real Chrome/session identity, region/permission, provider metadata completeness/live quality formats/invalid variant repair, huge bulk UI and Windows user-machine acceptance |
| P06 | SRT/VTT/ASS, sửa/lock/cache/quota/provider adapters; atomic caption files, verified sidecar reuse, bilingual split/merge; bounded 100-state in-session cue-table Undo/Redo, raw-draft recovery and Qt focus-aware shortcuts (Linux/Windows CI) | Unlimited/persistent Undo, cue timeline drag, live dịch/chi phí/ngôn ngữ provider và nghiệm thu thiết bị Windows thật |
| P07 | Compositor, motion/keyframes, font, mask, alpha, audio, reference | Từng tổ hợp style/OS/GPU, performance target |
| P08 | Batch nhiều folder local/khử trùng, FFprobe metadata filters; **audio shared/by-name/ordered/random + manual absolute playlist đa thư mục, 1:1 theo thứ tự video, FFprobe preflight/cache, snapshot giữ music/SFX và FFmpeg/PCM render proof**; duration solver; SFX anchor/repeat/trigger_times; music loop crossfade; Editor decoded PCM Peak/RMS meter pre-device; CI Linux/Windows + frozen PASS | Per-track/true-peak/EBU loudness/solo hardware, corpus lớn/ETA/output size, Windows audio/installer máy đích, real user-device acceptance |
| P09 | Lazy matrix/seed/W/K/history, per-cell lock/regenerate/usage/formula, weighted/manual seconds/speed bounds, Qt scene drag/order; **source-scanned scene/angle exclusion + global pinned G, manifest-gated per-root selection, mixed-scene history/atomic enqueue QA**; [CI 41021003352](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41021003352): Linux 728 / Windows 727 +1 skip, frozen packaged PASS | 10^10 logical-space candidate balance CI PASS (2,000 outputs, spread 5); 100k real-media/large solver optimality, real Windows mouse/drag/HiDPI/installer, identical hash across different scene folders (fail closed), NTFS/exFAT/power-loss, full product acceptance |
| P10 | Workflow/watch/scan-first new-only schedules và resources; Settings quota proxy cache/janitor nền an toàn, bảo vệ file QMediaPlayer đang phát; CI/frozen PASS | Task Scheduler, GPU/VRAM/driver thật, cache khác/installer và Windows/ACL/soak |
| P11 | P11-05 preset/profile; P11-08 archive/install/lease/receipt/rollback/Settings update-busy + AUTH bridge handoff/revocation ordering; [CI 41088435585](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41088435585) exact HEAD PASS: Linux 892 / Windows 888 + 4 intentional skips; production/native-host/frozen proof both OS | P11-01…08 full requirement audit, pending pairing-code issuance/revocation race, physical Windows ACL/AV/disk-full/power-loss, signed installer/update UX, real Chrome/provider auth, GPU/HiDPI/audio, real-media corpus/soak, SQLite issue #6 and release gates |
| P12 | Script/build app + native host; frozen proof Linux/Windows CI đã đạt | Cài đặt/rollback, máy Windows người dùng, Chrome/GPU/HiDPI/audio và nghiệm thu release còn mở |

Chạy `uv run fonesi-edit`. Bản CLI/prototype cũ vẫn giữ để hồi quy. Runtime, browser profiles, video và API keys không được commit.

Baseline local trước lát cắt hardening: 92 tests qua. CI mới nhất: Linux 108 pass; Windows 107 pass + 1 skip có chủ đích. Cả hai runner build app/native host và chạy frozen proof thành công; binary chạy render batch/ma trận song ngữ, tải video/ảnh localhost, rename/undo, UI smoke và giải mã frame Qt. 36 file source khớp hash của bundle. Xem [báo cáo](LOCAL_VERIFICATION.md), [evidence JSON](evidence/desktop-verification.json) và [phần đã có/còn mở theo 95 nhóm](IMPLEMENTATION_COVERAGE.md).

CI P02: [run 40634117095](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40634117095). CI hardening P03: [run 40635978628](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40635978628). Cả hai dùng synthetic/localhost evidence, không phải nghiệm thu máy Windows người dùng. Mạng xã hội nguyên kênh, API dịch thật, Chrome session handoff, GPU/VRAM/driver, HiDPI/audio và installer/rollback máy thật vẫn cần kiểm chứng riêng. Những tùy chọn nâng cao chưa hoàn tất tiếp tục được ghi trong coverage, không tự đổi thành đã đạt hoặc loại khỏi phạm vi. Giọng AI/ASR/OCR/tracking thuộc giai đoạn sau.

## Cập nhật code và CI trên nhánh tổng 28/10/2026

Đã tiếp tục bổ sung code/kiểm thử theo phase P04–P10 và sửa CI P12 trên duy nhất nhánh `develop/fonesi-full`. [Sổ thực hiện](PHASE_EXECUTION_LEDGER.md) dẫn từng run và cổng còn mở. CI của bản tích hợp trước bộ test P11 mới nhất: [run 40639294385](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639294385) đạt 140 tests Linux, 139 tests Windows + 1 skip fixture POSIX, cùng packaged proof cả hai nền tảng. P11 đang bổ sung kiểm tra 95 nhóm yêu cầu. Kết quả synthetic/localhost và runner Windows Server không thay nghiệm thu dùng thật hoặc xác nhận toàn bộ tính năng.

**Bổ sung P11:** [CI 40639610919](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639610919) PASS (143 Linux, 142 Windows + 1 skip POSIX-fixture) cùng packaged proof binary hai hệ cho nhánh tổng. Bài kiểm tra 95 nhóm chỉ xác nhận mã truy vết/task/acceptance không rỗng, **không xác nhận 95 chức năng đã đủ hoặc sử dụng live đã hoạt động**.

## Cập nhật P05: quét chọn từng item (28/10/2026)

[CI run 40641870092](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40641870092) **PASS 162 test Linux, 161 test Windows + 1 skip**, build/frozen packaged proof trên cả hai hệ. Đã có cây chọn item, phân trang UI 200 hàng, lựa chọn qua nhiều trang, bảo vệ URL tải và account snapshot, chống job trùng, test scan→tải file PNG trên localhost. Phân trang UI không đồng nghĩa quét đủ nhiều trang nguồn; chưa xác nhận 10 nền tảng/live Chrome hoặc nghiệm thu installer trên Windows máy người dùng. Xem [P05_RESULTS](phases/P05_RESULTS.md) và [coverage](IMPLEMENTATION_COVERAGE.md).

## Cập nhật P08: âm thanh theo video (28/10/2026)

[CI 40642781347](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40642781347) PASS: **166 test Linux, 165 test Windows + 1 skip**, binary packaged proof hai hệ PASS. Thêm policy một audio chung/trùng tên/theo danh sách/ngẫu nhiên seed có dry-run mapping và audio track thật được FFprobe kiểm trước; không thay preset, không ghi đè nguồn. SFX/music crossfade/meters và thử nghiệm Windows trên máy người dùng vẫn mở. Xem [P08_RESULTS](phases/P08_RESULTS.md).

## P09 — Kết quả nâng cấp ma trận (28/10/2026)

[CI 40645339209](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40645339209) PASS **180 Linux / 179 Windows + 1 skip**, packaged proof hai hệ đạt. Đã code tạo lại riêng hàng không vi phạm W/K/history/lock, thống kê tần suất góc, ô nhập thời lượng cảnh theo weights hoặc số giây nhập tay, speed bounds trong Matrix UI, truyền chính xác đến solver và render. Chưa khép cổng Windows/exFAT thực tế, reorder cảnh UI và solver quy mô lớn. Chi tiết [P09_RESULTS](phases/P09_RESULTS.md).

## Cập nhật P04/P10 ngày 28/10/2026

CI [40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) **PASS 195 test Linux, 194 Windows + 1 skip**, build/frozen proof hai hệ đạt. Loop In–Out, thumbnail/cache source proxy và giới hạn dọn cache đã có code/test; hiệu năng thật, Chrome/live providers, GPU và phát hành Windows chưa được nghiệm thu đầy đủ.

## P03/P08 — Cập nhật test 28/10/2026

P03: job error được lọc ở worker **và tại SQLite Store.fail**, test failed/blocked; [CI 40652053745](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40652053745) PASS. P08: AudioDialog có SFX mốc theo phần trăm/cảnh/cuối video và FFmpeg export audio đúng mốc; BatchPage lọc/chọn video và hủy snapshot cũ khi UI/preset đổi. [CI 40655116611](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40655116611) PASS **219 Linux /218 Windows +1 skip**, frozen app/native host proof đạt hai hệ. Chưa phát hành chính thức; live account/Windows PC/installer/GPU và crossfade/meters nâng cao vẫn mở.

## P08-01 — Quét nhiều folder local

[CI 40656796768](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40656796768) PASS **222 tests Linux, 221 Windows +1 skip**, Linux/Windows production app/native host và frozen proof PASS. BatchPage quét nhiều folder, hợp nhất nhóm/kênh và khử source trùng khi folder chồng nhau; sửa root/hủy scan làm vô hiệu hóa lựa chọn cũ, background callback kết thúc muộn không được ghi đè. P08 vẫn chưa hoàn tất filter duration/resolution, music crossfade/meter/hiệu năng corpus, nghiệm thu Windows thực. Xem [P08_RESULTS](phases/P08_RESULTS.md).

## P08 — FFprobe metadata và FFmpeg music crossfade (28/10/2026)

**Metadata filter:** [CI 40658101720](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40658101720) PASS **225 Linux /224 Windows +1 skip**, frozen app/native host PASS. Lọc duration và cạnh ngắn ≥720/1080/2160, không bỏ lựa chọn file ẩn, xử lý lỗi từng file, callback nền cũ bị bỏ và chặn dry-run chưa áp dụng filter.

**Nhạc crossfade khi lặp:** [CI 40659216526](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40659216526) PASS **233 Linux /232 Windows +1 skip**, FFmpeg render và frozen packaged proof hai hệ PASS. Sửa lỗi FFmpeg 7.1.1 Windows ở lần chạy trước bằng input riêng cho vòng lặp. Chưa nghiệm thu âm thanh/HiDPI/driver trên PC người dùng, installer ký số, live provider và stress corpus.

## P08 — SFX repeat interval (28/10/2026)

[CI 40660385646](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40660385646) **PASS 246 test Linux, 245 test Windows +1 skip; frozen binary/native-host/render/download/UI proof hai hệ PASS**. SFX phát lặp 1–32 lần theo khoảng giây trên timeline đã resolve, chặn tràn thời lượng và role/policy không hợp lệ; đã thử âm PCM thật và round-trip UI. Vẫn cần trigger không đều/playlist, realtime meter và nghiệm thu Windows người dùng.

## P04 update — peer snap guides and crop ratio lock (28/10/2026)

- Peer snapping/viewport guide CI [40714649301](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40714649301): **326 Linux / 325 Windows + 1 intentional skip**, packaged proof both systems PASS.
- Crop ratio-lock/bounds CI [40716484637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40716484637): **339 Linux / 338 Windows + 1 intentional skip**, packaged proof both systems PASS.
- Anchor-preservation regression CI [40717364128](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40717364128): **347 Linux / 346 Windows + 1 intentional skip**, packaged proof both systems PASS.
- P04 remains in progress. Live provider, real Windows/HiDPI/GPU, rotated metadata/VFR and remaining shortcut/editor requirements are not marked accepted.

## P04 update — Save As and focus-aware layer clipboard (28/10/2026)

- Save As toolbar/shortcut CI [40719769956](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40719769956): **350 Linux / 349 Windows + 1 intentional skip**, packaged proof both systems PASS.
- Layer clipboard and focus-aware Ctrl+A/C/V/X CI [40721462280](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40721462280): **362 Linux / 361 Windows + 1 intentional skip**, packaged proof both systems PASS.
- P04 remains in progress; live provider, real Windows/IME, GPU/HiDPI, VFR/rotation and other unverified requirements are not marked accepted.

## P04 update — Escape drag cancellation (28/10/2026)

CI [40723004092](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40723004092) passed **363 Linux tests / 362 Windows tests + 1 intentional skip**; production desktop/native host and frozen proof passed on both runners. Escape cancellation restores the pre-drag snapshot and avoids a spurious Undo command. Physical keyboard/IME and real Windows/HiDPI acceptance remain open.

## P04 update — configurable canvas grid spacing (28/10/2026)

- Added persisted grid presets at 5%, 10%, and 20%; drawing and snap calculations use the same step.
- CI [40726135615](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40726135615) **PASS**: 398 Linux tests / 397 Windows tests + 1 intentional POSIX-fixture skip; packaged proof passed on both runners.
- Arbitrary custom numeric steps, dense-overlap guide priority, physical Windows/HiDPI and other P04/P12 acceptance gates remain open.

## P04 update — custom numeric grid spacing (28/10/2026)

- Added custom grid spacing from 1% to 50%, exact normalized guide placement, persisted project setting and Undo/Redo.
- CI [40728076508](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40728076508) **PASS**: 403 Linux / 402 Windows + 1 intentional skip; packaged proof passed on both runners.
- Inspector search/reset, dense-overlap guide priority, physical Windows/HiDPI and remaining P04/P12 acceptance gates remain in progress.

## P04 update — inspector property search/reset (28/10/2026)

- Added view-only case-insensitive property filtering and a reversible reset for selected unlocked layer transform/style/motion/keyframes.
- CI [40729358428](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40729358428) **PASS**: 406 Linux / 405 Windows + 1 intentional skip; packaged proof passed on both runners.
- Workspace layout persistence and remaining P04/P12 acceptance gates remain in progress.

## P04 update — workspace layout and dense guide priority (28/10/2026)

- Added safe UI-layout persistence for window geometry/state, navigation, editor splitter and inspector tab; no database migration or project/media changes.
- Added deterministic tie-breaking for equal-distance peer snap guides while preserving nearest-distance priority.
- CI [40731502132](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40731502132) **PASS**: 411 Linux / 410 Windows + 1 intentional skip; packaged proof passed on both runners.
- Physical Windows multi-monitor/HiDPI, remaining shortcut/IME and other P04/P12 acceptance gates remain open.

## P04 update — IME preedit shortcut guard (28/10/2026)

- Added focus-scoped IME preedit tracking to suppress editor actions during active text composition; preedit end/focus departure clears state and shutdown removes installed filters.
- CI [40734016363](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40734016363) **PASS**: 413 Linux / 412 Windows + 1 intentional skip; packaged proof passed on both runners.
- Synthetic tests pass; physical OS/IME and Windows multi-monitor/HiDPI acceptance remain open.

## P05 update — input validation, gallery session and no-overwrite proof (28/10/2026)

- Added strict downloader payload type checks before destination creation, a localhost CookieJar test that requires the cookie header, and repeat gallery image tests for unchanged path/content/mtime.
- CI [40736655575](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40736655575) **PASS**: 421 Linux / 420 Windows + 1 intentional skip; packaged proof passed on both runners.
- Provider pagination/checkpoint, live platform coverage, real Chrome/session handoff, account/region/permission and user Windows acceptance remain open.

## P05 update — scan result search/filter/sort (28/10/2026)

- Added title/ID search, media-kind and selectable-state filters, and stable source/title/kind sorting. Filtering does not clear selections on hidden pages, and downloads still reference the original scan indices and account snapshot.
- CI [40738678506](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40738678506) **PASS**: 422 Linux / 421 Windows + 1 intentional skip; packaged proof passed on both runners.
- Provider-side pagination/checkpoint, live platform/Chrome session, advanced metadata filtering, huge bulk-selection and real Windows acceptance remain open.


## P05 update — local scan metadata filters (29/10/2026)

- Normalized extractor metadata date/duration/width/height; UI now filters scan results by publication date, duration and maximum pixel height with validated inputs and explicit keep/exclude-missing behavior. Existing source indices, hidden selections, account/output snapshot and URL safety remain unchanged.
- [CI 40837035435](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40837035435) **SUCCESS**: Linux 449 tests; Windows 448 tests + 1 intentional POSIX-only skip. Plan validator, desktop/native-host build and frozen application proof passed on both CI runners.
- P05 remains in progress: provider pagination/checkpoint, live ten-platform and real Chrome login/session verification, region/permission/metadata correctness and user-device Windows acceptance remain open.

## P05 update — chronological scan ordering (29/10/2026)

- Added oldest/newest scan-result sort with deterministic source-index ties and missing/invalid upload dates at the end in both directions. Filters, original-index selection, account snapshot and download validation remain unchanged.
- [CI 40838160968](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40838160968) **SUCCESS**: 450 Linux / 449 Windows + 1 intentional skip; source suite, plan validator, app/native-host build and frozen proof PASS on both CI runners.
- P05 remains open for provider pagination/checkpoint, live corpus/metadata/auth and Windows user-machine acceptance.

## P05 update — Bounded scan continuation (29/10/2026)

- Added explicit yt-dlp video-playlist index-window continuation: limit 1–200/window, total snapshot cap 2000, parent result immutable, worker revalidates URL/engine/identity/options before network, duplicate URL protection, UI `submit_once`/checkbox original-index prefix, no unwarranted provider completion claim.
- [CI 40840732733](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40840732733) attempt 2 **SUCCESS on code SHA a140d9b517d71976ec64b4a098e0d91394349c37**: Linux 455 PASS, Windows 454 PASS + 1 intentional POSIX-fixture skip, plan validation and packaged desktop/native-host/frozen proof PASS both systems.
- Attempt 1 of that run had one Windows proxy close/autosave SQLite `database disk image is malformed` failure (453 PASS /1 FAIL /1 SKIP); not reproduced by rerunning Windows on the same commit. **Root cause not established; monitor P03/P04 shutdown/SQLite durability.**
- Whole-channel provider pagination/checkpoint, 10 real platforms, Chrome sessions/permissions/region, unsupported extractor index windows, real Windows machine/installer remain separate acceptance blockers. P05 is not fully completed.

## P05 update — Subtitle-only supplemental downloads (29/10/2026)

- `Tải bổ sung phụ đề` on scanned video items creates separate, idempotent yt-dlp jobs preserving account/URL/folder and skipping video/thumbnail/edit workflow. File verification checks path within `subtitles`, format, size, parser-readable cue timing and no-overwrite on repeat; synthetic actual yt-dlp writer/move test included.
- [CI 40845160133](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40845160133) **SUCCESS on code SHA 33dac071bf37a20ecf7ab1264b11c0f8d7791591**: 478 Linux passed, 477 Windows passed + 1 intentional POSIX fixture skip. Plan validator, production desktop/native-host build and frozen packaged proof PASS on both CI runners.
- This is **not** acceptance of provider live subtitle availability, source quality upgrades, full channel synchronization, real Chrome profiles/auth/region or Windows user-machine installer. P05 still OPEN. SQLite Windows intermittent incident: [#6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6), root cause not established.

## P05 update — Verified video quality variants (29/10/2026)

- Implemented explicit yt-dlp video quality-upgrade jobs from a successfully downloaded, FFprobe-valid **original** video with same scan URL/folder/account identity. Writes to independent `quality-upgrades/<target>p/videos/` directory with no-overwrite, strict resulting ID/height/path verification, original-size/mtime reconciliation, no sub/thumbnail/autoedit. Rejects unavailable original, stale account, invalid target, quality result not actually higher and mixed selection before enqueue/network where possible.
- Batch recursive scanner and automatic watch now exclude variants by default, preventing implicit duplicate processing; regression tests use actual 180p/360p FFmpeg/FFprobe fixtures and Qt.
- [CI 40849001694](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40849001694) **SUCCESS** on SHA `0ca96d300f0c3cce323291e5ac1759daf766625d`: Linux 510 tests PASS, Windows 509 PASS + 1 intentional skip; plan validator, desktop/native-host builds and frozen packaged proof PASS both runners.
- Not accepted: live provider availability/target resolution, chained quality upgrades, invalid variant repair, complete channel sync, 10-platform/Chrome/region/rights, Windows user-machine/installer and intermittent [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). P05 remains OPEN.

## P05 update — Verified chained quality upgrades (29/10/2026)

- A successful yt-dlp original or prior quality variant may be used as the next source when the requested ceiling strictly increases; UI chooses the highest recorded eligible source under the ceiling. Worker verifies ancestor job/video/account lineage, tier path, exact channel and on-disk FFprobe height before network/cookies and requires higher actual output resolution. No original or variant is overwritten, and Qt idempotence covers chained requests.
- [CI 40852244193](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40852244193) **SUCCESS on exact final code/test SHA [8dd9fec](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8dd9fec2268ab42c8e756e0b36a82af9d269531d)**: Linux 513 passed; Windows 512 passed + 1 intentional skip; desktop/native-host and frozen proof PASS on both. Earlier intermediate Windows CI red from the known intermittent SQLite [issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) is **not fixed/closed** by this result.
- Full P05 remains OPEN: live quality tiers, old corrupt variants, provider pagination/channel resync, 10 platforms, Chrome session identity and permissions, physical Windows user-device and installer.

## P05/P10 update — Manual and scheduled new-only sync (29/10/2026)

- Manual new-only verifies exact URL/engine/folder/account across full SQLite history, checks actual media via FFprobe/QImageReader, blocks invalid files and queues up to 500 jobs in one atomic transaction. [CI 40855868306](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40855868306) **537 Linux PASS /536 Windows PASS+1 skip**, desktop/native-host and frozen proofs both OS.
- Scheduled new-only enqueues a bounded *scan* first (default 100, max 200 items), then plans safe actual new media with persisted active/processed receipts; failed scans require Queue Retry. [CI 40857385183](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40857385183) **546 Linux PASS /545 Windows PASS+1 skip**, builds/frozen proof both OS.
- Full P05/P10 remain OPEN: provider-native checkpoint/full-channel, URL aliases/channel rename, broken old artifacts, live 10-platform/Chrome/rights, Windows user-device/installer/GPU, OS Task Scheduler while app closed and unresolved [SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6).

## P06 — Subtitle durability, safe reattachment and bilingual cue edits (29/10/2026)

- Added same-directory temp + fsync + atomic no-overwrite link for newly generated captions. Failed writes never publish partial subtitle filenames; existing manual files survive race/conflict. [CI 40862447183](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40862447183) **SUCCESS** at SHA `62cedf7`: 556 Linux / 555 Windows + 1 intentional skip, packaged proof both systems.
- Qt attachment now compares real source/translated cue text and timing before reusing hashed sidecars; altered/linked files are not silently attached or overwritten. [CI 40863067947](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40863067947) **SUCCESS** at SHA `1532c12`: 558 Linux / 557 Windows + 1 skip, packaged proof both systems.
- Bilingual cue split/merge preserves every source/target character, lock and time coverage, rejects too-short cues and avoids fabricated ellipsis. [CI 40863776921](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40863776921) **SUCCESS on final code/test SHA `99f1be8`**: 562 Linux / 561 Windows + 1 skip, desktop/native-host/frozen proof both. Intermediate incorrectly escaped newline assertion failure was corrected at `f94eb64` before final CI.
- P06 remains **IN PROGRESS**, not fully accepted: full cue undo history and timeline drag, quality/cost of live provider translation, large corpus, Windows user machine, live Chrome and accounts, non-NTFS/symlinks and power-loss tests are not verified. Unresolved intermittent Windows SQLite [#6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remains a separate P03/P04 blocker.

## P06 — In-session cue Undo/Redo and separate Editor shortcuts (29/10/2026)

- [Plan](phases/P06_CUE_UNDO_PLAN.md) was written before code. [Commit `39dc892`](https://github.com/danhgold7979-cyber/fonesi-edit/commit/39dc8927cb6b372974f8e1e599331374d4f0a389) introduces 100-state cue-table history preserving raw unfinished timestamps, cue IDs, text, locks and bulk-operation atomicity; undone drafts remain persisted and new documents reset this session's cue history. Ctrl+Z/Ctrl+Shift+Z operate on cues only on the Subtitle tab; Editor canvas Undo and native text Undo remain independent.
- [CI `40867002996`](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40867002996) discovered a cross-platform Qt editable-combo focus-proxy assumption (1 failed assertion on Linux/Windows). [Fix `8bfddb8`](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8bfddb8eef811b4421e7c2d7e2a3c02d197a3c3f) corrected both app routing and regression; no test was disabled.
- [CI `40867450628`](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40867450628) **SUCCESS on final code/test SHA `8bfddb8`**: **568 Linux PASS / 567 Windows PASS + 1 intentional POSIX skip**, check_plan, production desktop/native-host and frozen packaged proofs PASS both runners.
- Full P06 still **IN PROGRESS**: Undo history is bounded and not persisted as a command journal; drag cues directly on a timeline, live provider translation and cost, large corpus/IME/Windows user hardware and [intermittent SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) require separate acceptance evidence.

## P06 — Verified timing lane and ASS import style warnings (29/10/2026)

- **P06-05:** A selected cue can be moved or edge-trimmed via the Subtitle timing lane, with one Undo on mouse release, Esc cancellation, and original/translation text and locks preserved. [CI 40871166276](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40871166276) **SUCCESS on code/test SHA a6adf886**: Linux 579 PASS / Windows 578 PASS + 1 intentional skip, packaged desktop/native-host/frozen proof both OS.
- **P06-01:** Import ASS/SSA now clearly warns that style/position/effects/karaoke may not survive plain-cue editing/re-export. The warning is displayed with ordinary cue warnings, persisted through cue edits/draft reopen and cleared on loading plain SRT. Source ASS bytes untouched. [CI 40872415258](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40872415258) **SUCCESS on exact code/test SHA 67c8d015**: Linux 582 PASS / Windows 581 PASS + 1 intentional skip; plan validator and frozen app/native-host proofs passed both runners.
- **P06 NOT fully accepted.** ASS visual styles are not roundtripped. Multi-cue timeline dragging, all trim/speed preview/export parity, persistent Undo journal, real provider quality/cost, long corpus, Windows user-device/IME/HiDPI, Chrome/auth, GPU, power-loss and [intermittent SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remain OPEN. This is synthetic/local CI evidence, not full product acceptance.

## P06/P11 — Strict source-to-export subtitle timing under trim/speed (29/10/2026)

- Positive source cues that intersect a clip trim but become less than one representable output millisecond after speed rounding **fail explicitly** with cue index; no silent subtitle loss/success result. Rational offsets, adjacent cues and intentional out-of-trim exclusions have regression tests.
- Synthetic two-clip test checks different source trim/speed, transition overlap and independent source/target caption layers in the emitted ASS; both reference preview and actual export run, duration and source bytes verified. ASS centisecond timestamps are accepted with an **explicit max 5 ms edge rounding** (not 1 ms bitwise parity).
- Initial new test CI [40880618234](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40880618234) failed overstrict ASS timestamps, then [correction e8656dc](https://github.com/danhgold7979-cyber/fonesi-edit/commit/e8656dc8af45f80246c8a35624cad1ec602a8f40) fixed expectation. [Final exact-SHA CI 40881166137](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40881166137) **SUCCESS: 587 Linux / 586 Windows + 1 intentional skip; production desktop/native-host and frozen packaged proof PASS both**.
- P06/P11 remain **OPEN** for full frame/audio parity, VFR/rotation/mixed-FPS, live accounts/translation/quality/cost, physical Windows/HiDPI, sustained resources and power loss, and intermittent [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). No full release acceptance is implied.

## P11/P04 — Display-oriented rotation crop and VFR/mixed-FPS synthetic verification (29/10/2026)

- The FFprobe media model now captures Display Matrix rotation separately from encoded dimensions. Crop coordinates from `CropDialog` are **display-normalized** because its source preview is autorotated; compiled FFmpeg now uses the corresponding displayed pixel dimensions, including quarter-turn swap, rather than cropping from unrotated dimensions.
- FFmpeg synthetic +90° red/blue input verifies cropped reference and final MP4 center pixel colors match the chosen displayed area; original bytes remain unchanged. Additional P11 regression verifies a genuine VFR input with unequal frame PTS intervals alongside 24 FPS footage, without original audio, normalized to 25 FPS output with timed captions.
- [Final CI 40885720673](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40885720673) **SUCCESS at exact code/test SHA `5ab1bcad`**: 595 Linux PASS / 594 Windows PASS + 1 intentional skip; plan validator, desktop/native-host build and synthetic localhost frozen packaged proof PASS both. Windows development artifact created.
- **Only the bounded synthetic slice is verified.** Physical Windows/HiDPI/real mobile rotation and VFR audio sync, GPU, full frame/audio parity, longer corpus and durability, Chrome/live accounts, Windows installer and intermittent [SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remain OPEN. No full P04/P11 or product-release acceptance.

## P03/P11 — SQLite WAL initialization connection cleanup (29/10/2026)

- `Store.connect()` now closes the SQLite connection even if `journal_mode=WAL` or `busy_timeout` PRAGMA setup raises before handing the connection to a caller. No migration, rollback-policy change, WAL removal or configuration bypass was introduced.
- Parameterized fault-injection tests wrap real SQLite handles and confirm the setup failure is propagated, `close()` runs once, later settings/transactions work normally and SQLite `integrity_check` remains `ok`. [CI 40887831717](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40887831717) **SUCCESS exact source/test SHA `fd28de70`: 598 Linux PASS / 597 Windows PASS + 1 intentional skip**, plan checker and frozen desktop/native-host proof both OS.
- **Known Windows [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remains OPEN.** Intermittent `database disk image is malformed` is not reproduced or attributed to this fixed initialization-handle defect. Stress/NTFS/ACL/power-loss on real Windows hardware remain outstanding; P03/P11 not fully accepted.

## P06-03 — Verified collision-safe glossary protection (29/10/2026)

- Glossary replacements use a one-pass longest-match tokenization of the **original** source cue, with markers checked against source/terms/replacements; provider output must preserve marker occurrence counts or the cue is rejected before translation cache write. Regression includes legacy literal placeholders, overlapping terms and marker-prefix keys.
- [CI 40893822256](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40893822256) **SUCCESS on source/test SHA 1a2347b**: **602 Linux PASS / 601 Windows PASS + 1 intentional skip**, full desktop/native-host/frozen synthetic proof on both runners.
- **No live provider validation or paid-call quality/billing proof**; full P06 remains OPEN. Windows SQLite [issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) is unrelated and OPEN with unknown cause.

## P03/P04/P11 — Failed SQLite autosave recovery and bounded proxy shutdown regression (29/10/2026)

- [Source 085aa52](https://github.com/danhgold7979-cyber/fonesi-edit/commit/085aa5278ccb2d2d128b94371e10668e790d4ff1): `MainWindow.autosave` attempts atomic `recovery.json` with latest in-memory composition when SQLite fails, re-raises the original DB error, and `closeEvent` refuses to close before data/settings persistence succeeds. Window, scheduler and workers remain available to retry; no dangerous automatic DB/WAL deletion is used.
- [Tests 50a0137](https://github.com/danhgold7979-cyber/fonesi-edit/commit/50a0137dcbc75bb0042e3b02c9ffe5cc4162a440): real-Qt SQLite fault injection plus three rounds of same-test-DB FFmpeg proxy/background close/reopen, validating `journal_mode=wal`, `integrity_check=ok`, saved project and unchanged source. [CI 40897627521](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40897627521) **SUCCESS exact SHA**: **604 Linux / 603 Windows + 1 intentional POSIX skip**, frozen packaged proof both OS.
- [Known Windows SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) **remains OPEN**. No root cause was reproduced in bounded CI; true NTFS/AV interference, long soak and sudden loss of power still require separate evidence. P03/P04/P11 and all product gates are NOT fully accepted.

## P03-07 / P11-02 — Safe automatic replay of valid newer recovery snapshot (29/10/2026)

- [Code 8b5b67d](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8b5b67d5dbaa89618060962a800479ae09b69aef) extends startup restore: if SQLite is healthy, prefer a separately stored **newer, validated, same-project** `recovery.json` over a stale SQLite project. Ignore stale/mismatched/malformed/linked/oversized snapshots; allow recovery into otherwise empty project database without modifying stored rows before normal save.
- [Regression/fix 05ac32a](https://github.com/danhgold7979-cyber/fonesi-edit/commit/05ac32a7e425e2a721689b1450345c951b724e1f) covers actual fault-injected autosave snapshot, process-lock-safe reopen, wrong/old/corrupt snapshots, empty DB and subsequent persistence. Intermediate [CI 40902021585](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40902021585) failed the test fixture's prohibited concurrent scheduler instance; it was corrected without changing production lock protection.
- [CI 40902670624](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40902670624) **SUCCESS on exact SHA 05ac32a**: **607 Linux PASS / 606 Windows PASS + 1 intentional skip**, production desktop/native-host and frozen app proofs passed both runners.
- **Still OPEN:** if SQLite cannot even initialize, this feature does not launch/reconstruct the database. Physical Windows NTFS/AV/WAL stress, abrupt power loss and intermittent [SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remain unresolved. P03/P11 not fully accepted.

## P03/P11 — Atomic project + last_project autosave (29/10/2026)

- [plan](https://github.com/danhgold7979-cyber/fonesi-edit/blob/develop/fonesi-full/docs/phases/P03_ATOMIC_AUTOSAVE_SELECTION_PLAN.md) → [source/test d4117b5](https://github.com/danhgold7979-cyber/fonesi-edit/commit/d4117b580b90ff4b8471907b8e8b1fc56d702a4d). The selected project row and `settings.last_project` now share one SQLite transaction. Injected `last_project` INSERT/UPDATE errors roll back the project row as well; recovery.json still carries current unsaved edits for later safe replay, and a healthy retry succeeds.
- [CI 40905102578](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40905102578) **SUCCESS at exact SHA d4117b5**: Linux **611 passed** / Windows **610 passed + 1 intentional POSIX skip**; `check_plan`, desktop/native-host build and frozen synthetic/localhost proof PASS both. Windows development artifact uploaded.
- This fixes a deterministic partial-commit/autosave inconsistency, **not** the intermittent [Windows SQLite corruption #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6), whose root cause is UNKNOWN. Physical Windows NTFS/AV/power-loss, live provider/Chrome/GPU and full product gates remain OPEN; no `main` merge.

## P08-01 / P11-05 — Advanced codec/FPS/video bitrate Batch filters (29/10/2026)

- [P08 plan](https://github.com/danhgold7979-cyber/fonesi-edit/blob/develop/fonesi-full/docs/phases/P08_ADVANCED_METADATA_FILTER_PLAN.md) → [code 6307042](https://github.com/danhgold7979-cyber/fonesi-edit/commit/630704259e38e3ed829817230344ce7a14c993bd) → [tests 81952fd / a0d9e74](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a0d9e74e4fd356568ecaf60c49a5edc0a2bc9d6f). FFprobe video codec, rational FPS and optional video-stream kb/s power the asynchronous Batch UI filter. Unknown bitrate is not substituted with container bitrate; invalid min/max ranges are rejected, hidden selected source files and dry-run stay preserved. Source media and SQLite schema unchanged.
- [CI 40908188050](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40908188050) **SUCCESS at code/test SHA a0d9e74**: Linux **618 PASS**, Windows **617 PASS + 1 intentional POSIX skip**; plan references, production desktop/native host, frozen packaged synthetic/localhost workflows/UI proof PASS both runners, Windows development artifact uploaded.
- **Open:** very large Batch benchmarks/performance/ETA, advanced audio playlist/SFX/meter, physical Windows user-machine, Chrome/auth/live provider, HiDPI/GPU and full P08/P11/95-group acceptance. No `main` merge.

## P08-07/P11-02 — Partial batch planning with explicit bad-file report (29/10/2026)

- [P08 plan](https://github.com/danhgold7979-cyber/fonesi-edit/blob/develop/fonesi-full/docs/phases/P08_PARTIAL_BATCH_PLAN.md) → [code 0e9cb5c](https://github.com/danhgold7979-cyber/fonesi-edit/commit/0e9cb5cbc8f345dcd8e152912effe0b849380e8a) → [tests d0753e3](https://github.com/danhgold7979-cyber/fonesi-edit/commit/d0753e3586266fda33ae8e4f8367a124d718ac37); a bad video or infeasible clip-specific duration no longer aborts every valid source **in opt-in Qt report mode**. Source-only errors use sanitized reason categories; invalid global audio mapping remains fatal, legacy fail-fast callers preserved. Empty reports disable preview/enqueue and stale callbacks are ignored.
- [CI 40910523178](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40910523178) **SUCCESS on exact code/test SHA d0753e3**: Linux **621 passed** / Windows **620 passed + 1 intentional skip**, plan checker, production desktop/native-host builds and frozen synthetic/localhost proof PASS both; Windows development artifact uploaded.
- Remaining: large-corpus/ETA, physical Windows/NTFS/AV/ACL/long soak, live account/Chrome/GPU, playlist/meters and full P08/P11/product gates. No `main` merge.

## P08-07/P11-03 — Cancel-safe Batch progress and synthetic throughput (29/10/2026)

- [Plan](phases/P08_BATCH_PROGRESS_BENCHMARK_PLAN.md) → [code/test 6534c41](https://github.com/danhgold7979-cyber/fonesi-edit/commit/6534c41ed457f4380b319b9cd83a7409cba8cd10). Real Task cancellation now stops Batch planning cooperatively; no partial plans can be previewed/queued, and progress uses a known selected count. 512 logical-source regression and 128 generated FFmpeg MP4 copy/FFprobe benchmark included; disposable media never committed.
- [CI 40914027736](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40914027736) **SUCCESS exact SHA 6534c41**: 627 Linux passed / 626 Windows passed + 1 intentional POSIX-only skip; source, 128-file FFprobe benchmark, desktop/native-host and frozen packaged synthetic/localhost proofs passed on both runners. Windows development artifact uploaded. **Measured 128 synthetic input files**: Linux 5.938 seconds (21.556/s), Windows 10.462 seconds (12.235/s), with Python peak tracing and process RSS snapshots in CI evidence. These are NOT render ETA or hardware acceptance; full P11-03 performance scope remains OPEN.

## P08-07/P11-02 — All-or-none SQLite Batch enqueue (29/10/2026)

- [Plan](phases/P08_ATOMIC_ENQUEUE_PLAN.md) → [source 5c35b2f](https://github.com/danhgold7979-cyber/fonesi-edit/commit/5c35b2f8ab989c05346c01adefe77e27f6e8a0dc) → [code/test d6b218a](https://github.com/danhgold7979-cyber/fonesi-edit/commit/d6b218af9a7bd6cc0ac2a9789c3d9fec224da664). `Store.submit_many` prevalidates immutable snapshots/tool paths and commits all new Batch jobs in one SQLite transaction; duplicate/malformed outputs fail before insertion. SQLite injected failure at second INSERT and Qt retry tests confirm no partial jobs, untouched original plans/source files and no false Queue navigation.
- [CI 40916078055](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40916078055) **SUCCESS exact SHA d6b218a**: 631 Linux passed / 630 Windows passed + 1 intentional POSIX-only skip; source, 128-file FFprobe benchmark, desktop/native-host and frozen packaged synthetic/localhost proofs passed on both runners. Windows development artifact uploaded. **Still OPEN:** physical Windows user PC/NTFS/ACL/antivirus/power loss, diverse large corpus and actual FFmpeg render ETA/size, Chrome/providers/GPU/HiDPI/installer; [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remains unknown root cause; no `main` merge.

## P08/P11 — Existing-output Batch enqueue preflight (29–30/10/2026)

- [plan](https://github.com/danhgold7979-cyber/fonesi-edit/blob/develop/fonesi-full/docs/phases/P08_EXISTING_OUTPUT_PREFLIGHT_PLAN.md) → [code/test b845a4c](https://github.com/danhgold7979-cyber/fonesi-edit/commit/b845a4c38c9514794dce82eada8e867f8e9b4c9e). Preflight rejects a Batch output already present as file/directory/symlink (including dangling links) before atomic all-or-none SQLite submission. Existing source/output and old jobs preserved; Qt keeps dry-run on collision for a safe retry; renderer's no-overwrite finalizer remains unchanged.
- [CI 40919530634](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40919530634) **SUCCESS exact code/test SHA b845a4c**: **635 Linux passed / 634 Windows passed + 1 intentional skip**, plan validation, 128 synthetic FFprobe benchmark, desktop/native-host and frozen packaged synthetic/localhost proof PASS both runners; Windows artifact uploaded.
- P08/P11 and 95-group product gates still OPEN for physical Windows/NTFS/AV/ACL, true output size/render ETA, user-corpus performance, Chrome/live accounts/GPU/HiDPI and intermittent SQLite issue #6. No `main` merge.


## P08-04/P11-04 — SFX trigger không đều (30/10/2026)

[Code/test f6d90e4](https://github.com/danhgold7979-cyber/fonesi-edit/commit/f6d90e4470cdca3e98f23e48f4f0983521540a80) và [CI 40988695667 attempt 2](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40988695667) SUCCESS: Linux 656 passed; Windows 655 passed + 1 intentional skip. Check plan, benchmark 128 video, desktop/native-host và frozen packaged proof cả hai OS PASS. Artifact Windows development khoảng 197 MB, retention đến 06/11/2026. Lần Windows đầu lỗi Chocolatey 503; retry job PASS. Playlist nhiều nguồn, meter realtime và nghiệm thu máy người dùng vẫn mở.


## P08-03/P11-04 — Decoded playback PCM meter (30/10/2026)

[Source/tests](https://github.com/danhgold7979-cyber/fonesi-edit/commit/c706930e2c5e8a5026e37fb5fd856901585330b5) → [fix 743e68b](https://github.com/danhgold7979-cyber/fonesi-edit/commit/743e68b3e4c262fa4bc824f9ccca4f1ec67361c2) → [CI 40996183826](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40996183826) **SUCCESS exact SHA 743e68b**: Linux 676 tests PASS, Windows 675 PASS + 1 intentional POSIX skip, check_plan/128-FFprobe benchmark/desktop-native-host/frozen synthetic+localhost proof on both OS. Qt meter reports digital playback PCM Peak/RMS dBFS and warning count (threshold >=0.99) for source/proxy or rendered-composition preview, **not device output, true peak, calibrated loudness or pre-mix tracks**. Additional absent-Qt-tap test introduced in 651cb35 pending its own CI. User Windows/audio hardware, live Chrome/providers, large corpus and full P08/P11/product gates remain OPEN.


## P08-04 — Manual cross-folder audio playlist (30/10/2026)

[Implementation](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a4ea6a851ac912503ce4db6fb08841b9dae8257a) → [final integration fix](https://github.com/danhgold7979-cyber/fonesi-edit/commit/cfd2c4cf6a7c7a96e5619631d83c13ff2e2039c0) → [CI 41000959481](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41000959481) **SUCCESS exact SHA cfd2c4c**: 682 Linux passed, 681 Windows passed + 1 intentional POSIX-only skip; plan check, 128 synthetic FFprobe benchmark, desktop/native-host and frozen packaged render/Batch/Matrix/download/UI proof PASS both OS. Manual playlist maps one absolute audio path per selected video in editable line order across multiple directories, preflights all distinct paths before snapshot, allows duplicate sources/same basenames, and preserves music/SFX tracks. Real FFmpeg/PCM test verifies the selected 660 Hz track. P08/P11 remain in progress for ETA/size, per-track/hardware audio and real Windows acceptance.

## P09-01 / P11-05 — Scene order and legacy history safety (30/10/2026)

[Plan](phases/P09_SCENE_REORDER_PLAN.md), [code/test SHA 3ff0e31b28d6c12caeaaf4ae60d7f79eb28818b8](https://github.com/danhgold7979-cyber/fonesi-edit/commit/3ff0e31b28d6c12caeaaf4ae60d7f79eb28818b8) và [CI 41016748802](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41016748802) **SUCCESS**: Linux **701 PASS**, Windows **700 PASS + 1 intentional POSIX skip**; full source suite, plan checker, 128-video FFprobe synthetic benchmark, desktop/native host và frozen packaged render/Batch/Matrix/download/UI proof cả hai runner. Trong MatrixPage có kéo-thả cảnh và Lên/Xuống; thay đổi thứ tự logic không đổi bytes/path/hash của tệp, bảo toàn hàng/khóa, vectors thời lượng và riêng biệt job đã queue. SQLite history được căn theo scene identity duy nhất; nếu hash trùng/nguồn thiếu thì từ chối, không suy đoán/nới W/K hoặc sửa DB. Enqueue chặn cả tổ hợp đã reserved dưới thứ tự cảnh khác và rollback toàn batch khi lỗi.

**OPEN:** scene exclusion/scene-level lock nâng cao, lịch sử hash cross-scene ambiguous, solver corpus lớn, thao tác kéo thả trên Windows máy người dùng, filesystem/Power loss và SQLite issue #6 unknown root cause, Chrome/live provider, GPU/audio/installer/HiDPI; không coi P09 hay release đạt toàn bộ.

## P09-01/P09-03/P11-05 — Explicit C/G filter and scene-wide angle pin (30/10/2026)

[Detailed plan](phases/P09_SCENE_SELECTION_LOCK_PLAN.md), [source/test SHA `7d1f928a798b8cb50997a25e8f8947dfc0f83999`](https://github.com/danhgold7979-cyber/fonesi-edit/commit/7d1f928a798b8cb50997a25e8f8947dfc0f83999) and [CI 41021003352](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41021003352) **SUCCESS exact source/test SHA: 728 Linux PASS, 727 Windows PASS + one intentional POSIX skip**. Desktop/native host, 128-source synthetic FFprobe benchmark and frozen packaged render/Batch/Matrix/localhost/Qt proof pass on both runners. Qt MatrixPage now has explicit scene/angle checkboxes, a pinned G in all new rows, preserved path/hash/G with logical C ordering, saved selections only for an exact source manifest and stale-worker protection. Full prior SQLite history is mapped conservatively onto new scene subsets before generate and enqueue. A known shorter historical set is structurally incomparable to a larger composition; unknown/ambiguous hashes fail closed. Synthetic render, real Qt and SQLite regression do not replace physical Windows/large matrix/Chrome/live account/GPU/installer acceptance. [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) remains OPEN with unknown root cause; full P09/P11/release NOT accepted.


## P09-03 / P09-06 — Solver benchmark and cancel-safe Matrix queue (30/10/2026)

- Generator validates typed N/W/K/seed and finite positive budget; logical `scripts/benchmark_matrix.py` measures elapsed/tracemalloc on 14 scenes × 6 angles (capacity 6^14), validates 100 unique W=1/K=2 rows without full Cartesian media expansion, and explicitly reports incomplete rather than claiming UNSAT. No physical 100k-corpus proof.
- `enqueue_rows` supports cooperative Task cancel and progress, with all-new SQLite jobs/history rolled back if revoked before commit. SQL upsert now uses valid `excluded.job_id`; failed reservation retry explicitly tests new job ID. MatrixPage cancels obsolete pre-publication work on C/G filter/order, cell/locks, seed/W/K/output/audio/editor options, and global cancel; duplicate clicks blocked; successful prior-snapshot commits reported truthfully. Backend synthetic-media/SQLite and real Qt offscreen regressions included.
- [CI 41025266091](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41025266091) SUCCESS, exact code/test SHA `7d2d74a7173184d1e752e508ff83aa8971f72321`: 764 Linux PASS; 763 Windows PASS + one intentional POSIX skip; 128-source synthetic FFprobe benchmark, production desktop/native-host builds, frozen packaged render/Batch/Matrix/localhost/Qt proof PASS both runners. Windows development artifact 197,335,201 bytes, expires 2026-11-06. Synthetic/localhost evidence only; NOT physical Windows/HiDPI/installer, full 100k-real-media throughput/solver optimality, NTFS/exFAT/power loss, SQLite issue #6 root cause, live Chrome/provider or GPU acceptance.
- Full P09/P11 and all release gates remain OPEN; do not merge main.


## P09-03 / MAT-04 — Large-space balance selection (30/10/2026)

Bounded candidate pool (default 8, validated 1..64) now competes legal rows using projected per-scene sum-of-squares and seeded tie-breaking. Frequency is keyed by (scene index, content hash), so same-content assets in different scene folders are not merged. Candidate search preserves W/K/history/locks/uniqueness, bounded time and cancellation, with explicit incomplete-not-UNSAT result. The logical benchmark CLI records per-angle use, spread, elapsed time and tracemalloc peak; CI writes its JSON artifact.

[CI 41030170331](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41030170331) SUCCESS exact code/test SHA `4e759cdbaaa738b3df60a577e0a4cd6091cf6ed5`: Linux 781 PASS; Windows 780 PASS + 1 intentional POSIX-only skip. Both runners: 10^10 theoretical combinations, 2,000 outputs, per-scene max spread 5; Linux 9.302552 s / 1,379,048-byte Python tracemalloc peak, Windows 19.737411 s / 1,379,264-byte peak. Both passed Batch 128-source FFprobe synthetic benchmark, phase-reference check, production desktop/native-host build and frozen packaged render/Batch/Matrix/localhost-download/Qt proof. Artifacts: Linux evidence 390,000 bytes, Windows evidence 322,514 bytes (expire 2026-11-02); Windows development build 197,343,856 bytes (expires 2026-11-06). Logical IDs and synthetic/localhost proof only, not real 10-billion media or physical Windows/GPU/live-provider acceptance.

Still OPEN: 100k real-media corpus/global solver optimality, physical Windows/HiDPI/installer, NTFS/exFAT/power loss, SQLite issue #6 root cause, live Chrome/providers and GPU. P09/P11/full release not complete.

## P09-06 / P11-02 — Matrix reservation recovery (30/10/2026)

- Implemented same-job reservation ownership checks for retry; partial/missing identity and missing/foreign/succeeded reservation states fail closed.
- Added recovery/cancel/retry regressions, reassignment protection, unrelated-history invariants and missing-source no-false-success check.
- Exact HEAD [a6d1e95](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a6d1e9577c2017519c0ecf22edf63f8695a79402); [CI 41035225664](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41035225664) SUCCESS: 788 Linux PASS; 787 Windows PASS + 1 intentional POSIX-only skip. Both packaged synthetic proofs passed.
- Logical Matrix benchmark: 10^10 theoretical capacity, 2,000 generated, complete=true, max per-scene spread 5. Synthetic Batch benchmark: 128 sources, failed_count=0.
- P09/P11 remain OPEN. No physical Windows power-loss/AV/ACL/NTFS/exFAT, SQLite issue #6 root-cause, 100k real-media, live Chrome/provider or GPU acceptance is claimed. Do not merge main.

## P11-02 — Matrix artifact recovery at the worker commit boundary (30/10/2026)

- Added three regression cases: reuse an already-published MP4 + matching sidecar after recovery before Store.finish; reject an orphan output without sidecar; reject a tampered output whose sidecar SHA is stale.
- Matching artifact is reused with identical SHA and committed as succeeded exactly once. Unverifiable/mismatched artifacts are preserved, not overwritten or marked succeeded.
- Test commit [8101f21](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8101f210dfdeac160f7b9f2729fc1d01cfc33fa1); [CI 41037280021](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41037280021) SUCCESS: Linux 791 PASS; Windows 790 PASS + 1 intentional POSIX-only skip. Both packaged synthetic proofs passed.
- P11 remains OPEN. Physical power-loss/AV/ACL/NTFS/exFAT, SQLite issue #6, real-media scale, Chrome/live providers and GPU remain unverified.


## P11-05 / OPS-07 + AUTH-11 — Preset schema and pairing regression (30/10/2026)

[Plan](phases/P11_PRESET_SCHEMA_VALIDATION_PLAN.md) → [implementation a7f2328](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a7f2328fa3448b5e9664e83dcb5d0f7793f0bdec) → [profile revoke test e3d3272](https://github.com/danhgold7979-cyber/fonesi-edit/commit/e3d3272cf8753fe08652b8f1d54bf8f5359214cb) → [CI 41046744447](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41046744447) SUCCESS exact HEAD e3d3272.

Preset schema v1 bounds import at 2 MiB, rejects malformed UTF-8/JSON, duplicate keys, non-finite numbers, unsupported/boolean schema versions, unknown envelope fields, invalid names, secret-bearing payloads, source clips and clip bindings. Export strips source clips/clip IDs. Import validates fully before persistence, keeps active project/composition unchanged, and reports missing external image/font/audio assets without copying or deleting them. Regression tests cover round-trip, missing assets, invalid envelope/composition, secret fields, size, duplicate keys, atomic invalid import and valid Qt import/export.

Browser regression proves profile-scoped pairing revocation: A bridge and pending code are revoked, A/B Chrome profile directories and both account bindings remain, and B bridge is unaffected.

CI: Linux 817 PASS; Windows 816 PASS + 1 intentional POSIX-only skip. Batch 128-source synthetic FFprobe dry-run: 7.751278 s Linux / 10.102146 s Windows, failed_count=0. Matrix logical-ID benchmark: 2,000 complete outputs on both, max per-scene spread 5 (19.860847 s Linux / 17.556047 s Windows). Production desktop/native-host build and frozen packaged render/Batch/Matrix/localhost video+image download/UI proof passed both OS. Artifacts: Linux evidence 391,472 bytes; Windows evidence 323,245 bytes (expire 2026-11-02); Windows development build 197,366,359 bytes (expires 2026-11-06).

This closes only the bounded preset/revocation regression slice. P11 remains OPEN for full 95-group audit, physical Windows/HiDPI/GPU/audio, real Chrome/DPAPI/provider, SQLite issue #6 root cause, real-media corpus, power-loss/AV/ACL/NTFS/exFAT and long soak. Do not merge main.


## P11-08 / TOL-05 — ZIP installer archive preflight (30/10/2026)

- ZIP extraction now rejects traversal/absolute/drive paths, symlink/special Unix entries, encrypted members, Windows reserved names/invalid characters/trailing dot-space, case-insensitive duplicates and file/directory collisions. Full preflight occurs before any member is written; path separators are normalized for both OS.
- Final implementation [85654ec](https://github.com/danhgold7979-cyber/fonesi-edit/commit/85654ec780f3ab8752af834e081a46f406d124d8); [CI 41053597336](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41053597336) SUCCESS: Linux 850 PASS; Windows 849 PASS + 1 intentional POSIX skip; Batch/Matrix benchmarks, production/native-host builds and packaged proofs both OS.
- Synthetic Batch: 128 sources, failed_count=0 (5.012570 s Linux / 10.882223 s Windows). Logical Matrix: 2,000 outputs complete, max spread 5 (9.079294 s Linux / 17.686874 s Windows).
- Artifacts: Linux evidence 390,874 bytes; Windows evidence 323,726 bytes; Windows development build 197,380,520 bytes.
- Scope is archive preflight only. Real Windows ACL/AV/disk-full/power-loss, installer/update, tool lease/GC, Chrome authentication, providers, GPU/HiDPI/audio and full P11/P12 remain OPEN.


## P11-08 / TOL-04…06 — Replacement installer failure atomicity (30/10/2026)

- Added four tests: interrupted partial download, checksum mismatch, cancel immediately after fetch, and malicious archive rejected during installer integration.
- Every case keeps the previous verified FFmpeg/ffprobe binary bytes, companion path, active tool_paths and active-version metadata unchanged; no new version is published/activated, temporary staging is removed and failed progress never reaches 100%.
- [Commit 096d6bb](https://github.com/danhgold7979-cyber/fonesi-edit/commit/096d6bbb16768fb8c063109d2e4def5cd9e64dd6); [CI 41056951728](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41056951728) SUCCESS: Linux 854 PASS; Windows 853 PASS + 1 intentional POSIX skip; benchmarks, production/native-host build and packaged proof both OS.
- Synthetic Batch: 128 sources, failed_count=0 (7.996895 s Linux / 10.505177 s Windows). Logical Matrix: 2,000 outputs complete, max spread 5 (19.011149 s Linux / 17.623936 s Windows).
- Artifacts: Linux evidence 392,162 bytes; Windows evidence 323,821 bytes; Windows development build 197,385,904 bytes.
- Real Windows ACL/AV/disk-full/process-kill/power-loss, signed installer/update UX, Chrome/provider auth, GPU/HiDPI/audio and full P11/P12 remain OPEN.


## P11 progress — SFX timing and Settings update concurrency (30/10/2026)

[CI 41080729485](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41080729485) exact HEAD `0a0aef945fe3ca3759d30248aa50c3667ef58b48` SUCCESS: Linux 884 passed / 0 skipped; Windows 880 passed / 4 intentional platform skips / 0 failures. Custom and repeated SFX timing tests now pass on Windows after sample-clock normalization; five new Settings Qt tests cover per-tool busy reservation, FFprobe alias, independent tools, install-missing skip behavior, disabled/guarded actions and worker completion/scheduling races. Both OS passed synthetic Batch (128 inputs, no failed plans), logical Matrix (2,000 outputs, complete, max spread 5), production/native-host build and frozen packaged proof.

Remaining P11/P12 gates are still OPEN: real Windows user-machine ACL/AV/disk-full/power-loss, signed installer/update UX and cross-process coordination, live Chrome/provider auth and challenge/expiry, GPU/HiDPI/audio devices, large real-media corpus/soak and SQLite issue #6.

## P11-08 / AUTH-06, AUTH-08 — Bridge handoff/revocation ordering (30/10/2026)

[Exact-HEAD CI 41088435585](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41088435585) SUCCESS on 683f5326021f88da04441b43894d8e9dd16fcc83: Linux 892 passed / 0 skipped; Windows 888 passed / 4 intentional platform skips / 0 failures. receive_session checks the bridge inside BEGIN IMMEDIATE; revoke_pairing uses the same writer lock. Revoke-first and handoff-first deterministic concurrency tests pass. Both runners passed Batch 128-source dry-run (5.873457 s Linux / 7.603461 s Windows; no failed plans), logical Matrix 2,000 outputs (11.955144 s Linux / 9.672810 s Windows; complete, max spread 5), production/native-host builds and frozen packaged proof.

OPEN: pending pairing-code issuance is not yet serialized with revocation; live Chrome/extension/DPAPI/provider and physical Windows acceptance remain separate gates.
