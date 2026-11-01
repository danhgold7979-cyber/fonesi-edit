# Read-only source discovery boundary — P03-06 / BAT-03.04 partial

`media.discovery.scan_media` reuses Python `os.scandir`, `pathlib`, immutable
standard dataclasses, and the existing directory-pin capability in
`artifacts.filesystem.Destination`. It introduces no downloaded package or new
native handle implementation. It never calls the destination's write/publish APIs.

Inputs are an explicit existing absolute source root, explicit existing excluded
output/cache roots, and optional physical file identities already known to be
artifacts. Source root inside/equal an excluded root is an admission error, not an
empty successful scan. Nested excluded roots are pruned; staging-prefix folders,
symlinks/reparse entries and already-visited directory identities are not followed.
Known artifact hardlink aliases are excluded; other regular-file hardlink aliases
are deduplicated by identity. Missing/changed source or exclusion roots fail closed.

The bounded result contains candidate paths, examined/excluded counts and exactly
`COMPLETE`, `PARTIAL_CANCELED` or `PARTIAL_LIMIT`. Entry/result/depth caps and cancel
checks bound traversal work, not the duration of a blocking OS call. No candidate
content is read, decoded or changed. Default discovery includes all regular files,
so unfamiliar extensions are not silently removed; an optional explicit extension
filter is only a candidate filter. Actual probe/decode validation is still mandatory.
Directory traversal pins are held during traversal, not after return; results are
not enduring capabilities. Admission/use must re-open and revalidate each source.

Runnable headless entry:

```
fonesi-edit --scan-media /absolute/source --exclude-root /absolute/source/output --exclude-root /absolute/cache
```

It prints JSON candidate paths/counts and `media_validated: false`; exit 3 means
partial, exit 2 refused, exit 0 complete traversal only. No Qt or user-data/database
initialization occurs. Paths are deliberately printed only for this explicit local
command, not treated as telemetry or redacted logs.

This is the safe discovery substrate, NOT full batch UI, folder-watch deduplication,
queue admission, all source/output overlap checks, or whole BAT-03.04 acceptance.
The eventual application/coordinator must supply every configured output/cache root
and known artifact identity automatically; a caller omitting them cannot claim
that undeclared output namespaces were excluded. Native Windows junction behavior
and user-desktop integration remain target gates; no new CI was triggered.
