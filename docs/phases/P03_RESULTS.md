# P03 — Kết quả triển khai nền

Đã có domain/version/validation, SQLite WAL với project/preset/job/cache/profile/binding/tool/history/schedule, backup và từ chối schema mới hơn. Scheduler dùng subprocess, claim transaction, cancellation, dependency và phục hồi orphan. 5 test chuyên biệt đã qua, gồm render FFmpeg thật qua worker và đọc kết quả từ Store mở lại.

P03-08 registry/install và P03-09 browser metadata là nền cho phần tool/auth tiếp theo; giao diện, installer/session bridge và kiểm chứng Windows được theo dõi tiếp, không coi đã nghiệm thu toàn bộ. Tiếp tục theo chỉ đạo không dừng vì cổng bên ngoài.

Vòng tích hợp đã thêm schema v2 có backup, thời điểm bắt đầu job, khóa một scheduler/DB, phục hồi orphan cả sau startup, unblock dependency và bảo toàn trạng thái matrix khi retry. Các bài tương ứng có trong suite cuối. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).


## 4. Lát cắt hardening — backup và bảo vệ bí mật (28/10/2026)

**CI:** [Desktop verification #40635978628](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40635978628)  
**Commit:** 989368b9560b059c27c131c36ed12955f98c6602

- Linux: 108 tests pass; check_plan, build production/native host và frozen packaged proof đều pass.
- Windows runner: 107 tests pass, 1 skip có chủ đích cho fixture installer POSIX; check_plan, build production/native host và frozen packaged proof đều pass.
- Frozen proof xác nhận hai job render, tải video và ảnh qua localhost vào thư mục Unicode, phụ đề song ngữ, rename/undo và UI smoke/frame decode. Proof đánh dấu passed=true và frozen=true.
- Backup SQLite nay được tạo trong thư mục tạm cùng filesystem, xác nhận integrity_check, flush dữ liệu và công bố bằng hard link không ghi đè. Các connection backup được đóng tường minh để Windows có thể xóa file tạm.
- CI ban đầu phát hiện lỗi Windows thật: SQLite connection context manager không tự đóng connection, làm file tạm bị khóa khi cleanup. Đã đổi sang đóng tường minh; lần chạy mới nhất pass trên cả hai hệ điều hành.
- Payload validator chuẩn hóa tên trường và chặn thêm alias credential; worker error sanitizer che Bearer/Basic, trường credential, signature và query/fragment URL nhưng giữ lại mã lỗi/host/path cần chẩn đoán.

**Giới hạn còn mở:** CI dùng media synthetic và localhost; không chứng minh mạng xã hội live, dịch API thật, Chrome session handoff, GPU/VRAM, installer trên máy người dùng hoặc soak/crash/power-loss dài hạn. P03 không được coi là nghiệm thu toàn bộ chỉ dựa trên lát cắt này.

## P03-05 — Bảo vệ lỗi ở ranh giới SQLite (28/10/2026)

`Store.fail` giờ áp dụng `sanitize_error_message` **trước khi INSERT/UPDATE lỗi vào SQLite**, kể cả caller không phải worker. Bảo vệ query URL token/signature, Bearer credentials và các alias khóa API; giữ mã lỗi/host/path phục vụ chẩn đoán. Test đọc trực tiếp SQLite cho job `failed` và `blocked`, bảo toàn trạng thái/chức năng. [CI 40652053745](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40652053745) PASS Linux/Windows và packaged proof. Chưa chứng minh mọi chuỗi credential lạ được lọc hoặc vận hành trên máy thật.

## P03-07 — Release SQLite file handles when WAL initialization fails (29/10/2026)

[Plan](P03_SQLITE_CONNECTION_INIT_PLAN.md) preceded [code b31b46d](https://github.com/danhgold7979-cyber/fonesi-edit/commit/b31b46d7c7c6d5cc822f5fecb1a9c1529407cd89) and [fault-injection tests fd28de7](https://github.com/danhgold7979-cyber/fonesi-edit/commit/fd28de70c1f82ef61c355dd2cd91386910ce5e2e). `Store.connect()` previously called `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=15000` before the `try/finally`, so a setup-time OperationalError could bypass explicit `conn.close()` and retain a SQLite handle, especially problematic for Windows cleanup. Both PRAGMAs now run inside the guaranteed cleanup block, while post-yield transaction commit/rollback semantics remain intact.

Regression tests simulate either PRAGMA failing, assert that the real wrapped connection is closed exactly once without silently continuing, and verify subsequent normal setting write/read plus `PRAGMA integrity_check = ok`. The normal commit/rollback behavior is also covered. [CI 40887831717](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40887831717) **SUCCESS on exact source/test SHA fd28de70**: **598 Linux PASS; 597 Windows PASS + 1 intentional POSIX skip**. Source plan validation, production desktop/native-host and frozen packaged synthetic proof PASS on both OS.

This fixes a **demonstrable setup-time handle cleanup defect**, **not the established cause** of intermittent [Windows SQLite corruption issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). Root cause unknown; keep the issue open and separately reproduce Windows shutdown/WAL/database corruption before claiming resolution. No DB schema change or deletion of WAL files.

## P03-07 / P11-02 — Recovery snapshot survives SQLite autosave failure (29/10/2026)

[Plan](P03_SQLITE_SHUTDOWN_RECOVERY_PLAN.md) preceded [source 085aa52](https://github.com/danhgold7979-cyber/fonesi-edit/commit/085aa5278ccb2d2d128b94371e10668e790d4ff1) and [Qt fault-injection/stress tests 50a0137](https://github.com/danhgold7979-cyber/fonesi-edit/commit/50a0137dcbc75bb0042e3b02c9ffe5cc4162a440). When a project SQLite write fails, `autosave()` now attempts atomic `recovery.json` write with the current composition and re-raises the original error; the window rejects a failed-persistence close event, keeps worker/scheduler alive for retry and avoids raw database errors in the UI message. SQLite commit/rollback, schema, WAL mode and source media are unchanged.

The new synthetic Qt test injects `sqlite3.DatabaseError`, checks the latest recovery JSON, unchanged DB `integrity_check=ok`, rejected close with active clock and successful later retry/reopen. The companion WAL stress uses three controlled app/proxy open-close cycles on the same test DB (real proxy creation for two qualities, guaranteed canceled background worker for the third), with pre/post-closure `integrity_check` and WAL mode checks.

[CI 40897627521](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40897627521) **SUCCESS at source/test SHA 50a0137**: Linux **604 PASS**, Windows **603 PASS + 1 intentional skip**, plan checker, desktop/native-host and frozen packaged proof PASS both systems.

This is **failure-impact mitigation and bounded nonreproduction**, not a proven repair of [intermittent Windows SQLite corruption #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). When both DB and recovery filesystem writes fail, the app cannot guarantee data durability. Windows native/NTFS WAL timeline and long soak remain open.

## P03-07 — Verified safe startup replay of a newer recovery.json (29/10/2026)

[Plan](P03_RECOVERY_REPLAY_PLAN.md) preceded [source 8b5b67d](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8b5b67d5dbaa89618060962a800479ae09b69aef) and [Qt final test 05ac32a](https://github.com/danhgold7979-cyber/fonesi-edit/commit/05ac32a7e425e2a721689b1450345c951b724e1f). The existing independent `recovery.json` from a faulted SQLite save is now read on subsequent healthy startup. A validated, newer snapshot for the **same selected project** restores unsaved composition in memory; older/cross-project/corrupt files are refused. A wholly empty SQLite project table can adopt a valid leftover recovery snapshot without creating or overwriting a project row before normal autosave. Invalid, symlinked or oversized recovery files are not trusted. Original source media, SQLite schema and WAL/SHM are unchanged.

The first [CI 40902021585](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40902021585) failed the new test because it concurrently initialized two windows with the same scheduler lock; that lock correctly rejected the duplicate. [Test fix 05ac32a](https://github.com/danhgold7979-cyber/fonesi-edit/commit/05ac32a7e425e2a721689b1450345c951b724e1f) instead simulates the old application finishing its shutdown and releasing the lock, then reopens the same database to validate replay; no scheduler assertion was removed.

[CI 40902670624](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40902670624) **SUCCESS on exact code/test SHA 05ac32a**: **607 Linux tests passed / 606 Windows tests passed + 1 intentional POSIX fixture skip**; plan/desktop/native-host/frozen app proofs PASS both systems.

**Not proven:** recovery from a DB that cannot even initialize, long NTFS/AV/power-cut soak, and the cause of [intermittent Windows SQLite corruption #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6), which remains OPEN. This is a bounded recovery feature, not full P03/P11 acceptance.
