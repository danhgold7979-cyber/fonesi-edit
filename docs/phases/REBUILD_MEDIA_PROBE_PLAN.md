# Rebuild P02-01 / P03-03 — bounded local media probe

Scope: validate a real local media asset through installed ffprobe without shell or network URL input. This is not render/UI/Windows acceptance. Exact contracts: executable is an explicit existing absolute path; source is a regular local file; protocol whitelist file/pipe; timeout 10 seconds and stdout/stderr each at most 64 KiB. Over-limit, timeout, nonzero exit, malformed JSON, missing stream/duration or unsupported metadata fail closed. Reports expose fixed error codes, not raw source paths/stdout/stderr. Duration parsed as exact rational decimal, stream type allowlist. No thumbnail, output or source mutations.

Tests: parser missing fields/non-finite duration/oversize/invalid stream; subprocess timeout/output cap with controlled Python fixture; actual synthetic WAV through local ffprobe. Source bytes SHA before/after must match. Windows and hostile-media corpus remain unverified. Do not infer all codecs supported.
