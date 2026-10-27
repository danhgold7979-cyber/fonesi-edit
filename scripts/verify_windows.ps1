param([switch]$OpenUi)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "Can uv cho moi truong developer P02. Ban san pham P12 se khong yeu cau uv/Python."
}
& uv sync --locked
if ($LASTEXITCODE -ne 0) { throw "uv sync failed" }
& uv run python scripts/check_plan.py
if ($LASTEXITCODE -ne 0) { throw "Plan validation failed" }
& uv run pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed; do not mark Windows accepted" }
$proof = Join-Path ".local" ("windows-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Path $proof -Force | Out-Null
& uv run fonesi-prototype scan | Out-File (Join-Path $proof "tools.json") -Encoding utf8
if ($LASTEXITCODE -ne 0) { throw "Tool scan failed" }
& uv run fonesi-prototype demo (Join-Path $proof "landscape")
if ($LASTEXITCODE -ne 0) { throw "Landscape render failed" }
& uv run fonesi-prototype demo (Join-Path $proof "portrait") --portrait
if ($LASTEXITCODE -ne 0) { throw "Portrait render failed" }
if ($OpenUi) {
    $metadata = Get-Content (Join-Path $proof "landscape/evidence.json") -Raw -Encoding utf8 | ConvertFrom-Json
    & uv run fonesi-prototype ui --source $metadata.source
    if ($LASTEXITCODE -ne 0) { throw "UI failed" }
}
Write-Host "P02 local proof stored in $proof. Chrome/auth/GPU/live translation need separate real checks."
