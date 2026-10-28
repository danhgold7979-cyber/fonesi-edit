$ErrorActionPreference = "Stop"
uv sync --locked
if ($LASTEXITCODE -ne 0) { throw "Dependency sync failed" }
uv run python scripts/check_plan.py
if ($LASTEXITCODE -ne 0) { throw "Plan check failed" }
uv run pytest -q
if ($LASTEXITCODE -ne 0) { throw "Source regression failed" }
uv run python scripts/build_desktop.py
if ($LASTEXITCODE -ne 0) { throw "Build failed" }
uv run python scripts/verify_packaged.py
if ($LASTEXITCODE -ne 0) { throw "Packaged proof failed" }
