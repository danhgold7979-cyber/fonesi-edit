# Fonesi Edit — Trạng thái triển khai

Bản phát triển, chưa tuyên bố nghiệm thu toàn bộ 95 nhóm yêu cầu. Theo chỉ đạo người dùng, tiếp tục phần độc lập qua mọi phase; không dừng vì mạng/tài khoản/Windows/GPU và không gắn các mục đó là pass.

| Phase | Code/kiểm chứng hiện có | Cổng còn riêng |
| --- | --- | --- |
| P01 | Thiết kế, luồng, contracts, traceability | Cập nhật theo thay đổi đã được chấp thuận |
| P02 | Source tests và frozen packaged proof Linux/Windows CI đạt; đã sửa lỗi gallery-dl Unicode console | Live nguồn/dịch, Chrome/session handoff, GPU/VRAM, installer/rollback và nghiệm thu trên máy Windows người dùng |
| P03 | Domain/SQLite/snapshots/worker; backup có integrity/no-overwrite, credential alias checks và error redaction; CI Linux/Windows pass | Soak/crash/power-loss, filesystem không hỗ trợ hard link, installer và nghiệm thu máy Windows người dùng |
| P04 | Canvas/inspector/timeline/undo, rendered In–Out loop, async thumbnail strip, validated source proxy; peer snap + viewport guides; normalized crop + ratio-lock/anchor tests; Save As + Ctrl+Shift+S; focus-aware Ctrl+A/C/V/X layer clipboard; Escape cancels active drag; latest slices CI Linux/Windows + frozen proof PASS | Rotation metadata/VFR/mixed FPS, HiDPI/4K/seek/audio-sync/long timeline, remaining shortcut/customization cases, remaining P04 tasks and real Windows user-machine acceptance |
| P05 | yt-dlp/gallery-dl, profile/binding và bridge; thêm scan→cây checkbox theo trang, lựa chọn/tải item đúng engine/account, URL signed/duplicate bảo vệ; CI/packaged Linux/Windows PASS | Provider pagination/checkpoint và live 10 nền tảng, tài khoản Chrome/identity thực, batch lớn và filter/sort nâng cao |
| P06 | SRT/VTT/ASS, sửa/lock/cache/quota/provider adapters | Chất lượng/chi phí dịch live và kiểm tra ngôn ngữ provider |
| P07 | Compositor, motion/keyframes, font, mask, alpha, audio, reference | Từng tổ hợp style/OS/GPU, performance target |
| P08 | Batch nhiều folder local/khử trùng, filter FFprobe duration/short-edge, chọn/đảo/chặn stale; audio mapping/duration solver; SFX giây/%/scene/video **và repeat count/interval FFmpeg + AudioDialog**, music loop crossfade FFmpeg; CI Linux/Windows + frozen PASS | Trigger SFX tùy ý/playlist, metadata codec/FPS/bitrate, corpus lớn/ETA, meter/solo realtime, Windows audio/installer máy đích |
| P09 | Lazy matrix, W/K/history/lock, **regenerate một hàng** không đổi hàng khác, thống kê usage, formula sync; **weights/manual seconds** và speed bounds từ UI đến render; CI/frozen Linux/Windows PASS | Stress solver ma trận lớn, reorder cảnh/locks nâng cao và Windows/exFAT thực |
| P10 | Workflow/watch/schedule và resources; Settings quota proxy cache/janitor nền an toàn, bảo vệ file QMediaPlayer đang phát; CI/frozen PASS | Task Scheduler, GPU/VRAM/driver thật, cache khác/installer và Windows/ACL/soak |
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

