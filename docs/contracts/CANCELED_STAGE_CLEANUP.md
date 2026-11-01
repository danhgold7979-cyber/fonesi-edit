# P03-06 canceled owned stages (local source, native integration pending)

Scope: canceled synchronous PublicationSession staging only. Not failure retry,
expired/restarted recovery, download/browser caches or future external renderer
workspaces. Source/final paths are never deletion targets. No POSIX path unlink.

## Ownership before a write can fail

Exclusive O_CREAT|O_EXCL creates the payload. Immediately duplicate/retain that
original descriptor before invoking any producer/cancel callback. Record a separate
frozen StageOwnership (original root/directory/file identities) in that Destination;
it is NOT StageReceipt, has no validation hash, and cannot authorize publication.
Original Windows stage-directory handle is already retained from creation. Every
attempted stage name is tracked. If creation fails before ownership capture, the
attempt/record mismatch returns UNKNOWN and retains the directory, never falsely
reports no temporary files. A reconstructed value is not the live creation record.

## Lifecycle and authority

An internal staging-operation latch spans parsing/copying/validation, unwinding
writers and owned process retirement. Both cleanup methods refuse while it is set,
without closing a live writer's session. A validator exception permanently latches
quiescence UNKNOWN: current validator exceptions carry no typed descendant-retirement
proof, so even an acknowledged DB cancellation cannot authorize either cleanup or
resume/claim. Conservatively this also retains stages after otherwise ordinary
validator failures/cancellation until typed lifecycle evidence exists. No caller
boolean grants quiescence.

Canceled cleanup requires the current same-snapshot/same-attempt acknowledged
`canceled` job, cancel_requested=true, cleared worker lease and newer version;
current coordinator OS lock/DB incarnation/epoch; never claimed/linked outputs.
Prepared journal rows, if any, must exactly match this live session's original
manifest/validation/receipt and remain prepared/version1 with its owner epoch.
No artifact or completion-history row may exist. Unexpected/uncertain prepare
commit is refused, not adopted. Failed/expired/publishing jobs are not canceled.

Inventory is only this Destination's original exclusive-created records, not a
filesystem scan. If no creation was attempted, cleanup safely returns0 on any OS.
Otherwise Windows passes continuous original file and directory handles into the
already native-tested DeleteCapability; before each disposition it rechecks live
canceled-job/journal authority. No validation/content hash is required to delete
one's OWN unvalidated temp, but physical original ownership is mandatory. Foreign
replacement/extra child is refused/preserved. Any entered-maintenance failure is
UNKNOWN and session permanently retired; no destructive replay or DB success/state
mutation. Prepared rows remain audit evidence with canceled job, never resumable
as published artifacts. Unsupported POSIX retains existing stages.

## Affected evidence

New local source tests prove interrupted producer/copy retains original FD, invalid
ownership cannot publish, active staging blocks cleanup, postflush cancel exits
operation, noncanceled/publishing attempts refuse, no-stage no-op, failed anchor
capture UNKNOWN and reconstructed record refusal. A test fixture initially had
media output geometry inconsistent with CompositionPlan; corrected fixture only,
then interrupted-copy case PASS. Existing postflush-cancel test now observes actual
writer return, not the old assumption that an anchor appears only after flush.

Actual Windows canceled cleanup remains NOT_RUN for this delta: exact prepared/
unprepared set, postwrite partial ownership, interrupted copy, foreign child and
handoff replacement, authority loss at native effect. Previous completed-cleanup
run41303347554 proves only its earlier sequence. `[cancel-cleanup]` alone selects
four targets and28 affected cases, omitting unchanged aggregate/frozen/Qt installs.
No new child/task acceptance until exact required conjunction is reviewed.
