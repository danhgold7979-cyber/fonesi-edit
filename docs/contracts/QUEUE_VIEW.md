# Actual queue observations — P03-05 partial

The desktop's Hàng đợi/Lịch sử area now reads actual `jobs.sqlite3` beside the
application project store. Missing jobs storage displays an honest empty state and
is not created by this view. Existing storage must have the owned receipt, exact
current application/schema identity and stable opened database identity. This is
the read-side observation contract: no migration, job admission, cancel, retry,
completion or takeover. Explicit selected-job commands are a separate path below.

A Qt QThread opens its own read-only SQLite connection, with 0.5s busy timeout,
cooperative SQL progress cancellation and a bounded maximum 500 displayed rows.
No connection is shared with the GUI thread. Query selects only job UUID/state,
attempt count, version, cancel-request flag and unresolved required-set flag. It never
selects snapshot JSON, request keys, provider data, source filenames or credentials.
Unknown states/invalid records fail closed. Read-only SQLite can still use its WAL
shared-memory machinery; this is no business-data mutation, not a promise of zero
OS metadata/SHM changes.

Manual refresh displays real states and explicitly unknown progress, not invented
percentages or renderer throughput. Existing rows after a failed refresh are
explicitly labeled stale. Stage/progress event integration remains unavailable,
not simulated. Reading a row does not prove its output files valid.

Closing the window requests cooperative reader interruption and defers actual
window close until the thread has finished; no thread termination or connection
closure from another thread. Busy timeout bounds SQLite lock waiting, not arbitrary
OS/filesystem latency. Actual Windows GUI responsiveness/shutdown remain native
gates; Linux offscreen tests are not a substitute.

The red-circle Edit communication/status marker is not treated as authorization to
change application or installer branding. Existing app branding is preserved.


## Selected-job requests — P03-04/05 partial

Buttons require exactly one visibly selected row (not merely keyboard/current-row
focus) and capture its job UUID/version plus the observed owned-store
creation receipt token. Snapshot replacement clears selection rather than retargeting
an old row index. Later selection changes cannot retarget the request. Command
acknowledgment/uncertain-outcome/cancel-only notices remain separate from refresh
status, so an automatic read cannot erase them. A
separate Qt worker uses an existing-only current-schema database open (SQLite
`mode=rw`), never creating/migrating/adopting a stale target. A different owned DB
with the same job UUID/version is rejected by its different store token before any
coordinator epoch is written. Tokens are receipt hashes, not artifact ownership
proof or credentials.

The worker acquires the existing nonblocking coordinator OS lock and epoch, then
performs one transaction with expected job version and live ownership checks.
Allowed actions are pending→paused, paused→pending, and the existing cancel-request
protocol. Configuration/recovery holds cannot be resumed by this UI. Publishing or
terminal jobs cannot be canceled. Running/validating cancellation only sets the
request flag; it does NOT certify child quiescence or pretend the job has stopped.
No filesystem output is changed and no provider/network operation is performed.

A live other coordinator causes refusal, never lock bypass. Routing requests to a
future already-running coordinator remains an integration gate. No operation is
automatically replayed after SQLite errors or unknown COMMIT outcome; a fresh
observation shows the actual state/version. Closing requests cooperative stop before
mutation when possible, but a transaction already committed is not undone by close.
Both reader and command workers finish before the window closes. Full queue-level
pause, worker admission/execution, progress events and native Windows integration
remain OPEN.

### Thread retirement evidence boundary

Qt documents that `finished()` may precede thread-local cleanup; complete effect
synchronization requires `wait()` to return true:
https://doc.qt.io/qt-6/qthread.html#isFinished . The UI therefore retains each worker
and remains busy until nonblocking `wait(0)` succeeds, checking again through a Qt
timer rather than blocking/terminating the GUI. Only then are deletion and window
close permitted. GUI tests keep one session-wide QApplication and drain deferred
objects rather than recreating the application between tests.

One earlier local selection-test process segfaulted during interpreter/Qt exit after
its assertions passed; that run is FAILED. Its precise original cause was not
captured and one unchanged faulthandler rerun did not reproduce it. The documented
retirement gap and per-test application lifetime were corrected as concrete risks,
not asserted as a proven diagnosis. Eight affected cases then exited0; an isolated
real Qt process performing three queue read/pause/window-close cycles also exited0.
This bounded local evidence does not prove all native shutdown behavior or Windows.


Further isolation reproduced exit135/134 in no-real-worker tests (including a
single snapshot-refresh case); the first wait/fixture change was therefore NOT a
clear fix. Plain QApplication and standalone page subprocesses exited0. Keeping
application lifetime alone left closed QWidget/QObject graphs alive until interpreter
cleanup. The fixture now explicitly closes/disposes top-level objects and verifies
any real threads are joined before QApplication teardown. With production source
unchanged, the previously failing three-case subset then exited0.

The application entry point now also requests cooperative worker stop, completes
retirement, and explicitly delivers owned-window deferred deletion while QApplication
is still alive. Qt's official lifetime rule is first-created/last-destroyed application:
https://doc.qt.io/qt-6/threads-qobject.html . Two isolated real-process regressions
(three queue command/window cycles and the actual GUI entry point closing during
a read) exited0. Exact native fault attribution without a captured C++ stack remains
limited; independent recheck and actual Windows evidence are still required.
