# P08 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-08`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P08-01 — nhiều folder/đệ quy/checkbox/loại/đảo chọn/tìm/lọc, không xóa nguồn, không nhận output/cache.

- **Depends on:** P03-03/07,P04-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Multiple selected input roots, exclusion roots and format/metadata filters.
- **Output/interface:** Bounded background scanner/tree/checkbox/invert/search/canonical selected manifest.
- **Errors/cancellation:** Loops/output/cache excluded; unreadable paths reported; cancel scan labelled partial; no deletion on remove.
- **Tests and acceptance:** Nested output, duplicate roots, Unicode/symlink, unknown metadata, 10k paths; visible-selection operations never modify hidden items unintentionally.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P08_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P08-02 — preset/ghi đè clip/xem tác động/snapshot, output theo kênh/mẫu tên/phiên bản không đè.

- **Depends on:** P08-01,P01-04,P03-05/06. Only independent work may proceed while external portions remain blocked.
- **Input:** Selected clip manifest and preset/scoped overrides/output policy.
- **Output/interface:** Impact preview and immutable per-item snapshots with source/channel output naming.
- **Errors/cancellation:** Stale plan/changed media invalidates enqueue; collision no-overwrite; cancel all-new enqueue transaction.
- **Tests and acceptance:** Preset changes cannot mutate queued/running items; nested locks retained; names/roots same as preview and unique by IDs.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P08_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P08-03 — tiếng gốc/âm chính/nhạc/SFX, mute/solo/gain/fade/trim/delay, meter/clipping/chuẩn hóa.

- **Depends on:** P07-08,P04-05. Only independent work may proceed while external portions remain blocked.
- **Input:** Original/main/music/SFX audio clips and master mix options.
- **Output/interface:** Track mixer mute/solo/gain/fade/trim/delay, decoded meter/clipping and normalization.
- **Errors/cancellation:** No-audio explicit; over-limit warns; meter absent=unknown; cancel audition stops owned playback not project.
- **Tests and acceptance:** Known tones/impulses prove gain/delay/mute/solo/fades; meter label distinguishes decoded signal from speakers; target loudness measured.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P08_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P08-04 — audio cả lô/theo tên/danh sách/random và playlist thủ công đa thư mục có preflight/snapshot/render verification; nhạc lặp chuyển tiếp; SFX theo giây/cảnh/tỷ lệ và trigger không đều; ducking theo chính sách hỗ trợ.

- **Depends on:** P08-03,P08-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Shared/by-name/ordered/random/manual cross-folder playlist and SFX/ducking settings.
- **Output/interface:** Audio assignment preflight/snapshot; explicit loops/crossfades/trigger events and envelope policy.
- **Errors/cancellation:** Ambiguous basename/count mismatch/missing audio rejects affected mapping before jobs; canceled playlist picker unchanged.
- **Tests and acceptance:** Manual paths incl same basenames and duplicates map correctly; seeded assignment; event timings on final duration; actual PCM output verifies chosen audio.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P08_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P08-05 — duration planner một hoặc nhiều clip; đích video/audio/nhập tay, min/max speed/đoạn, giữ cao độ, lặp/freeze/cắt theo lựa chọn.

- **Depends on:** P08-03/04,P01-05. Only independent work may proceed while external portions remain blocked.
- **Input:** One/multi-clip mode, target duration source, limits and selected trim/speed/loop/freeze policies.
- **Output/interface:** Pure duration solver returns exact segmented map and preserve-pitch decisions.
- **Errors/cancellation:** Infeasible reason without auto mode/speed changes; bounded search/cancel no plan commit.
- **Tests and acceptance:** Rational oracle per allocation mode, insufficient one-clip duration, preserve pitch tone test, all min/max/speed constraints maintained.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P08_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P08-06 — tính chuyển cảnh/audio crossfade vào thời lượng, time map sub; báo bất khả thi, không tự bỏ cảnh/ghép clip ngoài chế độ.

- **Depends on:** P08-05,P06-05. Only independent work may proceed while external portions remain blocked.
- **Input:** Adjacent transitions/audio crossfades and cue mapping.
- **Output/interface:** Overlap-aware final duration/time map with required scene order.
- **Errors/cancellation:** Invalid/triple overlap rejected; no hidden scene drop; canceled adjustment rolls back.
- **Tests and acceptance:** D=sum segments−overlaps oracle, subtitle boundaries/repeats, audio event positions and exact scene presence.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P08_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P08-07 — chạy thử một video/đoạn, ước tính dung lượng/ETA, render lô/resume, kiểm tra duration/tracks/media.

- **Depends on:** P08-02..06,P03-04/06. Only independent work may proceed while external portions remain blocked.
- **Input:** Confirmed snapshots and test-segment/full-batch selection.
- **Output/interface:** Real sample render, estimates labelled with basis, per-item queue/resume/validation.
- **Errors/cancellation:** Unknown ETA/disk estimate labelled; one failure not whole-lot restart; cancel only unfinished owned stages.
- **Tests and acceptance:** Mixed aspect/FPS/audio/sub batch output decode/track/duration checks; reopen keeps successes and retry failed only; sample and full same model.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P08_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
