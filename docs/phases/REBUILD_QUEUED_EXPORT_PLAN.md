# Rebuild P03-04/05/06 — explicit queued CPU export contract

Plan before implementation. Current RenderIntent v1 is a foundation-only schema: output directory/seed/source path do not capture destination filename, trim or tool identities. It must NOT be treated as a complete executable job. Preserve v1 parsing/digests; introduce a separately tagged CpuExportSnapshot v1, not reinterpret old rows by guessing defaults.

## First bounded slice: immutable executable snapshot (not yet execution)

Fields: fixed format/version, canonical project UUID, absolute source and destination paths, source SHA256, explicit absolute FFmpeg/ffprobe paths and SHA256, exact optional ClipMap, explicit rational duration tolerance, seed. Fixed CPU H264/AAC MP4 capability only; destination .mp4, output offset0, speed0.5–2, tolerance0–1 seconds matching current renderer. Paths belong to current host at execution; cross-platform documents may be parsed but never guessed into native paths. Source/destination must be distinct at execution, not inferred from spelling alone. SHA256 identifies bytes, not trusted origin or execution authorization. No tool install/download, credential/command/script fields or arbitrary config blob.

Strict duplicate-key/unknown-field/version/size/type validation and immutable canonical JSON/hash; bounded rational integers and path lengths. Reject bool-as-int/NaN/negative/unsupported mode. Golden Unicode/rational/field-order test; changes to trim/destination/tool identity must change digest. Old RenderIntent schema remains independently readable but cannot enter new coordinator by automatic conversion. Snapshot creation does not hash files or cause filesystem/process side effects.

## Later execution slice prerequisites (NOT implemented by snapshot work)

- Explicit trusted tool provenance/capability from registry; SHA alone is not trust.
- Stable input preparation: copy authorized input into owned staging with bounded byte/time/cancel policy, verify copied bytes against snapshot digest before encoding. Never claim two path hashes provide hostile-writer immutability. Budget failure blocks job, never falls back to mutable source silently.
- Worker owns SQLite connection; persist complete snapshot before claim; explicit lease token/generation checked at transitions. No UI-thread FFmpeg/backup, no automatic retry of uncertain publication.
- Validated artifact and ledger success are separate atomic domains: a crash after file publication but before DB commit is uncertain and needs explicit reconciliation. Existing output is not proof of prior success. Never delete final output to conceal uncertainty.
- Complete source/tool/settings snapshot must drive actual render. Exact output hash/size/duration/tracks validation before success; stale tokens never commit. Bounded cleanup only owned staging. Keep no success path in generic transition.
- GUI queue, descendant containment, heartbeats, pause/resume, restart recovery and filesystem/power-loss faults require their own implementation/tests before full P03 acceptance.
