# P03 — fresh foundation, slice A

Status **IN_PROGRESS / LOCAL_VERIFIED slice only**. No P03 task or phase accepted yet. P02 live provider/Chrome/Windows/GPU/continuous-playback/tool-distribution gates remain inherited and OPEN. Entry: P01 design accepted and bounded P02 developer-toolchain evidence independently reviewed. Main remains accepted P01; parent owns remote publication.

## Source and contracts

Fresh `src/fonesi_edit/domain` implements immutable strict CompositionPlan parsing, structural validation and initial semantic preflight, exact rational time segments/cue mapping/keyframe interpolation, execution and render-content digests. Packaged schema derives from the new reviewed P01 contract, not archived implementation. Pure validation does not prove that assets, fonts, tools or a renderer exist. Design schema checker retains its own NOT_IMPLEMENTED semantic label: that script is structural only; new source semantic coverage is partial, not all R01–R15 accepted.

Fresh `storage/projects.py` provides SQLite version-1 project repository with optimistic version checks, transaction fault rollback, consistent verified migration backup, future-schema rejection before mutation; JSON project envelope strict parsing; same-filesystem hardlink no-replace for new files; explicit identity+digest-gated atomic update with backup for existing projects. Advisory locks serialize cooperating writers only; external writers ignoring locks do not receive filesystem CAS guarantees. Windows hardlink/lock/flush behavior and real process-kill durability are NOT_RUN. This is project persistence, **not JOBS artifact publication**.

Fresh eight-area native shell opens a validated project into one shared model. Empty state is truthful; remaining controls explicitly say unavailable. No simulated jobs, metrics, media, accounts or rendering. Invalid open preserves current project. Headless CLI validates plans without initializing Qt or creating user-data; normal GUI defaults to Qt user-data directory, not install directory. No FFmpeg dependency for startup.

## Checkpoint commands (Linux, Python 3.12.14)

- `UV_CACHE_DIR="$PWD/.uv-cache" uv lock && UV_CACHE_DIR="$PWD/.uv-cache" uv sync --locked`: PASS, 25-package resolution; fresh editable package installed. Universal lock records hashes; other Python/Windows installations not yet tested.
- `.venv/bin/python -m pytest -q`: **71 PASS**, 1.14 s. 50 domain/time tests, 19 storage tests, 2 offscreen native-shell/CLI tests. No live service or physical audio/device tests.
- `.venv/bin/python scripts/check_plan.py`: PASS 12 phases /94 tasks /95 groups /438 assertions /392 clauses /101 acyclic milestones; runtime feature evidence remains 0.
- `.venv/bin/python scripts/check_schema_design.py`: PASS 2 positive/22 negative structural fixtures; not semantic-feature acceptance.

Affected tests preceded this aggregate. Unchanged P02 synthetic probes were not rerun. Independent source review pending against the source checkpoint introducing this result file. No inherited legacy test result is used.

## Remaining P03 work

Real media probe/hash cancellation; worker/coordinator leases/recovery/process-tree ownership; queue snapshots/redacted events; exact durable multi-artifact JOBS publication; autosave/relink/cache; dependency registry and ownership/trust; account/profile schemas and isolation; real Windows integration. Application shell is a foundation, not a functioning video editor. Source formatting and broader semantic edge cases remain subject to independent review before acceptance.

## Slice B affected verification

`tests/test_probe.py`: **11 PASS**, includes real developer FFmpeg-generated 0.1-second WAV → ffprobe metadata/hash/source-unchanged round trip; cancel/hash rename identity and subprocess malformed/duplicate/nonfinite JSON, nonzero exit, timeout, oversize negatives. Local protocols restricted to file/pipe; no network source probing. Child capture disk files are polled every10ms and killed above limit (transient disk overshoot possible); memory read bounded. Only direct owned ffprobe process ownership is covered, not arbitrary descendants/Windows job objects. Full CompositionPlan stream normalization, video/VFR/rotation corpus and full P03-03 acceptance remain open.

Probe fixture correction: initial addition of the two strict-JSON negatives had a test-source quoting syntax error (collection FAILED, no tests ran). Corrected quoting in the next normal commit, then reran affected probe suite: 11 PASS. The preceding 9-case run had passed before those negatives were added; only the corrected 11-case run supports Slice B strict-JSON evidence.

## Slice C affected verification

Dedicated `jobs/repository.py` is admission/lease substrate only, not full worker runtime. `tests/test_jobs.py`: **8 PASS**: idempotent submit/different-snapshot conflict, reopen, competing SQLite connections, stale version/lease and forged record rejection, held admission, cancellation request/acknowledgment, expiry discovery without blind retry, foreign version-one DB unchanged. Deliberately no publication/success method: validated artifact-set integration must supply that protocol later. Snapshot currently composition+seed only; full resolved tool/provider/account configuration remains pending. No process tree, worker launch, UI queue, retry policy or Windows durability acceptance is claimed.

## Independent review corrections (initial foundation not accepted)

Reviewer reproduced content-digest alias ambiguity for same-byte assets with differing probe records; same content identity now rejects conflicting semantic metadata, including font face/fallback records. Font graph validation replaced recursive expansion by iterative O(V+E) colored DFS; shared 1,000-node DAG/cycle regression added; duplicate fallback references rejected, explicit 4,096-node/65,536-edge resource limits. Deep JSON fails with controlled diagnostic.

Actual file reads now use shared `read_bounded(limit+1)` in project open, existing-file save/readback and headless CLI, not a post-allocation parser check. Regression asserts bounded read call and oversize open leaves current project unchanged. The first affected run caught one remaining unbounded load path (37 PASS/1 FAIL); fixed that path, then 38 affected file/project/shell/probe tests PASS. Metadata numeric exponent overflow ±1e999 now rejected with finite float parser and `allow_nan=False` output.

Self-review added project SQLite application identity guard before WAL activation; foreign version-one DB byte-identical rejection tested. Composition/project affected tests initially 56 PASS, then deep-JSON added and composition affected suite rerun. Independent recheck pending; no accepted task status changed.

## Slice D affected verification

POSIX owned process-group adapter: `tests/test_process.py` **7 PASS**, real subprocess stdout/stderr/nonzero exit, closed-stream timeout, output cap, cancellation with grandchild, successful leader with silent descendant. Leader exit is observed through `waitid(WNOWAIT)` and retained until group cleanup to prevent PID/PGID reuse before signaling; cleanup idempotent, then reap. Platform lacking WNOWAIT and Windows fails closed pending tested Job Object adapter. Tests are local Linux building-block evidence, not full coordinator/Windows worker acceptance.

Independent targeted recheck closed original four findings, but reproduced application-ID-only guard accepting malformed matching-ID/version databases. Added exact normalized expected CREATE TABLE signature verification (table set, columns, PK and constraints) before WAL to both project/jobs stores; matching-ID malformed project/jobs fixtures remain byte-identical and raise controlled errors. Affected `tests/test_projects.py tests/test_jobs.py`: **30 PASS**. Targeted recheck pending for this final guard.

## Windows adapter authored, NOT YET VERIFIED ON WINDOWS

`jobs/windows_process.py` uses native CreateProcessW/STARTUPINFOEX, atomic JOB_LIST plus CREATE_SUSPENDED, explicit HANDLE_LIST for NUL/stdout/stderr, unnamed noninheritable KILL_ON_JOB_CLOSE job, IsProcessInJob before ResumeThread, bounded pipe reads, job-wide termination and handle retirement. No breakaway or protection changes. Common process entry dispatches Windows to this adapter. Microsoft primary-source rationale linked in P03 plan.

Local source check `tests/test_windows_process.py tests/test_process.py`: **8 PASS /7 SKIPPED**. PASS includes Win64 structure sizes only (104/112/24/144 bytes) and7 actual POSIX tests. All7 Windows runtime cases remain explicitly SKIPPED here: output/Unicode argv/exit, timeout, overflow, grandchild cancel, supervisor crash, unlisted inherited handle, common dispatcher. New hosted clean-foundation workflow targets Windows/Linux×Python3.12/3.13 and uploads JUnit skipped/pass/failure results. Source review and actual Windows run pending; no Windows PASS claim.

Isolated package boundary at codea5e1695: fresh wheel built with `uv build --wheel`, installed in separate runtime/package-venv (not editable), CLI successfully validates multi-stream plan from `/tmp`, outside checkout working directory. Wheel ZIP inspection:22 members restricted to package/dist-info, packaged schema present, no cache/tests/media. SHA/size recorded in `docs/evidence/p03/wheel-smoke.json`. Runtime dependency installation resolved current transitive dependencies for this smoke; this is not a second locked-environment claim. Not frozen/Windows/GUI/media acceptance. uv warned cache located in source; ZIP inspection confirms wheel excludes it.

Additional target-only retirement test authored after a5e1695: isolated Windows supervisor compares GetProcessHandleCount before/after10 success+timeout cycles. Local collection now1 ABI PASS/8 Windows SKIPPED for Windows test file; no runtime result invented. Actual target execution pending.

Hosted workflow additionally prepares actual Windows3.12 onedir and executes frozen CLI multi-stream schema validation. This is a pending package/resource-boundary check, not GUI startup/render/audio/media or release acceptance; no artifact is distributed as a usable product.

Actual fresh application Linux onedir build at a5e1695 also completed (PyInstaller6.22.3,6.9s build); resulting executable successfully validated multi-stream plan with packaged schema. `docs/evidence/p03/linux-frozen-cli.json` pins executable hash/size and regular-file bundle bytes. This replaces no earlier result and is not the P02 synthetic probe; it is current product-code CLI packaging only. GUI/media/Windows remain unverified for this build.

Windows self-review correction before CI: retirement now checks owned-job termination, process wait and handle close results; unconfirmed retirement raises ProcessError rather than falsely reporting confirmed cancellation. All remaining handles are attempted before reporting cleanup failure. Windows low-level cancellation is immediate job termination; cooperative FFmpeg/tool-specific soft cancellation remains a worker-layer gate, not claimed through shared grace_seconds.

Target regression coverage additionally checks a separate sibling process survives owned-job cancellation; readiness markers wait for complete contents to avoid file-create/write races. Windows test file currently1 ABI PASS/9 target SKIPPED on Linux; actual hosted result pending.

## Aggregate checkpoint 9bfc1ea (2026-11-01 04:55 UTC)

Single owner aggregate `.venv/bin/python -m pytest -q --junitxml=runtime/p03-local-results.xml`: **110 PASS /9 SKIPPED**,3.60s. All9 skips are actual Windows Job Object runtime tests, not counted as success. Versioned JUnit copy at `docs/evidence/p03/local-foundation-junit.xml`; source pin9bfc1ea. Plan integrity94/95/438/392/101 PASS and structural schema2/22 PASS. All product runtime criteria remain NOT_RUN; whole P02/P03 not accepted. Independent source and actual Windows CI verification remain pending.

Independent source review9bfc1ea: **CLEAR FOR HOSTED CI only**, schema residual closed; see `docs/reviews/P03_SOURCE_CI_READINESS.md`. Whole P03 and Windows runtime still unaccepted. Before coordinator can reuse artifact resources, add separately observed all-descendant quiescence (ACTIVE_PROCESS_ZERO), not just leader wait.

CI-only follow-up: official GitHub API readback verified checkout v4→11d5960a326750d5838078e36cf38b85af677262, setup-python v5→a26af69be951a213d495a4c3e4e4022e16d87065, upload-artifact v4→ea165f8d65b6e75b540449e92b4886f43607fa02 (2026-11-01). Workflow pins those commits, exact PR-head/push SHA with persist-credentials:false, and source/tree/platform/Python artifact. `tests/test_ci_identity.py`:2 PASS including wrong-SHA failure. No application source changed; prior aggregate110PASS/9SKIP plus2newfocused identity tests, no duplicate aggregate.

## Later quiescence increment (not included in reviewed3c222a9 tree)

Windows retirement now queries owned-job BasicAccounting.ActiveProcesses until0 after leader/thread handle release; bounded failure/query error remains explicit unconfirmed retirement. On unverified-membership setup failure, exact created suspended process handle is terminated directly (no arbitrary PID) before cleanup. 3 pure accounting-sequence tests PASS (pending→zero/query failure/timeout); ABI test PASS;10 actual Windows tests SKIPPED locally, including new native quiescence-observation regression. This later source needs independent focused review and target execution before use for artifact resource cleanup.

Independent focused rechecka8d1b31: **CLEAR FOR CI**, source-level Windows quiescence gap closed; exact-SHA CI changes clear.6 reviewer-selected checks PASS;10 actual Windows tests deselected, no aggregate rerun. This is permission to verify target behavior, not a Windows/P03 PASS claim.

## Independent account-domain slice (later than reviewed27760da CI candidate)

Fresh account/profile pure models and in-memory catalog;13 affected tests PASS. One auth binding per platform/profile with alternate identities isolated, multiple source pages/channels share auth without sharing source rights. Website/bridge/source-rights checks separate; freshness timestamps explicit, stale/future/unknown observations block. Same-identity refreshed session can satisfy old job only with fresh current-generation scoped rights; changed identity never silently rebinds/falls back. Job-reference export closed allowlist rejects secret/path fields; unlink only removes mapping/default, retains profile. No Chrome/browser launch, cookies/credentials, provider/network, path mutation or claimed live-auth checks. Persistence, profile paths/version/check UI, rate limits and real connector evidence remain required P03/P05 work.

Independent account-domain review6e96f09 CLEAR for no-I/O scope,13 selected checks PASS. Clarified API name to `check_auth_rights`: successful auth/rights checks are NOT permission to acquire a busy/locked profile. Later admission separately enforces profile lease, connector capability and rate-limit; no hidden login/profile operation. Added independent future/stale web/bridge/source timestamp and missing/incompatible browser cases:20 affected account tests PASS. Source remains pure, no live auth evidence.

Actual project crash tests added independently:4 PASS on Linux. Owned child is killed at after-staging, after-backup, after-publish and before-SQLite-commit boundaries. Previous/new complete file visibility matches linearization; SQLite rollback preserves old version; OS releases advisory lock without deleting lockfile and next save works. Same tests will run on Windows CI but Windows result remains NOT_RUN. This is project persistence, not artifact publication or full autosave recovery.

Self-review rational-interface hardening: direct TimeSegment/frame/sample/rounding/keyframe calls previously relied on caller Fraction typing; now runtime rejects float/bool/nonfinite input and normalizes exact integers.4 new parameterized interface cases exercise6 entry points each. Affected time+composition suite:58 PASS. This strengthens exact-time model only, not rendered timing/parity acceptance.

Self-review found adjacent project lock could write a byte into a preexisting zero-length lock target on Windows (and symlink target). Replaced lock creation with exclusive marked file; existing unmarked/foreign files are never written, symlink/reparse/nonregular/changed identity fail closed. Existing development-era empty lock files are intentionally not adopted without ownership evidence; choose a new project path rather than deleting unknown lock files.2 new foreign-empty/symlink regressions plus project/crash/shell suite30 PASS; final affected project+crash27 PASS. No Windows runtime claim. This safety correction must be included before publication, not the older27760da candidate alone.

Final source clearance throughd501491: independent reviewer cleared account/time/crash increments and adjacent lock ownership correction; O_BINARY-only follow-up verified without repeating unchanged tests. Source-only CLEAR FOR CI, not Windows/P03 acceptance. Lock initialization interruption remains explicit fail-closed/manual recovery (never delete unknown lock file automatically). Full aggregate remains pinned9bfc1ea plus enumerated affected-suite results; do not report a fabricated new full aggregate.

## First hosted target result — FAILED, not accepted

Public sourcec59f7129 (locald501491) then approved docs-only1b0520cd (localbab7741) triggered runs41276078838/41276112120 before crossed skip-CI instruction arrived. Both failed; final-head run41276112120 is authoritative. Windows3.12:134 PASS/3 FAIL/18 SKIP; Windows3.13:134 PASS/3 FAIL/18 SKIP. Ubuntu both fail Qt import collection (libEGL.so.1 unavailable). Frozen Windows step correctly skipped after failure. Details in `docs/evidence/p03/hosted-initial-failures.json`; none is a Windows/P03 acceptance claim.

Repair iteration: owned backup flush opens r+b (Windows read-only fsync EBADF); fingerprint compares unchanged named/descriptor signatures independently and retains cross-API file identity;2 new invariant/mutation tests. Warm handle-count baseline measures10 per-call cycles, still forbids growing handles, records cold/warm/series. Linux CI installs Qt runtime libraries normally. SQLite post-kill failure receives extended error/version diagnostics, remains unresolved pending actual rerun; no WAL/SHM deletion or generic error suppression. Affected local tests45 PASS/10 Windows SKIP; source review required before re-publication.

Second hosted run41276612605/public1805ae68: Ubuntu3.12/3.13 completed SUCCESS,146PASS/11SKIP each. Windows3.12 source tests139PASS/18SKIP (including native owned-job tests), then strict preserved-spec hash fails from checkout CRLF; frozen step remains gated. Windows3.13 now only1FAIL/138PASS/18SKIP: SQLite3.50.4 extended1546 SQLITE_IOERR_TRUNCATE, matching upstream Windows post-exit mapped-SHM gap. Warm handle plateau passed; initial+3 cold attribution remains unproven and is not called a fully explained leak-free startup.

Iteration2: .gitattributes keeps canonical source/reference bytes exact under autocrlf. Ownership sidecar established only after ID/full schema validation records physical DB identity and schema signature. Startup version read retries Windows1546 only with matching receipt/header/identity, closes each failed connection, admits retries only within3seconds (not a hard OS-I/O wall-clock guarantee); missing ownership/non1546/nonWindows/exhausted errors remain failures. No statement mutation/commit/job replay, journal deletion, SQL error masking or SQLite binary replacement.45 affected local tests PASS including ownership/noownership, bounded deadline, foreign receipt, source writes and simulated CRLF checkout. Actual target result and independent review pending.

Independent reviewec83a07 CLEAR for diagnostic CI,9 focused helper/receipt/autocrlf checks PASS. Tightened follow-up prevents a new attempt after final deadline sleep and caps SQLite busy timeout to remaining budget; ordinary jobs busy timeout restored after validation. OS filesystem calls remain nonpreemptible, so3seconds describes retry/admission budget rather than a false hard total wall-clock guarantee.

## Actual hosted foundation checkpoint — scoped PASS, phase still IN_PROGRESS

2026-11-01: independent review a935fccc cleared the final retry-admission delta;6 focused helper checks PASS. Public source `f16dca9986fd1181363c52580b11d7cef5a8b70c` is tree-equivalent to local `a935fccc6746eff726b26dbf352189e0f8f1a30e`, exact tree `b0ade7e3b53bf551981466f643e3e2fe730ff9dd`. [Run41277250696](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/41277250696) completed SUCCESS across all four jobs.

| Target | Python / SQLite | Passed | Skipped | Failed/errors |
|---|---|---:|---:|---:|
| Hosted Windows Server2025 |3.12.10 /3.49.1|148|18|0|
| Hosted Windows Server2025 |3.13.16 /3.50.4|148|18|0|
| Ubuntu24.04 |3.12.15 /3.45.1|155|11|0|
| Ubuntu24.04 |3.13.17 /3.45.1|155|11|0|

Downloaded all four JUnit/source artifacts, verified exact public SHA/tree and counts; byte-preserved files plus SHA256 and skip reasons in `docs/evidence/p03/hosted-41277250696/`. Windows skips are10 POSIX executable fixtures,7 POSIX process tests,1 unavailable developer FFmpeg test. Linux skips are10 actual Windows tests and1 unavailable FFmpeg test. Skips are not passes. Actual Windows tests include owned nested jobs, cancellation/grandchildren, supervisor crash, inherited-handle exclusion, sibling survival, quiescence and warm per-call handle plateau. Cold +3 handle attribution remains unproven. Actual project child-kill/recovery tests pass on both Windows versions, including the previously failing SQLite1546 case; this does not establish power-loss durability or replay safety for arbitrary mutations.

Windows3.12 also successfully builds the actual fresh application onedir and runs frozen CLI multi-stream CompositionPlan validation with packaged schema. This is not a full GUI, rendered-media, physical-audio, GPU, installer-distribution or user-desktop test. Preserved-plan integrity and structural schema checks pass on all targets. No unchanged local aggregate rerun was performed. Earlier failed runs remain recorded above.

Main remains accepted P01 design. P02 external gates and complete P03 tasks remain OPEN; initial receipt did not close criteria; subsequent independent evidence assessment accepts exactly OPS-03.05 and OPS-04.02 (2/438 children, not whole tasks/groups). See P03_ACCEPTANCE_LEDGER.md for the remaining cases in all9 P03 tasks. Later docs-only receipt commits use `[skip ci]` and must not be represented as independently executed source. Next source work follows P03-06 publication ownership/recovery and P03-04 coordinator integration contracts, with focused tests and independent review before target verification.

## P03-06 filesystem substrate (later source, not in hosted f16dca99)

Fresh `artifacts/filesystem.py`: existing explicit local destination, no-delete Windows
ancestor/directory handles or POSIX dirfd operations, exclusive UUID staging, bounded
small-sidecar writer, physical identity/hash receipt, atomic hardlink no-replace with
retained staging, recovery refusal for foreign identical bytes/missing or changed
staging. No final-file deletion, cleanup shortcut, job success API or weaker fallback.
Trusted coordinator-only receipt input; not authority from imported project JSON.
Windows directory fsync/power-loss durability is not claimed. Streaming media writer,
durable journal and required-artifact final transaction remain unimplemented.

24 focused Linux filesystem tests PASS, including two real owned-child kill/reopen
cases (after retained publication vs before link with foreign-identical final),
Unicode names, destination race, unsupported hardlink, changed staging, symlink and
root replacement refusal. This source has not run Windows CI yet; existing hosted
foundation evidence does not cover it. Independent source review precedes publication.

Independent review identified persisted dev/inode recycling ambiguity. The current
substrate now duplicates the exclusive-created file descriptor before writer close
and retains it for the Destination lifetime. Publish/verify require that live anchor;
reopening after process death is always UNKNOWN, even if receipt/path/hash match.
No inode-only resurrection is accepted.28 affected Linux tests PASS; after tightening
anchor acquisition to eliminate the close/reopen gap,5 relevant retained/replaced/
missing/child-kill cases PASS. Crash tests now prove fail-closed UNKNOWN and preserved
output, not durable recovery success. Incarnation-safe restart proof remains a required
future P03-06 gate, not removed scope. No Windows result for this increment yet.

Independent review ac4f063: CLEAR for scoped target testing,5 selected Linux checks
PASS/23 deselected; uninterrupted original descriptor closes live inode-reuse gap.
Namespace review found no additional blocker within that boundary. Restart remains
UNKNOWN and full journal/cleanup/P03-06 remains OPEN, no additional child closure.
See `docs/reviews/P03_PUBLICATION_LIVE_ANCHOR_CLEAR.md`. Target CI publication is
pending specific external-publication approval after the ledger commit action was
rejected; technical review is not authorization to bypass that block.

## Same-DB journal design and schema-v2 prototype (not published/accepted)

`docs/contracts/PUBLICATION_IMPLEMENTATION.md` specifies exact migration, records,
claim/cancel/member/final-set transactions and current restart UNKNOWN boundary.
Fresh schema-v2 prototype adds required-set/publication/artifact/history tables in
same jobs DB; no publication/success methods implemented yet. Exact v1 table SQL
signature preserved; populated migration keeps snapshots and known creation-lineage
ownership receipt, with independent full-schema check before writes. Unknown/future,
foreign and extra-trigger schemas rejected. Verified SQLite backup and transactional
DDL rollback with explicit fault points; mutation outcomes are never auto-replayed.

28 affected jobs/migration/ownership/startup-read checks PASS;27 affected project/
actual child-kill persistence regressions PASS after shared ownership-lineage helper
change. Initial new migration fixture used11placeholders for10columns and was fixed
before these passes. No full unchanged aggregate rerun. This is local Linux evidence,
not target Windows migration/recovery proof. Design/prototype independent review
pending; coordinator APIs follow only after that review. Public ledger/descendants
remain held by publication authorization block.

Independent design/prototype review e534771 found two real issues: foreign existing
ownership receipt was checked after migration, and whitespace/lowercase SQL
normalization could accept changed CHECK literal semantics. Both corrected before
publication: receipt preflight precedes backup/mutation/WAL; absent versioned receipt
requires explicit adoption; SQL signatures compare exact stored statements, preserving
literal case. Concurrent migration guard now rechecks application ID. Added coordinator
epoch schema and precise live OS-lock authority/post-claim lease policy to design;
coordinator implementation still pending review.33 affected schema/jobs/ownership/open
checks PASS including foreign-receipt unchanged bytes, changed literal rejection,
explicit missing-receipt adoption and concurrent app-ID mutation refusal.

Independent targeted review01abeaa CLEAR for next implementation slice:4 precise
regressions PASS; foreign receipt ordering, literal semantics and app-ID race closed.
The concrete OS-lock/epoch/post-claim policy permits coordinator implementation entry,
not full publication acceptance. Nonblocking design clarification: UNKNOWN on restart
is derived from publications unknown/job blocked while set stays claimed; earlier
unpublished v2 prototype signatures remain unsupported and fail closed.

2026-11-01 06:05 UTC: new explicit user approval resolved the ledger publication block.
Exact local743b27f ledger published as `ded362aac99d4f01dbb026c4c7ad85eb1059fa78`,
tree `0e0744366dff7fc4289b5114c4e898dc6049b95f`, normal leased fast-forward and `[skip ci]`.
Main remains e514b51. This docs HEAD is not the executed foundation source f16dca99.
Later reviewed publication/schema source is scheduled for target CI separately;
ongoing unreviewed local coordinator work is excluded from that publication.

## Live coordinator ownership substrate (later than reviewed schema01abeaa)

Fresh `jobs/ownership.py` holds a marked nonblocking native byte-range/flock lock for
its lifetime, pins DB incarnation, and allocates a never-reused coordinator epoch in
SQLite. Guards verify live lock identity/marker, pinned DB identity and current epoch;
caller epoch/PID/file existence alone is not authority. Foreign markers are not written,
lock files are never deleted, and process death releases OS ownership but not history.
Marker content is read only after acquisition, avoiding reading another Windows owner's
locked byte. No publication claim/member/final success methods exist yet.

16 affected coordinator/jobs checks PASS; after the Windows lock-read ordering fix,
7 coordinator checks PASS, including actual owned-child kill, contender rejection,
new epoch after death, foreign/symlink/changed lock and out-of-band epoch refusal.
Actual Windows target evidence remains pending. Public source6729ef7 publication was
separately rejected as outside the specifically approved ledger; no tree/ref update
or alternate route was used. Approved ledger remains publicded362.

Independent review e69eae8 reproduced a connection/anchor split: replacing the DB
pathname after repository open could make ownership pin a different file than the
SQLite connection. Fixed by pinning the repository's original file before SQLite
open, checking identity immediately after open/before mutations, retaining that anchor
for repository lifetime, and duplicating THAT anchor into coordinator ownership.
Replacement before owner acquisition now fails before any epoch write (Windows may
prevent replacement itself). Detected continuity/epoch loss is permanently latched;
restoring the old name/epoch cannot silently reactivate the same ownership instance.
34 affected coordinator/jobs/migration checks PASS, including both causal negatives.
Target execution and independent targeted recheck remain pending.

Independent targeted review dc11978 CLEAR:2 causal tests PASS; original DB anchor
and permanent revocation fixes accepted for the cooperating private-namespace scope.
No malicious same-user timed ABA guarantee or new full criterion acceptance claimed.

Probe now uses the reviewed owned-process runner instead of its early direct-Popen
loop, so cancellation/timeout/normal leader exit retires descendants as well. Explicit
path/no fallback/local protocols, strict finite JSON and source fingerprints retained.
21 affected probe tests PASS including actual local FFmpeg audio probe, finite bounds
and Linux descendant retirement;2 targeted descendant/secret-stderr regressions PASS
after process-state race-safe check refinement. This later probe increment is not in
hosted f16 or reviewed public-source candidate6729; independent review pending and
actual Windows FFmpeg remains unavailable/unverified. No provider calls or source writes.

Independent probe integration review6c94e1e CLEAR for scoped target testing;7 selected
bounds/descendant/stderr checks PASS. Raw OSError messages can still contain local tool
paths, so complete sanitized-log acceptance remains OPEN. Self-audit follow-up bounds
fingerprint reads by opened file size+1: a continuously growing file now fails changed
rather than following EOF indefinitely.3 existing affected fingerprint checks plus
1 separately selected new producer regression PASS, including a
producer that appends on every read (fails after2reads). This is a source-level bound,
not a hard OS-I/O wall-clock promise; cancellation remains checked per chunk.

## Reuse-first bounded subtitle boundary — provisional source adoption

After meaningful-use/quality/provenance review, installed only official pysubs21.9.1
pure wheel with verified SHA2564210ebed… and exact public-index lock. MIT notice is
preserved in docs and packaged application resources. No fork/random GitHub code,
ASR, live provider/network download workflow or browser credential operation added.
Thin adapter delegates timestamp/text parsing to upstream; bounds bytes/lines/cues,
validates explicit formats/encoding and framing, preserves raw source/labels/stable
internal IDs/exact rational milliseconds, rejects malformed ASS timestamps and all
upstream default/clamp warnings. VTT unsupported metadata/layout and ASS attachments/
drawings fail clearly; ASS style mapping explicitly pending, no lossless roundtrip or
word-timing invention.20 focused Linux tests PASS. Built wheel verified adapter,
exact dependency declaration and byte-identical MIT notice inclusion. This is not an
actual Windows/frozen renderer test; independent adapter review and target gates OPEN.

Independent review of bf818ed found upstream ignores ASS/SSA Format declarations and
normalizes out-of-range timestamp components. Corrected boundary requires upstream's
canonical event/style layouts, proper sections and exact field counts; rejects ignored
garbage and noncanonical timestamp precision/ranges before conversion. Conversion still
uses pysubs2; unsupported reordered layouts fail explicitly rather than importing the
wrong caption.23 affected subtitle tests PASS on local Linux, including both ASS/SSA
field-order corruption, extra garbage, missing fields, misplaced records and style
layout mismatch. Earlier built wheel is bf818ed only, not this correction; target
Windows/frozen and independent corrected-source review remain pending.

Independent corrected-source review d5ba647: CLEAR for scoped target testing;
3 new ASS/SSA/style regression cases independently PASS (20 deselected). Pin/license/
package checks remain valid for unchanged dependency and license files; report
`docs/reviews/P03_SUBTITLE_ADAPTER_CLEAR.md`. No additional child criterion accepted;
actual Windows adapter corpus and frozen dependency/license gates remain OPEN.

## Explicit subtitle file entry (local only)

Reuses existing actual-read limit+1 helper and independently reviewed parser; returns
an immutable document only after final cancellation check, with no source/current-track
mutation. Seven focused Linux tests PASS: Unicode paths, pre-read/pre-parse/post-parse
cancel, oversized actual read before parser, redacted I/O error and malformed/missing/
directory input preserving the caller's prior value. This is not UI/worker wiring or
an OS I/O deadline; cancellation cannot interrupt a blocking filesystem read. Local
regular-file preflight is not a hostile concurrent namespace guarantee. Windows and
independent source review remain pending; no new criterion closure.

Independent file-entry review 9d01a94 CLEAR; seven affected tests independently PASS.
Wording corrected: these are filesystem-path reads (links/mounts/UNC can resolve to
network storage), not a network-isolation claim. The helper performs no provider API.
Added mutually exclusive headless --validate-subtitles with explicit format/encoding:
only cue count/fixed diagnostics, no caption/path disclosure, Qt/user-data writes or
fidelity claims. Ten affected CLI/shell checks PASS on local Linux. Frozen packaging
and independent CLI-delta review are pending; no new criterion closure.

Independent CLI source review bc2a85f CLEAR; seven focused CLI tests independently PASS.
Local frozen Linux CLI at **bc2a85f** passed four valid format fixtures and malformed
SRT rejection; Unicode paths/source preservation checked, packaged MIT byte-equal.
Binary/license/fixture hashes and outputs: `docs/evidence/p03/subtitle-local-bc2a85f/summary.json`.
Reviewer independently verified binary/license hashes and inspected harness (did not
repeat unchanged executions). This is not Windows/GUI/render evidence. CLI source now
uses None-only default encoding: explicitly empty encoding is rejected (one new focused
negative PASS), rather than silently substituting UTF-8. Frozen evidence remains anchored
to bc2a85f, not this subsequent strictness correction. Argparse usage errors can echo
user-supplied argument values; content redaction claim applies to loaded subtitles/I/O
errors, not arbitrary command-line text. No additional child assertion accepted.

## Typed subtitle staging observation

Five focused Linux tests PASS for parsing before any stage write, exact immutable
bytes/hash/size binding, source/sentinel preservation and three cancellation points.
Post-write cancellation carries retained stage receipt; no final link, job transition,
cleanup or auto-recovery occurs. Policy explicitly `subtitle-parse-only-v1`: not media
validation, snapshot-content matching, authorization, full style fidelity or success.
Uses existing live-anchor Destination and pinned pysubs2, no new package/infrastructure.
This source slice requires independent review and actual Windows target verification.
Final CLI strictness pin 8fa8182 independently CLEAR with one focused negative PASS;
unchanged frozen evidence still anchored to bc2a85f. Accepted child count remains 2/438.

## P03-06 actual media validation slice — SRC-08.02 / OPS-06.01 partial

Uses existing owned-process FFmpeg/ffprobe machinery: exact expected stream set/type/
codec/start/duration and video coded geometry/frame rate or audio sample rate/channels,
then full mapped decode to null with fatal decode/empty-stream policy. Source hash is
rechecked after decode. No extension-only success, stream-copy bypass, raw stderr log,
publication/job transition or new dependency. Timeout applies separately to probe and
decode (not a total filesystem I/O deadline); metadata without explicit per-stream
start/duration fails closed pending supported format-specific resolution. This is not
visual parity, subtitle rendering, tool-registry attestation or durable journal authority.

14 focused checks initially PASS on Linux, including actual locally generated H.264/AAC
MP4 probe+decode, wrong geometry and truncated-file rejection with original bytes intact.
After stricter integer metadata checks, seven affected metadata negative cases PASS
(including one new float-width case); unchanged actual FFmpeg execution was not repeated.
Five earlier subtitle-stage tests remain valid evidence for unchanged staging source.
Canonical coverage: SRC-08.01/OPS-06.04 staging and SRC-08.02/OPS-06.01 decode are partial
until coordinator-required-set publication and supported target corpus integration.
SUB-02.01/.02/.04 adapter support is partial until editor track/style attachment workflow.
No child criteria newly accepted; actual Windows FFmpeg and independent combined review OPEN.

Independent combined review caught a rational-metadata resource hole: an 80-character
string can still contain an enormous scientific exponent before Fraction conversion.
Now accept bounded ASCII fixed decimal/integer/numerator-denominator syntax only;
reject exponent/NaN/bool/float before Fraction is called. Eleven new focused cases PASS
(seven resource/type negatives, four exact decimal/rational positives). Unchanged
actual FFmpeg test evidence is reused, not rerun. Corrected-source review pending.

Combined staging/media corrected source **4213529** independently CLEAR for scoped
verification; reviewer ran only eleven new rational-resource cases (15 deselected).
Actual additional Linux negative: intact H264 MP4 metadata with zeroed mdat payload
passed probe, then failed full decode; bytes stayed unchanged. Author executed once,
reviewer inspected harness without duplicate execution. Exact tool/version/fixture/
harness hashes and reproducible script: `docs/evidence/p03/media-decode-local-4213529/`.
Review: `docs/reviews/P03_MEDIA_STAGE_REVIEW.md`. No Windows/visual parity/publication/
phase acceptance or child assertion closure. Next integration must bind these observations
to coordinator-owned immutable expected snapshots and all-required-artifact journal,
not accept serialized receipts or caller-provided `validated=True` as authority.

## Immutable required-output intent before journal APIs — P03-05/06

New v2 job snapshots optionally bind a closed immutable required-output manifest (roles,
media/subtitle kind, explicit root and safe final leaf). Omitting a previously required
subtitle or changing destination under the same request key now conflicts. Canonical
role ordering is idempotent; input DTO/serialized-copy mutation cannot change stored
intent. Existing no-manifest v1 snapshots remain byte-identical and reopen unchanged;
no automatic migration invents roles. Nineteen affected manifest/job tests PASS locally.
Exact-name duplicate rejection is not native case/alias reservation proof; live root
identity/source-overlap/capability checks still belong to publication admission.
No prepare/claim/success API or new criterion acceptance yet. Independent review OPEN.

## Streaming owned staging — real media larger than sidecar cap

Shared exclusive writer retains original live anchor before closing creation descriptor;
new copy_stage reads regular source in ≤1MiB chunks, bounded by opened size+1, detects
identity/size/timestamp changes, never opens source for writing. Existing byte API keeps
its 32MiB sidecar limit; streaming receipt supports native signed-64-bit size and still
checks actual size/hash/held identity. Partial failures retain stage; final cancellation
returns exact completed receipt on the cancellation exception, never publishes output.

Affected first run:37 PASS/1 FAIL (new33MiB copy hit old receipt32MiB guard). Fixed the
receipt-size gate without weakening actual identity/size/hash checks; failed33MiB case
alone rerun PASS. Added four causal receipt/cancel checks; six affected cancel/forged-size
checks PASS (three deselected). The original37 unchanged PASS were not rerun. This proves
local33MiB streaming/copy/hardlink/readback, not arbitrary-scale/Windows durability or
journal cleanup. Independent lifecycle review remains OPEN; no new child closure.

## Coherent required-set journal admission — P03-05/06

New immutable output policy binds exact media stream expectations (cross-checked with
composition output) or subtitle format/encoding/produced-byte hash. Strict persisted
readback verifies canonical snapshot/hash/closed policy; legacy/intent-only snapshots
cannot infer publish roles. Coordinator session owns live destination anchors and
actually parses/stages subtitles or streams/probes/decodes media. It accepts no worker
`validated=True` receipt. Complete role set required before atomic prepare; atomic claim
rechecks fresh lease/cancel/epoch/job/set/member identity and marks all publishing/claimed.
No publish_member/finish/success/cleanup/restart-adoption API is implemented yet.

Thirty affected manifest/job/session tests PASS initially. Stronger claim-row identity
checks: seven targeted PASS/one new integration test-only failure (comparing tuple order
rather than canonical manifest); fixed assertion, actual media+subtitle required-set
integration alone PASS. Three additional fault/cancel/policy cases PASS: mid-claim denied
member UPDATE rolls back job/set/members, cancellation before prepare inserts no journal,
unknown policy/noninteger version refused. No unchanged aggregate or frozen tests rerun.
Actual local FFmpeg pipeline reaches publishing only after video plus subtitle pass;
source unchanged, no final files or success/history. Native Windows/hosted verification
for all these newer changes remains pending denied source publication. Independent
combined admission review OPEN; no new child criterion closure.

Previous streaming source fba4159 independently CLEAR (five focused growth/cancel/forged
size cases PASS, no33MiB repeat); output-intent a863713 independently CLEAR. Reports
recorded alongside this coherent batch, not separate cosmetic review cycles.

Independent admission review found typed expected-stream policy allowed rational values
larger than its persisted reader's128-bit bound. Unified typed/serialized bounds before
job insertion; boundary policy round-trips, oversized policy inserts no job. Also reject
oversized subtitle bytes before hashing (not only before parser), and assign in-memory
claimed job only after successful COMMIT. Four affected causal checks PASS,16 deselected;
no baseline/actual FFmpeg rerun. Reviewer previously checked nine rollback/cancel/corrupt/
member-mutation/legacy cases PASS. Final combined correction review pending. After it,
checkpoint waits for exact-source Windows/hosted verification under unresolved public
upload approval, before adding final publication/success/cleanup/recovery behavior.

**Final bounded checkpoint b086ccccb94a6d2eff8bd09610c8cdc1273fb0de independently CLEAR**
for owned staging/atomic required-set prepare+claim and target testing. Four exact
correction regressions independently PASS (16 deselected), no broader rerun. Report
`docs/reviews/P03_REQUIRED_SET_REVIEW.md`. No identified source blocker remains within
this scope. Further final-publication/success/cleanup/recovery expansion is held for
actual newer-source Windows/hosted verification, which depends on resolving the denied
public-source upload. Main remains accepted P01; P03 remains IN_PROGRESS,0/9 tasks
accepted and2/438 overall child assertions accepted. This checkpoint is not app completion.

## New hosted checkpoint301934ae and scoped native recovery

Run41286035491: Windows3.12/SQLite3.49.1 source313PASS/22SKIP and frozen CompositionPlan
SUCCESS; Ubuntu3.12/3.13 each322PASS/13SKIP. Windows3.13/SQLite3.50.4 had312PASS/22SKIP/
1FAIL: existing idle DB connection's first coordinator BEGIN after killed peer returned
I/O error. Four original source/JUnit artifacts downloaded and SHA256-verified; no PASS
job replay. Diagnostic-only public8dad3c6/run41286452680 reproduced exact1546
SQLITE_IOERR_TRUNCATE, in_transaction=False; no runtime behavior was changed in diagnosis.

Repair adds read-only epoch preflight before any coordinator BEGIN/INSERT. Only exact
Windows1546 on idle, physically anchored, receipt-owned DB closes/reopens connection
through existing bounded startup-read helper; rechecks appID/schema/WAL and restores
connection settings. No BEGIN/COMMIT/job replay, journal deletion or other-error retry.
Known matching upstream report: https://sqlite.org/forum/info/ba7afbd0e81501118563617430fe06d0aca052e55ece2b0d457f8e16fcf85bba .
38 affected local recovery/ownership/journal tests PASS, not native proof. Scoped
[coordinator-recovery] CI runs affected DB/coordinator/journal tests on all4 OS/Python
targets; unchanged parser/UI/frozen suites retain prior exact evidence rather than rerun.
Independent repair review and native corrected-source evidence pending; no new criteria.

## Scoped native recovery result and later LOCAL integration checkpoints

Public `c416c60a5b70409df587c670d3215348378bd33e`, tree
`0bd033794bb6a7ba84fada901808b7bbbf3d775e`, run **41287172473**:
Windows3.13.17/SQLite3.50.4 **70 PASS/1 SKIP**, Ubuntu3.12/3.13 each
**70 PASS/1 SKIP**. Windows3.12.10/SQLite3.49.1 **69 PASS/1 SKIP/1 FAIL**:
test assumed immediate OS byte-lock release after killed child; failed before any
SQLite recovery statement. Microsoft LockFileEx documents asynchronous OS lock
cleanup. Local test now bounds observation after confirmed exit, but still requires
actual lock acquisition and propagates SQLite/identity errors. This correction is
not yet verified on Windows. All four artifact ZIP hashes match GitHub and their
source receipts pin the public SHA/tree; see `docs/evidence/p03/hosted-41287172473/summary.json`.
No frozen/GUI suite reran in this affected-only run; original frozen evidence remains
301934ae CompositionPlan-only, not Windows subtitle packaging.

User subsequently requested phase-batched remote publication rather than frequent
pushes. No new remote commit/ref/CI trigger follows from the LOCAL commits below.
Main stays accepted P01. Local checkpoints preserve work on the existing phase-03
branch and do not imply remote ancestry equivalence or phase readiness.

- **5535e56421360b85f5a15d9a0c8cdfcdf9781f77**, tree
  `ae6bc9c73ea69d4cfb3dfaa126d8d7fed0bf97cf`: reviewed 12-path P03-06 batch.
  Live `publish_member` records only its artifact; `finish` verifies every required
  retained anchor/final and atomically commits set/job/history. Before/after-COMMIT
  uncertainty reconciles only from the same live proof; foreign identical files
  never adopted. Epoch is checked after slow readback immediately before native
  link. Filesystem post-link uncertainty remains fail-closed. Author:32 affected
  session cases before correction,9 selected corrected cases; independent5 COMMIT
  cases and7 corrected authority/completion cases, not an aggregate count.
  New-owner quarantine retains files and non-resumable validating/publishing jobs;
  7 initial tests include4 real child kills (prepared/claimed/one/all members),2 new
  rollback/snapshot negatives; independent5 in-process cases, no repeated kills.
  Source discovery excludes configured output/cache/staging/link loops and known
  artifact identities; actual `--scan-media` CLI returns bounded candidate counts/
  paths and explicit partial status, never a decode/render claim.9 author cases,
  independent6 focused cases. Automatic configured-policy wiring remains open.
- **5cbb079499c4f205683dba6833a8b63b373ec571**, tree
  `767a0972600fd62bf42fd0eae02b5fa15f7735ff`: actual read-only desktop queue view.
  Bounded own-thread SQLite observations omit snapshots/request keys/secrets;
  truthful missing store and unknown progress, stale-on-error labeling, cooperative
  close.7 affected tests (including existing shell navigation), then targeted visual
  fixes; independent4 boundary/lifecycle cases. Existing app branding preserved;
  red-circle chat identification was not treated as an app-icon requirement.

Reviews: `P03_LIVE_FINISH_LOCAL_REVIEW.md`, `P03_QUARANTINE_LOCAL_CLEAR.md`,
`P03_DISCOVERY_LOCAL_CLEAR.md`, `P03_QUEUE_LOCAL_CLEAR.md` under docs/reviews.
Linux offscreen queue image was inspected, not actual Windows desktop evidence.
No unchanged full aggregate or frozen bundle was rerun. Automatic restart recovery,
owned staging cleanup, complete source-overlap admission, queue commands/progress,
other P03 task gates and actual Windows verification remain open. Exact acceptance
counts remain **2/438 children,0/9 P03 tasks**; test counts are not tool completion.

### Selected-job commands and Qt shutdown correction (LOCAL, later than5cbb079)

Queue buttons now capture one actually selected UUID/version and owned-store receipt
token, not a merely focused/deselected row. Refresh clears old selection. Existing-only
`mode=rw` opening refuses missing/foreign/old-schema stores without creating/migrating
or adopting them. Under the existing nonblocking coordinator lock, one CAS transaction
pauses pending jobs, resumes only explicitly paused jobs, or records cancellation.
Running/validating cancellation is only a request, never a process-stopped claim.
Publishing/configuration holds are not bypassed; a live coordinator causes refusal
until a real command-routing integration exists. Errors/unknown COMMIT are not replayed.
Persistent command notices survive refresh; no snapshots/credentials are emitted.

Author16 affected backend/view cases then2 targeted old-schema/late-selection cases;
independent6 backend stale/store-token/busy/unknown-outcome cases. Review caught the
visibly deselected/current-row mismatch, now causally covered. A later UI test process
segfaulted after passing assertions; independent no-worker tests reproduced exit135,
author reproduced exit134/pure-virtual and isolated snapshot-only exit-7. These runs
are FAILED, not silently counted as PASS or explained away as worker TLS.

Qt's documented application-outlives-QObjects ordering was enforced in fixture and
actual GUI entry point: retire/join workers, delete owned widgets while QApplication
still exists, drain deferred deletion. Nonblocking wait(0) confirms full thread
retirement rather than assuming finished signal means all cleanup completed. The
original failing3-case subset then exited0; independently3PASS/14deselected exit0.
Actual GUI-entrypoint close-during-read subprocess independently1PASS/16deselected
exit0; author real-process3command/window cycles also exit0. Exact original native
C++ fault attribution remains limited; the observed lifecycle risk is addressed,
not an assertion that every platform shutdown is proven.

Final scoped local review CLEAR: `docs/reviews/P03_QUEUE_COMMAND_LOCAL_REVIEW.md`.
No Windows/GUI/frozen CI was triggered for these newer local commits. Full live queue
routing/admission/worker progress and all remaining phase gates remain OPEN. Original
accepted child count2/438 and whole P03 task count0/9 remain unchanged.

### Owned account/profile metadata repository — LOCAL P03-09/P03-02

`accounts/store.py` persists reviewed profile/login-binding/SourceAccess models with
strict bounded field allowlists, distinct exact schema/application identity, original
DB anchor, CAS and observation timestamps. Reuses existing SQLite/ownership helpers.
Review caught and corrected two pre-commit defects: login identities must be unique
per profile/platform (channels/pages are separate scoped access objects), and a
preexisting unmarked empty/v0 DB must never be silently initialized. Corrected SQL
UNIQUE covers insert and update; initialization now requires actual exclusive creation.

One login binding can retain multiple channel/source access observations without a
new Chrome profile. Changed identity/generation cannot reuse old-scope rights.
Defaults CAS-match previous selection and current binding version. Unlink removes
only DB mappings/default/access rows; foreign Chrome sentinel files remain unchanged.
Reopened auth/browser/rights states retain their original timestamps and are explicitly
last-known observations, not fresh browser permission. No cookies/passwords, browser
launch, credential-vault access or network/provider action occurred.

Corrected schema affected16 account cases PASS; independent5 causal correction cases
PASS/11deselected. Review `docs/reviews/P03_ACCOUNT_STORE_LOCAL_REVIEW.md` scoped CLEAR.
The initial unpublished prototype is not adopted/migrated; exact signature mismatch
fails closed. Native Windows, credential refs/secure store, path/version persistence,
full cache retention, job/export/live Chrome integration remain OPEN. No new task or
child assertion acceptance and no remote publication/CI follows from this local batch.

### Local project session/recovery and actual shell save — P03-07

New `storage/autosave.py` reuses typed Project/CompositionPlan, SQLite CAS and atomic
file saves. Explicit file/local-observation/cancel choices revalidate both observed
values. Completed typed commands advance revision and persist before model replacement;
stale versions refuse. Unknown DB/file write outcomes latch reconciliation and prevent
replay. Project-relative recovery/Save As refuses when original base is unproven; it
never silently rebases media/fonts. This is not latest-state ordering, relink/cache or
automatic crash recovery acceptance.

The actual Overview UI offers the choice (cancel default) and an explicit Save button.
Canceled/failed opens retain the current model; recovered content is not written to the
file until Save. Stale saves preserve external changes; unknown saves disable repeat.
There is no editor producing completed commands or timer autosave yet. Existing
ProjectStore unmarked-v0/receipt limitations are explicitly documented, not repaired
or inherited as ownership acceptance by this slice.

Initial12 new core tests PASS. Independent review found a real shared writer defect:
the advisory-lock context caught permission/blocking errors across the entire writer,
misclassifying post-publication failure as a known pre-write conflict. Catching now
covers only native lock acquisition; yield/body errors propagate as uncertainty.
Two new actual after_publish fault regressions PASS, showing changed disk bytes,
latched reconciliation and no second write. Five new UI cases plus two affected prior
open/model-preservation cases PASS, process exit0 with faulthandler. No unchanged
aggregate, frozen build, Windows or remote CI was rerun. Final independent review
is recorded separately before local checkpoint; no additional child/task acceptance.

### Windows FFmpeg reuse evaluation — P02-09/P03-08, read-only

`docs/dependencies/WINDOWS_FFMPEG_CANDIDATE.md` records official vendor linkage,
versioned Gyan9.0.2 ZIP/digest metadata, community-package adoption, publisher bug
signals and incomplete advisory/build provenance. Candidate only: no binary obtained,
installed, executed or redistributed; no system PATH changed. Actual Windows
capability/negative corpus, verified archive and complete licenses/source remain gates.

Final scoped review CLEAR: `docs/reviews/P03_AUTOSAVE_LOCAL_REVIEW.md`;
independent5 postpublish-permission/blocking/UI-choice/save/unknown-retry cases PASS,
14deselected, exit0. No new phase/criterion/native acceptance.

### ProjectStore ownership dependency correction — LOCAL P03-02/P03-07

The session work exposed an inherited constructor gap. Existing unmarked empty/v0
DBs are no longer initialized implicitly; new initialization requires exclusive
creation, while existing stores require valid ownership before SQLite opens. The
connection uses mode=rw, retained original descriptor and permanent continuity-loss
revocation. Exact schema/extra-object validation precedes WAL; guards run again before
WAL/receipt updates. Existing valid ownership receipts stay compatible. Failed new
initialization leaves an unmarked diagnostic/recovery artifact, not an auto-adoption
path. Automatic backup restore/legacy import is still OPEN, not removed from scope.

COMMIT errors no longer get hidden by an unconditional ROLLBACK after commit already
completed. Initial16 new/affected persistence tests PASS. Reviewer then identified
KeyboardInterrupt initialization leaking the newly retained descriptor; outer cleanup
now handles BaseException. Two new interruption/pre-WAL identity-change cases PASS.
The first zero-identity test had an incomplete fstat proxy causing pytest-capture
teardown failure; corrected proxy retains all unrelated attributes, exact test PASS.
No app runtime PASS is inferred from that failed harness run. No unchanged full suite,
Windows or hosted CI repeated; independent final pin review recorded separately.

Final scoped review CLEAR: `docs/reviews/P03_PROJECT_STORE_HARDENING_LOCAL_REVIEW.md`;
independent3 interruption/zero-identity/pre-WAL replacement cases PASS,6deselected.
No additional accepted criterion/task. Existing unmarked DB import/restore still needs
an explicit future recovery workflow; foreign bytes are not modified as a shortcut.

### Original-base persistence and same-content relink — LOCAL P03-02/P03-07

Projects DBv2 retains nullable original directory metadata atomically with completed
commands, outside exported Project JSON. Owned v1 migration validates old schema and
receipt, creates/validates a SQLite backup and transactionally adds the field. Legacy
rows remain unknown, never guessed. Recovery resolves relative asset/font paths
against a known saved origin even if the selected project file moved; rendering still
must verify actual file identity. Different known bases trigger a choice even when
Project JSON matches. Unknown origins remain a relink requirement.

`storage/relink.py` reuses the existing fingerprint helper: explicitly selected asset
or font must match its full stored SHA256; different content is a replacement, refused
by this operation. Returns a typed completed command; source bytes remain unchanged,
probe/timing semantics and render-content digest remain equal. Integration exercises
relink→session CAS autosave→explicit file save. No picker/background hashing, root-folder
batch mapping, media replacement/reprobe or cache invalidation UI is claimed.

24 new/affected origin+autosave cases PASS, plus1 later relink/session/file case and
3 affected initialization/CAS cases. Self-review found ambiguous project-relative
syntax could discard the known base during join; absolute/Windows-drive/root/NUL
forms now refuse before model mutation. Five new causal cases PASS; legitimate '..'
relative paths are not arbitrarily forbidden. Independent review5 migration/base/
samecontent cases and5 ambiguity cases PASS, final source CLEAR in
`docs/reviews/P03_ORIGIN_RELINK_LOCAL_CLEAR.md`. A mistyped reviewer test filter selected
no tests before the corrected exact run; it contributes no PASS. No aggregate,
Windows/hosted or full child/task acceptance; 2/438 accepted count unchanged.

### Local root-folder relink with responsive actual shell — P03-07 / ED-L142

The user selects original media root and replacement root; mapping uses the separate
known project base, so choosing a media subfolder does not reinterpret every relative
path. All mapped SHA256 checks finish before one completed command is applied; outside
references stay unchanged. Hashing uses an owned QThread, real verified/total counts,
cooperative cancellation and GUI-owner SQLite commit. Captured session/revision must
still match; Open/Save are disabled during verification. Close waits for both queue
and relink threads to retire, without forced termination or fake progress.

Initial8 targeted cases yielded7PASS/1FAIL: cancellation could race a finished thread's
queued result because Qt's interruption flag was no longer set when delivered. A
separate GUI cancellation latch now suppresses that late result; the2 exact cancel/
close cases PASS exit0. Affected unknown-save UI test also PASS: neither save nor relink
can retry an uncertain session. Existing real GUI-entrypoint subprocess passed among
the initial7; no duplicate frozen/aggregate run. Actual empty-state offscreen screenshot
`runtime/project-relink-empty-offscreen.png` inspected: truthful unavailable actions,
eight areas and no fabricated data; process exit0, Fontconfig cache warnings remain.
No claim of Windows GUI acceptance or exact native font behavior.

Final independent scoped review CLEAR: `docs/reviews/P03_ROOT_RELINK_UI_LOCAL_CLEAR.md`;
5 selected root/subroot/cancel/close/stale-session cases PASS exit0; final shutdown-only
latch inspected without repeating unchanged tests. Public/native acceptance remains
unchanged. Local work now includes the actual root picker and background verification;
full editor, replacement/reprobe, cache and Windows targets remain open.

### Bounded executable candidates and no-fallback preference — LOCAL P03-08

New stdlib-only `dependencies/discovery.py` and headless `--scan-tools` enumerate only
named candidates in explicit/PATH/common Chrome/extra directories, never recursively
scan drives or execute candidates. Explicit invalid path never silently falls back;
Auto class preference and declared PATH order are retained. Every candidate remains
UNCHECKED/NEEDS_CHECK, not READY or ownership/trust proof. Permission errors and limits
remain partial rather than false complete-missing; oversized PATH roots refuse rather
than silently truncate. No installs, profile access, PATH edits or user-data writes.

9 initial focused cases PASS plus2 final order/deadline/fresh-process tests PASS;
fresh process forbids Qt/storage imports and still enumerates successfully. Independent
4 no-fallback/partial/order/headless cases PASS, scoped review CLEAR:
`docs/reviews/P03_TOOL_DISCOVERY_LOCAL_CLEAR.md`. No unchanged actual FFmpeg, native
Windows or aggregate rerun. Verified registry, tool functional/pair tests, manifests,
leases, installation, automatic settings UI and other original dependency types remain
open. Source discovery alone does not close any tool-readiness criterion.

### Explicit pinned FFmpeg pair functional observation — LOCAL P03-08

`dependencies/checks.py` requires explicit caller-authorized executable pins and a
known-hash fixture with exact expected streams. Both pins are checked before launch;
there is no discovered-candidate execution shortcut. Reported versions/library tuples
must match; existing media validation provides full fixture probe/decode, followed by
one exact bounded black RGB16 frame to stdout. No output/staging files or source writes
are introduced. Errors suppress arbitrary stderr and never automatically retry.

13 targeted unit cases PASS. One actual new-wrapper integration PASS in1.37s reuses
unchanged approved Linux FFmpeg/ffprobe7.1.5 binaries and retained synthetic H264 fixture
c374672f…; exact source/tool/fixture/harness hashes and observations are preserved at
`docs/evidence/p03/tool-pair-local/`. No binary acquisition, fixture regeneration or
unchanged corrupt-payload baseline rerun. Scope is that fixture/raw-frame observation,
not all codecs/GPU/subtitles/Windows, publisher provenance or a production version lease.

Independent6 pin-before-launch/drift/version/policy/cancel cases PASS,7deselected;
actual FFmpeg receipt reviewed without duplicate execution. Caller must provide a
trusted stable tool namespace during this check: before/after path hashes are drift
observations, not atomic executable identity or protection against swap-and-restore.
No extra task/criterion acceptance or remote publication follows.

### Final jobs-opening repair and coherent hosted checkpoint preparation

Disposable repro confirmed default JobRepository silently adopted a preexisting
unmarked empty DB (bytes changed,v0→v2). Default opening now refuses before SQLite;
exclusive new creation or valid ownership is required. Explicit adoption is separately
opt-in and cannot override a foreign receipt. Leaf symlinks are not resolved away,
connections/reopens use mode=rw, identity loss permanently revokes the instance, and
pre-WAL/receipt/submission-COMMIT guards prevent known discontinuity. Post-COMMIT errors
are preserved without invalid rollback or replay. No jobs schema version, native
1546 retry conditions or process security policy changed.

10 new/affected identity/adoption/migration cases PASS plus1 explicit-adoption/foreign-
receipt negative; exact owned1546 reopen regression PASS with mode=rw. Discovery fixture
names and isolated PATH/common-directory inputs now support the Windows test target;
4 selected portable-discovery cases PASS locally, not native proof. Frozen harness3
unit cases PASS; its actual Windows run is still pending. Independent final scoped
review7 jobs identity cases PASS exit0 and source/harness/workflow hashes checked:
`docs/reviews/P03_INTEGRATION_CHECKPOINT_CLEAR.md`.

New human authorization permits important coherent checkpoint publication before a
whole phase finishes. Planned one ordinary4-target source/native aggregate plus
Windows3.12 onedir/frozen schema/subtitle/empty-encoding/tool-discovery/exact-MIT tests.
No diagnostic marker or new binary acquisition. Main stays accepted P01; phase03 is
IN_PROGRESS. Reconciled all9 machine-readable P03 states from stale PLANNED to
IN_PROGRESS, never ACCEPTED. Accepted children remain2/438 and whole tasks0/9.

## Hosted integration 41295642110 and bounded repair

Public `5d8a3389affe5386f52b0925d6943f78b2a2d313` (local f996800, tree
`e5fd4c1538b79beaf53f37782538a798f1074866`) ran the full 505-case matrix.
Ubuntu Python3.12/3.13 each:491 PASS/13 SKIP/1 FAIL. Windows Python3.12/3.13
each:475 PASS/22 SKIP/8 FAIL. All jobs terminated normally; actual native process,
coordinator crash/lock, publication, queue and Qt lifetime cases have individual
PASS evidence, not whole-phase acceptance. Frozen build/checks were skipped after
source-test failure, NOT passed. Exact source/JUnit receipts retained in
`docs/evidence/p03/hosted-41295642110/`; summary records ZIP and member SHA256.

Failures: one old test expected 'receipt' while the strengthened pre-SQLite guard
returned an otherwise correct refusal message; Windows media discovery incorrectly
used cached DirEntry.stat identity (zero device/inode); subprocess environment
removal still allowed a real host Chrome candidate. No foreign DB adoption or
source overwrite occurred. Repair preserves ownership refusal and changes only
its diagnostic wording; discovery now fresh no-follow os.stat with anchored POSIX
dir_fd or pinned Windows directory path. Zero identity still refuses. Python's
primary contract: https://docs.python.org/3.13/library/os.html#os.DirEntry.stat .
Test/frozen harness explicitly assigns the owned empty directory to Chrome search
roots instead of removing variables; this changes only the test process environment.
No application tool availability is fabricated.

30 affected local tests PASS, independent causal discovery regression1 PASS.
Next `[integration-repair]` checkpoint uses all4 platforms but ONLY affected
migration/open-identity/discovery/harness tests; unchanged prior native/GUI PASS
cases are carried forward, not rerun. Pending plan/schema and actual Windows3.12
frozen schema/subtitle/tool-discovery/license checks remain enabled. A green repair
is affected evidence, not a new full aggregate or P03 acceptance. No criterion
closure;2/438 and0/9 remain unchanged.

### Native repair result and corrected boundary oracle

Run41296135792 public9b62a1a7b067ad340a1be41996d3aa86861f6abc,
treeea3a2a4d6bffe1f58c2d4bc097b484c8dd189357: Linux3.12/3.13 each48 PASS;
Windows3.12/3.13 each47 PASS/1 FAIL. All media discovery identity/hardlink/exclusion
and jobs migration/ownership repairs now pass on actual Windows. All4 ZIP API
hashes/source identities verified, exact members retained under hosted-41296135792.
The remaining test incorrectly assumed an empty host candidate list; Windows child
still observed installed Chrome despite attempted process-local search hints. The
precise environment/startup mechanism has NOT been established. Earlier wording
that explicit environment values prevent restoration was too strong and is corrected.

The actual requirement is read-only candidate discovery, no GUI/storage startup,
no execute/install/readiness grant, and invalid explicit selection never falling
back—not absence of installed tools. Corrected fresh-process/frozen oracle explicitly
selects an owned nonexistent Chrome path and requires INVALID_EXPLICIT_PATH with no
selected candidate, while any real host candidates remain UNCHECKED and other
selections only MISSING/NEEDS_CHECK. Input/no-appdata checks remain. Application
source is unchanged; four affected local harness/import tests PASS exit0.
Next [integration-repair] [windows-boundary] run covers only these four affected
checks on both Windows Python versions plus still-unrun Windows3.12 frozen build;
Linux48 and unaffected Windows47 results are carried forward. No aggregate rerun,
new criterion closure, permission/security setting change or fake tool readiness.

### Terminal scoped native/frozen evidence

Run41296433758 public61622936684fbbd7faa56eaeb332cc877170b619,
treec8580226a98f022a2001bf924ed18359a2a71a49: both Windows jobs SUCCESS,
4 affected tests each,0 skips/failures. Windows3.12.10/SQLite3.49.1 actual onedir
build and five frozen CLI cases PASS: CompositionPlan, Unicode subtitle, invalid
timestamp refusal, explicit empty encoding refusal, read-only tool discovery with
invalid explicit Chrome/no fallback. Exact packaged MIT SHA256
93d82c4caf14f9ac8845377399860ee8e3628481d8017ebe33febb8bf7236211;
harness-reported binary SHA256
f9befc6a9941dc22fed7d8b86bc9c8dfacafea7f83e4aae50d1b21302804f6ef.
Binary itself was not uploaded/rehashed independently; receipt is exact executed
harness evidence. Fixture hashes unchanged and app-data directory absent.
Windows3.13.16/SQLite3.50.4 ran four source/harness checks only, no frozen build.

Both artifact ZIP API hashes and all five source/JUnit/frozen members verified;
exact bytes preserved under hosted-41296433758. Prior native/GUI/publication tests
remain attributed to5d8a3389 and corresponding runtimes; affected discovery/ownership
proof to9b62a1a7. No blanket final-source full-aggregate PASS. Full run41295642110 used Windows3.13.16, intermediate repair41296135792 used
3.13.17, and final boundary returned to3.13.16; exact source attribution remains. This
coherent causal evidence closes the observed integration failures without repeating
unchanged tests. Full P03, actual GUI/media/GPU/provider/release gates stay OPEN;
no extra criterion accepted beyond2/438, whole P03 tasks0/9.

## P03-06 live namespace admission (local, native run pending)

Actual source: jobs/admission.py and jobs/publication.py. Immutable composition
source/font absolute paths now acquire original read-only descriptors and parent
pins; unresolved project-relative execution references refuse rather than guessing
cwd. Source/name continuity loss permanently revokes the session. Recheck before
staging, after slow readback and immediately before native no-replace link. Existing
final/source hardlinks remain conflicts. Source continuity is not content-SHA/media
validation; manual inputs in output folders are not categorically forbidden.
Configured cache overlap is refused, and session.scan_sources automatically supplies
manifest output roots, configured cache roots and bounded durable artifact identities.
Seven new cases cover source/font replacement, unresolved/cache refusal, source-final
hardlinks, automatic scan exclusions, late collision before stage, source change after
hash/beforelink, and differing Windows path/FD timestamp precision with true mutation.

Initial affected admission/session/recovery run48 PASS; after independent review found
cross-API timestamp precision issue, corrected separate per-API baselines and exact
new regression PASS (also independently1 PASS). No repeated unchanged full aggregate.
No new accepted criterion or whole P03 task. Planned [publication-admission] native
four-target affected49-case check skips unchanged frozen build (latest frozen proof
remains6162293/run41296433758).

Owned cleanup was investigated, NOT shipped: review reproduced foreign replacement
between last identity stat and pathname unlink, so held FD alone was insufficient.
The entire unpublished destructive prototype was removed; active filesystem adapter
is byte-identical to prior reviewed checkpoint. Source staging still remains retained.
Original local cleanup assertions did not establish race safety and are not acceptance
evidence. A separately reviewed object-bound deletion capability plus worker quiescence
is required before cleanup can safely ship. No automatic cleanup/unsafe retry/foreign
file deletion remains in active source.

### Admission target result / metadata-observation repair

Public2c5ddff85e04fcbfc77389b209452f8ca29c6426 run41300558073: Ubuntu3.12.15,
Ubuntu3.13.17 and Windows3.12.10 each48 PASS/1SKIP (actual FFmpeg unavailable).
Windows3.13.16:47PASS/1SKIP/1FAIL, solely the precision test's immediate same-size
write observation. The original test assumed timestamps necessarily change; the
namespace admission contract explicitly does not validate content hashes. Two test
mutations now change size (precision and pre-link observation) so they deterministically
exercise observable metadata loss. No application source/guard is changed. Same-size
edits with unchanged/coarse/delayed/restored metadata are explicitly NOT detected;
fingerprint/probe validation remains required before execution and after relevant I/O.
The exact hosted timestamp mechanism is unknown. Primary timestamp limitations:
https://learn.microsoft.com/en-us/windows/win32/sysinfo/file-times .

All four ZIP API digests/source identities and8 exact member hashes retained in
hosted-41300558073. Local2 affected cases PASS and independent2 PASS; next paired
[publication-admission] [admission-observation] targets only those two cases on
Windows3.12/3.13. Prior48/47PASS cases are carried forward, not repeated. Frozen
unchanged remains skipped. No source-byte immutability, safe cleanup or criterion
acceptance inferred.

### Admission observation terminal evidence

Run41300884252 public556c9ad3a35637613053dcc423ab32c2a6300a4f/tree0573e501:
both Windows3.12.10 and3.13.16 SUCCESS,2 targeted cases PASS each,0 skips/failures.
Exact source/4members and both ZIP API hashes verified under hosted-41300884252.
No application changes from2c5ddff; prior unaffected48/47PASS evidence carried,
not called a new full aggregate. No frozen rerun, new child or P03 closure.

### Windows cleanup capability prototype (not integrated)

New artifacts/windows_cleanup.py + tests/test_windows_cleanup.py reuse official
Win32 APIs through stdlib ctypes; original→bridge→DELETE-handle continuity, pinned
expected parent, deny-write/delete target, no-follow/no-create/no-inherit, no pathname
unlink. This module is NOT invoked by PublicationSession or normal app flow. Actual
Windows tests must establish native hardlink/foreign replacement/disposition/handle
retirement behavior before completed-job integration. Local unsupported-platform
case PASS; native tests remain SKIPPED/NOT_RUN until scoped [windows-cleanup] CI.
No claim that the earlier destructive race is solved on POSIX (still retain).

Independent prototype review caught authority failure allowing another mark attempt;
fixed one-shot latch before all guards/callbacks and permanent revoke. New platform-
neutral causal regression PASS (also independently1PASS), actual native remains pending.
Final scoped source/workflow CLEAR in P03_NATIVE_CLEANUP_PRIMITIVE_REVIEW.md.

## Local P03-04 incremental progress observation (after b32795a)

26 new affected tests PASS (exit0); actual pinned Linux FFmpeg emitted25frames,
1000000us/end through new owned stdout observer, exit0, unchanged tool/input hashes.
See WORKER_PROGRESS contract and progress-local receipt. No job state mutation,
percent/ETA, renderer/queue completion, Windows or additional criterion acceptance.
Meaningful independent work continued while exact native cleanup publication was
blocked; b32795a approval payload was not expanded or retried.

## Windows object-bound cleanup primitive — hosted evidence

Exact authorized localb32795a published tree-equivalent as ccfa0b1d after one
same-operation retry on new explicit user approval. Run41301972313 terminalSUCCESS:
Windows3.12.10 and3.13.16 each10PASS/1SKIP (non-Windows-only branch). Both ZIP API
digests and all4members verified; evidence under hosted-41301972313. Only native
primitive, not production cleanup/phase completion. Later progress code excluded.

Progress follow-on: one real SQLite+owned subprocess callback test PASS/26deselected;
initial test-only context-manager assumption failed, corrected to explicit closing.
No app source change or unchanged26case repeat. Thread affinity documented; queued
UI consumer and active worker coordinator remain open.

## Local completed-publication cleanup integration prototype

Changed shared anchor ownership to close-once descriptors and retained original
Windows stage-directory handles. Added completed-journal/history guarded Windows
cleanup with continuous final bridge/pin; no POSIX deletion or restart adoption.
Affected local39PASS/6WindowsSKIP plus33publication-sessionPASS; two further native
fault/hash cases authored but not executed locally. Windows bridge/delete-pending
integration remains unverified; prior primitive10PASS pertarget is not reused as
proof of this new sequence. Source review pending. No criterion closure.

Independent integration source review CLEAR for affected CI after correcting
post-entry failure classification: once native maintenance begins, later known
JobConflict/PublicationError is conservatively UNKNOWN with original cause. Pure
classification regression1PASS plus independent1PASS; close-uncertainty1PASS.
Nine actual Windows integration cases remain NOT_RUN locally. Reviewed workflow
`[worker-cleanup]` alone selects four runtimes/five affected files; skips unchanged
full aggregate, frozen build and unused LinuxQt package installation. Normal workflow
behavior is unchanged. Exact combined review: P03_CLEANUP_INTEGRATION_REVIEW.md.

## Hosted worker/completed-cleanup checkpoint and exact child closures

Run41303347554, public341d304e/tree29c5378 (localec38f59):4SUCCESS.
Linux3.12.15/3.13.17 each100PASS10SKIP; Windows3.12.10/3.13.17 each108PASS2SKIP.
Windows9cleanup integration cases prove final bridge/classic disposition sequence
and failure retirement;27progress cases pass everytarget. All4 ZIP API digests and
8source/JUnit members verified independently. Actual FFmpeg media+subtitle case is
SKIPPED everywhere hosted (unavailable), not fake target proof. Linux9nativecleanup
skips and Windows1unsupported-platform skip are explicitly recorded. No aggregate
or frozen rerun; earlier exact evidence retains its own source/runtime.

Independent review and root accept exactly BAT-03.04 (prior unchanged scanner case),
OPS-06.02 and OPS-06.04. Ledger now5/438 exact children,5/78 P03-mapped; whole P03
remains0/9 tasks. Not tool percentage. Source-clause conjunctions, renderer, full
queue/UIprogress, cancellation temps and restart recovery remain open. Exact links,
cases and restrictions recorded in records.json and P03_ACCEPTANCE_LEDGER.md.

## Local canceled-owned-stage checkpoint (native target pending)

Original exclusive file descriptor is now retained before a producer/cancel can
interrupt writing; separate StageOwnership cannot publish or validate. Exact
acknowledged canceled live attempt/prepared journal may clean only its own original
Windows stage handles; source/final/foreign children are not targets. No-stage noop
is safe on allOS; existing stages remain unsupported on POSIX. Active staging cannot
be cleaned; any validator exception permanently latches quiescenceUNKNOWN, because
current exception types do not prove descendant retirement. Cancel ack cannot clear
that state. This closes a real review blocker without pretending failed validators
are quiescent; typed retirement integration remains future P03-04 work.

12 new locally applicable cases passed in impact-selected runs, plus3affected copy
cancellation cases and5prepare/validation cases. One media test fixture initially
contradicted composition geometry; fixed fixture then exactcasePASS. Initial10PASS
run's failure is not relabeled aggregatePASS. Independent final unknown-retirement
causal regression1PASS. Seven actual Windows cancellation cases remain NOT_RUN;
source review CLEAR for `[cancel-cleanup]` fourtarget28affectedcases. No unchanged
aggregate/frozen/Qt install or new criterion closure. Ledger remains5/438,0/9tasks.

## Hosted canceled-stage checkpoint

Run41304594711 public0591bd80/tree2cf936e (local65c622c) terminal4SUCCESS.
Windows3.12.10/3.13.17 each27PASS1SKIP; Linux3.12.15/3.13.16 each20PASS8SKIP.
Runtime values from exact source receipts, not carried by assumption from priorruns.
Four ZIP API digests/eight source+JUnit members independently verified. Seven actual
Windows canceled-cleanup cases and completed-cleanup carry-forward passed; validator
retirement-UNKNOWN refusal passed allfour. Windows skip is POSIX-only retention;
Linux skips are eight actualWindows cleanup cases. No FFmpeg process was launched
in the interrupted-copy case: cancellation was proved to stop before validation.
No newchildclosure;5/438 and0/9 P03tasks unchanged. Next meaningful P03-04 gate is
fresh typed retirement observation through probe/validation so a genuinely confirmed
validator cancellation can permit own-temp cleanup without overriding UNKNOWN.

## Local typed validator-retirement checkpoint

Owned adapters now emit internal per-invocation retirement observations only after
all checked finalizer work; Windows ActiveProcesses0 proof distinct from NO_PROCESS
setup failure and POSIX group-policy observation. Validation tracks probe/decode in
one fresh operation/thread-bound single-use lifecycle; unknown invocations survive
sanitized exceptions. Session rejects successful validator return without provenance
as well as unknown failure; existing sticky UNKNOWN never clears.

13 newly applicable local cases PASS across impact-selected runs, Windows finalizer
case NOT_RUN locally; old unknown-validator regression1PASS and6affected default API/
validation casesPASS. Actual Python child+descendant stand-in exercised cancellation
through validator wrappers onLinux, not FFmpeg support. Reviewer caught pre-job
failure mislabeled WINDOWS_JOB_EMPTY; fixed NO_PROCESS with new1PASS+independent1PASS.
Source CLEAR for22affectedcases/fourtargets via `[validator-retirement]`; no unchanged
aggregate/frozen/Qt install. Actual Windows cancellation→proof→own-temp cleanup and
native finalizer-unknown test remain target gates. No newchild/task acceptance.

### Typed validator retirement — hosted41306207422
Four targets SUCCESS, each20PASS/2inapplicableSKIP. Windows3.12.10/3.13.16;
Linux3.12.15/3.13.17. Exactsource7a87baa7/tree7637a86c. Independent API/ZIP/member
verification recorded in P03_TYPED_RETIREMENT_HOSTED_41306207422.md. SRC-08.04
accepted only for live owned Windows cleanup; ledger6/438, P03 6/78, tasks0/9.
Python decoder/descendant is a lifecycle stand-in, not actual FFmpeg proof.

### Active coordinator inbox — local implementation
P03-04/P03-05: bounded cross-thread immutable command routing, owner-thread CAS,
no second coordinator lock, pending cancellation/close, unknown-COMMIT retirement,
and optional Qt command route. New8 inbox tests PASS across affected runs, exit0, including actual owned
Python child/descendant cancellation and Qt dispatcher. Default shell scheduler
and progress consumer are still open; no new criterion or Windows claim.

Bounded latest-per-job numeric progress transport and actual optional queue consumer
added:5newcases PASS across affected runs, including real Python stdout to Qt
frame/time/byte display, selected cancellation through live owner, retirement and
acknowledgment. Store/hash/attempt/final-state filtering, initial read retention and
failed-read pause exercised. This is not a default production scheduler or FFmpeg
codec test. Independent progress source review CLEAR; native checkpoint pending.

One integration aggregate:573PASS/36nativeSKIP/1FAIL (old privacy repr assertion
rejected intended snapshot_hash field). Exact field-allowlist/full-body exclusion
test corrected, focused1PASS exit0; no unchanged aggregate rerun. Failed original
JUnit and source hashes preserved under docs/evidence/p03/inbox-progress-local/.
Normal four-target checkpoint will establish native integration afresh.

### Normal integration checkpoint41307781141 — independent verification
Public1835c790/treeaf55e0ee, local714bb50. FourSUCCESS; Windows3.12.10/3.13.16
each584PASS26SKIP, Linux3.12.15/3.13.17 each571PASS39SKIP. All13new inbox/progress
cases non-skippedPASS on all4. Windows312 actual onedir build and5frozen CLI
schema/subtitle/discovery/license casesPASS; binaryhash is harness-reported, not a
separately downloaded release artifact. API4ZIP digests and9members independently
verified in P03_NORMAL_INTEGRATION_HOSTED_41307781141.md. Actual FFmpeg unavailable
remains skipped; physical GUI/default scheduler/provider/fulltask gates open.
Ledger6/438 and0/9P03tasks unchanged.

### Transition refresh and combined selected cancellation — local
P03-04/06: owner revisions coalesce durable state refresh; busy UI cannot lose
latest revision; closed route is not terminal until admitted commands finish.
Final durable read attempted, error remains visible/manual-refresh, no command
replay. Three newcasesPASS across affected runs; prior13affected inbox/progress
casesPASS once. Combined real Qt selected cancellation to owned Python
probe/decoder/descendant, typed retirement, acknowledgment and safe POSIX retention
PASS locally; actual Windows object-bound stage removal in this combinedcase
awaits scoped16-case4targetCI. No FFmpeg simulation passed as codec evidence.
Initial test referenced nonexistent job_history, corrected to completion_history;
not an application failure. No new criterion accepted before native proof.

### Combined cancellation native gate41308555823
Exactpublicf40bdf3c/tree085c9aca (local672490c), fourSUCCESS/all16PASS/noSKIP each.
Windows3.12.10/3.13.16 own-stage cleanup and Linux3.12.15/3.13.17 safe retention
actually executed in combined UI path. API4ZIP digests/8members/source/JUnit
independently verified; exact OPS-02.02 child accepted with root concurrence.
Ledger7/438 globally,7/78P03mapped; wholeP03tasks0/9 unchanged. Not FFmpeg/default
scheduler/provider/restart or physical-desktop acceptance. No unchanged test reruns.

### Typed durable diagnostics — P03-05 local source
Separate owned diagnostic SQLite store; no jobs schema migration or native lock
change. Allowlisted codes/stages/numeric exit values only, capped retained rows,
fixed plain-text UI labels, original-FD/receipt/schema checks. Selected command
outcome remains committed if diagnostic append/open/close fails; explicit warning
without command/log replay. Read-only selected view runs outside UI thread and
creates no missing store/sidecars; original-FD SQLite header rejects WAL before
SQLite connection. DELETE journal/zero busy wait; no hard OS-I/O deadline claimed.

18backend+4UI newcases exercised across affected local runs, including actual
worker-thread Python exit7 with private stderr→typed store→Qt fixed error text,
row caps, foreign/future/corrupt/unmarked refusal, unknown append, busy log store,
read-only byte/file preservation and close lifetime. Initial receipt test used a
wrong filename, corrected to receipt_path; no app failure hidden. Reviewer reproduced
unsupported-WAL sidecar creation, fixed header preflight and causal negative.
Four shared command/inbox/progress/cancel regressions plus3UI cases7PASS exit0; no
aggregate repeat. Independent source CLEAR; scoped55-case4targetCI remains pending.
Ledger7/438, tasks0/9 unchanged; full provider/executor/error integration not accepted.

Native exit-code model includes signed POSIX signals and unsigned Windows DWORD
crash codes (e.g.0xC0000005); exact bounded numeric roundtrip regression1PASS.

### Typed diagnostic native gate41310543152
Exactpublic97af44fd/treef107870e (local08dd4d0), fourSUCCESS/all55PASS/noSKIP each.
Windows3.12.10/3.13.16 and Linux3.12.15/3.13.17. API4ZIP digests/8members/source/JUnit
independently verified. OPS-05.03 exact child accepted with root concurrence;
ledger8/438, P03 8/78, whole tasks0/9. Scope limitations remain as above.

### Offline project migration backup restore — local source checkpoint
P03-02/07: explicit headless restore into a NEW exclusive store, ownership receipt
last, no live-store overwrite/source SQLite open/path deletion/replay. Actual v1
migration backup→copy→normal reopen/migrate preserves all original IDs/documents/CAS
versions and unknown origins, while old live DB retains its newer state unchanged.
Local affected runs:17 initial restore cases,7 CLI cases,1 explicit rollback-v2
origin case,4 complete metadata/NUL cases,3 SQLite BLOB-type negatives PASS. The
first v2 fixture used a WAL-header snapshot and correctly refused; fixture then
explicitly prepared rollback format, not a claimed WAL recovery fix. Reviewer found
TEXT substr NUL truncation; replaced with bounded BLOB projections, original text
type gates and full comparisons. Fresh CLI subprocess imports no Qt; errors omit
private paths/project content. Native Windows gate pending. No new child accepted;
8/438 and0/9 full P03tasks remain. GUI store switching/latest-backup choice and WAL
backup recovery are separate open scopes. No unchanged aggregate/frozen rerun.

### Restore native evidence41312580297
Exactpublicd3cf2b17/tree0abcf2c2 (local968cd74): fourSUCCESS, each72PASS0SKIP.
Windows3.12.10/3.13.16, Linux3.12.15/3.13.17. Independent API/4ZIP/8member verification
supports only OPS-03.04; root concurred. Ledger9/438, P03 9/78, tasks0/9. Original
WAL refusal/current-v2 fixture/GUI/latest/frozen limitations retained. No reruns.

### Overview restore entry — local UI integration
New dedicated restore panel adds an explicit offline-backup/new-directory action,
new `projects.sqlite3` only, current store/session preserved. Worker-only SQLite,
10Hz copied-byte observations labelled not complete; final result after actual thread
retirement. Cancel/close request stop and wait; late cancel does not erase confirmed
creation, unknown/partial retained with no-retry guidance, stale worker signals ignored.
Four new focused GUI cases PASS exit0 including actual backup restoration and live
event loop;15 affected existing shell/recovery/root-relink cases PASS exit0. Native
UI route still pending; no extra child/whole-task acceptance or GUI store switch.

### Restore UI hosted evidence41313112557
Exactpublicc44a5d3b/tree7ec7498f (local02b25cf): fourSUCCESS, each19PASS0SKIP.
Windows3.12.10/3.13.16, Linux3.12.15/3.13.17. Independent4ZIP/8member/source/JUnit
verification confirms actual offscreen UI→worker restore and cancel/close, with
existing active DB preserved. No new child (9/438), task (0/9), native desktop
picker interaction/latest-state/WAL/frozen claim. Evidence bundled with next work.

### Typed stream observations and explicit inspection CLI — local P03-03
Immutable observations preserve every global stream index, signed exact tick timing,
per-stream SAR/geometry/audio layout and raw matrix/rotation provenance. Unknowns,
cover art and non-timeline tracks remain visible; no silent stereo/zero/CFR defaults.
All observations explicitly render_ready=False; no full frame-PTS asset conversion.
Explicit --inspect-media/--ffprobe runs only caller-authorized tool, with existing
owned process/fingerprint path, fixed errors and no arbitrary metadata tag export.
19 new focused cases across initial+causal runs PASS;18 affected existing headless
CLI regressions PASS, no aggregate. Review found pre-encoding allocation and false
rotation-summary provenance, fixed together with3causal regressions. Actual existing
Linux FFmpeg/ffprobe generated no-audio48x32SAR4:3 fixture and CLI observation passed;
receipt pins exact measured pre-correction source/tool hashes, not a claimed rerun.
No actual Windows FFmpeg/full VFR/renderer/newchild acceptance; ledger9/438 unchanged.

### Typed observation hosted41314168015
Exactpublic68cb784a/tree0cbe4c4b (local281eac3): fourSUCCESS/37PASS0SKIP each;
Windows3.12.10/3.13.16, Linux3.12.15/3.13.17. Independent API/4ZIP/8member verification.
No actual hosted FFmpeg/frame-map/render-ready acceptance; ledger9 unchanged.

### Decoded frame observation — local P03-03
Explicit source/tool/global-stream/timebase/start binding, owned ffprobe frame query,
raw signed PTS/best-effort/duration fields kept separately and in original order.
EOF status only command/JSON completion, not trusted full coverage/media validity.
Nonzero/error-stderr/count cap returns INCOMPLETE; malformed/capture/process/cancel
failure cannot fabricate partial parseable records.19new focusedcases across17initial
and2preflight/CLIcap runsPASS. Actual Linux generated VFR fixture yielded exact times
0,.2,.3,.5,.6,.7,.8,.9 through CLI; receipt exact source/tool binding, preflight-only
subsequent delta documented. No synthetic CFR timestamps or actual WindowsFFmpeg
claim. max_frames limits retained prefix after byte-bounded JSON, not cheap early
termination. Independent source CLEAR, target CLI/native runtime gate pending.

### Frame observation hosted41316355671
Frozen09e82b0 publication initially denied; exact user approval resolved same-operation
retry, publicc6adf209/treec7768733. FourSUCCESS/42PASS0SKIP each, Windows3.12.10/3.13.16,
Linux3.12.15/3.13.17; independent4ZIP/8member/source/JUnit verification. No actual
WindowsFFmpeg/framevalidity/extra child; ledger9/438 remains.

### Visible read-only Editor media inspector — local P03-03
Explicit media/tool paths plus reset-on-tool-change trust checkbox; no fallback,
registry claim/project apply/timeline/render. Worker-only I/O; optional globalstream
frames; bounded allstream facts and first64records. Fresh internal lifecycle requires
1/2confirmed invocations for successful observations; unknown retirement sticky and
blocks repeat, including after tool/path changes. Close waits actual worker and
checks native proof separately. Six newUI+two frame lifecycle cases PASS across
focused runs; cancel regression uses ready-stdout handshake before close to prove
actual Python stand-in child launched. Stand-ins are not FFmpeg capability evidence.
Actual existing Linux ffprobe through offscreen UI observed8irregular VFR records,
confirmed process retirement/source unchanged/cleanexit0; Fontconfig cache warnings
were present, no desktop/font-readiness claim. Exact source/tool hashes in scoped
receipt. Independent source CLEAR; scoped Windows UI gate pending, ledger unchanged.
Affected shared shell/recovery/root-relink/restore UI regression19cases PASS exit0
after inspector integration; independent reviewer did not duplicate this baseline.

### Media inspector hosted 41317345741
Public 3ce071c5/tree5939a550 (local58969dd): four SUCCESS, each27PASS0SKIP.
Windows3.12.10/3.13.16, Linux3.12.15/3.13.17. Independent API/4ZIP/8member
verification includes all six inspector and two frame-lifecycle cases. This proves
scoped Qt/owned-process protocol integration, not actual hosted FFmpeg, frozen GUI,
editor import/frame-map validity or another child criterion. Ledger9/438 unchanged.

### Prepared Windows FFmpeg candidate gate — NOT RUN
Exact official-referral BtbN dated asset695397553 downloaded and inspected read-only:
archive/member hashes, LGPLv3 notice and static DLL imports recorded. No PE execution,
installation/PATH change, binary redistribution or complete dependency/security audit.
Dedicated Windows3.12/3.13 synthetic harness prepared;11sentinel/control unit cases
PASS locally, independent bounded source review. Actual candidate execution awaits
specific user scope authorization; no codec/renderer/criterion acceptance implied.

### First candidate target attempt 41320165222 — FAIL before candidate execution
User authorized exact pinned candidate execution on synthetic Windows media. Source
publica7ef68d/tree85ff6691: both Windows targets10PASS1FAIL sentinel tests; candidate
download and native execution skipped. Backslash fixture name was normalized by
Windows ZipInfo construction, so test did not inject the expected invalid raw name.
Correction preserves raw fixture spelling and rejects orig_filename/filename aliases
before extraction (including NUL truncation). Actual FFmpeg capability remains NOT_RUN.

### Candidate attempt 41320537260 — partial native evidence, overall FAIL
Both Windows targets13sentinelPASS; actual pinned8.1.3 pair/full decode/black frame,
no-audio/SAR and exact VFR observations passed. Rotation fixture assertion then
failed; corrupt/cancel cases not reached. No final capability PASS. Existing Linux
causal comparison showed legacy output rotate metadata emits no matrix while explicit
input display_rotation emits matrix+90summary. Harness switches to official input
option, keeps original assertion and records typed facts; no app normalization change.
Primary option reference: https://ffmpeg.org/pipermail/ffmpeg-user/2024-July/058428.html .

### Actual pinned Windows gate 41320954332 — independently verified
Public31ecf1c2/tree72d11bca, Windows3.12.10/3.13.16: both SUCCESS, all five native
synthetic groups pass with exact BtbN8.1.3 archive and ten member pins. Independent
API/2ZIP/4member/source/runtime verification. Thirteen sentinel cases per target
carry forward from41320537260 unchanged, not rerun. Earlier whole-gate failures remain.
No GPU/renderer/full-codec/redistribution/GUI-pair result acceptance; TOL-03.01 still
requires its exact GUI binding. Ledger9/438 unchanged.

### Settings executable inventory UI — local P03-08
Metadata-only explicit scan off GUI thread, actual candidates/reasons and unknown
version/capabilities, invalid explicit path no fallback, no startup scan or execution.
Six new local Qt cases: initial5PASS1FAIL was an empty-queue cancel fixture assumption;
adding a queued candidate makes the actual cancellation boundary meaningful, exact
corrected casePASS. No production cancellation predicate weakened. Typed path inputs
remain session-only; no persistent resolver/activation/installer claim.
Additional bounded-display casePASS; seven distinct new cases now locally verified.
Affected shared UI25casesPASS/exit0 after shell integration. Independent source and
workflow CLEAR; target profile covers six test files/32cases, not the full aggregate.

### Explicit pair Settings self-test — subsequent local slice, publication separate
Composed existing retirement scopes2+2+1, explicit trust for both paths/companions,
fixed own encoded MPEG4 fixture, no automatic tool selection/install/activation.
Ten new focused source/Qt cases PASS; initial6FAIL2PASS came from Linux venv Python
symlink test input rejected by existing regular-file policy; corrected tests select
resolved real Python without weakening product checks. Affected existing pair13PASS.
Actual existing Linux FFmpeg7.1.5 through new Qt path returned5POSIX retirement proofs,
exact selected hashes and fixture SHA; source-pinned receipt records pre-decode-size
hardening delta separately. No actual Windows paired GUI claim yet. Prior inventory
378ae98 publication remains held independently; these source edits are not added to it.
Shared Settings/shell/recovery/inspection32cases PASS/exit0 after paired-tab integration.
Prepared future native GUI gate uses a Unicode/spaced owned root and exact unchanged
candidate pin; no Windows GUI-pair run has been triggered. Review pending slot.
Independent paired source/workflow CLEAR at frozen manifest; exact combined markers
are documented. Three causal negatives independently PASS, no actual tool rerun.
Actual Windows GUI-pair/TOL03.01 remains pending; prior denied inventory payload
stays independently frozen and is not bypassed by this later local checkpoint.

## Selected Settings pair and inventory — hosted checkpoint72eb57d6

Independent API/artifact review confirms four source/Qt targets55PASS0SKIP each in
41324375838 and two actual Windows selected-pair GUI targets in41324375928, each
positive fixed synthetic pair plus swapped-role refusal (5+1 owned retirement
proofs). Exact source tree1e4dcae6, runtime versions and all six ZIP/twelve member
hashes are retained under docs/evidence/p03/hosted-* and the paired hosted review.
No aggregate/frozen/old native-five-group rerun. Accepted precise children:
TOL-03.01, TOL-02.01, TOL-01.03. Global12/438; P03-mapped11/78; tasks0/9. The last
child maps P01/P04, not P03. No startup scan/registry/install/GPU/fullcodec claim.

## Durable explicit tool preferences — local implementation, native pending

New separate owned SQLite preference snapshot with original identity/receipt/schema,
CAS and conservative unknown-write reconciliation; Settings explicit read/save
worker, stale edits preserved and no execution/trust/activation persistence.
Initial17storage cases:12PASS/5FAIL (SQLite substr of empty BLOB yielded NULL, so
empty path readback rejected); strict type-preserving coalesce correction followed
by only affected5PASS. Added interruption/pre-COMMIT/schema cases3PASS. Five new Qt
preference cases plus seven affected inventory cases12PASS, clean process exit0.
No actual tools run, no native/full aggregate rerun or child closure for this slice.

Independent review found a post-COMMIT competing writer could be returned as the original save result. Exact intended value/version/token readback now required; divergence is UNKNOWN, never another writer falsely labelled as own. New causal case1PASS, independently repeated1PASS only. Source/workflow CLEAR in P03_TOOL_PREFERENCES_LOCAL_REVIEW.md. Scoped next marker [tool-preferences] alone: four targets/eight affected files58cases, no candidate execution/aggregate/frozen.

## Preference target evidence and next first-navigation slice

Preference run41325878717 independently verified fourSUCCESS at publicd174a247,
treef0dd567c, each58PASS0SKIP; exact Windows3.12.10/3.13.16 and
Linux3.12.15/3.13.17. Four ZIP digests/eight source+JUnit members match;26preference
and32shared cases actually passed. No new child acceptance; ledger12 unchanged.

Next SB-L032 first Settings navigation chains one background preference read into
bounded metadata scan, once per panel. Missing defaults create no files; corrupt
preferences refuse without fallback; no automatic executable launch or trust.
Six new/changed Qt causal tests PASS, plus3affected all-area shell cases PASS,
clean exits. Independent reviewer selected3corrupt/stale-edit/queued-cancel cases
PASS. Queued-gap test proves cancel supersession specifically; do not relabel it
as separate explicit-Load/Save/close injections. Close during load has its own case.
Source/workflow CLEAR in P03_FIRST_SETTINGS_SCAN_LOCAL_REVIEW.md. Next scoped
[tool-first-open] alone runs fourtargets/eightfiles42cases; no unchanged storage,
FFmpeg download/execution, frozen build or full aggregate rerun.

First-navigation target checkpoint b7dd8bea/tree538231c1: run41326388409 four
SUCCESS, each42PASS0SKIP independently verified with fourZIP API/local digests and
eight exact source/JUnit members. Windows3.12.10/3.13.17, Linux3.12.15/3.13.17.
All six first-open/changed navigation cases ran. No new child closure inferred from
42cases alone; scanner-specific prior bounds evidence is separately assessed.

## Blank-project creation foundation — local source independently reviewed

Pure empty-plan factory plus existing exclusive writer/readback and authoritative
session activation; explicit modeless form, no demo assets or simulated renderer.
Core8casesPASS. Initial four Qt cases3PASS/1FAIL: dialog close after confirmed write
could still activate because finished QThread interruption state cleared. Added an
explicit per-attempt UI cancel latch; affected case1PASS cleanexit0, preserving the
created file without activation. Prior3PASS unchanged. Shared all-area shell3PASS
was before the form moved to a modeless dialog; do not claim that earlier pass proves
the final dialog layout. Target shared-shell coverage remains in next scoped batch.

Creation final source/workflow independently CLEAR; reviewer selected3causal cases
PASS. Added NUL destination preflight in core/UI (known invalid, no writer/worker or
UNKNOWN panel lock),2newcasesPASS; final target scope56cases. Initial failures stay
recorded. TOL-01.02 independently accepted with exact unchanged-source historical
carryforward plus current first-navigation GUI; root concurrence13/438, P03still11/78.
No creation criterion or whole task is accepted.

New-project target run41328128912 independently VERIFIED at publicfa3675f6,
treeaff45856: fourSUCCESS, each56PASS0SKIP, including real empty-project write/open/
Save and cancellation/unknown/stale-session cases. Windows3.12.10/3.13.16,
Linux3.12.15/3.13.17; fourZIP API/local digests/eight member bytes verified. No
renderer/editor/full autosave/crash criterion closure; ledger13 unchanged.

## Unresolved media library persistence — local coherent batch

P03-02/03/07 only: independent stable UUIDs/content references and typed unresolved
observations persist in explicit project envelope v2, while v1 remains byte-compatible.
Completed library additions use existing project revision CAS; duplicate exact content
is a no-op, conflicting identity/facts refuse. Save/autosave/recovery/same-content and
root relink preserve v2 library and library-only relative origins. Current composition
readiness and source ownership are not inferred from library facts. No P04 UI added.

Author focused evidence: initial26newcasesPASS;62affected existing storage/autosave/
creation/origin casesPASS. Additional streaming-bound1PASS; real owned-v1 migration
backup containing v2 document→restore→reopen1PASS (initial fixture lacked receipt and
correctly failed; fixed fixture, no relaxed ownership). Six additional mixed legacy/
library relink and strict array/path casesPASS. Reviewer found two causal bugs:
v2→v1 completed command could erase library; duplicate SHA early-return could hide
another existing UUID. Fixed no-downgrade at session/direct DB/existing-file boundaries
and precheck all UUID collisions before SHA no-op. Two ID-order regressionsPASS;
combined session/DB/file/explicit-empty-v2 testPASS after correcting its initially
missing persisted-row fixture. Original failing observations are not counted asPASS.

[media-library] ALONE scopes next CI to four targets/13 affected files/165collected
cases, with Qt recovery/relink/creation plus actual process-kill persistence tests.
No unchanged FFmpeg, frozen bundle or unrelated aggregate rerun. Native result is
PENDING, not inferred from local checks.13/438 and P03 11/78 remain unchanged.
Independent final source review CLEAR: prior4selected cases and exact3correction
instancesPASS, no repeated baseline. Workflow fe4191f9 reviewed for165-case scope.

 
## Unified development branch — desktop coordinator integration (2026-11-02)
The pre-code master and exact P03 plan were reviewed at the existing clean P03
checkpoint. Commit on `develop/fonesi-full` introduces an opt-in, long-lived
Qt coordinator host for a read-only-verified existing jobs store. The worker
thread owns its SQLite repository, native coordinator lock/epoch and bounded
command inbox; the GUI handles only selected typed command requests and durable
read-only refresh. Shutdown requests interruption and waits for owner release,
never QThread.terminate or automatic command replay. An unavailable owner leaves
the queue read-only. This is a queue-control integration, NOT scheduler, worker
execution, render, provider, or P03 acceptance.

Verification: focused source/Qt tests and complete Linux/Windows CI at the exact
code commit are PENDING. A past CI pass from phase-03 or an archived generation
does not verify this change. Accepted runtime criteria remain 13/438 and P03
whole-task acceptance remains 0/9 until separately reviewed evidence.

 
### Desktop coordinator native CI and refusal follow-up
Initial unified-branch source commit 2d85a971 reached actual Linux/Windows CI
run 41480333908: Ubuntu 796PASS/39SKIP for Python3.12 and Python3.13;
Windows 809PASS/26SKIP on each; Windows3.12 frozen CLI five checks PASS.
These are exact source/hosted synthetic and scoped frozen checks, NOT physical
Windows GUI/media/product acceptance. A subsequent review identified a Qt
refusal-vs-finished retry window, addressed with a delayed-refusal regression.
That delta's exact CI remains pending; 13/438 child and 0/9 P03 whole tasks
remain accepted until separately reviewed evidence.
