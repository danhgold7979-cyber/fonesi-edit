# P03 evidence and remaining acceptance ledger

Evidence checkpoint: public source `f16dca9986fd1181363c52580b11d7cef5a8b70c`, local source `a935fccc6746eff726b26dbf352189e0f8f1a30e`, tree `b0ade7e3b53bf551981466f643e3e2fe730ff9dd`, hosted run `41277250696`. This ledger does not change the original 94 task / 95 group / 438 child-assertion denominators. Test-case count is not product completion percentage. A task closes only when its complete planned acceptance is satisfied; shared child assertions may close before either owning task.

## Child evidence assessment

Independent review accepted these exact two closures on 2026-11-01; see `docs/reviews/P03_HOSTED_EVIDENCE_AND_CRITERIA.md`:

- **OPS-03.05 — Newer schema never overwritten.** ProjectStore future SQLite version refuses before migration/WAL mutation; hosted `tests.test_projects::test_newer_database_untouched` verifies full file bytes unchanged. Project envelope future schema is rejected by `test_invalid_project_envelope_rejected[<lambda>0]`. Supported JSON saves validate existing ownership/schema before replacement. This is the project compatibility criterion, not a claim that every future repository exists or autosave is implemented.
- **OPS-04.02 — Canonical snapshot immutable.** Hosted `tests.test_composition::test_caller_and_returned_dict_cannot_mutate_snapshot` proves defensive copies and frozen snapshot. `tests.test_jobs::test_idempotence_snapshot_conflict_and_reopen` proves immutable canonical composition+seed persistence and conflicting submission rejection across reopen. Competing claims, stale versions/leases and forged lease records cannot rewrite it. Complete resolved tool/account/provider snapshot fields and artifact traceability remain P03-05 / OPS-04.01 work; this criterion addresses immutability, not field completeness.

All other P03-mapped criteria remain unaccepted until their full conjunction is proved. Native child termination alone does not close OPS-02.02, which also requires safe temporary cleanup. Pure account reference allowlists alone do not close actual job/export lifecycle criteria. Save/kill tests do not close autosave/latest-state/relink or migration-backup restore. An unavailable feature is not evidence that its failure cannot occur.

## Nine task gates: actual implementation and specific missing cases

| Task | Implemented and exercised | Remaining before task acceptance |
|---|---|---|
| P03-01 | Locked install, CLI, truthful eight-area shell, user-data paths; hosted Windows/Linux tests; actual Windows onedir/frozen schema CLI | GUI startup on actual Windows user desktop; read-only install + Unicode user-directory scenario; invalid-config quarantine; orderly owned-task shutdown integrated with shell |
| P03-02 | Project/job SQLite identity/schema guards, project JSON, CAS, transactional initialization, backups, process-kill rollback | Media/preset/artifact/history/cache repositories and version migrations; verified backup restore path and fault at every migration step; complete repository integrity/corruption integration |
| P03-03 | Bounded probe/hash, unchanged-source identity checks, exact rational time mapping, selected streams | Normalize real no-audio/rotation/VFR/malformed corpus into complete typed probe; actual Windows FFmpeg/ffprobe corpus; large-media cancellation and stream timing integration |
| P03-04 | Durable admission/idempotence/lease CAS, native owned Windows jobs and POSIX groups, termination/quiescence/crash tests | Coordinator/worker integration, progress events, queue-level pause, classified retry/blocked states, startup lease recovery, stale completion integration, UI responsiveness under workload |
| P03-05 | Immutable canonical composition+seed snapshot and pure account reference models | Fully resolved tools/account/provider/preset/matrix/output snapshot; redacted bounded log/error taxonomy; queue commands/UI/progress; preset-change and secret-sentinel integration |
| P03-06 | Reviewed ownership/no-replace/multi-artifact design only; project-file no-overwrite is a different protocol | Actual publication journal/required-artifact set/validator/retained-hardlink adapter/reconciler; source exclusions; all crash/collision/foreign-identical/cancel/disk-full/symlink/partial-set cases |
| P03-07 | Explicit atomic project save/open, backup, process-kill old/new file visibility, cooperating-writer lock | Autosave/recovery selection/relink/cache implementations and end-to-end crash/identity/invalidation tests; unknown unmarked lock recovery diagnostics |
| P03-08 | Explicit probe path only; trusted tool distribution contract | Registry/manifests/pair capability/discovery/resolver/ownership installation receipts; version leases, staging/self-test/activation/rollback/cleanup; actual Windows trusted installation and UI evidence |
| P03-09 | Pure profiles/bindings/access axes/cache-scope/account reference models, identity/freshness tests | Durable repositories and credential-reference boundary; defaults/export/log integration; profile acquisition/lease/version/path checks; live Chrome/provider handoff remains external gate |

**Child assertions accepted: 2/438 globally; 2/78 P03-mapped, 76 P03-mapped remain open/partial.** These are exact assertion counts, not a tool-completion percentage.

**Whole P03 tasks accepted: 0/9.** No main merge or phase-complete claim follows from the foundation checkpoint. P01 accepted design tasks remain separately 8/94; P02 external gates stay open. Next implementation priority is P03-06 publication protocol plus P03-04 coordinator integration, preserving worker quiescence and ownership contracts.
