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
