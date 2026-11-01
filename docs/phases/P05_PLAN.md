# P05 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-05`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P05-01 — registry/capabilities, nhiều URL, bài/kênh/playlist, ID chuẩn và loại trùng.

- **Depends on:** P03-03/09,P02-02. Only independent work may proceed while external portions remain blocked.
- **Input:** URL lists/files and connector capability definitions.
- **Output/interface:** Registry identify/canonicalize URL kind+stable ID; deduplicate input before enqueue.
- **Errors/cancellation:** Unknown/invalid URL not guessed as channel; unsupported kind explicit; canceled import no partial jobs.
- **Tests and acceptance:** Ten-platform URL fixture types and canonical duplicate tests; live identity comparison for declared capability.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P05_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P05-02 — phân trang/checkpoint, ảnh/video/Reels/Shorts/album khi nguồn hỗ trợ, lọc ngày/thời lượng/số lượng/chất lượng.

- **Depends on:** P05-01,P02-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Source/filter/account context and durable cursor.
- **Output/interface:** Paged enumerate with date/duration/count/quality/type/order filters; explicit complete/partial/unknown.
- **Errors/cancellation:** Cursor loop/expired auth/rate limit partial result; cancel checkpoint durable; unknown metadata not zero.
- **Tests and acceptance:** Multi-page fixtures plus permitted live source, boundary filter/date/order, new-only second scan; each media type independently accepted.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P05_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P05-03 — cây nội dung, chọn mục, tổng chưa biết/quét ngắt, cancel và tiếp tục khi hỗ trợ.

- **Depends on:** P05-02,P04-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Incremental enumerated items and selection state.
- **Output/interface:** Source tree with checkbox/type counts, unknown totals and resume checkpoint.
- **Errors/cancellation:** Late page cannot resurrect deselected source; cancel retains partial label; resume unsupported shows restart consequence.
- **Tests and acceptance:** Qt incremental scan/cancel/navigate/repeat/resume, selection and counts correct without fabricated percentage.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P05_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P05-04 — downloader/tệp tạm/validation, tốc độ/retry/rate limit/auth; không log cookie/token.

- **Depends on:** P03-04/06/08,P05-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Selected source item/quality/account and staging target.
- **Output/interface:** Downloader worker with actual byte progress, bounded retry/rate limit and validated artifact handoff.
- **Errors/cancellation:** Auth/quota wait; incomplete/invalid bytes fail; cancel only owned temp; secret redaction; no silent public fallback.
- **Tests and acceptance:** Local HTTP fault server and actual live output by capability; interruption/resume where supported; no success until decode validation.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P05_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P05-05 — folder/kênh/album Unicode có ID, video/images/subtitles/metadata, thiếu đĩa/quyền ghi/tên dài/xung đột.

- **Depends on:** P05-01/04,P01-05. Only independent work may proceed while external portions remain blocked.
- **Input:** Stable source/item/album IDs and destination policy.
- **Output/interface:** Unicode channel-ID folder naming, ordered image album/media/sub/metadata paths.
- **Errors/cancellation:** Reserved names/long paths/disk-full/collision exact errors; cancel no source mutation.
- **Tests and acceptance:** Same-name different channel, renamed channel stable root, album order, Windows path rules and final no-overwrite sentinel.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P05_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P05-06 — chống trùng theo ID/chất lượng/tệp hợp lệ; bổ sung sub riêng, tải lại tệp lỗi, đồng bộ lần hai và kênh đổi tên.

- **Depends on:** P05-04/05,P03-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Validated artifact history/source quality/sub inventory.
- **Output/interface:** Idempotent sync, subtitle-only fetch, corrupt-file repair and explicit quality-upgrade job.
- **Errors/cancellation:** Missing video/hash mismatch not skipped; incomplete scan not all-done; cancel transaction atomic.
- **Tests and acceptance:** Second sync zero redundant media; missing sub only sub; corrupt output repaired via new safe publication; renamed channel does not duplicate.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P05_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P05-07 — kiểm chứng nguồn/loại media/auth, lưu ngày/phiên bản/evidence. Thiếu quyền ghi blocker, không dùng mock để báo hỗ trợ.

- **Depends on:** P05-01..06,P02-02. Only independent work may proceed while external portions remain blocked.
- **Input:** Per-platform real scans/downloads/account rights and tool versions.
- **Output/interface:** Timestamped capability matrix with evidence links and limitations.
- **Errors/cancellation:** Expired evidence/source change marks degraded, not universal support; user lacks permission→BLOCKED.
- **Tests and acceptance:** Reviewer opens actual artifacts and matches each claimed URL/media/auth cell; all ten platforms retained even blocked.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P05_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P05-08 — profile manager mở Chrome thật vào đúng user-data-dir/nền tảng, tạo/đặt tên/gán nhiều nền tảng, tách nick cùng nền tảng, xử lý khóa/bận mà không phá profile.

- **Depends on:** P03-09,P04-08,P02-10. Only independent work may proceed while external portions remain blocked.
- **Input:** Official Chrome installation and app-owned profile IDs.
- **Output/interface:** Create/name/open correct user-data-dir/platform URL; busy/lock lifecycle.
- **Errors/cancellation:** Wrong binary/browser rejected; do not remove lock/force close; canceled profile create cleans only unused owned staging.
- **Tests and acceptance:** Command args/path/ownership tests plus Windows official Chrome A/B isolation and restart evidence.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P05_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P05-09 — session broker theo cơ chế đạt P02, đăng nhập/kiểm tra/đăng nhập lại cho mọi nền tảng, nhận diện nick, trạng thái website khác khả năng connector dùng phiên và quyền nguồn.

- **Depends on:** P05-08,P02-10. Only independent work may proceed while external portions remain blocked.
- **Input:** Expected account identity and supported broker capability.
- **Output/interface:** Session broker verify web identity/bridge/source rights, refresh/relogin and account-scoped handles.
- **Errors/cancellation:** Expired/challenge/mismatch/bridge-unavailable separately blocked; no cookie-copy/decrypt fallback; revoke stops future handoff.
- **Tests and acceptance:** Live correct-account private-permitted source scan/download, concurrent revoke/verify, no session in exported data/logs.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P05_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P05-10 — chọn account theo nguồn/job, nhớ mặc định, refresh cùng danh tính/resume, mismatch chặn đúng job; không silent fallback sang công khai hoặc tự xoay nick; auth cache không lẫn tài khoản.

- **Depends on:** P05-09/04,P03-05. Only independent work may proceed while external portions remain blocked.
- **Input:** Source default account and immutable job binding.
- **Output/interface:** Preflight choose/persist binding; same-identity refresh resumes; explicit rebinding revisions.
- **Errors/cancellation:** Mismatch blocks old job; no account rotation/public downgrade; cancellation during refresh preserves job.
- **Tests and acceptance:** A/B account cache separation and repeated restart; expired→same account resume no duplicates; switched identity cannot execute old snapshot.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P05_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
