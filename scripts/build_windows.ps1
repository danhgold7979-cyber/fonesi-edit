$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($env:OS -ne "Windows_NT") { throw "Build Windows must run on Windows" }
& uv sync --locked
if ($LASTEXITCODE -ne 0) { throw "uv sync failed" }
$ffmpeg = (Get-Command ffmpeg -CommandType Application -ErrorAction Stop).Source
$ffprobe = (Get-Command ffprobe -CommandType Application -ErrorAction Stop).Source
$buildArgs = @("run", "pyinstaller", "--noconfirm", "--clean", "--onedir", "--windowed",
    "--name", "FonesiP02", "--paths", "src", "--add-binary", "${ffmpeg}:tools",
    "--add-binary", "${ffprobe}:tools", "scripts/prototype_entry.py")
& uv @buildArgs
if ($LASTEXITCODE -ne 0) { throw "Packaging failed" }
Write-Host "P02 package: dist/FonesiP02. Launch and test on Windows; this is not P12 acceptance."
