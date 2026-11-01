# Account/profile metadata persistence — P03-09 / P03-02 partial

`accounts.store.AccountStore` persists only the already reviewed BrowserProfile and
Binding/SourceAccess dataclass fields, with a strict bounded JSON allowlist, row identity checks,
version CAS, observed_at timestamps, foreign keys and explicit platform defaults.
It reuses Python SQLite, existing bounded SQLite startup-read recovery and owned DB
receipts. No new downloaded package/native adapter/browser operation is introduced.

A new distinct account database has exact schema/application identity, original
opened file identity retained for its lifetime, transactional initialization, WAL
and full synchronous writes. Existing unmarked/foreign/newer/malformed stores are
refused before WAL/schema mutation. Even preexisting unmarked zero-length or
empty version0 SQLite files are refused: initialization requires successful exclusive
creation by this constructor. There is no speculative migration or silent adoption. Initialization crash after schema commit but before receipt remains
fail-closed/manual, not advertised as automatically recovered.

Stored browser/web/bridge flags are LAST-KNOWN observations with their original
observed/check timestamps, not refreshed permission on reopen. Existing partial
account/rights preflight, real profile lease, connector capability and fresh identity
checks remain separate mandatory integration gates. No credential value, cookie,
password, Chrome filesystem path or browser process handle can enter this store's
closed model shape. User-provided labels/identity strings are metadata, not a secret
vault; credential-store references and actual secure-store integration remain OPEN.

Same profile UUID cannot silently change installation/ownership identity; label,
color and observation updates use expected version. Binding profile/platform/account
identity changes require advancing generation, invalidating old references. Exactly one signed-in Binding identity exists per (profile,platform), enforced by
a database UNIQUE constraint on insert AND update, matching the reviewed Catalog.
Multiple channel/page SourceAccess objects share that one login binding/account scope
without creating another Chrome profile or pretending channels are login identities.
Rights observations are versioned and keyed by current account identity/generation;
rebind/refresh cannot reuse an old-scope rights cache. Unlink cascades only metadata.
Defaults validate platform and binding version and CAS-match the previous default
binding ID. Unlink deletes only that binding and its default reference in one
transaction; it never opens or removes browser data or source files. Changing a
binding's platform clears its old default so cross-platform defaults cannot survive.

No account/job/export/credential integration, actual authenticated provider test,
profile-path/version persistence, complete cache eviction policy, or full P03-09 acceptance is claimed.
The repository is a local metadata prerequisite, not a live browser controller.

The superseded unpublished prototype schema is not adopted: its differing exact
schema/receipt hash fails closed. No user store or remote code used that prototype.
