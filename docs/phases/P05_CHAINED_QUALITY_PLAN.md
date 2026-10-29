# P05-06 — Verified chained quality variants (continuation)

**Date:** 2026-10-29. **Repository:** `danhgold7979-cyber/fonesi-edit`.
**Branch:** `develop/fonesi-full`. **Status:** planned before implementation; P05 overall remains OPEN.

## Inputs and gap

Reviewed `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md` P05-04/05/06, `PRODUCT_REQUIREMENTS.md` §3.2–3.3, `REQUIREMENTS_TRACEABILITY.md` SRC-05/08/09/10, `IMPLEMENTATION_COVERAGE.md`, `CURRENT_STATUS.md`, `PHASE_EXECUTION_LEDGER.md`, `P05_PLAN.md`, `P05_QUALITY_UPGRADE_PLAN.md`, `P05_RESULTS.md`, `downloads.py`, `ui/pages.py`, `storage.py`, and the quality/Qt integration tests. Commit `ded02678` has clean Linux/Windows source, build and frozen proof CI, but upgrading from an existing successful quality variant is explicitly unsupported.

## Implementable scope

1. Permit a `succeeded` single-video yt-dlp `quality_upgrade` job as the source of a **new, strictly higher target ceiling**. Preserve URL, destination, account binding and expected identity; reject unrelated/failed/missing/invalid source jobs. Retain support for original `media` downloads.
2. Select the best reported *verified* source height under the new ceiling among recent jobs, with deterministic tie-breaking; never choose a variant whose previous target ceiling is at or above the new ceiling. The worker revalidates actual video bytes/height through FFprobe before any cookie, directory or network operation. If source history/file is stale or corrupt, fail clearly rather than silently falling back or deleting it.
3. For variants verify persisted mode/target/actual height and expected `quality-upgrades/<previous-target>p/videos` path, enforce exact channel component of the source for the new output, and reject symlinks/foreign paths. Do not silently overwrite original media, previously generated variants or output files, and never mutate source files. Preserve `source_height < actual_height <= target_height` proof after downloading.
4. Extend synthetic FFmpeg/FFprobe and fake yt-dlp tests for original 180p → variant 360p at 720p ceiling → variant 720p at 1080p ceiling, choose-source priority, identity/path tampering, unchanged source and no-overwrite reruns. Include Qt enqueue regression choosing the best variant from existing jobs and distinct idempotence key.
5. Run `scripts/check_plan.py`, all source tests and production desktop/native-host + frozen proof on GitHub Actions Linux/Windows at the exact code HEAD. Record actual SHA/run results in P05 results, coverage, current status and ledger **only after CI confirmation**.

## Gates and exclusions

- Chained upgrade only succeeds when both source and new output can be independently validated, ID and channel match, and actual resolution increases.
- Existing source files and other variants must remain unchanged; no delete/replace of invalid artifacts. Existing target ceiling is a maximum, never a guarantee of a provider format.
- No claim of live provider format availability, repaired corrupt sidecars, channel resync, account/Chrome handoff, ten-platform corpus or user-device Windows acceptance.
- Never merge to `main`; no secrets/media/fixture outputs in Git.
