# P04 artifact-entry audit — proposal, not branch entry or phase acceptance

2026-11-01. P03 remains IN_PROGRESS,0/9 full tasks; main remains accepted P01.
This audit does not change the101-node dependency graph or open phase-04.

The graph already states artifact readiness is NOT task acceptance. P04-01 consumes
P03-01 shell/runtime and P03-07 project model/persistence artifacts, not an assertion
that every P03 queue/provider/installer/publication capability is complete. Requiring
all P03 task acceptance before any P04 work would add an undocumented gate: P03
worker/progress accepts real execution plans, while meaningful renderer/editor plans
are delivered in later phases. Conversely, declaring the broad P03 artifacts ready
would overstate their still-open cache/recovery/integration portions.

## Narrow entry deliverables to review before creating phase-04

1. `P03-01.ui_host_ready`: actual eight-area Qt shell, reproducible pinned environment,
   explicit project/user-data separation, shutdown lifecycle, no tool prerequisite
   for Settings. Existing source/native evidence is available; exact UI reference
   conformance/physical HiDPI remains a later target check, not assumed.
2. `P03-07.project_edit_boundary_ready`: immutable validated project envelope,
   revision-CAS completed commands, save/autosave/open/recovery preserving ALL
   source records, library-only relative origin handling, no implicit source write.
   Current v2 media-library batch must finish source/native review before this can
   be proposed as ready. Existing save/recovery evidence alone predates v2.
3. `P03-03.observation_boundary_ready`: content-bound unresolved observations and
   explicit cancellation/retirement, stable library identity separate from render
   assets. File observation→captured project/revision admission still needs an exact
   contract before import/drop applies records. Unknown metadata remains visible.

If accepted, add separately named readiness nodes with exact evidence refs and
change ONLY P04-01 entry prerequisites to these narrow deliverables plus approved
P01 UX contracts. Do not mark broad P03-01/03/07 artifact nodes or tasks accepted.
Do not change task counts, requirement IDs, acceptance assertions or scope.

## Still-open work must retain its own gates

- Default real job executor/scheduler, pause/retry/restart reconciliation and durable
  tool/account capability admission remain P03 requirements; no fabricated executor.
- Trusted manifest/install/activation/lease/rollback and credential/account integration
  remain open. Explicit synthetic tool tests are not installation/registry readiness.
- Cache ownership/invalidation, renderer preview/export parity, thumbnails/waveforms,
  platform/Chrome/GPU and Windows physical interaction retain later real gates.
- P04 import/bin/Explorer drop, canvas/timeline/undo and visual reference fidelity
  belong phase-04, not P03 evidence relabelling. Branch entry requires root's actual
  dependency review and normal history-preserving checkpoint decision.

Next immediate implementation remains the coherent P03 v2 persistence batch. This
proposal exists to prevent either a circular all-phase gate or premature phase claims.
