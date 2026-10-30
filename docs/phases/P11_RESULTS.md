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

## P11-02 — Batch output preflight and no-overwrite QA (29–30/10/2026)

[plan](https://github.com/danhgold7979-cyber/fonesi-edit/blob/develop/fonesi-full/docs/phases/P08_EXISTING_OUTPUT_PREFLIGHT_PLAN.md) → [code/test b845a4c](https://github.com/danhgold7979-cyber/fonesi-edit/commit/b845a4c38c9514794dce82eada8e867f8e9b4c9e) → [CI 40919530634](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40919530634) PASS on exact SHA b845a4c (635 Linux / 634 Windows+1 intentional skip, both frozen proofs). Existing output file/directory/symlink is rejected before a grouped Batch queue transaction; Qt retry and content/mtime invariants are tested. Final renderer's no-overwrite protection remains essential for races. Physical Windows ACL/AV, power-loss, full P11 acceptance and SQLite issue #6 remain OPEN.


## P11-04 — Playback decoded-stream PCM meter regression (30/10/2026)

[Plan](P08_AUDIO_PLAYBACK_METER_PLAN.md) → [code and Qt/PCM tests](https://github.com/danhgold7979-cyber/fonesi-edit/commit/c706930e2c5e8a5026e37fb5fd856901585330b5) → [Python 3.12 fix](https://github.com/danhgold7979-cyber/fonesi-edit/commit/743e68b3e4c262fa4bc824f9ccca4f1ec67361c2) → [CI 40996183826](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40996183826) **SUCCESS exact SHA 743e68b**: 676 Linux PASS, 675 Windows PASS plus 1 intentional POSIX-only skip, desktop/native-host and frozen packaged proofs both OS. Real QAudioBuffer signal tests cover dBFS meters/clipping, source changes/EOS/invalid data and unchanged project model; the optional backend tap shares the existing playback QMediaPlayer. Subsequent missing-Qt-tap regression in [commit 651cb35](https://github.com/danhgold7979-cyber/fonesi-edit/commit/651cb350140d35ef171f3b8ff3cd848a0e911360) has separate CI pending. This is **not** real speaker, true-peak, integrated loudness, per-track solo, device calibration or full P11 acceptance.

## P11-05 — Matrix scene selection, pinned angle and historical source identity (30/10/2026)

[Plan P09](P09_SCENE_SELECTION_LOCK_PLAN.md), [code/test SHA 7d1f928a798b8cb50997a25e8f8947dfc0f83999](https://github.com/danhgold7979-cyber/fonesi-edit/commit/7d1f928a798b8cb50997a25e8f8947dfc0f83999) and [CI 41021003352](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41021003352) **SUCCESS at exact SHA**: 728 Linux PASS / 727 Windows PASS + 1 intentional POSIX-only skip, packaged desktop/native host/frozen synthetic proof both runners. Source/angle checkboxes, all-row G pins, same-manifest preferences, invalid/revoked asynchronous work, immutable source bytes and complete→subset→complete hash-only SQLite history projection/rollback received real Qt, SQLite and synthetic FFmpeg regressions. A known shorter-scene historical row is not a duplicate longer-scene composition; missing or ambiguous hash provenance fails closed. Full P11 and real user Windows/long corpus/Chrome/GPU/SQLite #6 gates remain open.

## P11-02 / MAT-07 — Matrix worker recovery and fail-closed retry (30/10/2026)

[Plan](P11_MATRIX_RECOVERY_PLAN.md) → [reservation guard 58d94f7](https://github.com/danhgold7979-cyber/fonesi-edit/commit/58d94f738ca7cd9b5dab39caef8f952719b78718) → [recovery tests e54a66c](https://github.com/danhgold7979-cyber/fonesi-edit/commit/e54a66cf3c69e6fc6f91a0d4c51b4064480bb46b) → [partial-identity guard 872c98e](https://github.com/danhgold7979-cyber/fonesi-edit/commit/872c98eebb9a7d15cd2e2d5c335336c4f0c9d346) → [final tests a6d1e95](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a6d1e9577c2017519c0ecf22edf63f8695a79402).

Matrix stale-worker recovery preserves the same job, payload, output target and reservation. Cancellation marks the reservation failed; explicit retry reuses the same job ID. Store retry rejects missing/partial identity and missing, succeeded or foreign-owned reservations, including a failed reservation reassigned to a newer job. The current owner can still retry. A missing source after enqueue produces failed/blocked job + failed reservation, never success. Unrelated succeeded history remains unchanged.

[CI 41035225664](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41035225664) **SUCCESS exact SHA a6d1e9577c2017519c0ecf22edf63f8695a79402**: Linux 788 PASS; Windows 787 PASS + 1 intentional POSIX-fixture skip. Both runners passed phase-reference validation, 128-source synthetic FFprobe Batch benchmark, 10^10-capacity logical Matrix benchmark (2,000 complete outputs, max per-scene spread 5), desktop/native-host build and frozen packaged render/Batch/Matrix/localhost download/UI proof. Artifacts: Linux evidence 390,012 bytes; Windows evidence 322,683 bytes; Windows development build 197,350,911 bytes (retention through 2026-11-06).

Only synthetic/localhost CI evidence. Physical Windows power-loss/AV/ACL/NTFS/exFAT, SQLite issue #6 cause, real 100k-media performance, live Chrome/providers, GPU and all remaining P11/P12 gates stay OPEN. This does not complete P11 or authorize merge to main.

## P11-02 / MAT-07 — Matrix artifact recovery before history commit (30/10/2026)

[Plan](P11_MATRIX_OUTPUT_RECOVERY_PLAN.md) → [tests 8101f21](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8101f210dfdeac160f7b9f2729fc1d01cfc33fa1).

Three recovery-boundary regressions now prove: (1) if the real worker renderer has published an MP4 and matching config/SHA sidecar but Store.finish has not committed, recovery reuses the same bytes and the retry commits succeeded once; (2) an orphan destination without sidecar is not adopted or overwritten; (3) a modified output with stale sidecar SHA is rejected and preserved. Failed cases leave the job/result/history non-succeeded and the reservation failed.

[CI 41037280021](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41037280021) **SUCCESS exact SHA 8101f210dfdeac160f7b9f2729fc1d01cfc33fa1**: Linux 791 PASS; Windows 790 PASS + 1 intentional POSIX-only skip. Both OS passed phase references, 128-source synthetic Batch benchmark, 10^10 logical Matrix benchmark (2,000 complete outputs; max spread 5), production desktop/native-host builds and frozen packaged render/Batch/Matrix/localhost download/UI proof. Artifact IDs/sizes and benchmark metrics are in P11_MATRIX_OUTPUT_RECOVERY_PLAN.md.

This closes only the output-recovery test slice. Synthetic crash-boundary tests do not prove physical power-loss recovery or Windows user-machine behavior. P11/P12 and external SQLite/real-media/live-provider/GPU gates remain open; do not merge main.


## P11-05 / OPS-07 + AUTH-11 — Strict preset schema and profile-scoped pairing regression (30/10/2026)

[Preset plan](P11_PRESET_SCHEMA_VALIDATION_PLAN.md) → [implementation a7f2328](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a7f2328fa3448b5e9664e83dcb5d0f7793f0bdec) → [profile revocation regression e3d3272](https://github.com/danhgold7979-cyber/fonesi-edit/commit/e3d3272cf8753fe08652b8f1d54bf8f5359214cb) → [CI 41046744447](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41046744447) **SUCCESS exact HEAD e3d3272**.

Implemented a shared schema-v1 preset builder/parser and routed the Qt save/import/export paths through it. Import is capped at 2 MiB and rejects invalid UTF-8/JSON, duplicate keys, non-finite numbers, non-integer/unsupported versions, unknown envelope fields, invalid Windows-portable names, secret-bearing payloads, source clips and clip bindings before Store.save_named. Export strips source clips and clip IDs. Referenced logo/font/audio paths remain external; missing local assets are listed without copying/deleting them. Qt integration proves invalid import creates no saved preset and does not mutate the active composition; valid import saves exactly one preset and also leaves the active composition unchanged.

Added a browser regression proving revocation is scoped to the selected Chrome profile: it removes that profile's bridge and pending pairing code, preserves both profile directories and both account bindings, and leaves the other profile's bridge usable. Existing focus-aware text Undo/Redo paths were not changed and remain in the full suite.

[CI 41046744447](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41046744447) **SUCCESS**: Linux **817 passed**; Windows **816 passed + 1 intentional POSIX-only skip**. Both runners passed the 128-source synthetic FFprobe Batch dry-run (failed_count=0), 10^10 theoretical-capacity logical Matrix benchmark (2,000/2,000 complete, max per-scene spread 5), production desktop/native-host build and frozen packaged render/Batch/Matrix/localhost video+image download/UI proof. Batch elapsed: Linux 7.751278 s, Windows 10.102146 s. Matrix elapsed: Linux 19.860847 s, Windows 17.556047 s. Artifacts: Linux evidence 391,472 bytes, Windows evidence 323,245 bytes (expire 2026-11-02), Windows development build 197,366,359 bytes (expires 2026-11-06).

This closes the bounded preset/revocation regression slice only. It does not complete every P11-05 option/HiDPI/physical input acceptance, full AUTH-11, all 95 groups, live Chrome/provider, GPU, physical Windows, SQLite issue #6, real-media corpus or power-loss/soak gates. P11 and P12 remain OPEN.


## P11-08 / TOL-05 — Installer ZIP archive safety and portability (30/10/2026)

The tool installer now preflights the complete ZIP before extraction. It rejects traversal/absolute/drive paths, control/NUL, symlink and special Unix file types, encrypted entries, Windows reserved device names, invalid characters/trailing dot-space, case-fold duplicates and file/directory collisions. Safe nested files and directory entries using slash or backslash separators extract consistently across Linux/Windows.

[Plan](P11_TOOL_ARCHIVE_PORTABILITY_PLAN.md) → [final implementation 85654ec](https://github.com/danhgold7979-cyber/fonesi-edit/commit/85654ec780f3ab8752af834e081a46f406d124d8) → [CI 41053597336](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41053597336) SUCCESS exact HEAD: Linux 850 passed; Windows 849 passed + 1 intentional POSIX-only skip. Both OS passed Batch 128-source synthetic FFprobe dry-run (failed_count=0), 2,000-output logical Matrix benchmark (complete=true, max spread 5), production desktop/native-host build and frozen packaged proof. Batch elapsed 5.012570 s Linux / 10.882223 s Windows; Matrix 9.079294 s Linux / 17.686874 s Windows.

Artifacts: Linux evidence 390,874 bytes; Windows evidence 323,726 bytes; Windows development build 197,380,520 bytes. This does not certify Windows user-machine ACL/AV/disk-full/power-loss, signed installer/update, Chrome/provider auth, GPU/HiDPI/audio or full P11/P12. P11 remains OPEN.


## P11-08 / TOL-04…06 — Interrupted download and verification failure atomicity (30/10/2026)

Four synthetic installer regressions now cover partial network transfer exception, SHA-256 mismatch, cancellation after fetch and malicious ZIP preflight failure at install integration. Each test first activates a known-good FFmpeg/ffprobe version and proves its bytes, companion, active paths and active-version record remain unchanged; no new version is published or activated, staging is removed and progress never reports 1 on failure.

[Plan](P11_TOOL_INSTALL_FAILURE_BOUNDARY_PLAN.md) → [tests 096d6bb](https://github.com/danhgold7979-cyber/fonesi-edit/commit/096d6bbb16768fb8c063109d2e4def5cd9e64dd6) → [CI 41056951728](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41056951728) SUCCESS exact HEAD: Linux 854 passed; Windows 853 passed + 1 intentional POSIX-only skip. Both OS passed Batch 128-source synthetic FFprobe dry-run (failed_count=0), 2,000-output logical Matrix benchmark (complete=true, max spread 5), production desktop/native-host build and frozen packaged proof. Batch 7.996895 s Linux / 10.505177 s Windows; Matrix 19.011149 s Linux / 17.623936 s Windows.

Artifacts: Linux evidence 392,162 bytes; Windows evidence 323,821 bytes; Windows development build 197,385,904 bytes. This does not certify physical Windows ACL/AV/disk-full/process-kill/power-loss, signed installer/update, Chrome/provider auth, GPU/HiDPI/audio or full P11/P12. P11 remains OPEN.


## P11-08 / TOL-06 — Settings managed-tool inventory and cleanup UI (30/10/2026)

[Detailed plan e258d06](https://github.com/danhgold7979-cyber/fonesi-edit/commit/e258d06c0cd336957f876b4f20f687577ba432e9) → [Qt regression commit 28b9385](https://github.com/danhgold7979-cyber/fonesi-edit/commit/28b938589b495d9e0c8aff66a6d37a06f840cead) → [CI 41066952938](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41066952938) **SUCCESS exact HEAD**.

Added `tests/test_tool_settings_ui.py` with three Qt integration tests using a real `MainWindow`, production `SettingsPage`, temporary user-data directories, SQLite registry rows and filesystem-backed managed versions. The tests verify: (1) the table labels eligible and active versions with protection tooltips, and confirmed removal deletes only the selected old managed folder/row while preserving the active FFmpeg path, Chrome profile marker and account binding; (2) declining confirmation leaves the folder, registry and selection unchanged; (3) a retryable job snapshot blocks cleanup before the confirmation dialog and retains its executable path.

CI on exact SHA `28b938589b495d9e0c8aff66a6d37a06f840cead`: Linux **873 passed / 0 skipped**; Windows **871 passed / 2 intentional skips / 0 failures** (POSIX fixture tool install and Windows symlink privilege). Both runners passed the 128-source synthetic FFprobe Batch dry-run (`failed_count=0`), 2,000-output logical Matrix benchmark (`complete=true`, max spread 5), production desktop/native-host build and frozen packaged proof. Batch: 7.623922 s Linux / 10.117165 s Windows. Matrix: 19.857709 s Linux / 17.514511 s Windows. Windows development artifact: 197,404,488 bytes.

This closes the bounded Settings UI cleanup regression only. Physical Windows ACL/AV/disk-full/power-loss, signed installer/update, real Chrome login/DPAPI/session handoff, live providers, GPU/HiDPI/audio, large real-media corpus, SQLite issue #6 and full P11/P12 remain OPEN.

## P11-08 / TOL-06 — Receipt identity and rollback path ownership (30/10/2026)

[Plan](P11_TOOL_ROLLBACK_IDENTITY_PLAN.md) → [implementation/tests 13a044e](https://github.com/danhgold7979-cyber/fonesi-edit/commit/13a044e51f96498d7b3ee0728e7892fffd8c4194) → [CI 41072242592](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41072242592) **SUCCESS exact HEAD**.

The installer activation path now validates receipt object/name/version identity, SHA-256 format, and requires the executable and optional ffprobe companion to be regular non-symlink files within the exact app-managed version folder before updating active metadata. Rollback now validates registry identity, managed-root ownership, executable hash/startup readiness, and any existing ffprobe companion under the same SQLite writer transaction. It rejects a registry path pointing outside the managed folder even when the external binary has identical bytes/hash, and rejects symlinked companions without changing active paths. If the selected FFmpeg version has no companion, only a stale app-managed ffprobe override is removed; a separate user/system override is preserved.

New tests cover malformed/name/version-mismatched receipts, external byte-identical rollback executable, symlinked ffprobe during activation, and symlinked ffprobe during rollback; the existing successful matching FFmpeg/ffprobe rollback test remains green.

Exact-HEAD CI: Linux **879 passed / 0 skipped**; Windows **875 passed / 4 intentional skips / 0 failures** (one POSIX fixture installer and three Windows symlink-privilege tests). Both runners passed 128-source synthetic FFprobe Batch dry-run (failed_count=0), 2,000-output logical Matrix benchmark (complete=true, max spread 5), production desktop/native-host build and frozen packaged proof. Batch: 7.526041 s Linux / 10.676617 s Windows. Matrix: 19.938691 s Linux / 18.143151 s Windows. Artifacts: Linux evidence 391,632 bytes; Windows evidence 324,455 bytes; Windows development build 197,408,920 bytes.

This closes the bounded receipt/rollback ownership slice only. Physical Windows ACL/AV/disk-full/power-loss, signed installer/update UX, Chrome real login/DPAPI/session handoff, live providers, GPU/HiDPI/audio, real-media soak, SQLite issue #6 and full P11/P12 remain OPEN.

## P11-01 / P11-04 — Cross-platform SFX sample-clock timing (30/10/2026)

The Windows regression in [CI 41076305870](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41076305870) reported peak 3830 in the pre-trigger silence window. [Fix ca32673](https://github.com/danhgold7979-cyber/fonesi-edit/commit/ca32673ccfe40eed14cc3b3c57c9d98807641719) normalizes trimmed SFX to `asetpts=N/SR/TB` after 48 kHz resampling and before delay for custom and repeated SFX. Strict pre-trigger silence and audible-window assertions remain unchanged. Exact-HEAD [CI 41080729485](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41080729485) SUCCESS: Linux 884 passed; Windows 880 passed + 4 intentional skips; both packaged proofs passed.

## P11-08 / TOL-04…06 — Per-tool update-busy guard (30/10/2026)

Settings now reserves a normalized per-tool busy key before scheduling work; FFprobe aliases FFmpeg. Duplicate install/update is rejected, independent tools may queue concurrently, install-missing skips busy components, relevant actions are disabled/guarded, and busy state clears after task completion, scheduling failure or a worker that finishes before signal hookup. Five Qt regressions were added. Exact-HEAD [CI 41080729485](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41080729485) SUCCESS: Linux 884 passed; Windows 880 passed + 4 intentional skips; production/native-host builds and frozen packaged proofs both OS.

Linux 884 passed / 0 skipped; Windows 880 passed / 4 intentional skips / 0 failures. Both runners passed the 128-source synthetic FFprobe Batch dry-run (failed_count=0; 7.013533 s Linux / 9.322799 s Windows), the 2,000-output logical Matrix benchmark (complete=true, max per-scene spread 5; 16.364985 s Linux / 16.197908 s Windows), production desktop/native-host build and frozen packaged proof. Windows development artifact: 197,420,154 bytes; evidence artifacts: Linux 391,868 bytes and Windows 324,574 bytes.

These close bounded synthetic SFX and in-process Settings concurrency slices only. Full P11/P12 and physical Windows/live-provider acceptance remain OPEN.

## P11-08 / AUTH-06, AUTH-08 — Serialize profile handoff and pairing revocation (30/10/2026)

Plan d684602 → implementation e4f7b3d → compatibility fix 683f532 → [exact-HEAD CI 41088435585](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41088435585) SUCCESS.

receive_session revalidates the bridge inside BEGIN IMMEDIATE; binding creation, account mismatch check, protected session write and binding status update remain in the same writer transaction. revoke_pairing uses the same writer lock. Two deterministic threaded tests prove both lock orderings: revocation-first rejects a stale bridge without creating a binding/session; handoff-first commits the complete session before revocation. Existing profile A/B isolation, mismatch, cookie filtering, expiry/relogin, pairing, job snapshot and DPAPI fail-closed tests remain passing.

Exact-HEAD suite: Linux 892 passed / 0 skipped; Windows 888 passed / 4 intentional skips / 0 failures. Batch 128-source dry-run: 5.873457 s Linux / 7.603461 s Windows, failed_count=0. Logical Matrix 2,000 outputs: 11.955144 s Linux / 9.672810 s Windows, complete=true, max spread 5. Both production/native-host builds and frozen packaged proofs passed (6.419 s Linux / 9.937 s Windows). Windows development artifact: 197,426,877 bytes.

Separate follow-up: serialize pending pairing-code issuance with the revocation transaction; this race is not yet covered. Synthetic evidence does not certify live Chrome/extension, DPAPI user profile, provider login, physical Windows or complete P11/P12 acceptance.
