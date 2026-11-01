# Bounded tool candidate discovery — partial P03-08

`dependencies.discovery.discover_tools` reads named executable candidates only:
ffmpeg, ffprobe, yt-dlp, gallery-dl and Chrome. It does not recursively enumerate drives,
run a candidate, inspect browser profiles, download/install/update/delete anything,
modify PATH or create application data. Other dependency types remain in original
requirements and P02 decision gates; this executable slice does not remove them.

Inputs are explicit configured paths and bounded managed/bundled/system/extra root
lists. Source is a search-location label, NOT evidence of ownership, publisher trust
or license. User-selected invalid paths return INVALID_EXPLICIT_PATH and never silently
fall back, even if another candidate exists. Auto preference lists managed, bundled,
system, extra in order, retaining declared-root/PATH order within a class. Every
candidate remains UNCHECKED; selection NEEDS_CHECK is not a runnable resolver grant.
The future verified registry must check exact binary identity/version/capabilities,
functional operation and pair compatibility, then hold the resolved version lease.

Stat metadata includes path, physical identity when available, size/time and a leaf
symlink/reparse flag. These observations can become stale immediately. They are not
persistent incarnation proof and cannot authorize deletion or execution. Parent links
or network-mounted paths are not isolated by metadata checks. No hard OS I/O deadline
is claimed: cancellation/time observation is checked between bounded stat operations.
Permission/other filesystem errors produce PARTIAL_ERRORS, not a false complete-missing
result. Entry/time limits and cancellation return partial status. Oversized PATH root
lists refuse rather than silently truncate; relative/empty PATH entries never add cwd.

Headless `--scan-tools [--tool-path TOOL=ABSOLUTE_PATH] [--tool-dir ABSOLUTE_DIR]`
prints actual JSON metadata without importing Qt or initializing SQLite. It reads PATH
and, on Windows, named common Chrome executable directories only. Exit0 means complete
candidate enumeration, NOT all tools ready; partial enumeration exits3, invalid input
exits2. Explicit invalid selection is represented in JSON even when enumeration is
complete. No tool functional checks, signature/manifests, managed ownership, leases,
persistent registry, automatic UI scan or installation acceptance are implied.

Reuse: Python standard-library pathlib/os/stat/dataclasses; no new dependency/package
or unknown-source execution. Target tests use owned temporary sentinel files, not
claims that those bytes are actual media tools. Actual Windows path/Chrome/runtime
behavior remains a target gate. No credential/profile content is accessed.

## Explicit pinned pair functional observation (subsequent local slice)

`dependencies.checks.check_pair` requires caller-authorized exact ToolPins and an
explicit known-hash fixture with exact expected streams. A SHA256 supplied by an
untrusted project/candidate is not authorization or publisher provenance. The controller
must establish trust/consent before calling; discovery never invokes this function.
Both executable pins and the fixture are checked before any launch; there is no path
fallback. Regular non-reparse tool files are capped at1GiB, fixture at32MiB. Calls use
the reviewed owned-process adapter, bounded capture and a per-process timeout (at most
five processes), with cancellation-aware fingerprints. This is not a hard OS I/O limit.

Matching reported version/library tuples is required by this initial conservative
check; mismatch means compatibility UNVERIFIED, not a universal incompatibility claim.
Reused probe/full-decode validation checks the chosen fixture, then one black16×16 RGB
frame is generated to bounded stdout and compared exactly. No temporary output file,
source write, installer or cleanup operation is introduced. Tool hashes are rechecked
between stages and at return. An observation does not pin future execution, authenticate
all dynamic libraries, establish Windows/GPU/subtitle coverage or replace version leases.
No arbitrary tool stderr is exposed in errors; no automatic process/mutation retry.

`PairObservation` names only the exact known fixture/streams and raw-frame scope, plus
reported versions, response hashes, executable pins and observation time. It is not
READY for every workflow. Actual local evidence reuses the already approved Linux
FFmpeg/ffprobe7.1.5 and retained synthetic H264 fixture; no new binary acquisition,
fixture generation or unchanged corrupt-input baseline rerun. Windows and packaged
self-test fixture/trust-controller integration remain OPEN.

Current-check prerequisite: the caller must hold/use a trusted stable tool namespace
while checking. Hashing paths before/after launches observes drift; it is not atomic
execution identity and cannot exclude swap-and-restore between those observations.
This limitation applies during this check, not only to future jobs. No observation
from a concurrently mutable/untrusted tool directory should authorize a workflow.

## Settings inventory UI (P03-08, metadata only)
Settings now exposes the existing five-executable bounded scanner on explicit click,
not on startup/navigation. All configured paths/search roots are captured by an owned
QThread; filesystem reads and PATH parsing stay off the GUI thread. No binary starts,
no installer/activation/PATH/config/database mutation. Empty tools do not block opening
Settings. Trial path inputs are session-only, explicitly not persistent configuration.
Each tool shows static role, observed selected candidate/source, time and exact reason;
version/architecture stay unknown, even when a filename exists. All candidates remain
UNCHECKED; source class is not ownership/trust. Invalid explicit path never falls back.
Font/runtime/model inventory and executable functional-check routing are still open.

Cancel/close requests interruption and waits for worker.wait(0); no force termination
or hard OS-I/O deadline claim. Partial/limited/error results remain labelled; complete
empty scan is genuinely complete even if a cancellation arrives after no work remains.
Captured revision and worker identity discard stale results after input changes. Five
selected paths remain available in the table; supplemental list renders at most64
candidates with512-character path previews, explicitly labelled as abbreviated.
No readiness/installation or pair capability may be inferred from this metadata UI.

## Explicit Settings paired self-test (subsequent local slice)
The separate self-test tab does not consume discovery selections automatically.
Both absolute paths require explicit trust confirmation covering companion DLLs;
changing either clears that consent and invalidates prior displayed observations.
Worker hashes BOTH regular bounded executables before either launches, then existing
check_pair verifies pins/versions, own fixed synthetic media probe/full decode, and
black16×16 output. Existing stable trusted tool-directory prerequisite still applies;
EXE hashes are not signature/full companion binding or protection against timed swaps.
No downloaded candidate is silently selected; no install/activation/config/lease occurs.

PairRetirement composes existing max2 ValidationLifecycle scopes in fixed order:
versions2, media2, frame1. Each scope is registered before delegate entry, single-use,
thread/operation-bound and sealed only after trusted-body unwind. Success requires
all five actual non-NO_PROCESS confirmations AND functional success. A known fully
retired failure/cancel permits only a fresh user action, not READY. Unentered or
unknown delegate invocation locks repeat permanently for that panel. A stale input
revision discards only capability display, never unknown-retirement safety state.
Close waits the worker and wait(0); Qt finished alone does not prove child retirement.

The2478-byte own-generated MPEG4 fixture (48×32,5fps,1s,SAR4:3,noaudio) is packaged as
bounded base64 source with exact SHA256/fixed expectations. Python tempfile.mkdtemp
creates a fresh exclusive directory beneath the controller's cooperating app-data
parent; fixture write/flush/close completes before tools read. No existing path is
adopted/overwritten, no private user media used, no pathname cleanup fallback. Tiny
fixtures remain for explicit future ownership-aware cleanup; uncertainty never causes
replay/delete. This is not a bounded-total disk retention policy or production installer.

Actual paired Qt Windows gate must bind final selected EXE hashes/fixture/result to
this source and pass a swapped-role no-fallback refusal. Python protocol stand-ins
prove lifecycle/UI behavior only. Native five-group CPU evidence is carried forward,
not rerun as GUI proof. Paired observations are timestamped historical facts, not
persisted capability registry, future tool lease, GPU, all-codec or renderer readiness.

CI marker contract for this paired checkpoint: use `[tool-pair-ui] [windows-pair-ui]`
TOGETHER and no other diagnostic markers. This selects four source/Qt targets
(55cases/eight files) plus two actual pinned Windows GUI-pair targets. Do not use
`[windows-pair-ui]` alone: it does not select the source affected-only profile.
Normal unmarked aggregate behavior is unchanged. Metadata-only inventory378ae98 is
an independently held publication payload; do not silently append this paired slice.

## Durable explicit preferences (separate store; not activation)

`dependencies.preferences` stores one bounded snapshot of five explicit executable
paths (TOOL_NAMES order), one additional nonrecursive scan root and include-system
boolean. Empty explicitly clears a path. Nonempty values must be native absolute
paths, no NUL and at most32768 UTF-8 bytes each. File existence is deliberately NOT
a save prerequisite: a missing explicitly chosen tool remains visible for repair,
never silently replaced. No trust, hashes, READY, capability, lease or credential is
stored. Existing queued snapshots and paired self-test inputs are not modified.

Settings offers explicit **Read saved configuration** and **Save paths/scope**.
Opening Settings neither reads this store nor scans/executes programs. This is not
implementation of the original first-open automatic background scan. Reads/saves
use a worker-owned SQLite connection; no connection crosses threads. Input revision
and exact worker filtering preserve newer edits. Close waits for actual worker
retirement, without a claimed hard OS I/O deadline. No automatic write retry.

Missing reads return defaults without mkdir/file/receipt creation. Save creates an
exclusive regular file only after checking orphan receipt/journal companions.
Existing unmarked/zero/future/foreign/unsupported-schema inputs are refused, not
adopted or reset. Read-only opens require original-FD rollback-header preflight
before SQLite, exact application/schema/receipt, non-reparse identity checks and a
bounded one-row projection. This assumes a cooperating private application namespace
and no concurrent external journal-mode changes; it is not a hostile same-user
filesystem sandbox. Existing rollback journals/WAL/SHM require explicit recovery;
this slice never deletes them or switches modes.

CAS binds creation-receipt token, version and complete prior snapshot, then rechecks
inside the transaction. Initialization/data commit precede ownership registration;
any failed own initialization is retained unmarked for explicit recovery, never
silently adopted. After transaction entry any failure is conservatively UNKNOWN,
including known rollback, COMMIT ambiguity, receipt/readback/close uncertainty.
Explicit reload clears a UI unknown only for the SAME known receipt token and either
exact old version/value or exact next intended version/value. A replacement store,
additional concurrent edit, or unknown first creation stays blocked in that session.
Reload is observation, never replay. Persistent startup quarantine/recovery UX,
backup/retention, Auto resolver/version leases and registry activation remain open.

Reuse decision: use Python's already pinned standard SQLite implementation and
existing clean-build receipt/physical-identity helpers; no additional package,
upstream source import, binary or dependency execution introduced.
