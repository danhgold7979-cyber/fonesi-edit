# Packaging diagnostics (clean rebuild)

1. Initial frozen proof failed `Unknown encoder libx264`: Qt and system FFmpeg had same libavcodec SONAME; root collection shadowed external tool codecs. Fixed by separate media/bin + media/lib and external-process library environment isolation. No encoder check removed.
2. Second frozen proof: render2/2 +gallery-dl passed; yt-dlp failed SSLContext creation because this executor adds a stdlib-adjacent certificate policy file. Bundled the existing `codex-rejected-cas.pem` alongside frozen stdlib. TLS verification remains enabled; no cert bypass or global trust-store edits.
3. Final frozen proof4:4/4 jobs succeeded, UI opened, original source hash unchanged,35/35 source hashes matched. Linux only. The source working tree was dirty at build time and is recorded as such.

The prior alpha Windows gallery-dl failure is not closed by these Linux results. New Windows CI must test the exact published rebuild commit.
