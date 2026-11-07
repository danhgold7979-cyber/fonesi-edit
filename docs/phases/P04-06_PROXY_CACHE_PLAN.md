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
