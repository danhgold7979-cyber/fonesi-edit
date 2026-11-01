# Windows FFmpeg reuse evaluation — candidate only, 2026-11-01

**Decision:** evaluate Gyan's versioned essentials ZIP as a reproducible candidate,
not an adopted/installed runtime. Keep existing developer FFmpeg7.1.5 evidence
separate. No binary download, execution, system PATH modification, installer or
repository publication occurred in this research pass.

## Provenance, adoption and pin

FFmpeg's own download page lists Gyan and BtbN Windows builds and identifies9.0.2
as the latest9.x stable release, dated2026-09-18. This establishes a primary-source
vendor link, not a guarantee that every binary works for Edit.
[FFmpeg download](https://ffmpeg.org/download.html)

Gyan lists9.0.2, Windows10+, x64 GPLv3 builds and separate essentials/full variants;
essentials advertises libass, font shaping, x264/x265 and other common components.
The site was updated2026-10-29. These are publisher declarations, not our capability
tests or legal compliance certification.
[Publisher](https://www.gyan.dev/ffmpeg/builds/)

Chocolatey's community FFmpeg package reported3,375,351 cumulative downloads and
34,866 for9.0.1 at this observation, with an approved version history and Gyan
provenance/checksum verification files. Counts measure package downloads, not unique
users or a quality rating. This is meaningful adoption beyond GitHub stars, but not
a security guarantee. Search/list pages had newer counts, so no synthetic exact
current total is inferred.
[Community package](https://community.chocolatey.org/packages/ffmpeg)

Candidate artifact, as published in the release asset list:

- version:9.0.2; archive: `ffmpeg-9.0.2-essentials_build.zip`
- URL: `https://github.com/GyanD/codexffmpeg/releases/download/9.0.2/ffmpeg-9.0.2-essentials_build.zip`
- published SHA256: `60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba`
- listed size:109MB (display-rounded, not an exact download-size bound)
- release source link uses FFmpeg commit prefix `946fcce07b`; full source/build and
  dependency provenance still need preservation before distribution.

[Release](https://github.com/GyanD/codexffmpeg/releases/tag/9.0.2),
[Published assets/digests](https://github.com/GyanD/codexffmpeg/releases/expanded_assets/9.0.2).
The archive digest is observed publisher metadata; bytes have NOT been downloaded
or locally hash-verified. Never use a moving `latest` alias as an immutable pin.

## Quality/security evidence and blockers

An open publisher issue reports intermittent empty ffprobe packet output after
`-read_intervals` seeks on gcc16 Windows builds, including9.0.2 full; the maintainer
responded and pointed to an upstream patch. Reported impact includes BtbN builds,
so switching vendor is not evidence of a fix. The report is not our reproduction
and does not establish that this exact essentials ZIP is affected or fixed.
[Issue240](https://github.com/GyanD/codexffmpeg/issues/240)

The issue index also lists a cold-Fontconfig drawtext crash report; its full page
was unavailable during this pass, so details/fix status remain unverified.
[Publisher issues](https://github.com/GyanD/codexffmpeg/issues)
FFmpeg's security page was found but repeated fetches timed out: advisory review
is incomplete, not “no vulnerabilities found.”
[Security source](https://www.ffmpeg.org/security.html)

## Required gates before adoption

Obtain exact archive bytes and verify pin; retain exact license/notices and complete
corresponding-source/build provenance; inspect archive entries without unsafe extract;
test both selected exe identities/version/library compatibility; run Windows actual
encode/decode/subtitle/font/seek regressions including empty-success negative cases.
Keep advertised filters distinct from actually tested capabilities. Installation
must remain explicit opt-in/per-user/versioned, no machine PATH edits, no update
while a version is leased, no overwrite/delete of linked external tools. These are
existing P02-09/P03-08 requirements, not new invented scope. Candidate evidence does
not close tool distribution, security, Windows, parity or release gates.
