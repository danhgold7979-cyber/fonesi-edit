# Fonesi Edit — clean rebuild

Personal Windows desktop media tool, rebuilt independently from preserved requirements. **Current phase: P01 design accepted; P02 bounded local experiments; P03 fresh foundation in progress. No application release or full phase/runtime acceptance yet.**

- [Master: 12 phases / 94 tasks](docs/IMPLEMENTATION_PLAN.md)
- [Current status](docs/CURRENT_STATUS.md)
- [95 requirement groups](docs/REQUIREMENTS_TRACEABILITY.md) / [438 child assertions](docs/requirements/criteria.json)
- [Technical contracts](docs/TECHNICAL_DESIGN.md)
- [Original product specification](docs/PRODUCT_REQUIREMENTS.md)

`python scripts/check_plan.py` checks plan integrity only; it does not certify semantic coverage, runtime behavior or target-platform support. Original source specs preserved; old implementation/tests/CI are not active code or new acceptance evidence. Historical visual/licensing references are labelled under docs/reference. Main history and old work are preserved externally before remote cleanup; see recovery manifest provided by parent.

## Development foundation

Python 3.12/3.13, fresh `uv.lock`: `uv sync --locked`, then `uv run fonesi-edit`.
The current shell exposes eight navigation areas and validated project open only;
unimplemented workflows are explicitly unavailable, not simulated. User-data defaults
to the OS user-data directory; `--data-dir PATH` overrides it. Headless plan validation:
`uv run fonesi-edit --validate-plan docs/schemas/examples/multi-stream-composition.json`.

`uv run python -m pytest -q` runs source tests. Platform-specific skips are not PASS.
The clean-foundation workflow targets actual Windows/Linux, Python3.12/3.13; pending
runs do not establish Windows support. See [P03 evidence and limits](docs/phases/P03_RESULTS.md).
