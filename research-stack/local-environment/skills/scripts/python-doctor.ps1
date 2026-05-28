$ErrorActionPreference = "Stop"

$skillsRoot = Split-Path -Parent $PSScriptRoot
$envRoot = Split-Path -Parent $skillsRoot
$runtimePython = Join-Path $envRoot "python\runtime\python313\python.exe"
$venvPython = Join-Path $envRoot ".venv\Scripts\python.exe"
$coreLock = Join-Path $envRoot "python\requirements\research-core-lock.txt"
$aiLock = Join-Path $envRoot "python\requirements\research-ai-extra-lock.txt"
$git = "C:\Program Files\Git\cmd\git.exe"
$gh = "C:\Program Files\GitHub CLI\gh.exe"

Write-Host "=== Path checks ==="
Write-Host "Environment root: $envRoot"
Write-Host "Project Python: $(Test-Path $runtimePython)"
Write-Host "Virtual env: $(Test-Path $venvPython)"
Write-Host "Git: $(Test-Path $git)"
Write-Host "GitHub CLI: $(Test-Path $gh)"
Write-Host "Core lock file: $(Test-Path $coreLock)"
Write-Host "AI lock file: $(Test-Path $aiLock)"
Write-Host ""

if (Test-Path $runtimePython) {
    Write-Host "=== Project Python ==="
    & $runtimePython --version
}

if (Test-Path $venvPython) {
    Write-Host ""
    Write-Host "=== Main virtual environment ==="
    & $venvPython -c "import sys, platform; print(sys.executable); print(sys.base_prefix); print(platform.platform())"
    Write-Host ""
    Write-Host "=== Core imports ==="
    & $venvPython -c "import pandas, statsmodels, pyreadstat, networkx, igraph, jieba, jupyterlab; print('core-import-ok')"
    Write-Host ""
    Write-Host "=== Jupyter kernels ==="
    & $venvPython -m jupyter kernelspec list
}

if (Test-Path $git) {
    Write-Host ""
    Write-Host "=== Git ==="
    & $git --version
    & $git config --global --get user.name
    & $git config --global --get user.email
}

if (Test-Path $gh) {
    Write-Host ""
    Write-Host "=== GitHub CLI ==="
    & $gh --version | Select-Object -First 1
}
