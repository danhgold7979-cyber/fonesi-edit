# P12 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-12`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P12-01 — đóng gói tái lập theo P02, FFmpeg/thư viện/font hợp lệ; chạy không cần bộ dev/admin nếu không thiết yếu.

- **Depends on:** P11,P02-06/09. Only independent work may proceed while external portions remain blocked.
- **Input:** Accepted exact code/dependency lock/trusted binaries/fonts/licenses.
- **Output/interface:** Reproducible Windows onedir/installer manifest+checksums+notices and build instructions.
- **Errors/cancellation:** Missing license/hash/build mismatch blocks distribution; cancel packaging leaves no release-labelled partial.
- **Tests and acceptance:** Fresh Windows without Python/dev tools starts and performs media workflow; verify manifest actual files and runtime dependencies.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P12_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P12-02 — phân biệt install/user data, Unicode/quyền ghi/antivirus thực tế, CPU-only và GPU phù hợp khi có.

- **Depends on:** P12-01,P02-05/07. Only independent work may proceed while external portions remain blocked.
- **Input:** Clean Windows10/11 machines as supported, CPU/GPU and Unicode/nonadmin paths.
- **Output/interface:** Install vs user-data/ACL/AV/compatibility report with actual hardware.
- **Errors/cancellation:** Admin/UAC need explicit user action; unsupported OS/GPU precise; cancel install leaves user data.
- **Tests and acceptance:** Nonadmin fresh install, Unicode paths, read-only install dir, real AV behavior and CPU fallback; unavailable target rows BLOCKED.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P12_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P12-03 — chạy workflow từ bản đóng gói, save/open/crash/restart/migration/cấu hình thiếu, mở kết quả bằng player ngoài.

- **Depends on:** P12-01/02,P11-01/02. Only independent work may proceed while external portions remain blocked.
- **Input:** Frozen executable and corpus/project/database versions.
- **Output/interface:** Packaged UI workflow/save/open/crash/restart/migration/media-player acceptance.
- **Errors/cancellation:** Missing config/tool/font handles recovery; cancel mid-export no success; old project backup preserved.
- **Tests and acceptance:** Run from EXE not source Python, actual FFmpeg input/output and external player, restart queue/reconcile, schema upgrade/rollback tests.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P12_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P12-04 — hướng dẫn Việt, preset mẫu, cấu hình dịch/phiên nguồn an toàn, phím tắt/chẩn đoán/báo lỗi.

- **Depends on:** P12-03,P01-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Verified available controls/capabilities and known blockers.
- **Output/interface:** Vietnamese user guide/presets/shortcuts/configuration/diagnostic steps.
- **Errors/cancellation:** Docs never claim blocked platform works; secret input only authorized provider/Chrome flow; sample import cancel harmless.
- **Tests and acceptance:** Fresh-user walkthrough matches actual screens/buttons, sample preset valid no private paths, troubleshooter recovers tested faults.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P12_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P12-05 — cập nhật tool/adapter có version/xác minh/tương thích/rollback, backup trước đổi schema.

- **Depends on:** P12-01,P03-08,P11-08. Only independent work may proceed while external portions remain blocked.
- **Input:** Versioned adapter/tool manifests and compatibility/migration rules.
- **Output/interface:** Verified update/rollback package and backup-before-schema path.
- **Errors/cancellation:** Interrupted update/checksum/active lease fails safe, no system binary modification; cancel retains prior usable version.
- **Tests and acceptance:** Install old→new→rollback real binary/version, running job pinned, corrupted package rejected, database backup readable.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P12_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P12-06 — manifest, capabilities, máy thật, release notes/giới hạn, lưu bản phục hồi.

- **Depends on:** P12-01..05/07. Only independent work may proceed while external portions remain blocked.
- **Input:** All release acceptance evidence, build hashes and limitations.
- **Output/interface:** Release manifest, capabilities, target-PC report, release notes and recovery bundle.
- **Errors/cancellation:** Any mandatory blocker prevents full-release label; cancel publication does not remove recovery.
- **Tests and acceptance:** Independent review validates exact commit/build/evidence and backup restore; no stale old CI as current proof.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P12_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P12-07 — Windows mới thiếu dependency/Chrome: từ Cài đặt tải-cài-kiểm tra, mở Chrome thật/login, dùng phiên tải mẫu; tool ngoại không bị sửa, offline vẫn dùng media cục bộ, giới hạn auth được ghi đúng.

- **Depends on:** P12-02/03,P05-09,P03-08. Only independent work may proceed while external portions remain blocked.
- **Input:** Fresh Windows missing dependencies/Chrome and permitted accounts plus offline media.
- **Output/interface:** Settings-driven install/check, official Chrome login/handoff/download, offline local editing workflow.
- **Errors/cancellation:** UAC/login user-controlled; missing account blocks only source, external tool never overwritten; cancel installer status truthful.
- **Tests and acceptance:** End-to-end from missing-tool machine, actual version check+source output, Chrome identities correct, offline editor/export works; live unavailable means BLOCKED.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P12_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
