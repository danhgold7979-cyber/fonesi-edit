# Windows object-bound cleanup prototype — P03-06, not production cleanup

This is a bounded stdlib ctypes wrapper over maintained Windows APIs, not copied
third-party GitHub code or an installed dependency. Primary contracts:
- https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
- https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfileinformationbyhandle
- https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_disposition_info

The old POSIX stat/unlink prototype was rejected and removed. This prototype does
not call unlink/rmdir/DeleteFile by pathname, does not change ACLs/privileges or
ignore readonly attributes, and has no fallback on unsupported targets/filesystems.
It is NOT called by PublicationSession or normal UI/CLI. Current user-visible cleanup
still retains staging. Native tests are a prerequisite, not whole cleanup acceptance.

## Capability chain

Trusted coordinator supplies an original live object descriptor and expected parent
identity, never a receipt reconstructed after restart. Pin the parent/ancestors with
the existing Destination capability. Open a metadata bridge with read/write/delete
sharing, OPEN_EXISTING and OPEN_REPARSE_POINT (BACKUP_SEMANTICS for directory).
Check type/reparse/identity against original before releasing original. The bridge
keeps the physical object alive throughout the transition, not a filename lock.

Acquire a new handle to the named object with DELETE plus GENERIC_READ (file) or
READ_ATTRIBUTES (directory), sharing READ only. This excludes new writers and
rename/delete operations while compatible handles exist. Check its identity against
the continuously live bridge and named path, and recheck pinned parent. Sharing
conflict/identity mismatch/unsupported filesystem fails closed with no disposition.
No authority is granted by matching hash or a recycled persistent inode.

Mark uses FileDispositionInfo4 with one-byte BOOLEAN, after rechecking current
name/handle/parent and the caller's live-authority callback. Attempt is consumed
BEFORE any guard/callback; failures cannot be silently retried with restored authority.
Only explicit native disposition applies deletion to the acquired object. Target
then bridge descriptors close once (native HANDLE ownership transferred exactly once
to CRT descriptor). Close uncertainty is not retried. Actual link removal is not
inferred from a successful mark return; native tests must confirm final hardlink
identity/bytes survive and only staged link disappears after retirement.

## Integration still required

Caller must prove exact committed required-set/history/current coordinator epoch,
no writer/validator/owned descendants, and final same-object hash immediately before
effect. Future integration must read/hash through the acquired deny-write handle
rather than reopening via incompatible CRT sharing. Directory deletion must be
object-bound and fail on foreign children; no recursive cleanup. Any partial file
mark/close/directory mark/observation failure retires the session with uncertainty,
never changes completed history to canceled or retries an unknown destructive effect.

Prototype native tests cover file/directory handoff replacement, final hardlink
preservation, empty/nonempty/late-child directory cases, authority loss and replay
refusal, conflicting DELETE handle, unmarked close, and warm20-cycle handle plateau.
These tests use exclusively owned temporary fixtures. Linux unsupported-branch and
control-flow tests are not Windows evidence. Parent/path identity is not proof against
an arbitrarily compromised OS; no power-loss durability claim is made.

## Native primitive evidence — 2026-11-01

Run41301972313, public sourceccfa0b1de7b6929c9909b0dc1b498b65ef5b00f1,
tree94399c9697a0c9613a197faa9cd6cd196f66837a, Windows Server2025:
Python3.12.10/SQLite3.49.1 and Python3.13.16/SQLite3.50.4 each10PASS/1SKIP.
The sole skip is the inapplicable non-Windows refusal case. Actual cases verify
only the staged hardlink disappears while final bytes/identity survive; file and
directory handoff replacements preserve foreign objects; late foreign child blocks
empty-directory deletion; authority loss consumes the one-shot operation; conflicting
DELETE sharing fails without unlink; unmarked close preserves; handle counts plateau.
Both artifact ZIP API digests and four extracted source/JUnit member hashes checked:
`docs/evidence/p03/hosted-41301972313/summary.json`.

This closes the narrow primitive target-test gate only. Production journal/required
set/final-hash/worker-quiescence integration remains absent; no full cleanup/task
acceptance. It is not arbitrary filesystem support, power-loss or restart adoption
proof. POSIX still retains staging with no unsafe pathname deletion fallback.

## Local completed-publication integration prototype (native integration pending)

`PublicationSession.cleanup_completed()` now has a local one-shot integration,
not yet target-verified. It admits only this session's exact succeeded job,
all-required committed member/artifact set and completion history under current
coordinator epoch. Its staging APIs are synchronous: their writers close and owned
validator process trees retire before a role enters `_staged`. No external output
producer or caller-supplied quiescence boolean is accepted. Future asynchronous
workers must preserve this lifecycle boundary, not bypass it with a flag.

Original Windows stage-directory handles are retained starting at creation, not
reopened from persisted inode identity. Stage-file anchors become close-once owners
so bridge transfer cannot leave a raw callback that later closes a recycled FD.
Cleanup reads/hash-checks via the acquired file DELETE/GENERIC_READ capability,
checks final name against original physical identity, then retains a compatible
final read bridge across staged-handle close. A strong final read pin denying
write/delete is acquired against the continuously live bridge before the original
stage directory's object-bound empty-directory disposition. Authority/history is
rechecked at both effects and after slow readback. No pathname deletion exists.

**Critical native integration gate:** holding a final hardlink bridge across classic
FileDispositionInfo/close may interact with Windows delete-pending semantics. The
primitive test did NOT prove that extra-handle sequence. The new target integration
must prove actual staged-link removal/final pin acquisition, or fail closed/retain;
no silent fallback or assertion that the prior primitive PASS proves it.

Any failure/partial close/disposition always retires the session; no replay, no
history rollback, no final-file deletion. Unsupported POSIX retains staging. No
restart recovery/adoption is added. New target negatives include missing history,
stale epoch, unfinished set, changed final bytes, foreign child, authority loss
after hash, and failure after payload disposition before directory cleanup.
