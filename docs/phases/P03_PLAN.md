# P03 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-03`. Status PLANNED, not implemented or accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P03-01 — scaffold module, môi trường tái lập, dependency lock, config và user data tách khỏi thư mục chương trình.

- **Depends on:** P01-07,P02-01/08. Only independent work may proceed while external portions remain blocked.
- **Input:** Chosen runtime/Qt versions, install/user-data policy.
- **Output/interface:** Fresh pyproject/lock/src package/entrypoint, eight-area shell, config paths and test runner.
- **Errors/cancellation:** Missing FFmpeg does not prevent app/settings startup; bad config quarantined with explanation; shutdown cancels owned tasks.
- **Tests and acceptance:** Fresh env install, CLI/GUI launch, Unicode user directory/read-only install; no demo metrics or old implementation imports.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P03-02 — schema/version/migration cho project/media/preset/job/artifact/history/cache; backup và phục hồi khi migration lỗi.

- **Depends on:** P03-01,P01-07. Only independent work may proceed while external portions remain blocked.
- **Input:** Project/media/preset/job/artifact/history/cache schemas.
- **Output/interface:** SQLite migrations/version table/verified backup; JSON project parser; transactional repositories.
- **Errors/cancellation:** Newer schema rejected read-only; failed migration rolls back and retains backup; interruption at every migration step.
- **Tests and acceptance:** Create/reopen/migrate/restore, corrupt DB/backup/fault tests; foreign keys and transaction atomicity verified.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P03-03 — probe, ID/fingerprint, rational timestamp/time map; media không audio hoặc metadata lỗi.

- **Depends on:** P03-01,P02-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Local video/image/audio paths and probe executable.
- **Output/interface:** Media probe record, stable IDs/hash, rational PTS/time-map service.
- **Errors/cancellation:** No audio/rotation/VFR valid; corrupt/truncated/unknown metadata diagnostics; bounded probe/hash cancel.
- **Tests and acceptance:** Corpus metadata matches expected streams/duration/PTS; source bytes unchanged; renamed identical media identity maintained.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P03-04 — scheduler/worker process, công đoạn/progress/cancel/pause/retry, quản lý tiến trình con trên Windows và lease phục hồi sau crash.

- **Depends on:** P03-02/03,P01-07. Only independent work may proceed while external portions remain blocked.
- **Input:** Durable jobs, execution plans, process capability policy.
- **Output/interface:** Coordinator/worker process, CAS lease/heartbeat, stage progress/pause/cancel/retry/recovery API.
- **Errors/cancellation:** Stale token/PID, duplicate event, timeout/crash; cancel owns process tree; unknown-billing not blindly retried.
- **Tests and acceptance:** All state edges including illegal transitions, real child kill/restart, pause admission, stale worker completion; UI heartbeat remains responsive.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P03-05 — snapshot cấu hình/seed, log lọc bí mật, phân loại lỗi và UI hàng đợi đầu tiên.

- **Depends on:** P03-04,P01-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Resolved snapshot/seed/tool/account refs and progress events.
- **Output/interface:** Canonical immutable snapshot hash; redacted event log; queue table commands and error taxonomy.
- **Errors/cancellation:** Secret-valued unknown keys rejected; malformed progress ignored with bounded diagnostic; cancel/update running disallowed.
- **Tests and acceptance:** Snapshot unchanged after preset edit; secret sentinels absent; unknown totals show counts; repeated submit idempotent.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P03-06 — output tạm → kiểm tra → tên cuối an toàn, không đè; truy vết nguồn; bỏ output/cache khi quét.

- **Depends on:** P03-02/04,P01-05. Only independent work may proceed while external portions remain blocked.
- **Input:** Validated staged output, final candidate, receipt and source roots.
- **Output/interface:** Publication journal/no-replace filesystem adapter/reconciler and Artifact repository.
- **Errors/cancellation:** Collision, disk-full, permission, symlink escape, cancel-before/after-claim; never adopt foreign file.
- **Tests and acceptance:** Inject crash at every JOBS boundary including real process kill; final readback hash+DB/history agree; foreign/source sentinels unchanged.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P03-07 — save/autosave/recovery, relink media, cache theo fingerprint/phiên bản; thử đóng bất thường có kiểm soát.

- **Depends on:** P03-02/03/05. Only independent work may proceed while external portions remain blocked.
- **Input:** Committed project commands, media refs, cache keys.
- **Output/interface:** Atomic save/autosave/recovery/relink; versioned bounded cache ownership.
- **Errors/cancellation:** Interrupted save preserves prior project; moved media prompts identity relink; cache busy not removed; cancel picker changes nothing.
- **Tests and acceptance:** Save/open equality, crash during write, latest valid autosave recovery, hash mismatch relink refusal, cache invalidation after asset change.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P03-08 — dependency registry/resolver, tool ownership/version/path/capabilities, trusted manifests, cài per-user, staging/self-test/activation/lease/rollback, không đè tool ngoài.

- **Depends on:** P03-02/04,P02-09. Only independent work may proceed while external portions remain blocked.
- **Input:** Tool manifest/install IDs, trusted bytes, ownership roots.
- **Output/interface:** Discovery/resolver, staging verification/activation/lease/rollback/cleanup registry.
- **Errors/cancellation:** Explicit invalid path no fallback; busy version cannot delete; archive/checksum/receipt mismatch fail; canceled install preserves active.
- **Tests and acceptance:** Real executable self-test; concurrent lease/update/cleanup; external binary unchanged; FFmpeg+ffprobe compatible pair and actual selected path recorded.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## P03-09 — schema BrowserProfile/PlatformAccountBinding, profile ownership/browser state/auth state, credential refs và account-scoped cache; không lưu cookie/mật khẩu trong project.

- **Depends on:** P03-02,P02-10. Only independent work may proceed while external portions remain blocked.
- **Input:** Profile and account binding schema; credential reference store.
- **Output/interface:** Profile/browser-state/account web+bridge+rights repositories and account-scoped cache.
- **Errors/cancellation:** No secret persistence/export; profile busy distinct auth expired; unlink does not delete Chrome data; cancel leaves mappings.
- **Tests and acceptance:** A/B identity isolation, export/log sentinel, default binding persistence, mismatch preflight; live handoff remains P02/P05 gate.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.
