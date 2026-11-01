# P03-04 bounded progress observations — source CLEAR

2026-11-01. Read-only bounded review, no aggregate/real FFmpeg rerun.
Verified hashes: process.py d4eed1fd8d1cc0184e9f79bcefcd0b233200d7b13194aba2cdf691fd9300dc3e; windows_process.py a8db33482ccc6555eb7331ca8479247e4e027d621a8ad98304538dbdcdc66a63; progress.py ade69280d69028d4d281e67330e08b91919cf3f6ebea1c43e48d40263f302c82; tests175005a69a3c2d14185daae8c7e9f7971fb2686cd629de7f53a5cf32aa4bf8ee; contractccaa4b959b9f319d3c4446261a460defe9ccfb6dfbe727c2da83a179cb483473; local receipt9ce69ca688f4ea2f637c9b5d226617cc5d8dee6a8edc6bddefe62f2d9800e717.

No blocker found for this observational slice. Callback runs after combined-output bound and only receives stdout; exceptions propagate through existing owned-group/Job Object retirement. Parser bounds chunks/lines/record size and signed integer range, rejects duplicate known fields and incomplete/end-followed streams, drops unknown/free-text fields, retires on parser/callback failure. End is not process success, media validation, job completion or publication permission. Observer checks live ownership, running state, snapshot/attempt/token, finite unexpired lease and cancellation, with no DB writes.

Independent selected tests: fragmented parser, end-without-repository-mutation, actual callback-exception descendant retirement — 3 PASS / 23 deselected, exit0. Recorded Linux FFmpeg receipt inspected but not replayed; it reports25frames/1second/end and unchanged input. Add exact source hash/commit provenance to receipt alongside its runtime/tool/input identifiers when recording checkpoint. Actual Windows callback behavior remains pending.

Integration boundaries: callbacks must remain bounded/nonblocking; synchronous callback cannot be forcibly deadline-limited. JobProgressObserver repository connection must be created/used on its owning runner thread; fake-repo tests do not prove SQLite thread wiring. Queued UI delivery needs its own stale-attempt filtering/coalescing at consumption. Those integration gates remain OPEN, not acceptance by unit-test count.

Official FFmpeg documentation fetch attempts at ffmpeg-all.html and ffmpeg.html Generic-options timed out; no new independently fetched protocol-source verification is claimed. No change to cleanup primitive acceptance or current publication authority.
