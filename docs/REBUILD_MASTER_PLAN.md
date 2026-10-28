# Clean rebuild master plan — 28 October 2026

## Boundary and recovery
- Work only in `/workspace/shared/fonesi-edit-rebuild`, branch `rebuild/spec-first-2026-10-28`. User subsequently authorized normal publication of coherent checkpoints on this new branch. No force push, merge, deployment or user-computer action.
- Recoverable baseline: `5e8ac83fdcd2182b5fcb71ed2ec6825cca384a2d`, local branch `baseline/pre-rebuild-5e8ac83`; original `main` and remote history remain untouched.
- Preserve original product/editor/settings specifications, traceability, architecture decisions, artwork/evidence assets, repository instructions and third-party notices. Old reports archived under `docs/baseline-5e8ac83/`.
- After this plan-only commit, remove old executable application, tests, scripts, extension code and old build configuration from the NEW branch. Rebuild contracts and behavior from specifications; do not blindly port the alpha source. Git retains all old code. No deletes outside checkout.
- 12 phases, 94 task IDs and 95 requirement groups remain in scope. No requirement is silently deferred; partial implementation remains partial. Future TTS/ASR/OCR/tracking stays out of scope.

## Fixed engineering contracts
- Python 3.12+, PySide6 desktop, SQLite durable queue, FFmpeg/ffprobe subprocess media pipeline; pin actual tested versions in lockfile. User data separate from installation.
- Core model independent of Qt: microsecond half-open intervals, rational speed/time maps; relative geometry evaluated in output coordinates. Canonical composition for rendered reference preview/export.
- Immutable serialized job snapshots include seed, tools and provenance; never secrets. Account bindings are references; no cookie database copying or protection bypass.
- Workers are subprocesses; queue pause stops admission, cancel terminates owned process tree; restart recovers leased jobs as interrupted, not success.
- Artifacts: temporary sibling → probe/decode/duration/track checks → non-overwriting finalize → transaction records success. Preserve all source media.
- Unsupported effect/provider/auth/capability must give explicit reason, never fake output. Localhost evidence is not live-platform evidence.

## Delivery order and gates
- **P01 — Contracts, screen map and traceability**: [concrete plan](phases/P01_PLAN.md), [results](phases/P01_RESULTS.md).
- **P02 — Reproducible technical proof**: [concrete plan](phases/P02_PLAN.md), [results](phases/P02_RESULTS.md).
- **P03 — Durable core and safe work execution**: [concrete plan](phases/P03_PLAN.md), [results](phases/P03_RESULTS.md).
- **P04 — Desktop workspace and direct editing**: [concrete plan](phases/P04_PLAN.md), [results](phases/P04_RESULTS.md).
- **P05 — Downloads, sessions and source organization**: [concrete plan](phases/P05_PLAN.md), [results](phases/P05_RESULTS.md).
- **P06 — Subtitle editing and configured translation**: [concrete plan](phases/P06_PLAN.md), [results](phases/P06_RESULTS.md).
- **P07 — Unified composition and export**: [concrete plan](phases/P07_PLAN.md), [results](phases/P07_RESULTS.md).
- **P08 — Batch, audio and duration planning**: [concrete plan](phases/P08_PLAN.md), [results](phases/P08_RESULTS.md).
- **P09 — Scenes, bounded matrix solver and history**: [concrete plan](phases/P09_PLAN.md), [results](phases/P09_RESULTS.md).
- **P10 — Workflow automation and resource admission**: [concrete plan](phases/P10_PLAN.md), [results](phases/P10_RESULTS.md).
- **P11 — Integration, durability and honest coverage**: [concrete plan](phases/P11_PLAN.md), [results](phases/P11_RESULTS.md).
- **P12 — Packaging and user handoff**: [concrete plan](phases/P12_PLAN.md), [results](phases/P12_RESULTS.md).

## Test strategy and stopping conditions
Unit tests per change; real FFmpeg integration and offscreen Qt tests before local implementation claims; final aggregate regression after changes; frozen build smoke before packaging claims. UI controls audited against subproperties, not just tab names.

Full acceptance requires all phase gates. Windows/GPU/Chrome/live-source/provider gates remain NOT RUN until suitable environment and authorized configuration exist. Continue all independent code/tests. At external or authorization limit provide exact pending step, evidence and requirement IDs; never label the whole app complete.

## Progress reporting
`CURRENT_STATUS.md` is the current phase/implemented/test/remaining tracker. `docs/rebuild/coverage.json` is the per-requirement evidence ledger. Commit plan before code. Update after each verified milestone and communicate exact branch, files and test counts.
