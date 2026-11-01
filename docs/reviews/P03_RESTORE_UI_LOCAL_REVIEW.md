# New-store restore UI — source CLEAR for target validation

2026-11-01. Scoped read-only source review, no aggregate repeat. Verified supplied RestorePanel, shell and UI test hashes.

Dedicated QThread calls reviewed restore without sharing GUI ProjectStore connection. No active-store replacement or silent newest-backup choice. Picked destination is projects.sqlite3 in explicitly selected folder; original exclusive no-overwrite semantics remain. Copied-byte observations explicitly do not mean validation/ownership success. Worker identity filters stale progress/completion. Completion checks wait(0) before release and honors actual confirmed outcome even when cancellation arrives late. Domain and unexpected errors use sanitized notices; uncertain destination/receipt is retained and never automatically retried/deleted.

MainWindow background_busy/request_stop/closeEvent now include restore; existing main retirement loop consumes that property, so the window/store cannot retire while restore is still running. Parent-owned worker lifetime and deferred deletion follow existing Qt pattern. Restored-store use is explicit separate startup via --data-dir, matching main's projects.sqlite3 filename; active session remains unchanged.

Independent actual restore while GUI event loop remains alive and active newer DB unchanged, plus cancellation/close held-worker uncertainty case: **2 PASS /2 deselected, exit0** on Linux offscreen. No native Windows, real desktop picker, frozen restore or current WAL-backup support inferred. Remaining two causal tests inspected, not repeated. No blocker found. Source CLEAR for corresponding target-native validation; no extra criterion closure or full project recovery/task acceptance.

Workflow verified SHA256 `185cb1018a074b4ea141eeb744d0d96bc4ad8cf3ed5c9ab6fb960222131e2a0a`: [restore-ui] ALONE runs unchanged four-target matrix with new UI + shared shell/recovery/root-relink tests; necessary Linux Qt stays enabled, unrelated aggregate/plan/schema/frozen excluded, unmarked default unchanged. CLEAR for scoped CI, no reruns.
