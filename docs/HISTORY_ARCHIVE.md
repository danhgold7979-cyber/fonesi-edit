# Recoverable history and clean branch reset

Remote archive checkpoint: `375518bb394e99ca61cf919469d96aabdd43a282`.
Its five exact parents preserve all old branch histories:

| Old branch | Exact tip |
|---|---|
| main | 5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d |
| develop/fonesi-full | edbb47189b0e864c74623d0a4db5b5f169f2103c |
| phase/p02-windows-packaged-proof | c3bc9973ff6fe23fba6228f9ce9035a93c58c77a |
| phase/p03-storage-durability-secrets | 2a84ad78f258eca1c99dad14983ea2c9f57a0c85 |
| rebuild | dd8a3a87b31750aa51ccfeb944017a339bf87ff5 |

Durable clean descendant `phase-01` was verified at `b1d02e7883d0c7f83221feddc861c523bf0a1cd4` (initial clean tree `18019c5b5c0a3691cfff7483dc2c5a2122eedaa5`). Main remained `5e8ac83…`. Parent verified on 2026-11-01 around04:09UTC that only main and phase-01 remain: four old non-main refs removed after archive verification. Associated draft PRs5/3/2 closed as GitHub branch-removal side effect, not merged. This record does not claim plan acceptance or runtime completeness.

Recovery: fetch retained phase-01/archive ancestry, verify the archive parents against this table, then create a new recovery branch at any exact old tip (`git branch recovery/<name> <SHA>`; push only when authorized). Never force-push a different local ancestry. Old tree equality alone is not remote-history equality. Subsequent clean commits descend from the archival checkpoint remotely; local working history may have different metadata, publication uses verified tree-equivalent normal commits.

Independent local recovery bundle and dirty-work originals remain outside this active tree in `edit-audit-20261101-v2`, including restoration proof and remote-archive-receipt.json. Original old dirty checkout was not reset/deleted. Secrets/runtime media/browser profiles are not part of the new repository. Legacy PASS is historical, never current clean acceptance.

Update verified by parent around04:14UTC: after the user explicitly confirmed replacing old Edit main with the clean baseline, main was fast-forwarded normally to `b1d02e7883d0c7f83221feddc861c523bf0a1cd4`, matching phase-01 at that checkpoint. No force/history rewrite. Both active branches then held documentation-only clean tree, not a runnable release. Subsequent phase-01 corrections are separate commits; this approval is not P01 semantic acceptance.
