$ErrorActionPreference = "Stop"

$skillsRoot = Split-Path -Parent $PSScriptRoot
$envRoot = Split-Path -Parent $skillsRoot
$venvPython = Join-Path $envRoot ".venv\Scripts\python.exe"
$requirements = Join-Path $envRoot "python\requirements\research-ai-extra.txt"
$lockfile = Join-Path $envRoot "python\requirements\research-ai-extra-lock.txt"

if (-not (Test-Path $venvPython)) {
    throw "Main virtual environment is missing. Run install-research-core.ps1 first."
}

& $venvPython -m pip install -r $requirements
& $venvPython -m pip freeze | Set-Content -Encoding UTF8 $lockfile

Write-Host ""
Write-Host "AI extra layer is ready." -ForegroundColor Green
Write-Host "Interpreter: $venvPython"
Write-Host "Lock file: $lockfile"
