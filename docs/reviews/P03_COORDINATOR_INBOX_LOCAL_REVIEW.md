# Coordinator inbox — corrected source CLEAR

2026-11-01. Bounded dirty-source review atop 6c43609; no aggregate or remote operation.

## Blocker
In CoordinatorInbox.drain, dequeuing occurs under self._lock, but Future.set_running_or_notify_cancel occurs after releasing it. Concurrent close can return while the removed future is still PENDING and absent from the queued list. Drain then marks RUNNING and executes SQL after route retirement. This contradicts close refusing queued work except already admitted/executing requests.

Independent deterministic reproduction paused set_running_or_notify_cancel, ran close on a separate thread, then resumed: observed closed=True / future.running=False followed by _apply_owned invocation. Mocked mutation boundary only, no actual DB writes in repro.

Fix: serialize dequeue plus transition to RUNNING against close using the same admission lock. Test both orderings: close wins => refusal and no mutation; admission wins => already admitted transaction can finish without replay. Do not hold lock throughout SQL unnecessarily.

## Other findings/evidence
Owner thread restriction, exact repository owner/store token/version CAS, no second coordinator lock, and unexpected/unknown COMMIT retirement are sound in reviewed scope. Author independently corrected Future.result TimeoutError ambiguity: completed future's stored TimeoutError must not become endless wait; source correction read and sound. GUI interruption cancels pending future only; running outcome remains unconfirmed, never undone or automatically replayed.

Independent selected tests: unknown COMMIT, real owner-thread child/descendant cancellation, GUI pending interruption — **3 PASS / 4 deselected, exit 0**. Fontconfig cache warnings are environmental; no GUI/native Windows runtime inference. Selection string stored_timeout did not match finished_timeout test; that test was inspected, not independently executed. Default shell still has no scheduler/live owner route; no OPS-02.02 or task closure.

## Targeted correction recheck, 12:35 UTC
Verified final inbox SHA256 `20f970c21b019cb65f598e16daff79ef23679c50840807ce6041382ec8a8faa2` and tests `6fd661f5bd3b6f4ef78dfa235132813b8999c709e2e4849be4b5a3fa8cca42f0`. Dequeue and transition to RUNNING now share close's lock; database execution and completion callbacks remain outside. Both close-first and admitted-first semantics are correctly represented. Prior blocker closed.

Independently executed only test_close_linearizes_with_running_admission: **1 PASS / 7 deselected, exit 0**. Source CLEAR for this bounded inbox/optional Qt routing slice; no default scheduler, Windows integration, full worker or criterion closure inferred. New unreferenced observations.py is explicitly outside this review.
