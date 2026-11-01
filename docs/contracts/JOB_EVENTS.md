# Typed durable job diagnostics — planned P03-05 / OPS-05.03

No arbitrary messages enter the event store. An immutable Event contains fixed
code/stage enums and an optional bounded OS process exit code (signed POSIX/unsigned Windows32) (PROCESS_EXIT only).
The store adds existing job UUID, attempt, version and finite clock time. Display
text is derived from a fixed local dictionary; diagnostics never echo exceptions,
raw subprocess/network content or credential/account/profile objects. This is an
allowlist, not regex replacement that might miss a secret. No external dependency
is required: reuse Python standard enum/dataclass/json and SQLite transactions.

Design choice: separate owned diagnostic SQLite store, not a jobs schema upgrade.
An already-open older writer can outlive a schema migration even when the native
coordinator lock is held during the upgrade; no such exclusion is claimed. Reuse
owned-store receipt/original-FD/schema guards without refactoring existing correct
coordinator semantics. Viewing logs is read-only and creates nothing.

Events are observational/best-effort, NOT atomic with job transactions. A successful
command remains successful if logging fails; the result separately reports logging
unavailable. No job replay/rollback follows from a log failure. Unknown append
outcome retires the current sink without retry; some event may already exist.
Live diagnostic emission verifies current owner and exact job version/attempt, but
the stored record is historical only. Store token separates copied/replaced job
stores sharing UUIDs. No raw exception/string callback content is accepted.

Retained events are capped per job/global, with validated configuration; defaults
500/5000. This bounds retained row payload, not physical SQLite/WAL size. Retention
settings integration is still open. Reader limits and field validation apply even
to owned but corrupted rows; unknown event contents are rejected, never displayed.
A fixed error category is informational: automatic retries still require explicit
idempotency/outcome policy in the future executor, not a log category.

The diagnostic store deliberately uses DELETE journal mode, not WAL: read-only
viewing must not create WAL/SHM sidecars. Reader rejects an unexpected journal mode.
Diagnostic writes use zero SQLite busy timeout and no open-recovery retry; contention
returns UNAVAILABLE rather than delaying an already committed command with busy
backoff. OS filesystem calls/fsync are not a hard wall-clock deadline. A missing
store read returns empty without creating its directory/file. The selected UI
panel is plain text from fixed labels, with a bounded100-record query, separate
worker connection and explicit close/interruption retirement. Logging failure is
shown separately from known committed command outcome, never as permission to retry.

Before any SQLite read connection, inspect only the original pinned FD's100-byte
header and require rollback read/write versions1, current app/schema IDs. This
rejects a cleanly closed owned WAL database before SQLite can create SHM/WAL files.
Offsets18/19 are defined by the primary [SQLite file-format specification](https://www.sqlite.org/fileformat.html#file_format_version_numbers).
Identity/header are rechecked after reading. This assumes cooperating application
writers do not concurrently switch journal mode; it is not a hostile timed
mode-switch/namespace guarantee. Unknown headers are refused, not normalized.
