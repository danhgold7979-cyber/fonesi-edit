# Project migration backup restoration — P03-02 / P03-07

An explicit restore copies a selected offline rollback-format project SQLite backup
into a NEW exclusive destination. It never replaces the active store, opens source
via SQLite, recovers a live source journal, deletes any path, or automatically retries.
User chooses an absolute source and new target in an existing local directory.
Target DB/receipt/sidecars must not exist. Sidecar/ownership suffixes are not valid
output database names. A backup import is explicit user intent, not inferred trust
from a filename/app ID; only validated project data becomes a fresh owned store.

Original source FD and pinned destination directory/file remain live. Source is
regular/nonreparse, known app/schema v1/v2, rollback-header only; reject WAL/SHM/
journal sidecars before and after copy. Reads are bounded by opened size+1, chunks
1MiB, with cancellation/deadline checks between operations (not OS-I/O preemption).
Per-API metadata baselines avoid Windows stat/fstat timestamp precision mismatch.
Hash source/copy, check identities and no sidecars, then read-only validate COPIED
unmarked target: exact known schema/no extra objects, quick_check, streamed bounded
Project envelopes, row ID/name/version/time and origin consistency. No fetchall.

Register ownership last after final checks; v1 origin remains unknown, never backup
folder/cwd. Restored bytes remain the original backup schema; normal current
ProjectStore can subsequently load/migrate this fresh owned copy. Original live
store and backup stay untouched. Registration/close failure is UNKNOWN, not false
success. Other failures retain an unmarked partial new target for explicit review;
no unsafe pathname cleanup. Partial files are never adopted automatically.

Threat boundary: explicit offline source and private/cooperating new destination
namespace; guards/hashes observe accidental change, not hostile same-user timed
swap-and-restore attacks. No concurrent source journal-mode switching or opening
new target by another app until completion. Source is never written by this API.
Full latest-state selection, UI store switching, in-place replacement and arbitrary
future DB formats remain separate requirements, not inferred from this copy gate.

## Headless user entry point

```
fonesi-edit --restore-project-store /absolute/offline/projects.sqlite3.backup-ID --restore-destination /absolute/new-folder/projects.sqlite3
```

The destination directory must already exist and be private/cooperating. On Windows use absolute drive paths. `--restore-timeout` is a cooperative deadline, not an OS-I/O kill guarantee. The restore mode rejects unrelated GUI/media options and imports no Qt. Exit 0 means the new copy and ownership registration were confirmed; exit 2 is not permission to replay. Inspect retained destination/receipt separately after failure. This command neither switches a running GUI store nor chooses a newest backup. A subsequent normal launch with `--data-dir /absolute/new-folder` opens/migrates the restored copy; v1 origin remains unknown rather than inferred from backup location.

Metadata is read as bounded BLOB projections with original SQLite text-type gates,
then strict UTF-8 decoded and compared in full. This avoids SQLite TEXT substr's
embedded-NUL truncation. Existing supported UUID spellings and matching full project
names are preserved; invalid origin/ID or inconsistent row/document names refuse.
Current-schema backup snapshots made from WAL-mode stores may retain WAL headers;
those are intentionally refused here, even without sidecars. The proven unmodified
migration backup path is rollback-format v1. A separately prepared offline
rollback-format v2 copy preserves its explicit origin; this is not WAL recovery.

## Overview GUI entry (new local slice)
The explicit picker selects an offline backup and an existing destination directory;
output is always that directory's NEW `projects.sqlite3`. It never switches the
active store/session. A dedicated QThread owns restore I/O/SQLite; no existing GUI
connection crosses threads. Copied-byte signals are throttled to10Hz plus final
copy observation and labelled as copying, not successful validation. Cancel/close
requests interruption and keeps the window alive until the worker actually retires.
Only the final worker outcome after wait-success determines confirmed/unknown;
a late cancellation never erases confirmed creation. Partial/uncertain files are
retained with explicit no-retry/no-delete guidance. Source/current-store unchanged
claims concern this restore operation, not independent concurrent user edits.
Old-worker progress/completion cannot retarget a newer operation. Selecting a
folder that already contains the DB/receipt/sidecars fails closed. GUI does not
choose a newest backup, recover WAL, or automatically launch another app instance.
