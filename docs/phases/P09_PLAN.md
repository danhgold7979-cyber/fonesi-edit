# P09 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-09`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P09-01 — quét C1…Cn/G1…Gm, natural sort/đổi thứ tự/khóa/loại, ID ổn định/tên logic; đổi tên thật có ánh xạ hoàn tác riêng.

- **Depends on:** P08-01,P01-05. Only independent work may proceed while external portions remain blocked.
- **Input:** Parent scene roots and stable asset hashes.
- **Output/interface:** Natural-sort scene/angle tree, logical IDs/order/locks/exclusions; separate real-rename preview/undo map.
- **Errors/cancellation:** Empty scene/duplicate physical file/collision flagged; canceled rename atomic compensation; logical rename never touches source.
- **Tests and acceptance:** C2 before C10, renamed same file identity, locks/order saved, source hashes/paths unchanged in logical mode.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P09_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P09-02 — tích tổ hợp/lọc/history dự án/hash góc/tổ hợp; phân biệt reservation và đầu ra thành công.

- **Depends on:** P03-02/06,P09-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Scene/angle identities and chosen project/global history scope.
- **Output/interface:** Lazy theoretical count/filter index/hash-based combination ledger and transactional reservation.
- **Errors/cancellation:** Duplicate reservation race rejected; failed/canceled distinct succeeded; cancel reservation rollback.
- **Tests and acceptance:** Small full-product oracle, same content renamed, concurrent enqueue uniqueness, successful history only with validated artifact.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P09_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P09-03 — generator seed/không trùng/cân bằng/W/K, phạm vi so sánh, timeout/cancel, chưa tìm đủ khác bất khả thi.

- **Depends on:** P09-02,P01-05. Only independent work may proceed while external portions remain blocked.
- **Input:** N/W/K/scope/seed/locks/history and search time/node budget.
- **Output/interface:** Bounded lazy generator with balanced candidate preference and explicit status.
- **Errors/cancellation:** Impossible simple bound reports proof; timeout partial≠infeasible; cancel no new jobs; never relax constraints.
- **Tests and acceptance:** Exhaustive small space constraints and seeded replay; large product bounded memory/time, all hard constraints checked on result.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P09_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P09-04 — bảng sửa/khóa ô/tạo lại hàng/preview/chuỗi C1G1+C2G2+…/thống kê/CSV; sửa hàng phải kiểm tra lại ràng buộc.

- **Depends on:** P09-03,P04-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Generated rows, selected locked cells and canonical scene map.
- **Output/interface:** Editable matrix table/regenerate-row/preview/CSV/stats with revalidation.
- **Errors/cancellation:** Running row immutable; edited row rechecks affected W/K windows; cancel edit restores; CSV no secrets/formula execution.
- **Tests and acceptance:** Manual conflicting edit rejected, locked cell regeneration stable, correct C/G strings/stats, CSV round-trip and preview exact snapshot.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P09_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P09-05 — chia đều/tỷ lệ/trọng số/nhập tay, dùng duration planner P08, tính chuyển cảnh, giữ đủ/thứ tự.

- **Depends on:** P09-04,P08-05/06. Only independent work may proceed while external portions remain blocked.
- **Input:** Scene row/audio target/equal-proportional-weight-manual allocation.
- **Output/interface:** Per-row duration plan using shared batch solver; preserve scene/order/overlap.
- **Errors/cancellation:** Insufficient scene rejects row, not silently remove; cancellation retains previous valid row.
- **Tests and acceptance:** Same inputs equal batch duration result, every scene represented, overlap/audio duration bounds and declared allocations.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P09_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P09-06 — render/validation theo hàng, snapshot nguồn/góc/preset/seed, commit lịch sử sau output hợp lệ, retry không sinh tổ hợp mới ngầm.

- **Depends on:** P09-02/05,P07-08,P03-06. Only independent work may proceed while external portions remain blocked.
- **Input:** Reserved immutable rows/assets/preset/audio/seed and tool leases.
- **Output/interface:** Per-row actual render/validation/publication/history commit and retry.
- **Errors/cancellation:** Missing source/version invalidates preflight; crash reconcilable; cancel before claim releases failed reservation only by policy.
- **Tests and acceptance:** Actual multi-scene output order/audio/sub/length; crash at publication commit; retry same row and history exactly once.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P09_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
