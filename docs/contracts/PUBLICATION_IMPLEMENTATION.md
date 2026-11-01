# P03 same-DB publication implementation contract

Status: DESIGN REVIEW PENDING. Refines JOBS.md, does not replace its required scope.
Current live-anchor filesystem substrate is independently reviewed at ac4f063; it
cannot authenticate a persisted inode after restart. No job-success API is currently
implemented. This contract makes that limitation explicit rather than treating a
journal row or matching output bytes as ownership.

## Scope and trust

- A single coordinator owns the SQLite connection and filesystem Destination
  objects. Workers only return staged-work/validation events; they cannot publish or
  directly commit job/artifact/history rows. Coordinator checks fresh attempt token.
- Destination and staging are explicit local paths. Staging is exclusively created
  with mode0700 in the selected destination filesystem. Filesystem operations retain
  directory handles/dirfds and original opened staging-object anchors. No source
  path is accepted as writable staging. Do not acquire a profile or call providers.
- Imported projects/worker JSON cannot manufacture an authoritative StageReceipt or
  validation result. Coordinator constructs and retains these internal capabilities;
  durable rows serialize observations, not arbitrary authority.
- This is not a security boundary against a compromised OS/admin or malicious same
  account able to edit both the private DB and files. Ordinary destination races,
  stale workers, user deletion, unexpected replacement, symlink/reparse escape and
  foreign identical files remain mandatory negatives. Hash checking is integrity,
  not ownership. Public final paths may later be modified by their owner: expose
  missing/corrupt status on verification, never rewrite prior history silently.
- Directory fsync on POSIX is used. Current Windows implementation has no equivalent
  tested directory durability primitive, so process-crash evidence is not a promised
  power-loss guarantee. Unsupported hardlink/physical identity fails preflight.

## SQLite v2 records (same database as jobs)

`coordinator_epochs`: monotonic AUTOINCREMENT epoch PK and unique owner UUID; rows
are not deleted/reused. Epoch acquisition requires the live OS ownership lock below.

`artifact_sets`: set UUID PK; job_id UNIQUE/FK; exact snapshot_hash; attempt and lease
captured from validating job; coordinator_epoch FK; canonical immutable expected role list; state
prepared/claimed/committed/conflict; CAS version>0. Initially one set per job; retry
with a new set must be separately designed, not delete historical rows.

`publications`: publication UUID PK; set_id FK; role UNIQUE within set; explicit root
and safe final leaf reservation; canonical staging receipt; canonical validation
receipt; state prepared/claimed/committed/conflict/unknown; CAS version>0. Existing
root+leaf reservation unique. Root aliases/case must also be resolved by physical
root identity + target filesystem name semantics in admission; SQLite raw strings
alone are not a no-overwrite proof. Atomic filesystem hardlink is final authority.

`artifacts`: publication_id PK/FK; verified final physical identity; SHA256; byte size;
verification timestamp. A row means only one artifact committed, not complete job.

`completion_history`: set_id PK/FK; job_id UNIQUE/FK; exact snapshot_hash; completion
time. Inserted only with final set/job success in one transaction. No earlier
artifact commit creates history or transitions a job to succeeded.

No public mutator takes SQL fragments, arbitrary state strings, file ownership bool,
or a caller-provided `validated=True`. Closed typed receipt parsing bounds sizes,
role counts and diagnostics and rejects unknown/secret-valued keys. Exact media
validation policy (ffprobe expected streams/duration plus decode) is separate from
filesystem hashing. Small sidecar-only tests are never labelled media validation.

## Entry and migration

1. Open with existing narrow owned-DB Windows1546 startup-read helper only. A receipt
   from a known reviewed creation-schema lineage can prove DB ownership; it does not
   prove current schema. No migration/mutation/COMMIT is automatically replayed.
2. Reject future version, wrong application ID, unexpected full table signatures,
   triggers/views/custom indexes before WAL/mutation. SQL comparison preserves quoted
   literal bytes/case (exact stored CREATE statements), not lowercased whitespace
   stripping. SQLite autoindexes are allowed. Any existing receipt must match known
   lineage/header/physical identity before backup or mutation. Missing receipt on
   a nonempty versioned DB is rejected by default; explicit `adopt_unmarked=True`
   is only for a deliberate app-owned restore/import after exact schema validation,
   not automatic fallback and not permission to retry Windows1546 without ownership.
3. For exact v1, create exclusive random backup via SQLite backup API, quick_check,
   writable-fd fsync. A failure retains backup/source; no deletion by glob. DB lives
   in app-owned user-data namespace; backup names are not user-selected targets.
4. BEGIN IMMEDIATE, recheck application ID/version/signatures against captured predecessor to stop
   concurrent migration; create all v2 tables, set version2, COMMIT atomically.
   Every error rolls back if still in transaction, propagates otherwise (unknown
   commit outcome is not replayed). Restore into a new explicit destination will be
   separately implemented; never blindly overwrite the active DB.
5. Existing verified v1 ownership receipt remains unchanged as creation lineage.
   Current full v2 schema is independently validated. This avoids a crash gap between
   SQL commit and sidecar rewrite. Unknown lineage/foreign marker is rejected.
6. Earlier unpublished v2 prototype signatures/hashes are not production migration
   predecessors: fail closed if encountered, never silently adopt them.
7. Reopen validates exact v2 schema then normal WAL/FULL/foreign_keys/busy settings.
   Existing jobs retain byte-identical snapshot JSON/hash and state/lease fields.

## Enforced coordinator ownership and post-claim policy

Future `CoordinatorOwnership` acquires a separately named marked lock file adjacent
to the jobs DB using exclusive creation or strict existing-marker/regular-file/
no-reparse identity checks. Hold a nonblocking Windows byte-range lock or POSIX flock
for the whole coordinator lifetime; never unlink/replace the lock file. Every
publication operation verifies its still-open lock descriptor matches the named
physical object. On contention fail BUSY, not a timeout-based takeover. Only app-owned
private user-data namespace is supported; unrelated foreign/unmarked locks fail
closed. Interrupted marker initialization needs explicit diagnostics, not deletion.

While holding that OS lock, BEGIN IMMEDIATE inserts one coordinator_epochs row,
obtaining the next never-reused epoch and private random owner UUID. Internal
coordinator instance retains lock/epoch authority; caller-supplied UUID/epoch/boolean
alone grants nothing. Before each publication transaction verify lock continuity,
current maximum DB epoch and owner UUID. Required sets record that epoch. A second
cooperating app cannot acquire the same OS lock. Unexpected named-lock replacement
or epoch drift stops operations UNKNOWN; no silent reacquisition in the old instance.

Before claim, the worker lease must be live and matching. After claim, publication
belongs to this live coordinator epoch, not the expiring worker heartbeat. Worker
heartbeats/completions cannot mutate a publishing job; no ordinary lease-expiry retry
is allowed. Coordinator crash releases the OS lock, but loses live staging anchors.
A new owner gets a new epoch and classifies old uncommitted sets UNKNOWN; it cannot
adopt their output or manufacture old authority. A claimed set cannot be transferred
until separately proven restart/incarnation recovery exists. This separates stale
worker suppression from valid post-claim publication completion.

## Coordinator APIs and linearization

### prepare_set(job, token, expected_roles, staged_validations)

Inputs: exact immutable job record, live token, nonempty bounded unique roles and one
coordinator-owned staged validation per role. Each output filename passes safe-name
validation; each root is pinned and has no source/output overlap prohibited by scan
policy. Each staged receipt matches its live anchor and validated bytes/type.

Within BEGIN IMMEDIATE: reload and CAS job id/version/state=validating/attempt/token,
lease deadline not expired, cancellation false, snapshot hash equal. Insert set and
all publications prepared atomically; missing/duplicate role or occupied reservation
rolls back everything. Job remains validating. Do not emit success or expose final.

### claim_set(job, token, set)

Within BEGIN IMMEDIATE recheck exact job/set CAS and live lease/cancel flag; every
prepared publication belongs to exact required set. Change job validating→publishing
and set/publications prepared→claimed in the same transaction. This is cancellation
linearization. Cancellation committed first blocks claim. A later cancel request
reports publication in progress and cannot mark canceled-with-output.

### publish_member(set, role)

Coordinator-only, claimed set/job must match snapshot/attempt and the live
coordinator epoch/OS-lock authority. Original worker lease expiry after claim does
not cancel this authority; a different coordinator epoch cannot use it. Perform atomic no-replace link using live Destination and retained stage;
readback identity/hash/size. In a short transaction recheck set/job/role and insert
artifact + change only that publication to committed. If destination already exists
before this invocation, conflict even if bytes equal; do not infer earlier success
from existence. A caught uncertain post-link DB error leaves job publishing and its
journal intact; only a proven same-live-anchor reconciliation path may continue.

Never keep a DB write transaction open across slow decode/render/hash operations.
The coordinator serializes operations; state is rechecked after I/O. No worker may
invoke this operation or revive an expired token by forging an in-memory record.

### finish_set(set)

Verify exact expected role set has committed artifact rows. Reopen every current
final with its still-held original anchor; recheck expected physical identity/hash,
size and validation receipt, keeping coordinator ownership through completion.
BEGIN IMMEDIATE, reload/CAS job publishing and set claimed, same snapshot/attempt,
all required publications committed and exact artifact rows. Atomically mark set
committed, job succeeded (or explicit warnings), insert one completion_history row.
This is the only success linearization. Duplicate completion returns the same
already-committed result only after validating identity of the requested set/job;
it cannot insert another history row. Stale/missing member never becomes success.

After commit, future ownership-checked staging cleanup can remove only the retained
owned link, never final. Cleanup is deliberately not yet implemented. Failure to
clean is a warning and cannot roll back a valid completed job.

## Recovery and errors

- Live same-session post-link interruption: original FD survives, so reverify exact
  object + content and use journal CAS to continue, without relinking over a path.
- After coordinator/process restart: current substrate cannot prove incarnation
  from persisted dev/inode/hash alone. Classify affected uncommitted publications as state `unknown`
  and expose `OWNERSHIP_UNKNOWN` manual-reconciliation hold while keeping the job
  `publishing` (or `validating` for an abandoned prepared set); never use ordinary
  `blocked_configuration` resume to requeue unresolved output. artifact_sets keeps its
  prior `claimed`/`prepared` state (UNKNOWN is a derived recovery classification, not an
  unsupported artifact_sets SQL enum); preserve both staging and final. Do not
  auto-adopt, delete, overwrite, retry billed provider operation, or report success.
- Future supported incarnation capability/protected owned-namespace recovery needs
  a separately reviewed contract and causal tests. Full JOBS crash recovery remains
  mandatory and OPEN, not removed to make this slice pass.
- DB already committed success: preserve history; verify current artifact state
  separately. Missing/corrupt output is visible and requires explicit new work.
- Errors typed: STALE_LEASE, CANCELED_BEFORE_CLAIM, RESERVATION_CONFLICT,
  FOREIGN_OUTPUT, OWNERSHIP_UNKNOWN, VALIDATION_FAILED, IO_ERROR, DB_UNKNOWN_OUTCOME.
  Logs contain codes/UUIDs, not raw credentials/provider response/file contents.

## Required focused checks before this slice is accepted

Migration: fresh v2; populated v1 unchanged snapshots; each DDL/commit fault rollback;
backup quick_check/readable old rows; crash-after-commit old receipt reopening; foreign,
future, malformed or extra-trigger database unchanged; concurrent migration fails
closed. Real Windows migration/backup flush required, not only Linux mocks.

Coordinator: two-process OS-lock contention/death release; foreign/changed lock refusal;
monotonic epoch; forged/stale epoch; heartbeat expiry before vs after claim; new owner
never adopts old set; cancel before/after claim; stale/forged token; reserved-name race; missing
and duplicate roles; single video commit with subtitle missing leaves job publishing;
final all-member transaction rollback leaves no success/history; duplicate finish
exactly one history; different snapshot cannot reuse set; foreign byte-identical final
never adopted; corrupt or deleted staging/final; live post-link error reconciliation;
real child kill before link/after each member/before final commit yields UNKNOWN on
restart until the supported recovery capability exists. No such UNKNOWN is PASS for
the full durable-recovery criterion. Source/root sentinel bytes remain unchanged.

### Local live-session completion implementation (unpublished working batch)

`PublicationSession.publish_member` and `finish` implement the above live-session
member and exact-set transactions without a new schema or dependency. Member
publication records in-memory linkage only after the no-replace operation, root
flush and retained-anchor readback all return successfully. A subsequent SQLite
error preserves that live proof; a later explicit call re-verifies the same final
and stage, then reconciles the exact journal without linking again. Both a rolled
back COMMIT and an error reported after an actually successful COMMIT are checked
by reading the exact durable state; mutation is never blindly replayed.

Filesystem errors after linking but before `Destination.publish` returns do NOT
currently establish session linkage. The final/stage remain untouched and a repeat
call conflicts rather than adopting the existing output. This narrower fail-closed
case still needs explicit reconciliation; no automatic restart reconciliation,
cleanup, power-loss durability, or whole P03-06 acceptance is claimed.

Success uses one transaction for job/set/history, only after every required final
has been re-read against its still-held original stage anchor and all member
artifact rows match their immutable observations. Duplicate finish verifies the
same content and durable identity before returning one history entry. Worker lease
expiry after claim does not substitute for, or revoke, the continuously held
coordinator OS lock and epoch. External epoch/identity changes fail closed.

The session supplies a `before_link` authority check executed by `Destination`
after slow staged-content verification, immediately before the no-replace native
link. Loss of coordinator epoch/lock or journal identity during readback therefore
prevents the filesystem effect, not merely its later SQLite record. This remains
the cooperating single-coordinator/private-namespace model, not an atomic
transaction spanning an adversarial filesystem and SQLite.


### Local abandoned-set quarantine

`quarantine_abandoned` requires a currently owned OS lock/epoch newer than the
set's original epoch and exact immutable job/set/manifest identity. It atomically
marks only old prepared/claimed publications `unknown`; committed member evidence
and the set/job states are retained. Even if all members committed before a crash,
no final-set success is inferred. The returned immutable `RecoveryHold` carries
only set/job UUIDs, required roles and `OWNERSHIP_UNKNOWN`. Repeated classification
does not increment already-unknown rows. No artifact file is opened, hashed, adopted,
overwritten or removed; no worker is admitted and no billing operation replayed.
A fully committed successful set is refused rather than rewriting its history.

This is a conservative quarantine/diagnostic path, NOT automatic crash resume or
proof of post-restart file incarnation. Full recovery remains an open gate.
