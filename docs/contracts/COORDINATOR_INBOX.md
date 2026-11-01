# Active coordinator command inbox — P03-04 / P03-05

The existing coordinator owns the SQLite connection and OS lock. A bounded
stdlib deque/Lock/Future inbox transfers immutable selected-job QueueCommand
requests from UI/other threads. No connection or native authority transfers.
Drain is restricted to the constructing owner thread and reuses the exact
store-token, job-version CAS and transaction path used by standalone commands.

Integrating workers must construct the inbox inside the owner lifetime, expose
it only to that store's UI, drain at process cancellation/progress polls, and
close it before releasing owner/repository. Context-manager exit fails pending
requests. The current shell has no scheduler and uses the existing standalone
route; QueuePage/QueueCommander accept an explicitly supplied live inbox for the
real coordinator integration, not a fabricated running job or progress display.

Capacity defaults64/max256; drain defaults16/max256. Full means not admitted.
Future.cancel before execution means no SQL effect. After execution begins,
interruption does not undo SQL: UI reports unconfirmed and reads durable state,
never retries automatically. Ordinary stale/invalid commands fail independently;
owner loss, unexpected exception or unknown COMMIT retires the route and fails
pending work. A cancel result for running/validating means cancel requested, not
process stopped. Only the worker observes owned retirement then acknowledges.

A live Python child/descendant test proves cross-thread request routing while the
owner lock remains held and same-thread SQLite is maintained. It is not a renderer,
provider, FFmpeg capability, cleanup integration or complete scheduler acceptance.
UI queue selection/CAS rules and truthful no-progress labels remain unchanged.

## Real observation transport
The route owns a bounded latest-per-job Progress buffer (64/max256); replacing
an observation coalesces it, overflow drops the oldest observation, not a job.
An older attempt cannot displace a newer buffered attempt. Owner-thread
progress_observer reuses JobProgressObserver authority/lease checks. Closing the
route clears and retires its observation buffer. No unbounded queued Qt signals.

QueuePage polls at100ms only after a successful queue snapshot and no read in
flight, matching store token, UUID, snapshot hash and attempt. It shows counters
only on running, noncancel-requested, non-publication-held rows. A snapshot refresh
clears previous labels; failed refresh prevents newer observations being painted
against stale rows. End means observation stream ended, NOT job success. Timer
stops on page retirement. Read-only queue query adds only immutable snapshot hash,
never snapshot body, request key or paths. The default shell still has no running
scheduler/executor; a supplied actual owner route is required. The real-owned
Python stdout/Qt selected-cancel test proves this path, not FFmpeg capabilities.
