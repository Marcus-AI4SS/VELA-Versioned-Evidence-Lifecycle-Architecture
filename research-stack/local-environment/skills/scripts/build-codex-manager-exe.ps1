param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$envRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$sharedRoot = Split-Path -Parent (Split-Path -Parent $envRoot)
$pythonCandidates = @(
    (Join-Path $envRoot ".venv\Scripts\python.exe"),
    (Join-Path $sharedRoot ".venv\Scripts\python.exe"),
    (Join-Path $sharedRoot "python\runtime\python313\python.exe")
)
$python = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
$entry = Join-Path $envRoot "skills\manager\app.py"
$assetBuilder = Join-Path $envRoot "skills\scripts\build-codex-manager-assets.py"
$outputRoot = Join-Path $envRoot "skills\outputs\manager-app"
$distPath = Join-Path $outputRoot "dist"
$workPath = Join-Path $outputRoot "build"
$specPath = $outputRoot
$iconPath = Join-Path $envRoot "skills\manager\assets\codex-research-console.ico"

if (-not (Test-Path $python)) {
    throw "未找到可用的 Python 解释器。已检查：$($pythonCandidates -join ' ; ')"
}

if (-not $SkipInstall) {
    & $python -m pip install --upgrade pyinstaller pyside6
}

& $python $assetBuilder

New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
New-Item -ItemType Directory -Force -Path $distPath | Out-Null
New-Item -ItemType Directory -Force -Path $workPath | Out-Null

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "CodexResearchConsole" `
    --icon $iconPath `
    --paths (Join-Path $envRoot "skills") `
    --hidden-import manager `
    --hidden-import manager.research_env `
    --hidden-import PySide6.QtCore `
    --hidden-import PySide6.QtGui `
    --hidden-import PySide6.QtWidgets `
    --distpath $distPath `
    --workpath $workPath `
    --specpath $specPath `
    $entry

$exePath = Join-Path $distPath "CodexResearchConsole.exe"
if (-not (Test-Path $exePath)) {
    throw "打包完成，但未找到 exe：$exePath"
}

Write-Output $exePath
