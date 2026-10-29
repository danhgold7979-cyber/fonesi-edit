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
| P08 | Batch nhiều folder local/khử trùng, filter FFprobe duration/short-edge, chọn/đảo/chặn stale; audio mapping/duration solver; SFX giây/%/scene/video **và repeat count/interval FFmpeg + AudioDialog**, music loop crossfade FFmpeg; CI Linux/Windows + frozen PASS | Trigger SFX tùy ý/playlist, metadata codec/FPS/bitrate, corpus lớn/ETA, meter/solo realtime, Windows audio/installer máy đích |
| P09 | Lazy matrix, W/K/history/lock, **regenerate một hàng** không đổi hàng khác, thống kê usage, formula sync; **weights/manual seconds** và speed bounds từ UI đến render; CI/frozen Linux/Windows PASS | Stress solver ma trận lớn, reorder cảnh/locks nâng cao và Windows/exFAT thực |
| P10 | Workflow/watch/scan-first new-only schedules và resources; Settings quota proxy cache/janitor nền an toàn, bảo vệ file QMediaPlayer đang phát; CI/frozen PASS | Task Scheduler, GPU/VRAM/driver thật, cache khác/installer và Windows/ACL/soak |
| P11 | Test local và app integration đang mở rộng | Regression cuối và đối chiếu đầy đủ tùy chọn |
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
