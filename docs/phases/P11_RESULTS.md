# P11 — Kết quả tích hợp local

Toàn suite cuối: **92 tests qua, không lỗi/skip**. Đã kiểm tra app save/reopen/worker/output, kéo preview bằng chuột và một drag một undo, undo riêng khi nhập chữ, sub draft/song ngữ/trim-speed/loop, preset deterministic, batch settings/random zoom/flip/rotation, audio solo/duck/normalize, ma trận W/K/reservation, rename/undo/rollback/recovery, khóa scheduler/migration/orphan và tool repair/hash/traversal.

HTTP localhost thực kiểm tra cả yt-dlp và gallery-dl; fake transport riêng kiểm tra cache/quota/glossary/translation recovery. Không dùng chúng làm bằng chứng hỗ trợ mạng xã hội hoặc chất lượng dịch live. Binary đã chạy các workflow CPU chính và giải mã frame Qt trong smoke; xem [báo cáo local](../LOCAL_VERIFICATION.md), [evidence](../evidence/desktop-verification.json), [đối chiếu triển khai](../IMPLEMENTATION_COVERAGE.md).

Những sửa đáng chú ý: sub template không giữ nhầm cue/video cũ; nhiều cue dùng chung ASS track; clip split/loop giữ phạm vi sub; W/K được kiểm tra trong transaction enqueue; retry không đổi thành công thành reserved; orphan được phục hồi sau startup; nick/profile không đổi khi refresh; FFmpeg gói không nạp libavcodec của Qt; nguồn đổi tên giữ bytes và journal.

Các mục nâng cao còn phải code/kiểm chứng vẫn ở coverage/master; Windows/live API/Chrome/nguồn/GPU có cổng riêng. 92 tests không chứng minh toàn bộ 95 nhóm đã hoàn tất.

## Bổ sung đối chiếu truy vết P11 (28/10/2026)

Đã cập nhật `scripts/check_plan.py` để phát hiện mất hoặc trùng nhóm trong 95 yêu cầu, thiếu tên/nguồn/task/tiêu chí nghiệm thu và task không có trong master. Bổ sung `tests/test_plan_contract.py` kiểm tra bản gốc và các trường hợp tài liệu bị thiếu/mapping sai. Đây là kiểm tra **tài liệu truy vết**, không đánh dấu 95 nhóm chức năng đã nghiệm thu. Bộ test P11 mới nhất cần kết quả CI riêng; khi chưa có run PASS thì chưa được ghi cả phase P11 thành công.

**Kết quả kiểm thử P11 validator trên nhánh tổng:** commit `eaed54fa54c0013959c2f552a3d9f8e9676189ff`; [CI 40639610919](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40639610919) PASS — 143 tests Linux, 142 Windows + 1 skipped fixture POSIX, packaged proof cả hai hệ PASS. Đã phát hiện/sửa lỗi import trong test mới trước run thành công. Chỉ nghiệm thu validator tài liệu/luồng kiểm thử synthetic, không nghiệm thu toàn bộ 95 nhóm hay live platform.


## Regression tích hợp P04/P10 — 28/10/2026

[CI 40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) PASS 195 Linux, 194 Windows + 1 skipped POSIX fixture. Source suites và frozen app proof trên cả hai hệ kiểm tra proxy/cache, rendered In–Out loop, thumbnail source FFmpeg, cache quota/protected/symlink và Qt Settings/preview integration. Không phải nghiệm thu đầy đủ 95 nhóm hoặc chứng nhận PC Windows/GPU/Chrome/live source.

## P11-01/P11-04 — Two-clip subtitle time-map QA (29/10/2026)

A new synthetic FFmpeg integration uses two clipped sources with different speeds, 100 ms transition and two independent source/translated subtitle layers. It inspects actual ASS cue timestamps and text for both clip scopes, probes the encoded output, renders a reference frame using the shared graph and verifies source media remains unchanged. Production mapping now raises on a positive source cue that becomes 0 ms in output timing, rather than reporting successful render with lost text. ASS output is quantized to 10 ms; test enforces deterministic centisecond serialization and ≤5 ms rounding per cue edge.

[CI 40881166137](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40881166137) **SUCCESS**, exact source/test SHA `e8656dc8`: 587 Linux/586 Windows tests PASS + 1 intentional Windows skip; desktop/native host and frozen synthetic proof both OS PASS. Intermediate [CI 40880618234](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40880618234) failed one new incorrectly strict millisecond assertion in ASS on each runner; verified centisecond expectation fixed without dropping the test.

This is not confirmation of full P11 pixel/audio parity, VFR/rotation/mixed FPS, real Windows device, GPU or 95 full requirement gates.

## P11-01/P11-04 — Rotation metadata crop and genuine VFR/mixed-FPS synthetic fixtures (29/10/2026)

[Plan](P11_ROTATION_VFR_PLAN.md) preceded [source metadata commit 5f8dd26](https://github.com/danhgold7979-cyber/fonesi-edit/commit/5f8dd264eb23440edfaf6123fec0beec7988b971), [orientation correction 2c14c2c](https://github.com/danhgold7979-cyber/fonesi-edit/commit/2c14c2cba8f1d286da1e22f7118003a95e21522f), and [regression 5ab1bca](https://github.com/danhgold7979-cyber/fonesi-edit/commit/5ab1bcad256eb0a1fe131f1dbf63de8bf52cd534). FFprobe reports raw encoded dimensions plus Display Matrix rotation. `CropDialog` previews FFmpeg's autorotated source frame, so its normalized crop is already display-space; the production compiler now calculates even-pixel crop dimensions **after** FFmpeg autorotation (width/height swap for 90/270°) rather than applying an encoded-space crop to rotated pixels. Non-orthogonal metadata plus cropped source fails explicitly.

The real FFmpeg fixture remuxes a 320×180 left-red/right-blue source with +90° metadata, crops the red **displayed bottom half**, checks the compiled filter, and reads both reference and exported PNG/MP4 pixels at the center (red dominant). A second fixture generates unequal VFR presentation-timestamp gaps, concatenates a different 24 FPS clip without source audio, checks subtitle cue timing, converts to target 25 FPS, renders actual preview/output, validates duration/geometry and confirms original source bytes were untouched.

[CI 40885720673](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40885720673) **SUCCESS on exact implementation/test SHA `5ab1bcad`**: **595 Linux PASS / 594 Windows PASS + 1 intentional skip**; plan checker, production app/native-host builds and packaged frozen smoke proofs PASS on both CI runners. Windows development build uploaded. Source-only intermediate rotation mapping was revised before this final CI.

**Remaining P11 gates:** real mixed-orientation/VFR user media and crop interaction at physical Windows/HiDPI resolution, codec/audio sync and full frame-level preview/export tolerance, large media soak, GPU and Chrome/account authentication, Windows installer, real external sources, power-loss testing and unexplained [SQLite corruption #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). Full P11 is NOT complete.

## P11-02 — SQLite initialization fault boundary (29/10/2026)

Source inspection identified a resource-leak path when `PRAGMA journal_mode=WAL` or busy-timeout setup raises **before** `Store.connect()` enters its prior cleanup block. [Fix b31b46d](https://github.com/danhgold7979-cyber/fonesi-edit/commit/b31b46d7c7c6d5cc822f5fecb1a9c1529407cd89) guarantees closure regardless of which initialization PRAGMA fails. [Tests fd28de7](https://github.com/danhgold7979-cyber/fonesi-edit/commit/fd28de70c1f82ef61c355dd2cd91386910ce5e2e) cover deterministic injected PRAGMA errors, exactly-once handle closure, intact rollback/commit and on-disk SQLite integrity.

[CI 40887831717](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40887831717) **SUCCESS on exact SHA fd28de70**: 598 Linux / 597 Windows + 1 intentional skip, production desktop/native-host and frozen application proof both OS. This **does not diagnose or close** intermittent Windows SQLite corruption [issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) or satisfy P11 Windows soak/power-loss acceptance.

## P11-02 — Fault-injected failed-close recovery and bounded SQLite/WAL proxy stress (29/10/2026)

[Plan](P03_SQLITE_SHUTDOWN_RECOVERY_PLAN.md) and [code/tests 50a0137](https://github.com/danhgold7979-cyber/fonesi-edit/commit/50a0137dcbc75bb0042e3b02c9ffe5cc4162a440) establish that an injected SQLite failure during final autosave preserves the newest composition in an independent atomic `recovery.json`, surfaces a controlled close failure, and keeps the app open for a successful retry. Bounded repeated real-proxy/background shutdown checks the same SQLite/WAL project database before/after each close/reopen with intact source bytes.

[CI 40897627521](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40897627521) **SUCCESS on exact SHA 50a0137**: Linux 604 tests / Windows 603 tests + 1 intentional skip, plus desktop/native-host build and packaged frozen proof both OS. **The intermittent [issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) corruption still has unknown root cause**; no true crash/power-cut/NTFS/antivirus soak, no full P11 acceptance.

## P11-02 — Faulted-autosave snapshot replay from separate recovery artifact (29/10/2026)

The prior P03-07 failure-impact mitigation persisted an atomic `recovery.json` on SQLite save errors. [Source 8b5b67d](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8b5b67d5dbaa89618060962a800479ae09b69aef) now replays a newer snapshot if SQLite opens and the selected project ID matches, while refusing stale, cross-project, malformed, linked or oversized backups; a DB with no saved projects can adopt an otherwise valid snapshot. Startup replay itself does **not** mutate SQLite. [Final test 05ac32a](https://github.com/danhgold7979-cyber/fonesi-edit/commit/05ac32a7e425e2a721689b1450345c951b724e1f) covers simulated failed-save-to-new-process recovery, later normal autosave, and identity/file-validation branches without disabling the real single-instance scheduler lock.

[CI 40902670624](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40902670624) **SUCCESS exact code/test SHA 05ac32a**: 607 Linux / 606 Windows passed + 1 intentional skip; desktop/native-host and frozen packaged synthetic proof both OS.

Full P11 still OPEN for corrupt-DB startup, physical Windows power-loss/WAL/AV interference, long soak, GPU/media parity, live sources/Chrome and all requirement gates. Intermittent SQLite [#6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) retains unknown root cause.

## P11-02 — Fault-injected atomic project selection regression (29/10/2026)

[plan](https://github.com/danhgold7979-cyber/fonesi-edit/blob/develop/fonesi-full/docs/phases/P03_ATOMIC_AUTOSAVE_SELECTION_PLAN.md) → [source/test d4117b5](https://github.com/danhgold7979-cyber/fonesi-edit/commit/d4117b580b90ff4b8471907b8e8b1fc56d702a4d) → [CI 40905102578](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40905102578) **SUCCESS on exact source/test SHA d4117b5**: 611 Linux passed / 610 Windows passed + 1 intentional POSIX skip; plan-check, desktop/native-host and frozen packaged proofs PASS both CI runners. The real SQLite `last_project` INSERT/UPDATE trigger failures now roll back project row and pointer together. Qt autosave preserves recovery.json on failure, old DB rows unchanged and valid retry. Regression covers partial-commit prevention, not corruption root-cause reproduction; [Windows SQLite #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6), physical Windows soak/power loss, live Chrome/providers and full P11 acceptance remain OPEN.

## P11-05 — Batch advanced metadata UI/regression parity (29/10/2026)

[P08 plan](https://github.com/danhgold7979-cyber/fonesi-edit/blob/develop/fonesi-full/docs/phases/P08_ADVANCED_METADATA_FILTER_PLAN.md) → [code 6307042](https://github.com/danhgold7979-cyber/fonesi-edit/commit/630704259e38e3ed829817230344ce7a14c993bd) → [tests 81952fd / a0d9e74](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a0d9e74e4fd356568ecaf60c49a5edc0a2bc9d6f) → [CI 40908188050](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40908188050) **SUCCESS exact SHA a0d9e74**: Linux **618 passed**, Windows **617 passed + 1 intentional POSIX skip**, plan validation, production desktop/native-host and frozen packaged synthetic/localhost proof on both. Qt tests cover codec/FPS/video-kbps filter combinations, missing bitrate exclusion without falsification, invalid FPS/bitrate bounds, UI checkbox preservation and no extra metadata worker when only filters change. Real FFprobe and synthetic JSON tests cover rational FPS, video vs container stream bitrate and legacy fixture compatibility. This is not physical Windows/large-corpus/performance/Chrome/GPU acceptance; P08/P11 remain open.

## P11-02 — Isolated invalid-media batch planning QA (29/10/2026)

[P08 plan](https://github.com/danhgold7979-cyber/fonesi-edit/blob/develop/fonesi-full/docs/phases/P08_PARTIAL_BATCH_PLAN.md) → [code 0e9cb5c](https://github.com/danhgold7979-cyber/fonesi-edit/commit/0e9cb5cbc8f345dcd8e152912effe0b849380e8a) → [tests d0753e3](https://github.com/danhgold7979-cyber/fonesi-edit/commit/d0753e3586266fda33ae8e4f8367a124d718ac37) → [CI 40910523178](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40910523178) **SUCCESS at d0753e3** (621 Linux / 620 Windows + 1 intentional skip, frozen proofs both). Real FFmpeg and Qt regressions confirm one invalid local video need not discard other valid plans; global audio mapping failure still blocks, empty plans cannot be queued, and stale results cannot resurrect obsolete selections. Physical Windows hardware/long corpus and complete P11 gates remain OPEN.

## P11-03 — Synthetic corpus planning measurements and cancellation (29/10/2026)

[Plan](P08_BATCH_PROGRESS_BENCHMARK_PLAN.md) → [code/test 6534c41](https://github.com/danhgold7979-cyber/fonesi-edit/commit/6534c41ed457f4380b319b9cd83a7409cba8cd10) → [CI 40914027736](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40914027736) **SUCCESS on exact code/test SHA 6534c41**: 627 Linux PASS, 626 Windows PASS + 1 intentional skip; 128-source real FFprobe benchmark, desktop/native host and frozen packaged proof both runners. 128 synthetic 640×360 clips, not a diverse real media corpus: Linux 5.937889 s (21.556/s), Windows 10.462162 s (12.235/s); Python allocation peaks 840520/848744 bytes, process RSS snapshots 30375936→32043008 and 32342016→33329152 bytes. Benchmark reports only dry-run time and does not include FFprobe subprocess peak RSS, FFmpeg rendering, GPU, UI frame timing or end-user Windows acceptance. 512 mock logical-source test checks progress and cancellation without fragile time limits.

## P11-02 — SQLite transactional Batch enqueue durability (29/10/2026)

[Plan](P08_ATOMIC_ENQUEUE_PLAN.md) → [code/test d6b218a](https://github.com/danhgold7979-cyber/fonesi-edit/commit/d6b218af9a7bd6cc0ac2a9789c3d9fec224da664) → [CI 40916078055](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40916078055) **SUCCESS exact SHA d6b218a**: 631 Linux PASS / 630 Windows PASS + 1 intentional POSIX skip, 128-file benchmarks, packaged proofs both. Real SQLite BEFORE INSERT trigger fails the second selected render job; first insert rolls back, existing jobs remain, retry creates full batch. Qt test confirms dry-run retained and no Queue navigation on failure. These bounded checks are not real Windows long-running power-loss/AV or [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) cause-specific acceptance; P11 remains OPEN.
