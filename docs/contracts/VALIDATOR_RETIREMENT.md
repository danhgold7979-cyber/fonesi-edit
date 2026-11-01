# P03-04 per-invocation validation retirement (local source)

A successful process exit, caught exception or DB cancel acknowledgment is not an
independent cleanup permission. Reuse the existing owned process adapters; no new
launcher, PID/global kill, security change or dependency.

## Internal provenance

Each fresh ValidationLifecycle is bound by opaque object identity to exactly one
session validation operation and owning thread. It starts unentered/unsealed.
Only the actual validator wrapper enters its body; body unwind seals once. Reuse,
nesting, cross-thread access or invalid invocation registration permanently revokes
it. A different operation cannot consume its result. This is internal Python
provenance, not an untrusted-project API or defense against arbitrary in-process
code injection. Nothing is serialized or accepted as a caller boolean.

Before any tracked launcher entry, the lifecycle registers a fresh UNKNOWN
_RetirementObservation. Adapter claims its one invocation with a fresh opaque token;
only its finalizer confirms the matching token. A runner returning normally without
confirmation remains UNKNOWN. Error sanitization never supplies confirmation.
At most two sequential invocations (one probe, one full decode) are permitted.
An unentered mocked validator—even one returning success—cannot provide evidence.

Windows confirms WINDOWS_JOB_EMPTY only after owned Job termination, observed
ActiveProcesses0 and every checked process/thread/pipe/job handle retirement;
setup/suspended-child failures use the same finalizer. If job creation fails before
any process can exist, the outcome is NO_PROCESS, never an invented empty-job query. Any retirement error leaves
UNKNOWN. POSIX records POSIX_GROUP_RETIRED only after its existing group signal/wait
policy and all checked closes complete, with a separate success flag, NOT the early
stopped latch. This is not Windows active-process-zero proof or escaping-process
containment; POSIX staging deletion remains unavailable. Prelaunch cancellation
records NO_PROCESS at the exact branch before child creation. Other early errors
may conservatively remain UNKNOWN. POSIX attempts remaining owned closes even if
one close fails, then exposes retirement uncertainty instead of confirming.

## Validation composition

Actual validate_media body tracks both probe and decode through the same lifecycle.
No-launch validation failure may be safe only after real trusted body entry/unwind.
If the first probe retires but decode remains UNKNOWN, the entire operation is
unsafe, even though media exceptions are sanitized. Session checks its fresh exact
operation after success or exception. Any unknown permanently latches session
_quiescence_unknown; no later successful operation or cancel acknowledgment clears
it. Known retirement does not make malformed media valid or authorize job success.

## Evidence scope

New affected local cases include first-known/second-unknown, callback exceptions,
POSIX finalizer-close uncertainty, invalid lifecycle replay, unobserved fake success,
real validator early no-launch failure, and actual Python child+descendant cancellation
through probe/validation wrappers then canceled-stage policy. The Python executables
are explicit lifecycle stand-ins, NOT proof that FFmpeg accepts arbitrary bytes or
that Windows codecs work. Real malformed-probe output after retirement stays invalid
but may permit cancellation cleanup. Existing sticky-unentered-validator regression
and6affected legacy API/validation cases pass. Windows finalizer fault and actual
native cancel→retirement→stage deletion remain target gates for this source.

`[validator-retirement]` alone runs four targets/22 affected cases, no unchanged
aggregate, frozen build or Qt installation. No new task/child acceptance from source.
