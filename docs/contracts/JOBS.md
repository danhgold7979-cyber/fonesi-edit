# Durable jobs and publication protocol v1

Target contract, not a claim of implementation. SQLite WAL with foreign_keys=ON, busy timeout, synchronous=FULL; one coordinator writer serializes transactions. Worker processes never share UI connections. Filesystem durability assumptions tested separately on Windows. DB, staging and outputs local; network/removable destinations need explicit capability verification before a durable guarantee.

## Records and states

Job: UUID, request_key unique, snapshot_json/hash, kind, state, stage, priority, created_at, attempt counter, cancel_requested, warning list, error code, current lease generation, version. State enum: pending/running/validating/publishing/retry_wait/blocked_configuration/paused/succeeded/succeeded_with_warnings/failed/canceled/skipped. Stage independently scanning/downloading/translating/rendering/validating; UI labels never create extra hidden runtime states. Paused is pending job held by user; queue-level pause additionally stops admissions, does not kill current workers. Skipped requires reason and matching validated artifact ref, not path existence.

Attempt: job_id, number, lease_token random UUID, generation, worker_pid+start identity, tool installation IDs/hashes, heartbeat/deadline UTC, start/end, error, external_request_id, unknown_billing. Lease updates are CAS against job/version/token. Stale worker events, duplicate completion and events after cancel are ignored and logged without secrets. Reuse of PID alone is never proof of ownership.

Snapshot: schema/evaluator version, resolved input IDs/hashes/probes, CompositionPlan, preset version/overrides/locks, seed, matrix row/history digest, output root/policy, tools required/resolved, provider model/version/settings, profile/account expected identity refs. No password, cookie, bearer token or API key. Snapshot immutable; updating pending jobs is explicit new revision plus preflight. Running jobs never change.

Allowed transitions: pending→running|paused|canceled|blocked_configuration|skipped; paused→pending|canceled; running→validating|retry_wait|blocked_configuration|failed|canceled; validating→publishing|failed|canceled; publishing→succeeded|succeeded_with_warnings|failed (reconciliation only); retry_wait→pending|canceled; blocked_configuration→pending|canceled after repaired preflight; failed/canceled→new attempt via explicit retry with same snapshot; terminal successful states immutable. Publication commit point wins over late cancellation: UI says completed, not canceled-with-output. Every transition in transaction requires expected prior state, job version, live lease when worker initiated. Success requires validated artifact receipt and final hash readback.

## Process, progress, retry

Coordinator invokes argv lists, shell=False, bounded stderr/stdout; FFmpeg progress from actual progress protocol. Unknown totals show count/activity, no fabricated percent/ETA. Cancellation signals process group, grace timeout, then terminates owned group; Windows uses Job Object ownership, Linux process group. Never kill unrelated PIDs. Handoff lease deadline 30s, heartbeat every 5s as initial policy, tested under load; expiry triggers reconciliation and ownership check, not instant success.

Retry only transient errors with capped attempts/backoff+jitter. Auth/quota/missing resource wait for configuration; permanent invalid input fails. Provider timeout after submission is unknown outcome/billing until request reconciliation or explicit permitted retry policy; no exactly-once claim without provider support. Crash render restarts unfinished render stage; completed verified stage reuse keyed by snapshot/input/tool hash.

## Output publication: journaled no-overwrite, DB and filesystem gap closed

Publication(id,job,attempt,lease,staging,final_candidate,sha256,size,validation_json,state,receipt_hash). States prepared→claimed→published→committed; conflicted/quarantined terminal alternatives. Staging is exclusive per publication UUID on destination filesystem; never arbitrary source path. Multi-artifact result uses per-artifact receipts and one manifest; job success after every required artifact committed.

1. Worker writes staging and closes. Validator probes required streams/duration, decodes integrity sentinel/full decode by policy, computes content hash; fsync file. Coordinator CAS verifies valid attempt and not canceled. Durable transaction records PREPARED with exact hash/size/expected tracks and reserves output candidate + matrix combination (unique DB constraints).
2. Publication claim transaction changes job validating→publishing and publication→claimed; this is cancellation linearization point. Prior cancellation wins and only owned staging is cleaned. After claim, cancellation cannot interrupt publication; finish/reconcile then communicate result.
3. Publish with filesystem atomic **no-replace** primitive. Prefer same-filesystem hard-link staging→final then unlink staging where supported, or OS rename-no-replace; never `os.replace` or exists-then-rename overwrite. Unsupported FS fails capability preflight or uses tested exclusive-write protocol labeled non-atomic (not accepted durable output until validated/reconciled). If foreign final exists choose new candidate through transaction or report collision, never modify/delete it. Flush directory where OS supports; record durability limitation where unavailable.
4. Hash/readback final against prepared receipt, fsync/close required handles. Record published in DB. One transaction inserts Artifact, transitions job to succeeded(_with_warnings), marks publication committed and matrix reservation succeeded. Only now UI exposes success/result. Transaction rollback leaves journal for restart.
5. After commit remove owned staging leftovers. Cleanup failure is warning, not lost output. No cleanup by filename pattern alone: ownership UUID/path/hash must match.

## Recovery at every crash boundary

- Before PREPARED: unreferenced owned staging quarantine/cleanup by age and lease, no job success.
- PREPARED before claim: canceled job removes only owned staging; otherwise revalidate staging and resume claim with new recovery lease.
- CLAIMED, final absent, staging valid: publish; neither exists: fail recoverably/rerender same snapshot; staging corrupt: quarantine.
- Final exists after linking but before DB published: exact hash/size plus journal ownership prove candidate; revalidate, complete DB transaction. Different hash means foreign/conflicted, never delete/overwrite/claim success.
- Both staging/final exist and inode matches (or verified same owned receipt): finish commit then clean staging. Equal bytes alone without matching publication journal do not establish ownership.
- DB says success but final later missing/corrupt: artifact status missing/corrupt, user-visible recovery needed; do not silently rewrite historical success or mark current file valid.
- Crash during DB artifact/history transaction: SQLite all-or-nothing; recovery ensures exactly one artifact/history row by unique publication/job keys.
- Expired worker attempts must not publish: coordinator owns publication; CAS lease generation blocks old worker completion. Restart marks old in-flight attempts interrupted, inspects actual child ownership and journal before retry.

Tests inject crashes after EACH numbered boundary and SQLite operation; external destination collision races; cancel-before/after-claim; stale heartbeat and duplicate result; disk full/permissions, corrupted staging/final; symlink escape, concurrent reservations; matrix history committed once; incomplete multi-artifact set never success. Run both process-kill and simulated failures: monkeypatch-only tests do not certify OS durability.
