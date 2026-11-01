# P03 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-03`. Status IN_PROGRESS; fresh slice A locally verified, not phase accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P03-01 — scaffold module, môi trường tái lập, dependency lock, config và user data tách khỏi thư mục chương trình.

- **Depends on:** P01-07.artifact_ready, P02-01.dev_toolchain_ready (not full P02-08 acceptance). Only independent work may proceed while external portions remain blocked.
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
- **Errors/cancellation:** Secret-valued unknown keys rejected; malformed progress ignored with bounded diagnostic; running cancellation allowed through coordinator; running snapshot update disallowed.
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

- **Depends on:** P03-02, P01-08.account_schema_ready (live P02-10 gates only authenticated handoff acceptance). Only independent work may proceed while external portions remain blocked.
- **Input:** Profile and account binding schema; credential reference store.
- **Output/interface:** Profile/browser-state/account web+bridge+rights repositories and account-scoped cache.
- **Errors/cancellation:** No secret persistence/export; profile busy distinct auth expired; unlink does not delete Chrome data; cancel leaves mappings.
- **Tests and acceptance:** A/B identity isolation, export/log sentinel, default binding persistence, mismatch preflight; live handoff remains P02/P05 gate.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome NOT_RUN.

## Phase gate
Every task acceptance above and corresponding master gate must pass. Unit/mock evidence does not close live/Windows/GPU/Chrome acceptance. Keep LOCAL_VERIFIED, BLOCKED_EXTERNAL and ACCEPTED distinct. Submit independent review and one aggregate checkpoint after affected tests; do not mark whole phase complete from a working slice.

## Fresh slice A — domain/schema/time and durable project entry

Entry evidence: independent P01 design accepted; P02 developer-toolchain/shared-raster milestones locally verified with codee0cfb14, scoped evidence review (not wholeP02 acceptance). Start P03-01/02/03/05 pure interfaces without authenticated provider/Chrome/GPU dependency.

Artifacts: fresh pyproject/lock; immutable CompositionPlan parser with structural+semantic validation; rational stream/cue/keyframe evaluator; distinct execution/render digests; transactional SQLite project repository/migration/atomic project-file persistence. No inherited source/tests. Runtime schema packaged with module from new P01 schema, not loaded from current-working-directory docs.

Focused tests: `tests/test_timebase.py` rational/bounds/rounding/easing/selected-stream and repeated-segment cue mapping; `tests/test_composition.py` strict JSON/refs/stream types/timing/layer/audio/ducking/immutable snapshot/path-vs-content digests; `tests/test_projects.py` save/open, invalid input, migration/backup/crash staging/readonly version/Unicode. UI/worker/publication integration follows its own affected tests. Pure domain tests are not full P03, compositor or runtime-feature-group acceptance.

Slice A extension: native eight-area shell with shared validated project open and explicit unavailable states; `tests/test_shell.py` covers navigation/open failure preservation and headless CLI. Fresh `uv.lock` owns reproducible installation. No production controls imply unimplemented workflows are available.

## Fresh slice B — local media probe and fingerprint

P03-03 independent entry consumes explicit ffprobe path and local source path; never discovers/downloads or falls back from an invalid explicit executable. Output is immutable raw stream/container metadata plus SHA-256 stable-content identity, stat-change guard and diagnostics; conversion to full selected-stream CompositionPlan snapshots follows separately. Hash and process waits support cancellation; wall-time and captured-output size bounded; argv list/no shell. Owned direct ffprobe child terminated/reaped on every exit; arbitrary descendant process-tree support remains P03-04 Windows gate. Tests use real generated tiny fixture plus fake executables for timeout/invalid/oversize/cancel and assert source unchanged. No source copied into repository.

## Fresh slice C — durable admission/lease state substrate

Independent P03-04 foundation after project SQLite transaction patterns. Dedicated jobs DB (not silently upgrading project DB) stores canonical plan-only snapshot plus seed; full tool/account/provider snapshot expansion remains future contract. Request-key idempotence rejects same key/different snapshot. Coordinator-only transitions enforce expected state/version and lease token; pause holds pending admission, cancel running records request and requires worker acknowledgment, publication is deliberately unavailable until validated artifact-set protocol exists. Expired leases are identified, never blindly succeeded/retried. Focused tests: duplicate submit, two coordinator connections competing claim, stale versions/tokens, cancel/paused transitions, reopen persistence. This substrate is not Windows worker/process/publication acceptance.

## Fresh slice D — owned process execution (POSIX developer adapter)

P03-04 execution adapter launches argv without shell in its own session/process group; drains bounded stdout/stderr via selectors; cancels/times out/output-overflows by terminating only its owned group then reaping. Input validation rejects implicit string/shell commands. Windows adapter deliberately raises unavailable until Job Object implementation and real tests; no parent-only-kill fallback. Focused real subprocess tests include grandchild cleanup, ordinary output, nonzero result, timeout, output cap and cancel. This is an internal worker building block, not UI responsiveness/full durable worker acceptance.

## Fresh slice E — Windows owned Job Object execution

User-authorized target priority: actual native Windows implementation, then source review and hosted Windows tests. CreateProcessW uses STARTUPINFOEX with explicit inherited stdin/stdout/stderr HANDLE_LIST and atomic JOB_LIST assignment, suspended launch, verified job membership, ResumeThread only after setup. Own unnamed nested job has KILL_ON_JOB_CLOSE and no breakaway flags. Parent crash closes sole job handle. Bounded anonymous-pipe capture, timeout/cancel terminate owned job, handles/attribute list retired on all failures; no global PID killing or security changes. Microsoft documents atomic JOB_LIST as closing the suspended-create/Assign orphan gap: https://devblogs.microsoft.com/oldnewthing/20230209-00/?p=107812 and HANDLE_LIST semantics: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute . Real target tests include grandchild cancel, parent crash, output bound, Unicode/space argv, unexpected inherited-handle sentinel. Linux structural ABI checks do not count as Windows runtime verification.

## Post-review quiescence increment (separate from 3c222a9 CI candidate)

Before publishing/cleaning worker resources, Windows retirement must observe owned job ActiveProcesses==0 via QueryInformationJobObject, after terminating owned job and releasing waited leader/thread handles. Bound query wait; failure/timeout remains unconfirmed retirement, not canceled-success. No output/resource reuse until this gate. Official accounting semantics: https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_accounting_information . Pure sequence tests cover pending→zero, query error and timeout; native Windows tests observe actual query path. Current reviewed CI candidate remains3c222a9, this later increment needs focused review/target execution.

## Independent slice F — account/profile domain without live browser effects

P03-09 pure model entry consumes reviewed account contract, not unavailable live Chrome gate. Browser ownership/state, website auth, connector bridge and source rights remain separate axes. One auth identity per platform/profile; multiple source pages/channels share that binding, alternate identity requires separate profile. Closed snapshot/reference allowlist excludes profile paths/session material. Account-scoped cache includes binding+identity+generation; identity mismatch blocks old job rather than public/account fallback. No browser launch, cookie read, credential entry, network or profile-folder mutation in this slice. Tests cover A/B isolation, source-vs-auth identity, stale snapshots and default/unlink semantics; persistence/live integration remain separate future work.

## Real process interruption checks for project durability

Use child processes paused at named save/SQLite boundaries, then terminate only their owned subprocess handles. Test before publish (old complete file), after publish (new complete file despite missing acknowledgment), before SQLite commit (old transaction survives), advisory lock release and subsequent save. Child markers contain only fixture readiness. Windows target runs same tests via CI; local Linux evidence never substituted. Orphan owned staging quarantine/autosave recovery remains separate implementation, no broad cleanup.

Direct rational API hardening: reject float/bool/nonfinite values not only at JSON parser but also TimeSegment construction, frame/sample/rounding and keyframe-evaluator entry points; normalize exact integers to Fraction. Regressions exercise public pure interfaces so later UI/worker callers cannot accidentally bypass exact-time contract.

## Hosted portability repair iteration 1

Exact-source hosted runs41276078838/41276112120 failed, so no target gate closes. Ubuntu needs normal signed-package Qt runtime libraries (libEGL missing); install those on ephemeral CI runner only, no security changes. Owned SQLite backup flush must use writable descriptor on Windows. Fingerprint invariants compare named-stat to named-stat and descriptor-stat to descriptor-stat (Windows APIs may report differing metadata timestamps), while retaining cross-API physical identity and mutation rejection. Handle-leak test measures warmed per-call plateau plus per-cycle counts, not one-time runtime initialization; no growing leak tolerated. SQLite3.13 post-kill I/O remains unresolved until extended error code/version is observed; no journal deletion or blind success retry.

## Hosted repair iteration 2 — observed SQLite1546 and exact checkout bytes

Run41276612605: Ubuntu bothgreen146PASS/11SKIP; Windows3.12 source139PASS/18SKIP then canonical-spec bytehash fails due checkout line endings; Windows3.13 only post-kill failure, exact SQLite3.50.4/SQLITE_IOERR_TRUNCATE1546. Preserve strict hashes, add .gitattributes exact canonical/reference bytes (no normalization workaround). Initial-open helper may reopen ONLY Windows+exact1546+verified app-owned DB receipt (application ID/header, schema signature, same physical file), within a3-second retry/backoff window, closing every failed connection. No new retry starts after deadline; SQLite busy wait uses remaining budget, but OS filesystem calls are not preemptible. Receipt established only after full schema validation/migration; absent/foreign receipt means no retry. No COMMIT/mutation/job replay or WAL/SHM deletion. Primary upstream reproduction/fix: https://sqlite.org/forum/info/ba7afbd0e81501118563617430fe06d0aca052e55ece2b0d457f8e16fcf85bba and https://sqlite.org/src/info/7c103a0b7d . This addresses the evidenced mapped-view retirement gap, not general I/O corruption.
