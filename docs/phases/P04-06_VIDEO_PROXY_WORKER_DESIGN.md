# P04-06 video proxy worker — implementation contract

Status: DESIGN ONLY. No encoder or playback implementation is claimed by this document.

## Scope
Generate a deterministic, low-resolution video proxy for a selected video stream, publish it atomically into the existing persistent cache, and let the Timeline consume the proxy without changing source media or project state. Audio playback and synchronized A/V seek are separate follow-on acceptance gates.

## Identity and reproducibility
- Cache key must bind source SHA-256, FFmpeg executable SHA-256, selected stream index, target width/height, target frame rate, video codec/profile, pixel format, audio policy, and encoder algorithm version.
- Rational frame rates and timestamps remain exact numerator/denominator pairs in project state and cache identity; never key by rounded UI seconds.
- The proxy command must map only the explicitly selected video stream. Audio must either be explicitly omitted or separately specified; never let FFmpeg auto-select streams.
- Use a fixed, documented encoder profile (initial candidate: H.264, yuv420p, bounded dimensions, bounded FPS, fast preset, CRF policy). The candidate must be tested against supported FFmpeg builds before becoming the product default.

## Worker lifecycle
1. Validate absolute regular source/tool paths, source fingerprint, selected video stream observation, output bounds and cache key before launching a process.
2. Create a unique staging directory under the cache filesystem; refuse symlinks/reparse points and never write beside the source media.
3. Launch FFmpeg through `run_owned` only. Use `-nostdin`, explicit `-map 0:<stream>`, `-progress pipe:1`, `-nostats`, bounded output and a finite timeout. Parse progress records incrementally; progress is telemetry, not proof of success.
4. Cancellation/timeout must retire the entire owned process group/Windows Job Object before deleting staging files. If retirement is unknown, retain the staging directory and report an unresolved retirement state; do not race cleanup against a live encoder.
5. Require zero exit status, non-empty bounded output, unchanged source/tool fingerprints, and a successful independent ffprobe validation of the staged proxy (one expected video stream, expected dimensions/pixel format, finite duration, decodable initial/middle/end samples).
6. Publish only after validation: atomically move the staged payload into the cache publication path with a manifest containing the full key, payload length, SHA-256, codec, dimensions, FPS, duration and validation evidence. Cache reader leases must prevent eviction while Timeline playback holds the proxy.
7. Cache read/write failure is an optimization failure: Timeline may fall back to original-source playback only if the source path and decoder path are independently valid. Never report a proxy hit on fallback.

## Timeline integration
- Add a cancellable background proxy job with explicit queued/running/validating/publishing/ready/failed/canceled/retirement-unknown states.
- UI progress must distinguish encode progress from validation/publication. No ready state before atomic publication.
- Keep the original clip/source identity and exact source-time mapping. Proxy timestamps must map back to source time; frame-rate conversion must not silently change edit timing.
- A/V playback and synchronized seek are not part of the first proxy-worker merge. They require a separate playback clock, audio-device lifecycle, decoder buffering, seek discontinuity and drift tests.

## Required tests before implementation acceptance
- Pure command construction: explicit stream mapping, no shell, no implicit audio, exact dimensions/FPS, deterministic flags.
- Process lifecycle: cancel before launch, cancel during encode, timeout, non-zero exit, output cap, child-process retirement, Windows Job Object emptiness and unknown-retirement handling.
- Filesystem: staging cleanup after confirmed retirement, retain staging after unknown retirement, symlink/reparse refusal, atomic publication, source untouched.
- Validation: empty/truncated/corrupt output, wrong stream, wrong dimensions/FPS, unknown/non-finite duration, source/tool mutation during encode.
- Cache: full-key separation, corruption, quota eviction, reader lease blocks eviction, release permits eviction, restart reuse.
- Integration: Timeline progress, cancel, app shutdown, project close, source relink, proxy unavailable fallback.
- CI: Linux/Windows Python 3.12/3.13 plus pinned FFmpeg candidate tests on real Windows runners. Synthetic source/ABI tests do not count as native Job Object or media acceptance.

## Acceptance gates
A. Worker unit/process/filesystem tests pass.
B. Real pinned FFmpeg candidate creates and independently validates a proxy on Windows and Linux.
C. Cancellation retires all descendants and does not publish partial output.
D. Cache restart reuse and reader lease/eviction behavior pass.
E. Timeline integration is exercised with real media fixtures.
F. Separate A/V playback and synchronized seek evidence is complete.

Until gates A–F are evidenced, P04-06 remains IN_PROGRESS. This design document is not implementation evidence.
