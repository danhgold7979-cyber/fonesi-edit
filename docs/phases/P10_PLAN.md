# P10 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-10`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P10-01 — DAG tải→sub→dịch→edit→render→validation theo lô/cuốn chiếu, công đoạn idempotent/trạng thái riêng.

- **Depends on:** P05–P09,P03-04/06. Only independent work may proceed while external portions remain blocked.
- **Input:** Enabled preset stages and source/batch item dependencies.
- **Output/interface:** Durable DAG coordinator batch and rolling modes with idempotent stage keys.
- **Errors/cancellation:** Failed terminal downloads unblock batch valid subset; cyclic DAG rejected; cancel descendants coherently.
- **Tests and acceptance:** Restart after each stage, mixed fail/success, rolling resource limits, no duplicate stage or fake pipeline completion.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P10_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P10-02 — lịch đồng bộ/watcher đợi tệp ổn định/loại output, chống job trùng/chạy chồng, chính sách lịch bỏ lỡ; chạy khi app đóng cần chế độ nền/Windows Task Scheduler được bật rõ.

- **Depends on:** P10-01,P08-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Schedules/timezone/missed-run policy and watched roots.
- **Output/interface:** Persistent due-run claims, file-stability watcher, debounce/exclusion/overlap guard; opt-in background registration.
- **Errors/cancellation:** Clock jump/sleep duplicate events safe; partially copied file waits; disabled closed-app mode truthful; cancel unregister scope only.
- **Tests and acceptance:** Replay events/restart/sleep with deterministic clock, nested output no loop, competing schedulers unique due key; Windows Task Scheduler actual gate.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P10_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P10-03 — kênh→logo/preset/output, auto layout có giới hạn, chạy lại riêng nhóm/giữ sửa tay/dry-run.

- **Depends on:** P10-01,P01-04,P07-06. Only independent work may proceed while external portions remain blocked.
- **Input:** Channel→preset/logo/output mappings and manual override provenance.
- **Output/interface:** Dry-run rule application, bounded auto layout, group-specific rerun.
- **Errors/cancellation:** Missing mapping asset blocked not borrowed; locked values retained; cancel impact preview no changes.
- **Tests and acceptance:** Channel identity not display-name lookup, partial rerun leaves other groups/manual cues unchanged, reasons persisted.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P10_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P10-04 — CPU/RAM/GPU/VRAM/đĩa, Êm/Cân bằng/Tối đa, giới hạn riêng quét/tải/dịch/render/luồng mỗi việc.

- **Depends on:** P03-04,P02-05/07. Only independent work may proceed while external portions remain blocked.
- **Input:** Actual CPU/RAM/disk/GPU metrics and user profile/resource limits.
- **Output/interface:** Timestamped metric sampler and admission semaphores per scan/download/translate/render/threads.
- **Errors/cancellation:** Unavailable sensor unknown; low disk stops new work; cancel sampler shutdown bounded.
- **Tests and acceptance:** Simulated threshold edges + actual sample readback; independent GPU encode/filter claims; UI not blocked by metrics.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P10_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P10-05 — benchmark gợi ý, giữ tài nguyên dự phòng/backpressure/giảm nhận việc, phục hồi có ngưỡng tránh dao động; encode khác filter GPU.

- **Depends on:** P10-04,P02-07. Only independent work may proceed while external portions remain blocked.
- **Input:** Measured workload budgets and rolling resource samples.
- **Output/interface:** Benchmark recommendations, reserved capacity/backpressure, hysteresis and cooldown policy.
- **Errors/cancellation:** Transient spike never kills healthy render; stale metrics conservative; cancel benchmark retains old config.
- **Tests and acceptance:** Deterministic high/low sequences avoid oscillation and starvation; concurrent workload measured on declared machine.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P10_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P10-06 — ETA/tốc độ/công đoạn/lô, ưu tiên/đổi job chờ/thông báo, hành động sau xong do người dùng bật, dọn cache an toàn.

- **Depends on:** P10-01/04,P03-07. Only independent work may proceed while external portions remain blocked.
- **Input:** Actual progress/rates and queue priority/cache ownership.
- **Output/interface:** Stage/batch estimates, pending reorder, notifications and opt-in finish actions; safe cache cleanup.
- **Errors/cancellation:** Unknown totals no ETA fiction; shutdown action off by default; leased/source/output/profile cache never removed; cancel cleanup bounded.
- **Tests and acceptance:** ETA label/basis, order only pending, interrupted repeated completion notification once, protected-directory sentinels; no unrequested shutdown.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P10_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P10-07 — preflight tool/Chrome/session/quyền nguồn, lease tool/profile và giới hạn theo account/domain; login lại đúng nick rồi resume, cập nhật tool không đụng job đang chạy, không dọn browser data như cache.

- **Depends on:** P10-01,P03-08/09,P05-09/10. Only independent work may proceed while external portions remain blocked.
- **Input:** Tools/profile/account/domain limits and readiness snapshots.
- **Output/interface:** Atomic preflight/admission tool+profile leases, account/domain throttles, repair-resume path.
- **Errors/cancellation:** Stale account identity blocks, expired correct account waits, busy tool update doesn't alter lease; cancel releases owned reservations.
- **Tests and acceptance:** Concurrent lease/update/revoke/auth refresh; selected identity preserved, profile data excluded cleanup, unrelated local jobs continue.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P10_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
