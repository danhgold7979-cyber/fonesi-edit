# Rebuild P02-01 / P03-03 — bounded local media probe

Scope: validate a real local media asset through installed ffprobe without shell or network URL input. This is not render/UI/Windows acceptance. Exact contracts: executable is an explicit existing absolute path; source is a regular local file; protocol whitelist file/pipe; timeout 10 seconds and stdout/stderr each at most 64 KiB. Over-limit, timeout, nonzero exit, malformed JSON, missing stream/duration or unsupported metadata fail closed. Reports expose fixed error codes, not raw source paths/stdout/stderr. Duration parsed as exact rational decimal, stream type allowlist. No thumbnail, output or source mutations.

Tests: parser missing fields/non-finite duration/oversize/invalid stream; subprocess timeout/output cap with controlled Python fixture; actual synthetic WAV through local ffprobe. Source bytes SHA before/after must match. Windows and hostile-media corpus remain unverified. Do not infer all codecs supported.

## Explicit container boundary before further pipeline integration

Owned synthetic experiment: direct current ffprobe with file/pipe protocols accepts a valid local .m3u8 and reads its owned MPEG-TS segment; adding format_whitelist rejects it while MP4 control succeeds. A disguised .mp4/.bin playlist was already rejected by this Linux build's extension rules, so do NOT claim the current captured UI path was demonstrated to leak arbitrary files. Make policy explicit rather than rely on incidental suffix/version behavior.

Central input-option tuple allows MOV/MP4-family, Matroska/WebM, AVI, WAV and MP3 demuxers only, in addition to existing file/pipe protocol restriction. Apply to probe, preview, encode input and output decode. Playlist/raw/other formats are unsupported in this narrow developer slice; broader product input requirements are not deleted and require explicit reviewed format/corpus expansion later. A demuxer allowlist is NOT process/hostile-filesystem isolation or proof every codec/container is safe/supported. Tests valid owned MP4 and valid HLS baseline then guarded rejection/no output; retain all real media regressions. No private files/network accessed.
