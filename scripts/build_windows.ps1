$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($env:OS -ne 'Windows_NT') { throw 'Build Windows must run on Windows' }
& uv sync --locked
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& uv run python scripts/build_desktop.py --native-host
if ($LASTEXITCODE -ne 0) { throw 'Production packaging failed' }
Write-Host 'Development build: dist/FonesiEdit. Run scripts/verify_packaged.py before accepting this build.'
