# P01 — Design before new implementation

Revision clean-2026-11-01; branch phase-01 (initialized after recovery inventory). Status ACCEPTED_DESIGN against independent review dbc3f30; runtime not accepted. Master alignment: eight areas, all 94 tasks and 95 original requirement IDs; technical proposals do not remove functionality. Read the three source specs and master before executing. Design deliverables are subject to independent review, not old implementation results.

## P01-01 — Requirement baseline and executable criteria
- Input: three immutable original specs; 95 rows of REQUIREMENTS_TRACEABILITY; 94 original task scopes.
- Output/interface: `requirements/criteria.json`: group ID, stable child ID, exact source section/quoted clause, owning task IDs, default, invalid-input behavior, acceptance scenario, evidence kind, status, evidence reference. `tasks.json` retains original task ID/scope.
- Dependency: none; feeds every other task. No requirement may silently move to deferred scope.
- Errors/cancel: duplicate IDs, missing source clause, uncovered option or orphan task fail validation; interruption leaves prior complete inventory unchanged, draft in separate file.
- Tests: enumerate all 95 groups, 94 tasks; references resolve; source-backed child criteria account for every bullet/table option; independent reviewer compares to source, not merely counts.
- Acceptance: no generic “works” criteria, each group decomposed enough that one passing option cannot certify remaining options; defaults and unsupported/error policy explicit. Tool/Chrome and ten platforms remain mandatory.

## P01-02 — Eight-area interaction map
- Input: PR §2, ED §1–9, SB §1; P01-01 criteria.
- Output: `contracts/UX.md` with Overview, Downloads, Subtitles, Editor, Batch, Scenes/Matrix, Queue/History, Presets/Settings. Each area maps controls to requirement/command, basic/advanced, units, disabled reason and recovery route.
- Interface: a shared project selection/command bus, not eight disconnected demo pages; Editor media/preview/inspector/timeline layout. Red circle is a conversation marker, not an application rebrand.
- Errors/cancel: distinguish empty/loading/error/blocked/stale preview; leave dirty project unchanged on navigation cancellation; stale result cannot overwrite newer selection.
- Dependency: P01-01. Tests: source-to-control coverage, keyboard/focus order, mock-wireframe traversal for each state, no clickable unimplemented success action.
- Acceptance: eight unique navigable areas; all controls have units/defaults and same scoped edit model; source requirement review finds no missing area.

## P01-03 — End-to-end interaction sequences
- Input: UX and PR workflow clauses; current project/account/preset concepts.
- Output: UX numbered flows for URL→scan/select→download; folder→preview→batch; subtitle→translate/edit; logo manipulation; scenes→matrix→queue; failure→repair→resume. Count ordinary actions excluding first-time file/login setup.
- Interface: each enqueue path invokes shared preflight and immutable snapshot, yields stable job IDs; result opens only after artifact validation.
- Errors/cancel: cancel picker/scan/drag/translation, repeated enqueue, navigate during background completion; define pending edits vs committed commands. No lost edits or duplicate jobs.
- Dependency: P01-02 plus P01-07 job contract. Tests: scenario walkthrough shows initial state, action, state mutation, cancel/retry outcome; second click same request returns same job.
- Acceptance: common batch flow needs no per-file mandatory edit; all six flows reach validated result or actionable blocker without fake progress.

## P01-04 — Preset scope, manual override and locks
- Input: PR §5/8/9; ED §1/8/10; clip properties, typed paths and keyframe IDs.
- Output/interface: `contracts/PRESET.md`, `resolve(defaults,preset,overrides,locks)` and impact-preview contract; one clip/selection/batch scopes; immutable preset versions, migration and import validation.
- Errors/cancel: reject unknown schema, unknown properties, incompatible values/assets; cancel impact preview applies nothing; locked properties/keyframes survive auto; explicit reset only changes selected properties.
- Dependency: P01-01 and composition schema P01-07. Tests: precedence table with conflicting values, mixed clip locks, nested styles/keyframes, undo and pending/running job isolation.
- Acceptance: every precedence case has exact expected value and provenance; applying a new preset never changes a running snapshot; user edits are distinguishable from inherited defaults.

## P01-05 — Matrix, duration and filesystem rules
- Input: PR §3.3/5–7/10; scene/angle identity, source metadata and output root.
- Output: `contracts/PLANNING.md`: W and K comparison scopes; unique/history/reservation; duration equations including overlaps; missing-sub options; Unicode naming, collision and already-processed identity.
- Interface: pure planners return typed valid plan or reason (infeasible/proven, search_budget_exhausted, canceled, invalid_input); output names reserve through publication contract, not pre-check alone.
- Errors/cancel: W/K impossible, empty scene, locked conflicting row, insufficient duration, path conflict, disk full; bounded search canceled returns no enqueue/reservation; sources never renamed by logical scene naming.
- Dependency: P01-07 identity/publication. Tests: exhaustive small matrix oracle; rational duration cases; identical display names/different IDs; rename same content; failed reservation retry; canceled batch no partial enqueue.
- Acceptance: hard constraints never relaxed; each duration mode preserves all required scenes; every collision has no-overwrite behavior; no implicit multi-clip fallback in one-video mode.

## P01-06 — Corpus, measurements and release evidence
- Input: every media/language/error/platform clause; target Windows requirement.
- Output: `contracts/VERIFICATION.md` and later generated corpus manifest with source/license/hash/parameters; exact measured gates and distinction proposed vs achieved.
- Interface: report contains commit, OS/hardware/tool hashes, corpus hashes, commands, samples, quantiles, pass/fail, evidence path; live results include timestamp/account scope redacted and capability cell.
- Errors/cancel: missing codec/hardware/font/source permission becomes NOT_RUN/BLOCKED, not PASS; interrupted benchmark records incomplete samples; test artifacts cannot become user's production media.
- Dependency: P01-01/07. Tests: fixture-generation reproducibility, manifest validation, negative sentinel to prove comparison actually fails, report completeness.
- Acceptance: every required axis has fixture or explicit external prerequisite; timing/image/audio metrics have algorithm and threshold; unknown user's hardware is explicitly unresolved, never invented.

## P01-07 — Shared domain and durable workflow contracts
- Input: PR/ED/SB plus decisions under test; not old code.
- Output: `contracts/COMPOSITION.md`, `contracts/JOBS.md`, `TECHNICAL_DESIGN.md`, ADR-0001. Versioned project/preset/plan and artifact interfaces; authoritative evaluator; migration and process ownership rules.
- Interface: composition validation/evaluation, job state transition/CAS lease, snapshot hash, journaled output publication/reconciliation, tool/profile version leases.
- Errors/cancel: schema newer than supported opens read-only error, bad ref blocked, duplicate layer/timepoint invalid; stale workers rejected; crash boundaries enumerated; cancellation publication race has one durable winner.
- Dependency: P01-01; resolves P01-03/04/05 interfaces. Tests: schema negative vectors, evaluator boundaries, state transition table, crash/fault injection matrix, publication foreign-file sentinel.
- Acceptance: all mandatory fields/types/units/defaults/constraints specified, compiler and preview consume same evaluator, no “file exists means succeeded”, DB and filesystem commit gap has deterministic recovery.

## P01-08 — Tool/Chrome/account readiness UX and evidence gates
- Input: SB entire spec, ten source platforms, tool requirements by workflow.
- Output: UX settings tables and `decisions/ADR-0001.md`; tool discovery/install/verify/rollback and Chrome web identity/connector bridge/source rights independent checks.
- Interface: ToolInstallation ID/version/path/hash/ownership/capabilities; BrowserProfile ID/owned user-data-dir; AccountBinding platform/profile/identity refs plus checked_at. Never secret material in project.
- Errors/cancel: tool path explicit but invalid must not silently fallback; install cancellation preserves previous version; busy lease prevents cleanup; Chrome locked/expired/challenge/mismatch/bridge blocked remain distinct.
- Dependency: P01-02/07. Tests: walk missing-tool/install failure/rollback; Chrome A FB_A+TT_A vs Chrome B FB_B; mismatch on resumed job; login web success with bridge fail remains blocked.
- Acceptance: all ten platforms represented without supported claim; fixes target correct readiness axis; actual Windows Chrome handoff remains P02 acceptance, not inferred from design.

## P01 gate and result format
No ACCEPTED until all eight design deliverables exist and independent reviewer verifies source coverage and contracts. Results list task, file/section, check command or review record, outcome, remaining blockers. A P01 PASS cannot count as runnable application evidence. Current: all8 design tasks accepted after independent review dbc3f30; zero runtime feature criteria passed.

## Independent review corrections
Pinned4916a67 review identified prose-only coverage gaps, hash-vs-physical publication ownership, multi-artifact commit ordering, digest projection, stream/cue ambiguity, dependency cycles/cancellation contradiction and keyframe/ducking schema ambiguity. Corrections include explicit438 child assertions/392 mapped source clauses, all shortcut table rows individually, Draft2020-12 schema, content/execution digest separation,101 acyclic artifact milestones and final required-artifact-set publication. Reviewer must recheck; author changes are not acceptance.
