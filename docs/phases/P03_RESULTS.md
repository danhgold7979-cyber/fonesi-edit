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
