# Rebuild P02-09 / P03-08 / P04-08 — session-only existing media tool selection

Plan before code: a native dialog selects already installed trusted FFmpeg and ffprobe files without PATH edits, installation, download, elevation or persistent configuration. UI explicitly says session-only and origin trust is the user's prerequisite; CLI version/encoder output is capability evidence, NOT signature/vendor trust or complete registry acceptance.

Two explicit native absolute existing files, resolved paths, distinct executables. Worker calls bounded shell=False -version for each and -encoders for FFmpeg,10s/64KiB each, cancellation/close waits. Parse only exact expected version-line prefixes and bounded ASCII version tokens; require declared video libx264 and audio aac encoders. No raw stdout/stderr or paths in error codes. Actual rendering still validates media/output separately.

Draft edits invalidate prior verification; an async result applies only to its exact unchanged draft. Apply only after successful check and fresh no-active-media-job guard (main export/import or batch); never silently fallback from a bad explicit path to PATH. Existing in-flight jobs cannot be changed. Selected tools flow to current/new batch dialogs. Changing tools clears cached inspection/digests and requires explicit reinspection; preserve original media references/edits/project. No file/tool binary changes, no source overwrite.

Tests: actual trusted CLI positive; missing paths/wrong roles/missing encoders/nonzero/oversize/cancel; stale draft result, busy apply refusal, parent propagation and inspection invalidation; worker Escape/Close safe. UI retains existing theme. Installer/trusted manifests/tool ownership/version leases/persistence/rollback remain open, not hidden by this slice.

Parent Close must resume automatically after child tool/batch/subtitle workers safely finish, using one completion subscription per worker and a deferred UI close after child state clears. Do not leave a stale waiting message requiring a hidden second close. Reset closing state; test this explicitly. Each verification attempt also gets a fresh generation, even when path text is unchanged.
