# Builds tools/sirhurt-setup/setup.py into a single Windows .exe with Nuitka.
# Run from anywhere: powershell -ExecutionPolicy Bypass -File tools\sirhurt-setup\build.ps1
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

& $python -m nuitka --onefile --assume-yes-for-downloads --windows-console-mode=force --output-dir="$PSScriptRoot\build" --output-filename="SixSirhurtUnretardifier9000Pro.exe" "$PSScriptRoot\setup.py"
if ($LASTEXITCODE -ne 0) { throw "Nuitka build failed with exit code $LASTEXITCODE" }

Write-Host "Built $PSScriptRoot\build\SixSirhurtUnretardifier9000Pro.exe" -ForegroundColor Green
