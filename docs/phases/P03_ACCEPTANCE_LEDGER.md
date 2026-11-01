# P03 evidence and remaining acceptance ledger

Current accepted count: **12/438 child assertions; 0/9 P03 tasks**. Latest independently verified Settings evidence: runs41324375838/41324375928 at72eb57d6; earlier accepted children retain their exact historical evidence.

Original evidence checkpoint: public source `f16dca9986fd1181363c52580b11d7cef5a8b70c`, local source `a935fccc6746eff726b26dbf352189e0f8f1a30e`, tree `b0ade7e3b53bf551981466f643e3e2fe730ff9dd`, hosted run `41277250696`. This ledger does not change the original 94 task / 95 group / 438 child-assertion denominators. Test-case count is not product completion percentage. A task closes only when its complete planned acceptance is satisfied; shared child assertions may close before either owning task.

## Child evidence assessment

Independent review accepted these exact two closures on 2026-11-01; see `docs/reviews/P03_HOSTED_EVIDENCE_AND_CRITERIA.md`:

- **OPS-03.05 — Newer schema never overwritten.** ProjectStore future SQLite version refuses before migration/WAL mutation; hosted `tests.test_projects::test_newer_database_untouched` verifies full file bytes unchanged. Project envelope future schema is rejected by `test_invalid_project_envelope_rejected[<lambda>0]`. Supported JSON saves validate existing ownership/schema before replacement. This is the project compatibility criterion, not a claim that every future repository exists or autosave is implemented.
- **OPS-04.02 — Canonical snapshot immutable.** Hosted `tests.test_composition::test_caller_and_returned_dict_cannot_mutate_snapshot` proves defensive copies and frozen snapshot. `tests.test_jobs::test_idempotence_snapshot_conflict_and_reopen` proves immutable canonical composition+seed persistence and conflicting submission rejection across reopen. Competing claims, stale versions/leases and forged lease records cannot rewrite it. Complete resolved tool/account/provider snapshot fields and artifact traceability remain P03-05 / OPS-04.01 work; this criterion addresses immutability, not field completeness.

At that original checkpoint all other P03-mapped criteria remained unaccepted; seven additional narrow closures are recorded below. Native child termination alone does not close OPS-02.02, which also requires safe temporary cleanup. Pure account reference allowlists alone do not close actual job/export lifecycle criteria. Save/kill tests do not close autosave/latest-state/relink or migration-backup restore. An unavailable feature is not evidence that its failure cannot occur.

## Nine task gates: actual implementation and specific missing cases

| Task | Implemented and exercised | Remaining before task acceptance |
|---|---|---|
| P03-01 | Locked install, CLI, truthful eight-area shell, user-data paths; hosted Windows/Linux tests; actual Windows onedir/frozen schema CLI | GUI startup on actual Windows user desktop; read-only install + Unicode user-directory scenario; invalid-config quarantine; orderly owned-task shutdown integrated with shell |
| P03-02 | Project/job SQLite identity/schema guards, project JSON, CAS, transactional initialization, backups, process-kill rollback, native offline v1 migration-backup restore to a new store | Media/preset/artifact/history/cache repositories and version migrations; WAL/live backup recovery and fault at every migration step; complete repository integrity/corruption integration |
| P03-03 | Bounded probe/hash, unchanged-source identity checks, exact rational time mapping, selected streams | Normalize real no-audio/rotation/VFR/malformed corpus into complete typed probe; actual Windows FFmpeg/ffprobe corpus; large-media cancellation and stream timing integration |
| P03-04 | Durable admission/idempotence/lease CAS, native owned Windows jobs and POSIX groups, termination/quiescence/crash tests; local live-owner command inbox and bounded numeric Qt progress | Production scheduler/executor integration, queue-level pause, classified retry/blocked states, startup lease recovery, stale completion integration, UI responsiveness under workload |
| P03-05 | Immutable composition/seed/required-output policies; pure account references; actual bounded own-thread queue view with no snapshot/credential selection (local5cbb079); later reviewed selected pause/resume/cancel-request CAS and explicit Qt retirement | Fully resolved tools/account/provider/preset/matrix snapshot; complete executor/provider diagnostic integration (local typed bounded store/selected viewer implemented); production scheduler wiring (local owner routing/progress slice implemented); preset-change/secret-sentinel integration |
| P03-06 | Same-DB journal, semantic media/subtitle validation, streaming retained staging, live-anchor per-member publication and exact-set job/history commit; conservative new-owner quarantine with4real child kills; bounded exclusion-aware candidate CLI; actual Windows live-session completed/canceled owned cleanup and typed retirement | Incarnation-safe automatic restart recovery; automatic restart-safe staging cleanup; complete exclusion/source-overlap policy integration; remaining disk-full/permission/native Windows crash and lifecycle gates |
| P03-07 | Explicit atomic file save/open and process-kill evidence; local typed completed-command session CAS, explicit recovery choice/shell Save, atomic original-base metadata, same-content asset/font relink and actual background root-folder picker | Actual editor commands/timer autosave; unknown-origin recovery/latest-state ordering; cache and explicit different-content replacement; end-to-end crash/identity/invalidation and native GUI tests; unmarked DB/lock recovery diagnostics |
| P03-08 | Metadata-only inventory UI, explicit-path no-fallback, actual pinned Windows FFmpeg/ffprobe functional pair through Qt, trust-reset/retirement gates; local durable explicit preferences | Verified registry/resolver/ownership installation receipts; persisted preference native verification; version leases, staging/self-test/activation/rollback/cleanup; actual Windows trusted installation, automatic startup scan |
| P03-09 | Reviewed pure profiles/bindings/access models plus owned metadata persistence, CAS/defaults, one login identity per profile/platform, separately scoped channel rights and unlink-only metadata | Credential-reference/secure-store boundary; job/export/log integration; full cache retention; profile acquisition/lease/version/path checks; actual Windows/live Chrome/provider handoff |

**Child assertions accepted: 12/438 globally; 11/78 P03-mapped, 67 P03-mapped remain open/partial.** These are exact assertion counts, not a tool-completion percentage.

**Whole P03 tasks accepted: 0/9.** No main merge or phase-complete claim follows from the foundation checkpoint. P01 accepted design tasks remain separately 8/94; P02 external gates stay open. Next implementation priority is P03-06 publication protocol plus P03-04 coordinator integration, preserving worker quiescence and ownership contracts.


Local implementation status updated after reviewed5535e56/5cbb079 checkpoints;
these are not newer hosted or accepted-criterion evidence. Historical accepted
2-child receipt remains pinned to its original source. Selected queue-command source is now scoped reviewed; native/live-routing/progress
gates remain open, so no new complete criterion or task acceptance follows.

Four OPS-03 test implementation fields now explicitly record PARTIAL_LOCAL_VERIFIED; their full assertion gates are still unaccepted. Source reviews and affected tests are real progress, not additional PASS criteria.

## Later hosted coverage, not extra closures

Reviewed implementation above is now published through6162293. Full505-case
run41295642110 (5d8a3389), affected48-case repair41296135792 (9b62a1a7), and
Windows4-case plus five frozen CLI boundary41296433758 (6162293) establish the
scoped evidence in P03_RESULTS. Initial aggregate failures remain FAIL, then
causally corrected by affected runs; no blanket final aggregate PASS. Actual
Windows queue/Qt lifecycle, live journal/publication, quarantine and project
recovery tests now have hosted evidence, not only local evidence. Still no complete
worker/progress/cleanup/provider/GUI-display/release gate or extra child closure.
P03-08 also has pinned-pair functional observation on the recorded Linux FFmpeg
fixture, not a verified Windows tool registry/installation/lease capability.

## Additional independently accepted child assertions (run41303347554)

- **BAT-03.04:** session-derived nested output/cache roots excluded from real recursive
  scanner; exact case passed all4targets in41300558073. That run's unrelated precision
  failure remains recorded; scan_sources/exclusion logic unchanged. Not full batchUI.
- **OPS-06.02:** native no-replace collision inserted between validation/link and late
  foreign-identical destination remain unchanged; no false artifact/success row.
- **OPS-06.04:** foreign identical final and corrupt stage cannot become success;
  original live anchors + current validation/journal required. Restart staysUNKNOWN.

Exact testcase/source/runtime/hash mappings are in records.json and independent
P03_HOSTED_WORKER_CLEANUP_AND_CRITERIA_41303347554.md. Current run4SUCCESS:
Linux3.12.15/3.13.17 each100PASS10SKIP; Windows3.12.10/3.13.17 each108PASS2SKIP.
Actual Windows9completed-cleanup integration cases and27progress cases passed;
actual FFmpeg media/subtitle integration skipped on allhosted targets. No frozen
rerun or whole aggregate claim. Cancel-temp cleanup, fullworker/UI routing, renderer,
restart and provider gates remain OPEN; completed cleanup does not close them.

## SRC-08.04 narrow closure (41306207422)

Actual Windows owned Python child/descendant cancellation, typed retirement, DB
acknowledgment and object-bound own-stage cleanup passed. Prior41304594711
preservation and foreign-handoff cases remain unchanged. Unknown lifecycle, restart
and POSIX retain stages; no FFmpeg, full queue, task or phase acceptance. Independent
review: `docs/reviews/P03_TYPED_RETIREMENT_HOSTED_41306207422.md`.

## OPS-02.02 narrow combined cancellation closure (41308555823)

Actual selected Qt command→live owner→owned child/descendant→typed retirement→
DB acknowledgment→only-owned Windows stage deletion passed, preserving source and
foreign sentinels with no output/history success. Linux explicitly retains stages.
All16affectedcases passed on all4targets; Python decoder is not FFmpeg proof.
Default production scheduler/provider/restart/full task gates remain open. Exact
receipt review: `docs/reviews/P03_QUEUE_LIFECYCLE_HOSTED_41308555823.md`.

## OPS-05.03 narrow typed diagnostics closure (41310543152)

Actual worker exit7 with private stderr→allowlisted bounded durable event→selected
Qt fixed diagnostic passed all4targets, with row caps, foreign/corrupt refusal,
unknown/no-replay and known command-outcome preservation. Separate logs are not
job/publication/retry authority; default executor/provider/retention settings and
physical DB size remain open. Ledger8/438, P03 8/78, tasks0/9.

## Migration backup restore accepted (run41312580297)

**OPS-03.04**: real unmodified rollback-format v1 migration backup restores into
a NEW exclusive owned store, reopens/migrates with original IDs/content/CAS versions
and unknown origins, while live DB/backup stay unchanged. Actual CLI and refusal/
fault cases PASS all4targets (72cases each). Exact source/tree/runtime/receipt
mapping in records.json and P03_BACKUP_RESTORE_HOSTED_41312580297 review. WAL-header
inputs remain refused; v2 positive is an explicitly prepared rollback fixture. No
GUI switching/latest-state/frozen restore/full-task acceptance.

## Settings inventory and selected pair (41324375838 / 41324375928)

Accepted exact TOL-01.03 missing-tool Settings startup, TOL-02.01 explicit-path priority/no fallback, and TOL-03.01 compatible pair tested through actual Windows Qt. Four source targets each55PASS0SKIP; two native Windows targets each selected-pair success plus swapped-role refusal, with5+1 owned retirement receipts. Exact cases, source/tree/runtime and artifact hashes are in records.json and the independent P03_PAIR_SETTINGS_HOSTED_41324375838_41324375928.md review.

TOL-01.03 maps P01-08/P04-08, so P03 rises only9→11/78; global9→12/438. All P03 tasks remain0/9. Automatic startup scan, persisted selection, verified registry/version leases, installer/update, GPU/full codecs, frozen pair and renderer remain open. No broader source-clause/group acceptance.
