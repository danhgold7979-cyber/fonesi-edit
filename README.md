# Fonesi Edit — clean rebuild

Personal Windows desktop media tool, rebuilt independently from preserved requirements. **Current phases: P01 design accepted; P02 bounded local experiments with external gates open; P03 foundation and P04 editor workspace in progress. No application release or full phase/runtime acceptance yet.**

- [Master: 12 phases / 94 tasks](docs/IMPLEMENTATION_PLAN.md)
- [Current status](docs/CURRENT_STATUS.md)
- [95 requirement groups](docs/REQUIREMENTS_TRACEABILITY.md) / [438 child assertions](docs/requirements/criteria.json)
- [Technical contracts](docs/TECHNICAL_DESIGN.md)
- [Original product specification](docs/PRODUCT_REQUIREMENTS.md)

`python scripts/check_plan.py` checks plan integrity only; it does not certify semantic coverage, runtime behavior or target-platform support. Original source specs preserved; old implementation/tests/CI are not active code or new acceptance evidence. Historical visual/licensing references are labelled under docs/reference. Main history and old work are preserved externally before remote cleanup; see recovery manifest provided by parent.

## Development foundation

Python 3.12/3.13, fresh `uv.lock`: `uv sync --locked`, then `uv run fonesi-edit`.
The local development shell exposes eight areas, explicit project recovery/Save,
background same-content root-folder relink, and a real durable queue view with guarded
pause/resume/cancel-request commands. Unimplemented workflows stay unavailable, not
simulated. Reviewed source is integrated on `develop/fonesi-full`; hosted source/native and scoped frozen evidence
covers the checkpoints described in current status, not full desktop acceptance. User-data defaults
to the OS user-data directory; `--data-dir PATH` overrides it. Headless plan validation:
`uv run fonesi-edit --validate-plan docs/schemas/examples/multi-stream-composition.json`.

Read-only tool candidates: `uv run fonesi-edit --scan-tools` (UNCHECKED is not ready).
Read-only source candidates: `uv run fonesi-edit --scan-media SOURCE --exclude-root OUTPUT`.
Neither discovery command executes media tools or creates application data. For normal
work, run affected tests; reserve `uv run python -m pytest -q` for a meaningful integration
checkpoint rather than repeating unchanged passes. Platform-specific skips are not PASS.
The clean-foundation workflow targets actual Windows/Linux, Python3.12/3.13; pending
runs do not establish Windows support. See [P03 evidence and limits](docs/phases/P03_RESULTS.md).


The active integration branch is `develop/fonesi-full`; all phases remain in this repository and application. `main` is release-only and is not merged automatically. The Editor currently has a geometry-only layer workspace with Basic/Advanced transform inspector, Vietnamese property search, numeric/slider controls, reset actions and contextual disabled reasons; a local media library with a bounded 64-file drop review queue and explicit one-at-a-time import; a frame-based timeline with persisted half-open In/Out selection and named marker create/select/delete (M shortcut); and a crop/zoom inspector. It supports explicit still-frame/filmstrip and bounded waveform observations through a user-selected FFmpeg executable, but not continuous video/audio playback, synchronized A/V seek, persistent encoded proxies, a complete composition renderer or export.
