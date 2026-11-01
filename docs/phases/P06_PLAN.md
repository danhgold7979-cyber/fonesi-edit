# P06 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-06`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P06-01 — SRT/VTT/ASS về cue chung, báo style chưa hỗ trợ; ghép bằng ID/ngôn ngữ/tên, báo mơ hồ.

- **Depends on:** P03-03,P05-06 for downloaded sub. Only independent work may proceed while external portions remain blocked.
- **Input:** UTF-8/BOM SRT,VTT,ASS; source ID/language/name candidates.
- **Output/interface:** Unified cue parser preserving supported style/provenance; ambiguity-aware attachment resolver.
- **Errors/cancellation:** Bad timestamp/encoding/unsupported style diagnostics; no arbitrary matching; cancel import leaves current track.
- **Tests and acceptance:** Round-trip multilingual cues; malformed/overlap/multiple-candidate cases; exact cue IDs/text and unsupported fields reported.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P06_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P06-02 — nguồn/đích/ưu tiên, sub người đăng/tự động, chính sách thiếu sub và khác ngôn ngữ.

- **Depends on:** P06-01,P05-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Available track language/origin and user source/target/priority policy.
- **Output/interface:** Deterministic subtitle selection and missing/foreign-language policy.
- **Errors/cancellation:** No suitable track→continue warning(default)/skip/wait explicit; automatic origin labelled; cancel no selected track replacement.
- **Tests and acceptance:** Language/region/uploader-vs-auto priority tables; mixed valid/missing batch independent; foreign language not burned silently.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P06_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P06-03 — adapter dịch thật, thuật ngữ/xưng hô/tên riêng/ngữ cảnh, cache, chi phí/rate limit/retry.

- **Depends on:** P06-01/02,P02-03,P03-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Unlocked cue IDs/text/context/glossary, configured provider/model and spending limit.
- **Output/interface:** Real translation adapter, exact ID response validation, versioned cache/quota ledger.
- **Errors/cancellation:** Missing/duplicate/unknown cue IDs rejected; partial errors retain original; timeout unknown billing; cancel stops new requests.
- **Tests and acceptance:** Configured live Chinese→Vietnamese quality evidence; fixture rate/cache/quota/request-id faults; font changes cache-neutral; no fake translations.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P06_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P06-04 — gốc/dịch song song, sửa/tìm/thay/tách/gộp, dịch lại câu chọn, khóa câu đã sửa, lịch sử.

- **Depends on:** P06-01/03,P04-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Original/translated cue model and manual-lock metadata.
- **Output/interface:** Parallel editor find/replace/split/merge/selective-retranslate/history commands.
- **Errors/cancellation:** Locked cue not auto-overwritten; split/merge invalid bounds refused; replace preview canceled no edits; stale response revision ignored.
- **Tests and acceptance:** Undo/save/open text equality; selective request only chosen unlocked cues; repeated translate does not erase manual edits.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P06_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P06-05 — thời gian qua timeline/ô số, offset, kiểm tra chồng/tràn, time map sau trim/speed.

- **Depends on:** P06-01,P04-05. Only independent work may proceed while external portions remain blocked.
- **Input:** Cue intervals and segmented clip time map.
- **Output/interface:** Timeline drag/numeric edit/offset plus overlap/short/overflow validation.
- **Errors/cancellation:** Clip intersection preserves partial text; out-of-range warning not destructive; Esc restores drag.
- **Tests and acceptance:** Trim/speed/repeat/crossfade cue oracle at boundaries; one drag one undo; Vietnamese/Chinese text unchanged.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P06_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P06-06 — đơn/song ngữ, style cơ bản liên kết P07, xuất SRT/ASS và burn-in qua pipeline chung.

- **Depends on:** P06-04/05,P07-02/08 for full render. Only independent work may proceed while external portions remain blocked.
- **Input:** Linked mono/bilingual tracks/styles and output policy.
- **Output/interface:** SRT/ASS sidecars plus canonical burn-in execution plan; independent block styles/visibility.
- **Errors/cancellation:** Missing font/style capability blocks affected render; partial sidecar publication no success; cancel publication contract.
- **Tests and acceptance:** Reparse exported sidecars exact text/time, external-player burn-in, start/end frame assertions, two blocks order and independent toggles.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P06_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
