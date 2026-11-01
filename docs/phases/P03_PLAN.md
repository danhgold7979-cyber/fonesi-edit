# P03 — Task-specific clean implementation plan

Generation clean-2026-11-01; branch `phase-03`. Status IN_PROGRESS; fresh slice A locally verified, not phase accepted. Read master and mapped source clauses before code. No legacy runtime evidence is accepted. Contract files in docs/contracts are normative; any unresolved engine/provider gate remains explicit. Each row below is a separate task contract, not a generic checklist.

## P03-01 — scaffold module, môi trường tái lập, dependency lock, config và user data tách khỏi thư mục chương trình.

- **Depends on:** P01-07.artifact_ready, P02-01.dev_toolchain_ready (not full P02-08 acceptance). Only independent work may proceed while external portions remain blocked.
- **Input:** Chosen runtime/Qt versions, install/user-data policy.
- **Output/interface:** Fresh pyproject/lock/src package/entrypoint, eight-area shell, config paths and test runner.
- **Errors/cancellation:** Missing FFmpeg does not prevent app/settings startup; bad config quarantined with explanation; shutdown cancels owned tasks.
- **Tests and acceptance:** Fresh env install, CLI/GUI launch, Unicode user directory/read-only install; no demo metrics or old implementation imports.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome PARTIAL; see P03_ACCEPTANCE_LEDGER.md for exact accepted children and remaining complete-task gates.

## P03-02 — schema/version/migration cho project/media/preset/job/artifact/history/cache; backup và phục hồi khi migration lỗi.

- **Depends on:** P03-01,P01-07. Only independent work may proceed while external portions remain blocked.
- **Input:** Project/media/preset/job/artifact/history/cache schemas.
- **Output/interface:** SQLite migrations/version table/verified backup; JSON project parser; transactional repositories.
- **Errors/cancellation:** Newer schema rejected read-only; failed migration rolls back and retains backup; interruption at every migration step.
- **Tests and acceptance:** Create/reopen/migrate/restore, corrupt DB/backup/fault tests; foreign keys and transaction atomicity verified.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome PARTIAL; see P03_ACCEPTANCE_LEDGER.md for exact accepted children and remaining complete-task gates.

## P03-03 — probe, ID/fingerprint, rational timestamp/time map; media không audio hoặc metadata lỗi.

- **Depends on:** P03-01,P02-01. Only independent work may proceed while external portions remain blocked.
- **Input:** Local video/image/audio paths and probe executable.
- **Output/interface:** Media probe record, stable IDs/hash, rational PTS/time-map service.
- **Errors/cancellation:** No audio/rotation/VFR valid; corrupt/truncated/unknown metadata diagnostics; bounded probe/hash cancel.
- **Tests and acceptance:** Corpus metadata matches expected streams/duration/PTS; source bytes unchanged; renamed identical media identity maintained.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome PARTIAL; see P03_ACCEPTANCE_LEDGER.md for exact accepted children and remaining complete-task gates.

## P03-04 — scheduler/worker process, công đoạn/progress/cancel/pause/retry, quản lý tiến trình con trên Windows và lease phục hồi sau crash.

- **Depends on:** P03-02/03,P01-07. Only independent work may proceed while external portions remain blocked.
- **Input:** Durable jobs, execution plans, process capability policy.
- **Output/interface:** Coordinator/worker process, CAS lease/heartbeat, stage progress/pause/cancel/retry/recovery API.
- **Errors/cancellation:** Stale token/PID, duplicate event, timeout/crash; cancel owns process tree; unknown-billing not blindly retried.
- **Tests and acceptance:** All state edges including illegal transitions, real child kill/restart, pause admission, stale worker completion; UI heartbeat remains responsive.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome PARTIAL; see P03_ACCEPTANCE_LEDGER.md for exact accepted children and remaining complete-task gates.

## P03-05 — snapshot cấu hình/seed, log lọc bí mật, phân loại lỗi và UI hàng đợi đầu tiên.

- **Depends on:** P03-04,P01-04. Only independent work may proceed while external portions remain blocked.
- **Input:** Resolved snapshot/seed/tool/account refs and progress events.
- **Output/interface:** Canonical immutable snapshot hash; redacted event log; queue table commands and error taxonomy.
- **Errors/cancellation:** Secret-valued unknown keys rejected; malformed progress ignored with bounded diagnostic; running cancellation allowed through coordinator; running snapshot update disallowed.
- **Tests and acceptance:** Snapshot unchanged after preset edit; secret sentinels absent; unknown totals show counts; repeated submit idempotent.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome PARTIAL; see P03_ACCEPTANCE_LEDGER.md for exact accepted children and remaining complete-task gates.

## P03-06 — output tạm → kiểm tra → tên cuối an toàn, không đè; truy vết nguồn; bỏ output/cache khi quét.

- **Depends on:** P03-02/04,P01-05. Only independent work may proceed while external portions remain blocked.
- **Input:** Validated staged output, final candidate, receipt and source roots.
- **Output/interface:** Publication journal/no-replace filesystem adapter/reconciler and Artifact repository.
- **Errors/cancellation:** Collision, disk-full, permission, symlink escape, cancel-before/after-claim; never adopt foreign file.
- **Tests and acceptance:** Inject crash at every JOBS boundary including real process kill; final readback hash+DB/history agree; foreign/source sentinels unchanged.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome PARTIAL; see P03_ACCEPTANCE_LEDGER.md for exact accepted children and remaining complete-task gates.

## P03-07 — save/autosave/recovery, relink media, cache theo fingerprint/phiên bản; thử đóng bất thường có kiểm soát.

- **Depends on:** P03-02/03/05. Only independent work may proceed while external portions remain blocked.
- **Input:** Committed project commands, media refs, cache keys.
- **Output/interface:** Atomic save/autosave/recovery/relink; versioned bounded cache ownership.
- **Errors/cancellation:** Interrupted save preserves prior project; moved media prompts identity relink; cache busy not removed; cancel picker changes nothing.
- **Tests and acceptance:** Save/open equality, crash during write, latest valid autosave recovery, hash mismatch relink refusal, cache invalidation after asset change.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome PARTIAL; see P03_ACCEPTANCE_LEDGER.md for exact accepted children and remaining complete-task gates.

## P03-08 — dependency registry/resolver, tool ownership/version/path/capabilities, trusted manifests, cài per-user, staging/self-test/activation/lease/rollback, không đè tool ngoài.

- **Depends on:** P03-02/04,P02-09. Only independent work may proceed while external portions remain blocked.
- **Input:** Tool manifest/install IDs, trusted bytes, ownership roots.
- **Output/interface:** Discovery/resolver, staging verification/activation/lease/rollback/cleanup registry.
- **Errors/cancellation:** Explicit invalid path no fallback; busy version cannot delete; archive/checksum/receipt mismatch fail; canceled install preserves active.
- **Tests and acceptance:** Real executable self-test; concurrent lease/update/cleanup; external binary unchanged; FFmpeg+ffprobe compatible pair and actual selected path recorded.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome PARTIAL; see P03_ACCEPTANCE_LEDGER.md for exact accepted children and remaining complete-task gates.

## P03-09 — schema BrowserProfile/PlatformAccountBinding, profile ownership/browser state/auth state, credential refs và account-scoped cache; không lưu cookie/mật khẩu trong project.

- **Depends on:** P03-02, P01-08.account_schema_ready (live P02-10 gates only authenticated handoff acceptance). Only independent work may proceed while external portions remain blocked.
- **Input:** Profile and account binding schema; credential reference store.
- **Output/interface:** Profile/browser-state/account web+bridge+rights repositories and account-scoped cache.
- **Errors/cancellation:** No secret persistence/export; profile busy distinct auth expired; unlink does not delete Chrome data; cancel leaves mappings.
- **Tests and acceptance:** A/B identity isolation, export/log sentinel, default binding persistence, mismatch preflight; live handoff remains P02/P05 gate.
- **Evidence:** Record new commit, exact test command/corpus/tool versions and criterion IDs in P03_RESULTS.md; runtime acceptance requires executable behavior above, not file existence. Current outcome PARTIAL; see P03_ACCEPTANCE_LEDGER.md for exact accepted children and remaining complete-task gates.

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

## Fresh slice G — owned filesystem publication substrate (P03-06)

After the independently reviewed hosted foundation checkpoint, implement the actual
filesystem half of JOBS step3 before any job-success API. Input: explicit existing
local destination root, exclusive UUID staging directory/file, closed writer and
validator-produced SHA256/size. Output: retained staging plus atomic hard-link final,
with physical identity/hash readback; no overwrite, no deletion of final paths.
Pin directory identity/handles through operations; reject symlink/reparse paths,
invalid Windows filenames, foreign collisions (including identical bytes), changed
staging and unsupported hard-link filesystems. Return explicit conflict/unknown rather
than adopt a planned pathname. Cancellation before claim leaves staging owned; after
claim belongs to future journal reconciliation, not arbitrary worker cleanup.

Tests: actual filesystem no-replace race, foreign-identical destination, changed
staging, Unicode names, symlink/reparse refusal, retained link identity, reopened
receipt recovery with/without staging. Run relevant Linux tests then actual Windows
CI after source review. Directory durability limitations remain explicit. This slice
must NOT mark job success, delete retained staging, or close OPS-06.03: durable SQLite
journal, required-artifact set and final all-member transaction follow separately.

## Fresh slice H — same-database publication records and migration (P03-02/06)

Keep publication sets/artifacts/history in the jobs SQLite database so future final
success can commit atomically with job state. Introduce exact schema-v2 signatures,
transactional v1→v2 upgrade and verified pre-upgrade backup. Existing ownership
receipts retain their creation-schema lineage; only explicitly known lineage hashes
are accepted, and current full table signatures are independently checked before
mutation/WAL. Never rewrite a foreign receipt or accept its hash as schema validity.
Test fresh/reopen, populated v1 preservation, rollback at each migration boundary,
restoreable backup, malformed/future schema unchanged. This slice adds records only;
no artifact-set success API until filesystem/validation/journal protocol is integrated.

## Fresh slice I — probe routes through owned process adapter (P03-03/04)

Replace the early ffprobe-only direct Popen loop with the already reviewed owned
process adapter. Keep explicit executable/no fallback, local protocol whitelist,
strict JSON and unchanged-source fingerprints. Bounds and cancellation now retire
owned descendants too. Test real local audio probe and fake executable timeout,
overflow, cancellation, descendant retirement; Windows real-tool case stays OPEN
when FFmpeg is absent, not replaced by POSIX fixture results. No new UI-thread work.

## Fresh slice J — reuse mature subtitle parser at bounded sidecar boundary

Under the user's reuse/quality gate, source/adoption/quality/license evidence is in
`docs/dependencies/UPSTREAM_REUSE.md`. Provisionally integrate the exact official
pysubs2 1.9.1 wheel/hash, not a custom subtitle parser or third-party fork. Adapter
accepts explicit SRT/VTT/ASS/SSA and encoding, bounds bytes/lines/cues, converts library
millisecond times to exact Fractions, retains immutable original bytes and stable
internal cue IDs plus source labels. Reject malformed timestamp/default warnings,
unsupported VTT metadata/layout and embedded ASS attachments; no silent fidelity loss,
zero-time invention, word alignment or network/provider call. Preserve raw ASS styles
with an explicit mapping-pending diagnostic, not a full-render/roundtrip claim.
Test Unicode/overlap/labels/empty/corrupt/range/resource guards and known upstream
malformed-ASS issue. Actual Windows/frozen package and P04 editor workflows remain gates.

### Slice J filesystem-path entry
Reuse existing `fileio.read_bounded` (limit+1 actual read) for explicit regular filesystem
subtitle files, then the reviewed pure adapter. Return a new immutable document only
after successful parse and final cancellation check; caller owns atomic current-track
replacement. Typed cancellation and sanitized I/O/size errors do not expose raw paths
or file contents. No directory scanning, network URLs, auto-encoding, provider effects
or source mutation. A bounded byte read is not a hard OS I/O time guarantee; invoke on
the worker path, never synchronously in the UI. Tests prove Unicode paths, unchanged
source/current document on failure/cancel, oversized read rejection and redacted errors.

### Slice J headless packaging entry
Add --validate-subtitles PATH with required explicit --subtitle-format and optional
allowlisted --subtitle-encoding, mutually exclusive with --validate-plan. Delegate to
reviewed file adapter; no Qt/user-data creation, source/output writes or provider calls.
Filesystem paths may resolve through network mounts; do not claim network isolation.
Report only cue count and bounded fixed diagnostics, never source text/raw paths. This
is parsing validation, not full style/render fidelity. Test argument errors/redaction/
Unicode/headless behavior, then frozen dependency/license inclusion and fixture execution;
local Linux frozen proof is not Windows acceptance.

### Slice K — typed subtitle staging observation (not job acceptance)
For already-produced subtitle bytes, parse with pinned upstream before creating any
stage; reuse Destination.create_stage for exclusive same-filesystem retained-anchor
storage. Return immutable parse-policy/version/hash/size/cue-count/diagnostic observation
bound to that exact StageReceipt. This observation is not publication authority or a
caller-supplied validation boolean: coordinator must later bind required roles/snapshot
and retain live capabilities. No final path/link/job mutation, cleanup, rendered-video
validation, subtitle-to-snapshot content assertion or restart recovery in this slice.
Malformed data/cancel before write leaves no stage; cancel after write preserves owned
staging (explicit receipt on cancellation), never deletes unknown files. Tests prove
validation precedes writing, exact byte/hash binding, cancellation retention, no final
output and existing source/sentinels unchanged. No additional package is needed.

### Slice L — actual media validation, SRC-08.02 / OPS-06.01 (partial until publication integration)
Reuse explicit ffprobe and owned FFmpeg null-output decode, not a custom decoder. A
closed expectation describes exact video/audio stream indices, codecs, video geometry/
frame rate or audio sample rate/channel count, start and duration with rational bounded
tolerance. Reject missing/extra tracks, metadata mismatch, absent duration, decode error/
empty stream, changed bytes, cancellation and timeout. Decode all selected streams with
-xerror/-abort_on empty_output+empty_output_stream/-max_error_rate 0, no stream-copy or
skip based on extension. Return observation only; no success/publication authority.
References: https://ffmpeg.org/ffmpeg.html and installed explicit-tool help. Tests use
small locally generated fixtures plus targeted negative metadata/process cases; distinguish
actual Linux FFmpeg from mocks and unavailable Windows FFmpeg. Full renderer parity,
all-format corpus, tool registry and durable publication binding remain required/open.

### Slice M — immutable required-output manifest before journal admission
Current v1 job snapshot has composition+seed only; it must not invent required roles
from caller publication events. Add a closed immutable manifest for new v2 snapshots:
nonempty unique role IDs, media/subtitle kind, explicit absolute destination roots and
safe final leaf names. Preserve exact v1 serialization when manifest absent. Existing
request key with changed manifest conflicts; reopening cannot mutate required roles.
No filesystem reservation/validation authority or publish/success state added here.
Native root identity/case collisions and source overlap remain admission checks, not
claims from path spelling. Tests cover immutable manifest, duplicate roles/paths, unsafe
names/relative roots, exact old snapshots, new reopen/idempotence and manifest drift.

### Slice N — stream real media into existing owned staging
Remove the sidecar writer's 32MiB limitation from the separate media-copy path without
changing existing create_stage(bytes) limits. Reuse one internal exclusive writer/live
anchor routine; read regular source in ≤1MiB chunks, bound total by opened size+1, compare
source identity/size/timestamps per-API before/after. Never open source for write; retain
partial staging on cancel/I/O/source-change failure, no final path or cleanup. Chunk
cancellation is not an OS I/O deadline. Verify >32MiB copy/hash/retained hardlink, canceled/
growing/changed source, symlink rejection and regression coverage of affected writer.

### Slice O — bind semantic validation and required-set admission together
Extend new output manifests with optional versioned validation policy; intent-only
v1 manifests remain readable but non-publishable. Media policy binds exact ExpectedStream
records; subtitle policy binds explicit format/encoding and expected produced-byte hash.
Changing policy changes immutable job snapshot/idempotence identity. Stored readback
checks digest, closed keys/versions and typed values; no worker validation boolean.
Coordinator session holds native ownership and live Destinations, stages/copies and
actually validates every required role, then prepare/claim CAS transactions use only
its retained in-memory observations. Missing/failed member or canceled/expired worker
before claim cannot publish. No finish/success API until complete artifact readback and
all-member transaction are integrated. Test policy drift, malformed/legacy snapshots,
wrong role/content/type, cancellation, stale attempts and atomic all-role preparation.

## Local P03-07 session/recovery integration

Consume the existing typed Project/CompositionPlan, SQLite CAS and atomic explicit-file
save primitives. Opening a file inspects its matching last-known local project observation;
if different, offer explicit file/recovery/cancel, without calling the observation newer
merely because it exists. Recheck both observations before adopting a choice. Completed
typed edits persist before replacing the session model; stale revision/version refuses,
and uncertain writes stop further writes pending explicit reconciliation, never replay.
The shell exposes the actual recovery choice and explicit save of the current session;
no editor/render capability or timer autosave is fabricated. A canceled picker/choice or
failed open retains the previous model. Save uses the opened digest and existing backup
contract; Save As never silently changes project-relative media/font bases. Recovery with
unproven original relative base requires relink rather than guessing. Cache/relink and
complete persistence-ownership hardening remain separate open gates. Focused tests cover
choice/cancellation/stale observations/completed-command CAS/unknown outcomes and GUI
model preservation with clean process exit, not another unchanged aggregate.

Project-session dependency hardening: align ProjectStore initialization with the
already reviewed account-store exclusive-creation policy, require existing ownership
before SQLite/WAL, retain original identity for session reads/writes, reject extra
schema objects, and preserve unknown COMMIT errors. Failed unmarked initialization
requires explicit recovery, not silent adoption. Verify foreign-empty/receipt/trigger
byte preservation, stale-instance revocation and existing CAS behavior; backup restore
and authenticated legacy-import UI remain open.

## Local P03-07 original-base recovery and verified relink batch

Persist optional original project-directory metadata beside each autosaved Project,
not inside exported project JSON. Add an owned v1→v2 SQLite migration: validate exact
old schema/receipt before backup, validate backup, transactional column addition and
version change, preserve old receipt lineage, recheck ownership/identity and fail
closed on any unknown mutation outcome. Legacy rows retain unknown origin (NULL),
never infer it from a newly opened file. New completed session commands atomically
save their known base. Recovery of relative references with a known origin resolves
their execution paths against that origin; legacy unknown bases still require relink.
File Save As retains current no-silent-rebase rule.

A separate relink command verifies the explicitly selected regular candidate's full
SHA256 using the existing bounded-growth/cancel-aware fingerprint helper. Match only
against the chosen existing asset/font identity, retain probe/stream/timing semantics,
change path+revision only, and return a completed typed command. Different bytes are
a replacement requiring a future explicit re-import decision, not a relink. Cancellation,
unknown IDs or mismatch changes no model/DB/source. This proof is an observation, not
permanent authority: actual rendering must revalidate source identity. Tests cover
owned migration rollback/backup, legacy unknown origin, moved-file recovery, export
metadata exclusion, correct/mismatching/canceled relink and render digest parity.

## Local P03-07 root-folder relink and responsive shell

Implement the original ED-L142 root-folder workflow over the reviewed same-content
primitive: user explicitly supplies old root and chooses new root; map only references
under the old root, verify every mapped candidate before returning one completed
command, no partial model/DB update on mismatch/missing/cancel. Out-of-root references
retain meaning. Hash work runs on an owned QThread with cooperative cancellation;
SQLite/model commit stays on the GUI owner thread and applies only to the captured
still-current session/revision. No candidate authority survives to render admission.
Close/cancel discards late results and waits for actual worker retirement, reusing
Qt's established wait(0)/deferred-deletion pattern. Source and foreign files remain
read-only. Target tests cover full mapping, mismatch rollback, cancel/no commit, stale
session/result, close-during-hash and clean process exit. No Windows parity claim.

## Independent P03-08 candidate discovery / explicit preference slice

Reuse Python pathlib/stat and bounded iteration, not a new package or recursive drive
scanner. Read configured executable paths, caller-declared managed/bundled directories,
PATH and extra search directories for ffmpeg/ffprobe/yt-dlp/gallery-dl/Chrome only.
This is candidate metadata, never publisher trust, executable self-test or readiness.
Explicit invalid selection refuses without fallback; Auto lists managed/bundled before
system/extra candidates. Cancellation/check-count/time observation limits produce
partial results, never a complete-missing verdict. Symlink/reparse candidates are
reported as unverified, not adopted as managed files. No execution, downloads, installs,
PATH modification or SQLite/user-data creation. Headless --scan-tools exposes this
useful read-only result; functional checks/version leases/trusted installation remain
separate gates. Tests cover preference/no-fallback, limits, Unicode, source unchanged,
headless behavior and source-label-not-ownership semantics.

## Independent P03-08 pinned pair functional observation

Consume explicit caller-authorized FFmpeg/ffprobe paths and expected executable hashes,
plus an explicit known-hash test fixture and exact expected streams. Pins are integrity
inputs, not self-authenticating publisher trust; discovered candidates never authorize
execution. Reuse owned process retirement, fingerprint and media probe/full-decode
validation. Check reported versions/library tuples match, validate the known fixture,
and generate one bounded black RGB frame to stdout. No temporary output files, source
writes, installs or cleanup authority are needed. Return only fixture/raw-frame scoped
functional evidence, not full codec/GPU/subtitle/Windows readiness or a version lease.
Tests cover no-execution on pin mismatch, incompatible metadata, drift, cancellation,
malformed/oversized output and sanitized errors. One actual Linux integration uses the
unchanged previously approved system binaries and retained synthetic fixture; no
re-generation or repetition of the unchanged corrupt-media baseline.

## Jobs-store ownership consistency before further registry integration

A disposable reproduction showed default JobRepository initialized a preexisting
unmarked empty SQLite file. Align default opening with reviewed account/project stores:
track exclusive creation, require existing ownership before SQLite unless the caller
explicitly requests known-schema adoption, reject leaf links without resolving them
away, and use mode=rw after original descriptor acquisition. Permanently revoke an
instance on identity loss, guard again before WAL/receipt and submission COMMIT, and
preserve post-COMMIT errors rather than masking them with invalid ROLLBACK. Keep exact
known-schema adoption a separate explicit opt-in, not a fallback or automatic restore.
Tests cover no-open/no-write foreign-empty cases, link refusal, restore-after-loss,
known adoption, and unknown submission outcomes; no schema-version or native retry
policy expansion is intended.

## Coherent hosted integration checkpoint (new user publication authority)

Freeze all independently reviewed local P03 work since public c416c60a, including the
jobs opening repair and portable fixtures. Publish one normal phase-03 descendant
with exact tree/lease readback; main stays accepted P01. Ordinary workflow runs one
four-target Windows/Linux3.12/3.13 source/native aggregate. Windows3.12 additionally
builds onedir and tests frozen schema, Unicode subtitle parsing/invalid encoding,
read-only candidate discovery and packaged exact MIT notice. No diagnostic marker,
new binary install or unsupported Windows media/GPU/provider claim. Preserve exact
source/JUnit/skips/frozen report; inspect terminal failures and fix only affected scope.
Local scoped source reviews are not replacements for this actual target checkpoint.

## Next coherent P03-06 admission / cleanup batch (2026-11-01)

Entry: reviewed hosted source/native checkpoint6162293 plus exact carry-forward
receipts, not full P03 acceptance. First implement a live namespace admission bound
to immutable job composition/output intent: open original source/font descriptors and
pin their parent directories; reject unresolved project-relative references rather
than invent cwd, reject final-source aliases/existing finals and cache destinations;
recheck continuity before staging, after slow I/O and immediately before no-replace
publication. Source identity observation is not hash/media validation. A scanner
entry reuses canonical scan_media with ALL manifest output roots plus explicit cache
roots, preventing outputs re-entering recursive source candidates. Explicit manual
source selection in an output folder is not silently forbidden; only exact unsafe
alias/collision and cache/staging inputs are refused.

Then add explicit live-session cleanup after known successful all-required-set commit,
never arbitrary/restart receipt cleanup: verify exact final+retained staging and current
coordinator/history, refuse foreign children/replaced objects, unlink only the exact
owned staging payload and then empty owned directory. No recursive deletion, final
unlink, lost-anchor adoption, shutdown cleanup or process retirement by PID. Windows
open-file deletion may remain safely blocked; record native support honestly rather
than releasing the original anchor before destructive authority is proven. Partial
writes/canceled/unknown/restart sets remain retained until a separate safe policy.

Affected tests: source/font identity replacement, destination/source/cache overlap,
manifest-driven scanner exclusions/hardlink aliases, epoch loss after I/O, zero stage
creation on rejected admission; cleanup foreign child/same-bytes replacement,
final/history/epoch loss, success final preservation, repeat/partial outcome handling.
Independent review before coherent checkpoint. No new acceptance count by test volume.

### Windows object-bound cleanup capability prototype entry

After rejecting POSIX stat/unlink TOCTOU, reuse official Win32 CreateFileW and
SetFileInformationByHandle(FileDispositionInfo), through existing stdlib ctypes.
No new package or copied third-party implementation; no ACL/security/privilege changes.
A continuous original-FD→share-delete metadata bridge→DELETE-access deny-write/delete
handle chain preserves physical incarnation while acquiring destructive rights.
Expected parent namespace pinned before handoff; OPEN_EXISTING/OPEN_REPARSE_POINT,
correct directory BACKUP_SEMANTICS, type/identity/reparse checks, noninherited handles,
exact once HANDLE→CRT ownership, no path-delete fallback. Before disposition recheck
name/parent/handle identity and caller's live authority. Native disposal failure/close
uncertainty retires capability without retry. POSIX remains unsupported/retained.

Prototype first, NOT wired to production PublicationSession cleanup until actual
Windows hardlink, file/directory substitution, foreign child, authority loss,
sharing-conflict, unmarked close and handle-plateau tests establish the primitive.
Then integrate exact completed journal/history/quiescence/final readback as one
subsequent coherent slice. No generic process/worker abstraction invented while
this critical safe-deletion primitive remains unverified.

## Independent P03-04 actual progress slice while native cleanup CI is blocked

Keep reviewed cleanup checkpointb32795a and exact remote payload frozen. Independent
local work adds bounded stdout observations to the existing owned process adapters
(no alternate launch/retirement path), and a specific FFmpeg `-progress pipe:1`
key/value parser. Only allowlisted numeric frame/out_time_us/total_size plus explicit
progress boundary are exposed; raw stderr/unknown fields never become UI events.
Unknown totals remain unknown; protocol `end` is not job/artifact success.

Bind observations to current immutable snapshot/attempt/lease and running state,
ignore stale/canceled/expired observations; no state transition or success from
progress. Callbacks execute on coordinator/runner thread and must be bounded, never
update Qt directly. Callback failure/cancel must still retire owned descendants.
Real Linux FFmpeg observation on the already approved pinned fixture is one affected
integration check, not rerun of unrelated media validation. Actual Windows observer
behavior awaits its own target evidence; native cleanup authorization does not
silently cover an expanded descendant publication payload.

## Next P03-06 native integration boundary (after primitive target proof)

Use verified Windows handle disposition only; POSIX keeps stage. Completion cleanup
must require this live session's exact all-required committed set, artifacts and
completion history/current owner epoch, and only synchronously staged/validated
roles after owned process retirement. No caller boolean may assert quiescence.
Transfer original staged descriptor through a continuously live bridge, using a
close-once mutable owner rather than a raw ExitStack os.close callback.

Pin original stage directory; acquire file DELETE/read capability; read/hash through
that deny-write handle; check final name and physical identity. Keep a compatible
read-only final bridge alive before staged disposition/close, then acquire a strong
read-only final pin denying write/delete while bridge still preserves incarnation.
Only after physical/name proof release bridge. Strong final pin survives through
object-bound empty-directory disposition. Recheck exact journal/epoch/history at
each native effect boundary. No pathname unlink/rmdir fallback, no foreign child
removal, no inode/hash-only re-adoption after original handles close.

Cleanup is one-shot and always retires session. Any partial/close/observation error
is UNKNOWN, never retries, reverses successful job/history or deletes final output.
Focused local refusal/ownership-transfer tests plus actual Windows journal→file→dir
integration, failure injection, foreign child/handoff and final preservation gates
are required before reporting production cleanup working. Primitive PASS alone is
not that evidence. No unchanged full aggregate or frozen build is necessary for
this narrowly affected subsystem.

## Next P03-06 cancellation-owned temporary cleanup

Current completed cleanup does not satisfy SRC-08.04/OPS-02.02. Interrupted writes
retain files but currently acquire their live anchor only after successful flush.
Move original file-anchor retention to immediately after exclusive creation, before
feeding any chunks. Keep a separate immutable unvalidated ownership record (root,
stage directory identity, original file identity), never mistake it for a validated
StageReceipt or permit publication/success from it. Retain original Windows stage
folder capability as already implemented; no receipt-only restart adoption.

Add an explicit internal staging-operation latch spanning parse/copy/validation and
owned process retirement; canceled cleanup refuses while that operation is active.
Only a current exact canceled/cancel-requested same-snapshot/same-attempt job, before
publication claim and with no committed artifacts/history, may remove its own live
created stages. Prepared sets must match this exact live owner/session; do not
accept caller paths, arbitrary receipts or a boolean claiming worker quiescence.
Use object-bound Windows file/directory disposition, preserve foreign children and
all source/final paths, fail closed on platform/sharing/identity uncertainty. Any
entered maintenance error is UNKNOWN, one-shot retires session; no job replay or
DB success changes. Failed/expired/restarted jobs remain retained pending separate
recovery policy, not silently treated as canceled.

Affected tests: cancellation before creation/during copied chunks/after staged
flush, parser/validator interruption, original anchors retained despite failure;
source bytes unchanged; running/publishing/expired/foreign-owner cleanup refused;
actual Windows canceled-job cleanup removes only exclusive owned stages and leaves
foreign extra children/finals untouched. No unchanged full aggregate or frozen run.

## Next P03-04 typed validator retirement propagation

Reuse existing owned process adapters, never a new launcher. Per-invocation opaque
retirement observation defaults UNKNOWN; mark it only after the backend's complete
retirement path succeeds (Windows owned Job ActiveProcesses0 + checked handle
retirement; POSIX explicitly its existing group policy, not Windows proof).
A fresh validation-lifecycle object tracks every probe/decode invocation and seals
only after actual validator entry/unwind. This side channel preserves lifecycle
proof through sanitized error wrapping without string matching or caller booleans.
Unentered/faked validator, any unconfirmed process/handle retirement or reused
observation remains UNKNOWN. On exception, session may permit canceled-temp cleanup
only from its fresh sealed confirmed lifecycle; unknown remains sticky forever.

Target actual Python child/descendant standing in for an owned decoder—not a fake
FFmpeg-support claim—cancel → retirement → acknowledged job → native own-stage
cleanup. Inject unknown retirement → no native deletion. Preserve existing process
API/error types, cancellation deadlines and unsafe-PID/global-kill prohibitions.
No full queue scheduler/UI or renderer acceptance from this slice.

### P03-04 / P03-05 active coordinator command routing
Next coherent slice: bounded in-process command inbox owned by the existing
coordinator thread, reusing QueueCommand store-token/version CAS and transaction
semantics. UI producers must never share SQLite connections or acquire a second
coordinator lock. Owner drains requests at worker cancellation/progress polling
boundaries; accepted cancel remains a request until actual process retirement and
acknowledgment. Queue capacity and per-drain work are bounded. A canceled pending
future has no effect; once executing, neither interruption nor unknown COMMIT
permits replay. Owner loss/close fails pending requests permanently. Tests cover
cross-thread submission with same-thread SQLite, stale/token refusal, capacity,
pre-admission cancellation, unknown COMMIT, owner loss, and actual owned child
cancellation. This is routing, not a renderer/provider executor or full scheduler.

Following inbox routing, connect real progress observations without unbounded Qt
signals: bounded latest-per-job buffer on the coordinator route, drained by UI
at a fixed cadence. UI must match current store token, job UUID, immutable
snapshot hash and attempt; only active rows display observation counters. New
snapshots/retries/final states clear stale progress; progress=end never marks
success. Expose numeric frame/media-time/bytes only, never stderr/paths/credentials
or fabricated percent/ETA. Actual runner emits through existing JobProgressObserver
on its repository thread. This UI transport does not provide a missing renderer,
provider executor or queue scheduler.

### Owner transition refresh and end-to-end cancellation boundary
After the native inbox/progress checkpoint, add a coalesced owner-route revision
for committed commands and explicit worker state changes/route closure. UI reads
actual durable rows once per observed revision, never paints an invented terminal
state from a progress event. Busy readers/commands must not lose a later revision;
unknown COMMIT/closed route forces one durable refresh, no mutation replay. Include
a single actual UI selected cancellation→owner inbox→owned Python validator child
and descendant→typed retirement→DB cancel acknowledgment→owned-stage cleanup case.
The Python media decoder remains labelled a lifecycle stand-in. Windows removes
only its owned stage; POSIX retains without a pathname-delete fallback. Native
session cleanup proof and UI final-state refresh are separate from production
renderer/provider/scheduler acceptance.

### P03-05 / OPS-05.03 typed durable diagnostics
Reuse stdlib dataclasses/enums/json/sqlite3 and existing original-FD/schema/receipt
ownership helpers; no new package or raw logging formatter. Independent design
review rejected automatic jobs-v3 migration as insufficiently protected against
already-open older writers. Keep jobs schema unchanged. Use a separate owned,
versioned diagnostic store with an explicit observational/non-atomic contract.
A committed job command is never rolled back/replayed because diagnostic storage
fails; return a diagnostic-unavailable flag, retain known state outcome, and retire
an uncertain log sink rather than retry an unknown append.

Events expose only job-store token, UUID, attempt/version, finite observed time,
enumerated stage/code and optional bounded process exit code. No exception text,
traceback, argv, stdout/stderr, URL, account object, request key or free dictionary.
Default retained-row limits5000global/500perjob are configurable within bounded
ranges; this is not a physical SQLite/WAL byte bound. Settings UI remains open.
Selected-job read-only diagnostics returns only validated fields and never creates
or upgrades any database. Only explicit command/worker diagnostic emission may
initialize the application-owned event store; preexisting unmarked/foreign/future
or corrupt files are refused before mutation. Logs never confer retry/publication
or billing authority. No jobs schema/native coordinator lock refactor is needed.

Tests: exact foreign/future/schema refusal and original-FD continuity; append/read,
row caps, corrupt record rejection; raw secret sentinels unrepresentable; successful
job command remains committed when logging fails/unknown outcome is not retried;
current-owner/version checks before live worker diagnostic emission; actual selected
job Qt read-only view, close/cancel lifetime, no initialization from viewing logs.
This does not fabricate production executors or accept all OPS-05.03 by itself.

### P03-02 / P03-07 migration backup restoration
Provide an explicit restore-to-NEW-store operation and headless CLI, never replacing
an open/current store or source. No live-source SQLite recovery: original source FD
is read-only; require known rollback-format project backup header and no sidecars.
Copy opened-size-bounded chunks into an exclusively reserved pinned destination,
validate copied exact known v1/v2 schema and every bounded Project document/row,
quick_check, readback hash and unchanged source. Register ownership last. Existing
schema lineage lets normal ProjectStore subsequently load/migrate the fresh copy.
Cancellation, disk/full/permission/schema failures retain an unmarked partial target
without unsafe pathname deletion; registration-attempt uncertainty is explicit and
never auto-retried. Existing destination/foreign receipt is refused untouched.

Tests: actual migration-produced v1 backup restored and opened by current store;
original live store/backup unchanged, source origins preserved/unknown never cwd;
foreign/future/corrupt/oversize document and existing target refusal; midcopy cancel,
growth/source mutation, fault before/after registration, native Unicode paths and
CLI no Qt/unrelated data initialization. Full latest-state selection/UI picker and
in-place replacement are not implied by this bounded new-copy restoration gate.

## Restore UI entry — P03-02/07 after native CLI checkpoint
Expose the reviewed new-target restore operation from the existing Overview shell,
without switching the active ProjectStore/session. Explicit selected offline backup
and new destination; no overwrite, newest-version inference or automatic retry.
Run copying/SQLite validation on a dedicated QThread with no GUI-store connection.
Bound/coalesce copied-byte observations; label copy progress separately from full
validation/ownership completion. Cancel/close request interruption and wait for
actual thread retirement; late cancellation must not mislabel a committed new copy
as nonexistent. Preserve current project/queue and report retained partial/unknown
ownership plainly. Tests: actual worker restore while GUI event loop remains live,
cooperative cancellation/failure, no retry, close wait and no active-store mutation.
Reuse existing Qt worker ownership pattern; no new dependency or fake executor.

## Real-media typed observation entry — P03-03
The next dependency slice converts raw ffprobe metadata into immutable per-stream
observations without claiming render readiness. Preserve exact stream indices,
unknown timing/layout, attached-picture disposition and unsupported track types;
never silently select track0 or drop other tracks. Prefer integer PTS/duration ticks
with the stream's rational timebase over rounded decimal summaries. Geometry/SAR,
full display matrix and audio layout remain per-stream. Report unavailable fields
explicitly; do not fabricate zero start/duration, stereo layout, square pixels or
CFR frame PTS. Frame-index observation and strict CompositionPlan asset conversion
are separate following gates; avg/r_frame_rate cannot substitute for decoded PTS.
Use existing bounded numeric parsing/owned process/fingerprint substrate and stdlib
immutable dataclasses; no new dependency/download/provider operation. Primary source
reference: FFmpeg n7.1 ffprobe.c and libavutil/display.h (official GitHub); no copied
upstream implementation. Current ffmpeg.org documentation fetch timed out, so no
claim of successful retrieval there. Target corpus: no-audio, delayed multistream,
SAR/rotation, unknown duration, unsupported layouts, malformed/bounded numbers.

## Bounded decoded-frame observation — next P03-03 dependency
Use explicit trusted ffprobe and selected container-global video stream only, owned
process/no shell/file+pipe protocol boundary. Bind observations to source SHA256,
actual tool hash, stream index/timebase/start ticks; verify selected stream metadata
from the same scan, with before/after source/tool observations. Request frame pts,
best_effort_timestamp and duration ticks separately; preserve signed values/order/
repetitions/discontinuities, never sort/deduplicate or fabricate CFR/last-frame end.
No CompositionPlan-ready conversion yet. Bounded byte/frame/time budgets; malformed,
nonzero/decode-error/capped/canceled scans cannot claim full map. Retained bounded
prefix is explicitly INCOMPLETE where available; unconfirmed process outcome raises
without any cleanup/job authority. Empty/unknown timestamps remain diagnostic.
Target tests cover stream/tool/content mismatch, fragmented or malformed output,
negative/repeated PTS, duration-version fields, caps/cancel/nonzero/stderr and actual
small Linux VFR fixture. Hosted stand-ins are protocol/owned-process tests, never
actual Windows FFmpeg evidence. No new dependency or tool download.

## Visible read-only media inspection — P03-03 / P03-07 entry
Place a bounded observation panel inside the existing Editor area, without changing
approved area/navigation/branding or implying an editor/render engine exists.
User explicitly selects local media and a trusted executable, confirms that this
inspection runs that file; no automatic candidate/tool selection/download. Optional
frame scan uses a user-selected global index, no auto track0 selection. Worker owns
all probe/hash/frame I/O; no GUI-store connection or project/media mutation. Show
all bounded stream facts/unknown diagnostics and a labelled first64-frame view,
not a synthetic timeline. Reuse typed ValidationLifecycle for up to2owned launches;
unknown retirement permanently disables repeat in that panel, never authorizes
cleanup. Close/cancel waits actual QThread retirement; stale results cannot retarget.
Actual Windows codec remains unavailable until separately reviewed/pinned test tool.

## Durable explicit tool preferences (P03-08, SB §2.1)

Persist only the five explicit executable paths and bounded scan scope in a separate
owned SQLite store, never trust, READY, self-test receipts or job snapshots. Read and
save run on the Settings worker thread. Missing configuration reads as defaults
without creating files; explicit Save creates a new exclusive store. Existing
unmarked/foreign/newer/schema/receipt mismatches fail closed, not reset/adopted.
CAS binds a read version and store token; unknown save outcome requires explicit
reload, not mutation replay. Reopening does not execute tools or scan automatically.
Targets: roundtrip/Unicode, stale multi-window edit, store replacement, foreign empty
files and companions, bounded malformed rows, unknown commit, cancellation/close,
stale UI result and missing/corrupt preferences without preventing Settings startup.
This advances configured-path persistence only; Auto resolver/version leases,
installer, automatic first-open scan and readiness persistence remain absent.

## First Settings navigation discovery (P03-08; SB-L032)

Once per panel, first actual Settings navigation starts a background saved-preference
read then bounded metadata discovery. App construction remains independent of tools.
Missing preferences use defaults without creating files; corrupt/foreign preferences
show refusal and do not scan default roots. Explicit cancel/error/operation supersedes
that one-shot chain, never silently rearms; later navigation keeps in-session facts.
Exact worker, operation generation, edit revision, unknown-save latch and close state
must remain current at load completion AND queued scan dispatch. Loaded fields do not
become trust/capability or paired-worker inputs. Tests: first-open missing tools,
persisted explicit invalid path/no fallback, corrupt config, edit/cancel/close during
load, repeated navigation and queued callback supersession. No full registry or
pre-workflow version lease acceptance follows.

## New project foundation (P03-07; PR §9 / ED project save/open)

Provide a real empty project, not bundled demo media or a fake editor: explicit
name/output geometry/rational FPS/duration, fresh project/plan identities, no
assets/layers/audio clips or preset/account provenance. Output settings are intent,
not verified codec/renderer capability. Existing CompositionPlan validation applies.
Use existing exclusive no-overwrite project-file writer in a background worker;
no ProjectStore connection crosses threads. Only confirmed, revalidated creation
may activate through existing prepare_open/choose; captured old session/revision
must still match. Existing projects/foreign targets are not overwritten. Any write
uncertainty retains old active session and blocks automatic replay. Cancel/close
before work creates nothing; after creation the file is retained, not auto-deleted
or falsely reported canceled-with-no-effects. Dialog/picker cancel never writes.
This is project lifecycle foundation, not P04 editor/timeline or renderer acceptance;
shared writer's cooperating-namespace/owned-staging assumptions remain unchanged.

## Stable unresolved media persistence (P03-02/03/07; no P04 UI yet)

Implement reviewed MEDIA_LIBRARY_PERSISTENCE_PROPOSAL as a coherent model/storage
batch: symmetric bounded typed observations; independent stable media UUIDs and
content-bound references; project envelope v1 preserved vs explicit v2 library;
Project preservation helper; library-only completed commands advance the EXISTING
plan revision exactly once; all autosave/recovery/relative-origin and same-content
relink paths preserve the library. No lossy intermediate v2 writer may publish.
Existing SQLite document schema remains unchanged; future envelope versions refuse.
Initial scope is pure record/persistence/relink, not file admission, P04 import/drop
UI, render-ready conversion, executable trust or ownership/deletion capability.
