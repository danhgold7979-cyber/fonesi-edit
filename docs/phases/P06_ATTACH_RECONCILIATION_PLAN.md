# P06-06 / OPS-06 — Verify existing sidecars before editor attachment

**Date:** 2026-10-29. **Repository/branch:** `danhgold7979-cyber/fonesi-edit` / `develop/fonesi-full`. **Plan committed before code.**

## Context and requirements

Reviewed the 12-phase master plan, PRODUCT_REQUIREMENTS §4.2, REQUIREMENTS_TRACEABILITY SUB-02/SUB-10 and OPS-06, IMPLEMENTATION_COVERAGE, CURRENT_STATUS, existing P06 plan/results, `src/fonesi_edit/ui/pages.py` (`SubtitlesPage.attach`), `src/fonesi_edit/subtitles.py` and `tests/test_app_integration.py`.

P06 already attaches independent source/target layers to a chosen editor clip and hashes the caption snapshot into a filename. The current `if not path.exists(): write_captions(...)` skips writing on an existing name **without validating its actual cue timing/text**. An externally edited, corrupt or stale cache file could silently be attached as the wrong subtitle track despite the hash being calculated for different content. Both generated source and target sidecars require read-back checks before modifying the editor composition.

## Source and tests

1. On attachment, validate any existing destination before reuse: reject symlinks; parse SRT and compare every `(start_ms,end_ms,text)` against the requested target or source cues, in order. Reject differing content or unreadable files, do not overwrite or silently delete them.
2. For a missing destination, retain `write_captions(overwrite=False)` atomic no-overwrite semantics; an arriving competing file is a conflict, not permission to overwrite. Validate source and target before `editor.begin()` or changing selected clip/layers.
3. Add Qt integration regressions with actual generated bilingual SRT, then edit target/source sidecar under the same hash and attempt reattach. Verify rejection, preserved bytes and unchanged editor composition; verify valid existing files remain reusable.
4. Run plan validator, focused tests, full Linux/Windows source suite and packaged native-host/desktop proof. Update results/status/ledger only for verified runs and exact SHA.

## Acceptance gates

- [ ] Existing generated target/source sidecars are reused only after cue/timing read-back matches.
- [ ] Corrupt/edited/symlinked sidecars cannot be silently attached, overwritten or removed.
- [ ] Failed reattachment leaves editor state, source files and existing user-edited bytes unchanged.
- [ ] Linux and Windows CI plus packaged proof pass on the exact implemented commit.

External live translation, 10-platform/Chrome authenticated media, physical Windows/HiDPI/GPU, FAT/exFAT and power-loss testing remain separate, unresolved acceptance gates.