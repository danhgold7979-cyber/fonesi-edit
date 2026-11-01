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
