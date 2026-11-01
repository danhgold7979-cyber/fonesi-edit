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
