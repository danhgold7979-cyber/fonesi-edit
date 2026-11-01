# P03-04 bounded worker observations (local slice)

`run_owned(..., on_stdout=callback)` observes chunks (at most 65536 bytes) on its
runner thread after enforcing combined output bounds. It uses the existing owned
POSIX group / Windows Job Object launch and retirement; no second process launcher.
Callback failure follows the same retirement path as cancellation. Callback must
be bounded and nonblocking; a Python callback or OS I/O cannot be forcibly timed
out by this synchronous runner. Never mutate Qt widgets on this thread.

`FFmpegProgress.feed` consumes `-progress pipe:1`, frames records only at explicit
`progress=continue|end`, caps each line at4096 bytes and each record at128 lines.
The runner additionally caps total captured output and wall-clock observations.
Unknown keys are dropped; only bounded integer frame/out_time_us/total_size reach
immutable observations. N/A stays unknown; negative output time is allowed because
media timestamps can be negative. No percent/ETA is invented. `finish` rejects an
incomplete stream; process return code must separately be checked. `end` alone
never makes a job successful or validates an output. See official protocol:
https://ffmpeg.org/ffmpeg-all.html#Generic-options (`-progress`, `-stats_period`).

`JobProgressObserver` checks coordinator ownership and reads current job state at
observation delivery. Only matching snapshot hash, attempt and lease token with a
finite unexpired deadline, running state and no cancel request can deliver. Stale
observations permanently retire the observer. No DB writes/state changes occur.
This is an observation of that instant, NOT permission for any later side effect;
worker/publication authority must be rechecked at their own effect boundaries.
Events omit lease secrets, arbitrary stdout/stderr, tool/source paths and unknown
fields. Repository connections must be created/used/closed on this same runner thread
(SQLite thread affinity). UI-thread queued delivery/coalescing and durable queue integration remain
open; this module does not claim a functioning renderer or queue worker loop.

## Evidence and limitations

26 new affected local cases PASS; one additional real SQLite + owned subprocess
callback wiring case PASS (same runner thread, unchanged job after end, cancellation
suppresses subsequent observation), including a real subprocess output before exit,
callback-failure owned descendant retirement, parser limits and stale attempt gates.
`docs/evidence/p03/progress-local/receipt.json` records one actual already-approved
Linux FFmpeg7.1.5 null-output observation:25 frames/1000000us/end, exit0, source/tool
hash unchanged. No output file or live provider operation. This proves the new
stdout integration only, not repeated codec/media acceptance. Actual Windows
observer behavior is NOT_RUN. Earlier unchanged process/native evidence remains
scoped to its source/runtime and is not relabeled as this delta's Windows proof.
Cleanup prototype b32795a and its separately authorized13-file publication payload remain separate;
this progress delta is local, not silently added to that pending approval.
