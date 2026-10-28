# Clean rebuild — live status

**Checkpoint 2: playable desktop + verified frozen Linux pipeline; continuing implementation. Not a full release.**

- Branch: `rebuild/spec-first-2026-10-28`; main/base preserved at `5e8ac83`.
- Plan checkpoint published: `fe00cff1b55495b10c53eb3b5a99d465d54c2916` (all 12 plans before code).
- Old executable source/tests/scripts/extension removed only on new branch; clean code written from original specs. Git retains old implementation.
- **Latest aggregate: 59 tests passed, 0 failed, 0 skipped (18.54s Linux); compileall passed.** Tests do not mean all 95 requirement groups accepted.
- **Current focus: P04 advanced timeline/shortcuts, P09 persisted history, P10 workflow completeness; P12 Windows CI acceptance pending.**
- No full phase except plan checkpoint declared complete; advanced UI, workflow/history integration and target-platform evidence still open.
- User authorized normal publication of coherent checkpoints to this new branch; no force push, merge or deployment.

| Phase | Current evidence | Gate |
| --- | --- | --- |
| P01 | Master + all 12 phase plans, 94 tasks and 95 requirement groups retained before implementation. Baseline history/requirements/assets/notices preserved. | OPEN; see [results](phases/P01_RESULTS.md) |
| P02 | Pinned installed toolchain; headless Qt startup; real CPU H.264/AAC encode/probe/full decode in Unicode path. | OPEN; see [results](phases/P02_RESULTS.md) |
| P03 | Qt-independent versioned project model; rational time maps; immutable SQLite jobs, dependencies, pause/cancel/retry/lease recovery; process groups; safe artifact publication; backup/autosave. | OPEN; see [results](phases/P03_RESULTS.md) |
| P04 | Runnable Vietnamese 8-tab desktop; canvas drag/resize/rotate/lock/visibility/nudge; one-gesture undo; property inspector/keyframes; layer/cue timing drag; project save/open/autosave; background probe/reference rendering. | OPEN; see [results](phases/P04_RESULTS.md) |
| P05 | Public yt-dlp/gallery-dl adapters, URL registry, explicit scan completeness, staged validated media publication; 10-platform account settings, isolated Chrome profile schema/launch checks, fail-closed identity readiness. | OPEN; see [results](phases/P05_RESULTS.md) |
| P06 | SRT/VTT/ASS cue import/export with loss warning; language policy; edit/lock/time-map/validation helpers; bilingual burn; opt-in LibreTranslate adapter, cache and durable character quota/uncertain-outcome protection. | OPEN; see [results](phases/P06_RESULTS.md) |
| P07 | Canonical Pillow compositor shared by reference/export; text/font-glyph validation, logos, masks blur/mosaic/color, relative transforms, keyframes/easing, trim/speed/fit/crop/blur background, CPU render and output full decode. | OPEN; see [results](phases/P07_RESULTS.md) |
| P08 | Recursive safe folder scanning; batch dry-run and per-input validation failures; own subtitles resolved per clip; duration policies cut/speed/loop/freeze; audio mixer supports gain/delay/fade/loop/solo/limiter in renderer. | OPEN; see [results](phases/P08_RESULTS.md) |
| P09 | Natural scene sort/content IDs; bounded seeded lazy W/K/unique solver, exhaustive small-space proof vs bounded timeout; editable matrix revalidation, CSV, per-row project/queue and transactional reservation/history primitives. | OPEN; see [results](phases/P09_RESULTS.md) |
| P10 | App-open schedule anti-overlap primitives, stable-file watcher, owned-cache cleanup with leases, resource metrics/admission helpers and batch/rolling dependency planner. | OPEN; see [results](phases/P10_RESULTS.md) |
| P11 | First clean-code regression plus real renderer and worker checks; explicit per-group ledger. | OPEN; see [results](phases/P11_RESULTS.md) |
| P12 | Runtime CLI entry and frozen-worker dispatch design available; third-party notices preserved. | OPEN; see [results](phases/P12_RESULTS.md) |

## External acceptance NOT RUN
Windows packaged runtime; Windows real Google Chrome/account handoff; GPU; live per-platform full-channel/pagination/auth; configured provider Chinese–Vietnamese quality and costs; real HiDPI/IME/audio. These are not replaced by mocks/Linux/localhost.

## Inspectable artifacts
- [Master plan](REBUILD_MASTER_PLAN.md) and [95-group ledger](rebuild/coverage.json).
- [Actual Qt editor screenshot](rebuild/evidence/editor-checkpoint.png), synthetic scene, not live source evidence.
- [Measured environment proof](rebuild/evidence/environment.json).

For precise implemented/tested/remaining scope, read each phase result. Historical alpha reports remain in `baseline-5e8ac83/` and `docs/evidence/`; they are not evidence for rebuilt code.

## Checkpoint 2 verified deliverables
- Playable normalized proxy/audio and waveform; Qt really decoded a video frame in tests.
- Clip/audio/motion/preset/relink UI; background watcher and resource admission connected.
- **Frozen Linux final-code proof PASS**:4 real jobs (batch render, matrix render, yt-dlp video, gallery-dl image), UI opens, source unchanged,35 bundled source hashes match. [Proof](rebuild/evidence/packaged-proof.json). This does not certify live social sources or Windows.
- CI source check on prior published commit `d8c2cb2` passed [run40633636141](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40633636141). New checkpoint adds a Windows source+frozen acceptance job; status is pending until exact remote SHA/run is read.
- Build provenance marks local build dirty because it preceded commit; source hash audit identifies exact code. No false clean-build claim.
- New generated screenshot/frame evidence remains local pending explicit public-image publication approval; code and JSON proof are published independently. [Trusted tool sources](rebuild/TRUSTED_TOOL_SOURCES.md).
