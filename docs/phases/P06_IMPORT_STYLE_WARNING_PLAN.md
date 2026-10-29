# P06-01 / SUB-02 — Visible subtitle style-loss diagnostics on import

**Date:** 29/10/2026. **Repository:** `danhgold7979-cyber/fonesi-edit`. **Only integration branch:** `develop/fonesi-full`. **Status:** plan before source edit.

## Reconciliation with master and current code

Read `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` (P06-01, P06-04/06 and P11-05), `docs/PRODUCT_REQUIREMENTS.md` §4.2, `docs/REQUIREMENTS_TRACEABILITY.md` SUB-02/SUB-05/SUB-10, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, `docs/PHASE_EXECUTION_LEDGER.md`, `docs/phases/P06_PLAN.md`, `P06_RESULTS.md`, and `src/fonesi_edit/subtitles.py`, `src/fonesi_edit/ui/pages.py` and existing subtitle/Qt integration tests.

The app already reads SRT/VTT/ASS via `pysubs2`, normalizes each event to `Caption(start_ms,end_ms,plaintext)`, and supports a persistent cue draft, per-cue Undo/Redo and direct timing lane. However an ASS source with per-event styles, position, karaoke or override tags is silently reduced to plaintext; importing then re-saving cannot reconstruct the original formatting. P06-01 explicitly requires an informative warning when an imported style is unsupported. Do not duplicate the existing cue editor or alter the FFmpeg export contract.

## Planned narrow implementation

1. Add `read_captions_with_warnings(path)`, returning the **same cue contents/timing** plus stable format-loss diagnostics. Detect ASS/SSA presentation metadata and inline ASS override tags explicitly; preserve existing `read_captions` public behavior for workers and render. Diagnostics must never claim a format/style was retained when it was discarded. Plain SRT without such tags must not display false loss warnings.
2. Wire the existing background **Mở SRT/VTT/ASS** action to the report-aware import, display format diagnostics alongside normal overlap/duration warnings, and keep them visible during cue editing/Undo/Redo and when restoring a subtitle draft after a restart. Opening a different, plain document clears stale diagnostics. Limit persisted warnings to explicitly recognized constant messages, never write original ASS styles or private source content into settings.
3. Add pure parsing tests with a generated styled ASS file (Unicode, positioned line, font/style), confirm no input bytes change, timing/text are preserved and loss is reported; clean SRT roundtrip has no warning. Add a Qt offscreen test exercising the actual Open flow, warning persistence during editing/reopen, and clearing when loading a plain subtitle.
4. Run `scripts/check_plan.py`, relevant regression/full pytest and frozen packaged proofs in Linux and Windows CI on the exact commit. Preserve the immutable source and no-overwrite policies.

## Acceptance gates

- [ ] Styled ASS import explicitly warns that visual styling/position/effects are not carried into the editable cue model.
- [ ] Text, Unicode, timing, and source file bytes are preserved; clean plain SRT avoids a false warning.
- [ ] Format warning remains visible through editing and draft recovery but clears when a new plain document is loaded.
- [ ] Linux and Windows full CI, native-host/desktop builds and synthetic frozen proof PASS on the implementation commit.

**Outside this slice:** true ASS style-preserving roundtrip, external live providers/Chinese→Vietnamese review, physical Windows/HiDPI/IME, Chrome credentials, GPU, disk/power-loss soak and intermittent SQLite issue #6. Full P06/P11 gates remain OPEN.