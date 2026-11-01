# Decoded frame facts — partial P03-03

`observe_frames` takes an existing typed source observation, explicit trusted ffprobe
path and container-global video index. It verifies regular inputs, source content
hash, tool hash and scan-returned stream index/type/timebase/start ticks, then
rechecks source/tool content. This is drift observation in a trusted stable tool/
cooperating source namespace, NOT an atomic executable/path capability.

Owned ffprobe requests frames plus selected stream metadata, without read intervals,
shell or network protocols. Raw signed pts, best_effort_timestamp, duration and legacy
pkt_duration remain distinct. Preserve source order/repetitions/discontinuities and
missing fields; no sorting, deduplication, CFR synthesis or guessed last-frame end.
Best-effort timestamps are decoder observations, not silently relabelled raw PTS.

Status OBSERVED_EOF means successful command/JSON completion only; it does NOT prove
all damaged frames were decoded or establish media validity/full trusted coverage.
Every result says render_ready=False. Nonzero exit/error stderr/frame-count cap gives
INCOMPLETE with bounded retained records where complete JSON exists. Truncated JSON,
process output cap/timeout/cancel/unconfirmed retirement raises without inventing a
partial prefix or job/cleanup authority. Empty scans and unavailable fields remain
explicit; future conversion needs independently supported completeness/validity.

Defaults:100000retained frames,32MiB captured output,300s process timeout; maxima
1000000frames/64MiB/3600s. Cancellation checked before launch, during owned process,
between128-frame groups and fingerprint chunks. JSON parsing/OS I/O is not preempted;
no hard total wall-clock guarantee. Source/tool hashing adds I/O, with no unverified
large-media performance promise. No raw stderr/arbitrary tags exported.

CLI: `--inspect-media ABSOLUTE_MEDIA --ffprobe ABSOLUTE_TRUSTED_TOOL --frame-stream N`
optionally `--frame-limit N`. Normal metadata inspection unchanged without flag.
Frame INCOMPLETE JSON exits3; malformed/failed scan exits2; OBSERVED_EOF exits0 but
is still NOT render-ready or decode-validity acceptance. Tool trust is explicit
caller authority, not a grant from project/candidate metadata. No new dependency.

The frame-count cap limits retained records AFTER a byte-bounded full JSON parse;
it does not stop ffprobe early or promise a cheap first-N scan/parser object-count
bound. Captured byte limit, not max_frames alone, bounds input allocation.
