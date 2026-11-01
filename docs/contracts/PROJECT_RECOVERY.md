# Project session recovery — bounded P03-07 local slice

`storage.autosave.prepare_open(store, path)` returns a read-only `RecoveryOffer`.
The caller must choose `file`, `recovery`, or `cancel`; it must not treat a differing
observation as automatically newer/better. Cancel performs no further I/O and
changes neither file, store nor active model. Other choices re-read the file digest
and exact saved observation/version, refusing stale choices. The caller replaces its
active session only after a successful choice. An invalid/newer file never replaces
the current model. SQLite observations are durable completed-command snapshots,
not proof that any renderer or media exists.

`CompletedCommand(Project, expected_revision)` is submitted only after an editor
command is complete, never a transient drag/preview. Identity must remain unchanged
and composition revision must advance exactly once. `ProjectSession.commit` reuses
`ProjectStore.save` CAS and changes its authoritative in-memory model only after
confirmed commit. Stale memory revisions or DB versions refuse. Opening/choosing a
file does not itself overwrite an existing differing autosave.

`session.save()` uses the reviewed matched-digest file replacement/backup protocol;
Save As uses the reviewed new-file no-replace protocol and cannot overwrite an
unobserved target, even one with identical bytes. A read-only DB observation check
refuses already-stale sessions before file saving. This is NOT a cross-resource
SQLite/filesystem transaction: another editor can commit after this check; its
newer autosave remains intact and is offered on subsequent open. File writer safety
is the existing cooperating-writer lock/digest contract, not protection against
malicious same-user namespace races.

A failure after attempting a write may mean COMMIT/publication succeeded despite
failure to return. Such errors latch `reconciliation_required`; the old authoritative
model is preserved for failed command commits, and all subsequent session writes
refuse. No automatic write/command replay occurs. Inspect persisted state and make
an explicit fresh recovery/open choice (and reopen a failed connection if necessary).
A known repository/digest CAS refusal is not labelled unknown. Existing storage
fault/crash evidence remains attached to those implementations; these tests add
session-level unknown-return coverage, not a new power-loss guarantee.

## Relative paths and remaining dependency

Normal sessions keep the opened file's parent as their project-relative base.
Saving to a different parent with any project-relative asset/font refuses before
creating that directory; same-parent rename remains usable. The owned projects DB
v2 retains optional `origin_base` atomically with each completed-command observation,
not inside exported Project JSON. Version1 migration validates exact schema/receipt,
backs up through SQLite and validates the backup, then adds the nullable field in a
transaction. Old rows remain NULL: no inferred base or automatic legacy adoption.

Choosing recovery resolves relative asset/font execution paths against a known saved
origin, never against the newly selected project file's directory. This preserves
render-content digest but changes the execution snapshot. The saved base does not
prove files still exist or match hashes; rendering must revalidate them. If a legacy
observation's origin is unknown, recovery still raises `RelinkRequired`. A matching
project document with a different known base also triggers explicit choice. No claim
of newest-state ordering or a cross-resource transaction is introduced.

`storage.relink.relink` returns a completed typed command for one existing asset/font
ID only after the explicitly selected regular candidate matches its full SHA256.
It reuses the cancellation/growth-aware fingerprint helper, changes only execution
path plus revision, and preserves probe, stream and timing semantics. Different bytes
require future explicit replacement/re-import, never silent relink. The candidate is
not modified; no DB/model mutation occurs until the caller explicitly commits through
the session. Files may change after observation, so renderer admission must revalidate.
The caller is responsible for background execution and cancellation UI; this helper
makes no hard OS I/O deadline, full media validation or permanent ownership claim.

## Scope / gates

The core session contains no timer, GUI dialog, editor undo stack, media relinker,
cache eviction or filesystem watcher. Shell integration is described below.
The owner calls this single-thread session using the same
thread as its SQLite connection. It owns store lifetime; session does not close it.
Relink picker/background execution, unknown-origin mapping, cache fingerprint/version
invalidation, Windows and abnormal-close end-to-end session tests remain OPEN.
No P03 task or additional requirement assertion is accepted by this local slice.

Targeted command: `.venv/bin/pytest -q tests/test_autosave.py`. Tests use disposable
fixture projects/SQLite stores only, including recovery cancellation, stale offers,
command/DB CAS, Save As refusal, relative-base refusal, and uncertain write returns.

Historical inherited boundary at b183d54: `ProjectStore` could initialize an existing
unmarked empty/v0 SQLite file and register its receipt after WAL setup. The subsequent
local hardening section below supersedes that constructor behavior. Callers
must provide an app-created project store; do not expose arbitrary existing DB paths
as safe imports. Tests exclusively create disposable new store paths. Hardening that
constructor is a separate existing-source change, not a guarantee inferred from the session.

## Shell integration

The Overview page now opens this actual session and shows an explicit three-way
file/local-recovery/cancel dialog only for differing observations. Cancel is the
safe default/escape action; no observation is labeled newer without evidence.
Choosing recovery does not immediately overwrite the file. The separate Save button
uses the session's digest/backup contract. Failed opens/relative-base recovery keep
the prior shared model; a stale save keeps the external file and current model.
An unknown save disables the button, preserves the model and asks for explicit
inspection/reopening rather than retry. There is still no editor emitting completed
commands, timer autosave, relink picker or background I/O guarantee in this shell.

## ProjectStore ownership hardening (subsequent local dependency fix)

The earlier inherited constructor limitation above is addressed by the current local
ProjectStore delta: only exclusive new-file creation may initialize version0. An
existing database needs the exact existing app ownership receipt before SQLite is
opened; no implicit legacy/unmarked import. A newer header is rejected read-only.
Foreign/invalid receipts and unmarked empty files remain unchanged. Failed initial
creation may leave an unmarked file requiring explicit recovery; reopening is not an
adoption shortcut. No automatic migration-backup restore is claimed.

A retained original descriptor and continuity checks surround connection opening,
transactions and reads. Identity loss permanently revokes the instance; restoring
the path cannot revive it. Current exact versioned SQL tables and absence of unexpected
triggers/views/indexes are checked before WAL configuration. Existing valid receipt
hashes remain compatible. This uses the existing account/jobs ownership pattern,
not a new dependency or OS-security bypass. It assumes a cooperating private app
namespace, not protection against a malicious same-user timed ABA swap. A COMMIT
error is never replayed or hidden behind an unconditional invalid ROLLBACK.

Recovery additionally refuses project-relative references containing NUL, absolute
paths or Windows drive/root-qualified syntax; joining must not silently discard the
saved base. This is a recovery-boundary guard, not a claim that every CompositionPlan
path form is already validated by the cross-platform schema.

## Root-folder workflow

`relink_root` consumes separate explicit original media root, new media root and known
project base. Relative references resolve against the project base, not an arbitrary
chosen media subfolder. Only references under the original root are mapped; external
references remain unchanged. All mapped candidate hashes must match before one typed
command is returned. Missing/mismatching/canceled verification never applies a partial
command. Progress reports actual verified reference counts, not fabricated render
progress. Parent-directory links and OS file I/O are not a network-isolation/deadline
boundary; sources must be revalidated by eventual renderer admission.

The Overview relink panel asks for the old absolute root and a new directory, then
hashes on an owned QThread. SQLite/session commit occurs on the GUI owner thread only
for the captured still-current session/revision. Open/Save are unavailable during
verification; stale dialog/session results are discarded. Cancel has a separate GUI
latch because Qt's worker interruption flag alone may no longer be set once a finished
thread's queued result is delivered. Cancel/close before commit discards late results;
it does not undo a commit that already occurred. Unknown commit remains reconciliation
required. Close waits for both queue and relink retirement, without forced termination.

Root picker, actual hashing, autosave and explicit Save are exercised locally; Windows
GUI/filesystem behavior, full editor/timer autosave, automatic latest recovery/cache,
media replacement/reprobe and full phase acceptance remain OPEN.
