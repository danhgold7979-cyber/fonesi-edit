# P11 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-11`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P11-01 — end-to-end các workflow/nguồn hỗ trợ; dọc/ngang/CFR/VFR/rotation/audio lệch hoặc không audio/sub sau speed-trim.

- **Depends on:** P04–P10. Only independent work may proceed while external portions remain blocked.
- **Input:** Release candidate and full corpus plus permitted live source cells.
- **Output/interface:** End-to-end workflow report local/download/sub/translate/editor/batch/matrix/auto.
- **Errors/cancellation:** Missing capability remains blocker; cancel each long stage; no fixture masquerading live.
- **Tests and acceptance:** Landscape/portrait/CFR/VFR/rotation/no-audio/delayed-audio/transformed-sub pass from UI through validated output.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P11_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P11-02 — crash worker/app/mạng/auth/rate limit/quota/tệp hỏng/thiếu font-media/quyền ghi-đĩa đầy; retry/resume.

- **Depends on:** P03-04/06,P10-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Fault-injection harness and isolated filesystem/network/provider/process fixtures.
- **Output/interface:** Crash/restart/retry/auth/quota/media/font/permission/disk failure evidence.
- **Errors/cancellation:** Every failure typed; cancellation and crash race reconciled; source and manual edits preserved.
- **Tests and acceptance:** Kill app/worker at journal boundaries, partial network and unknown billing, corrupted assets; no false success/data loss; Windows OS faults separate.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P11_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P11-03 — lô lớn/nhiều layer/ma trận lớn/tải+render; đo UI/proxy/seek/RAM/VRAM/rò tài nguyên trên máy tham chiếu.

- **Depends on:** P02-07,P10-04/05. Only independent work may proceed while external portions remain blocked.
- **Input:** Declared hardware, large media/layer/matrix corpus, concurrent workload.
- **Output/interface:** Latency/memory/VRAM/leak/resource benchmark reports and remediation.
- **Errors/cancellation:** Incomplete run NOT_RUN not PASS; cancel benchmark doesn't change production caps.
- **Tests and acceptance:** Warm/cold p95/max event/seek, 10k inventory, bounded matrix and repeated open/close resource trend; target machine gates explicit.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P11_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P11-04 — đối chiếu frame/sub/audio/duration theo dung sai; sửa nguyên nhân, không tắt kiểm tra để đạt.

- **Depends on:** P07-08,P08-06,P09-06. Only independent work may proceed while external portions remain blocked.
- **Input:** Preview/export/audio fixtures and canonical expected values.
- **Output/interface:** Automated parity comparator report with failure artifacts.
- **Errors/cancellation:** Unsupported engine case blocks, never relax threshold to pass; canceled comparison incomplete.
- **Tests and acceptance:** Every transform/font/motion/sub/audio/timing option plus deliberate shifted/missing sentinel detected; measured thresholds in VERIFICATION.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P11_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P11-05 — rà mọi hàng truy vết, mọi tùy chọn/phím tắt/focus/HiDPI/theme/persistence/preset migration.

- **Depends on:** P01-01,P04–P10. Only independent work may proceed while external portions remain blocked.
- **Input:** 95 groups/all subcriteria and every control/shortcut/default.
- **Output/interface:** Coverage audit and option-by-option GUI/persistence/preset migration record.
- **Errors/cancellation:** Missing/disabled option remains open scope; text/IME/focus conflicts defects; canceled dialogs leave data.
- **Tests and acceptance:** Each mandatory child evidence mapped, every shortcut focus context, HiDPI/theme/windows resizing, scope locks and import migration; semantic reviewer checks.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P11_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P11-06 — nguồn có phiên bản/ngày/evidence, tách lỗi app/hạn chế nguồn/blocker cấu hình; không đóng mục chưa chạy thành công.

- **Depends on:** P05-07,P06-03,P05-09. Only independent work may proceed while external portions remain blocked.
- **Input:** Timestamp/version-specific live platform/provider reports.
- **Output/interface:** Capability status revalidation and explicit app-error/source-limit/config-blocker classification.
- **Errors/cancellation:** Source changed marks degraded, not obsolete permanent unsupported; cancel read probe safe.
- **Tests and acceptance:** Each declared supported cell has current actual output; all ten platforms and translation/Chrome blocked cells retained with retry prerequisite.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P11_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P11-07 — log/backup/cache/dependency, lỗi còn lại theo mức ảnh hưởng và cách khắc phục.

- **Depends on:** P11-01..06. Only independent work may proceed while external portions remain blocked.
- **Input:** Remaining failures, backup/log/cache/tool inventories.
- **Output/interface:** Severity-ranked defect report, sanitized diagnostics, recovery instructions and safe cleanup evidence.
- **Errors/cancellation:** Secret sentinel in log/export blocks release; corrupt backup or ownership uncertainty no delete.
- **Tests and acceptance:** Restore backup on fresh profile, log redaction, leased cache protection, unresolved critical defects=release blocked.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P11_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P11-08 — missing/wrong tools, installer ngắt/verify lỗi/quyền ghi/update bận; Chrome A nhiều nền tảng, Chrome B nick khác, phiên hết hạn/challenge/mismatch/lock/bridge không dùng được, export không chứa session.

- **Depends on:** P03-08/09,P04-08,P05-08..10. Only independent work may proceed while external portions remain blocked.
- **Input:** Missing/wrong tool installs and Chrome A/B real profiles plus fixtures.
- **Output/interface:** Tool lifecycle and browser/account security/lifecycle acceptance matrix.
- **Errors/cancellation:** Interrupt/verify/permission/busy rollback safe; locked/challenge/expired/mismatch separate; cancel never damages profile.
- **Tests and acceptance:** Archive attack/checksum/update lease, external tool sentinel; Windows official Chrome three bindings/restart/bridge/private permitted download; project/export no session.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P11_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
