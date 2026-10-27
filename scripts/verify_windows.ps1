param([switch]$OpenUi)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($env:OS -ne 'Windows_NT') { throw 'Run Windows checks on Windows' }
& uv sync --locked
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& uv run python scripts/check_plan.py
if ($LASTEXITCODE -ne 0) { throw 'Plan validation failed' }
& uv run pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
$proof = Join-Path '.local' ('windows-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
& uv run fonesi-edit --verify $proof
if ($LASTEXITCODE -ne 0) { throw 'Source application proof failed' }
if (Test-Path 'dist/FonesiEdit/FonesiEdit.exe') {
    & uv run python scripts/verify_packaged.py
    if ($LASTEXITCODE -ne 0) { throw 'Packaged proof failed' }
}
if ($OpenUi) {
    & uv run fonesi-edit
    if ($LASTEXITCODE -ne 0) { throw 'Desktop failed' }
}
Write-Host 'Local/source checks finished. Live platforms, translation, Chrome handoff and GPU each require their own evidence.'
