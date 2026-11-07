# P04-06 persistent proxy-cache slice

Status: planned for implementation on the unified integration branch. This slice establishes the persistent, content-addressed cache boundary only; it does not claim FFmpeg proxy generation, playback, synchronized A/V decoding, or render parity.

## Inputs and invariants
- Cache identity binds source SHA-256, selected tool SHA-256, stream index, output dimensions, and algorithm version.
- All inputs are validated before filesystem mutation. Cache root and entries must not traverse symlinks or Windows reparse points.
- Only bounded, non-empty encoded proxy bytes may be published.
- A cache entry is visible only after its payload and manifest have both been written and flushed in a staging directory, then atomically renamed into place.
- Manifest includes schema version, complete key, byte length, and payload SHA-256. Reads revalidate all fields and the payload digest.
- Cancellation before publication removes staging data and never exposes a ready entry.
- Changed source/tool/stream/size/algorithm produces a different cache identity; explicit source invalidation removes matching entries.
- Cache failures are fail-closed and must not mutate source media or project state.

## Implementation tasks
1. Add a pure key type with strict SHA-256, stream, dimension, and algorithm validation.
2. Add bounded persistent cache read/write/invalidate operations with safe path checks, atomic publication, and payload verification.
3. Add unit tests for cache hit/miss, key invalidation, source invalidation, corruption, size limits, cancellation, and symlink/reparse refusal.
4. Run the full clean-foundation matrix on Linux/Windows Python 3.12/3.13. Keep this slice partial until proxy generation, cancellation of owned FFmpeg work, A/V playback seek, warm/cold performance, and physical Windows filesystem checks have independent evidence.

## Acceptance boundary
This is persistent cache infrastructure for already-encoded bytes. It is not an encoded-proxy generator and does not close P04-06 or P04.



## Follow-on integration slice — still-preview worker (2026-11-07)

Implemented after the storage boundary:
- `extract_preview_frame(..., persistent_cache=...)` accepts only a validated `PersistentProxyCache` instance.
- Cache identity now binds source SHA-256, FFmpeg SHA-256, stream index, dimensions, and a hash of the exact rational decoder timestamp in the algorithm version.
- Existing bounded PNG header/dimension checks run on disk hits before use. Invalid cache data is invalidated and re-decoded; source/tool identity is rechecked before returning a persistent hit.
- Successful encoded still-preview bytes are published through the cache with cancellation checked before publication. Cache I/O failures are treated as optional optimization failure; valid decoded frames remain usable.
- Timeline `PreviewWorker` receives an app-local cache under Qt `QStandardPaths.CacheLocation/preview-proxies`. If cache initialization fails, the still-preview flow falls back to the existing in-memory path.
- Tests cover reuse after clearing the in-memory cache, corruption/redecode/repair, exact timestamp identity, and invalid cache object refusal.

Not integrated: audio waveform persistence, background proxy transcoding/worker queue, video playback, A/V synchronized seek, cache migration/cleanup UI, benchmark or render/export parity. This is still-frame persistence only.



## Follow-on integration slice — persistent waveform observations (2026-11-07)

- `extract_audio_waveform(..., persistent_cache=...)` now optionally reads/writes the same bounded content-addressed cache.
- Identity binds source SHA-256, FFmpeg SHA-256, stream index, exact rational decoder start/duration, 8 kHz sample rate, bucket count and waveform schema version.
- Payload is canonical JSON with schema, all identity fields, sample count and min/max peak pairs. Read validates the complete identity, sample count, bucket bound, finite normalized values and min<=max before returning.
- Corrupt bytes or malformed envelopes are invalidated and decoded again. Cancellation is checked before disk lookup and before publication. Optional disk failures do not discard a valid freshly decoded waveform.
- Timeline WaveformWorker receives a cache under Qt CacheLocation/waveform-cache. Cache setup failure preserves the previous memory-only observation path.
- Regression tests cover process-memory reset reuse, payload corruption/redecode/repair, exact rational window and bucket identity, and refusal of unvalidated cache objects.

Acceptance boundary: waveform remains a bounded amplitude observation, not loudness/clipping analysis or audio playback. No multi-chunk continuous A/V scheduling, device acceptance, export parity or physical Windows cache filesystem acceptance is claimed.
