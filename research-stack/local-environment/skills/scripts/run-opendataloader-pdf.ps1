$ErrorActionPreference = "Stop"

$skillsRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $skillsRoot
$runtimeRoot = Join-Path $repoRoot "python\runtime\jdk-21-adoptium"
$java = Get-ChildItem -LiteralPath $runtimeRoot -Filter "java.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $java) {
    throw "Portable Java runtime not found under $runtimeRoot. Install Temurin JDK 21 into python/runtime before running OpenDataLoader PDF."
}

$env:JAVA_HOME = Split-Path -Parent (Split-Path -Parent $java.FullName)
$env:Path = (Join-Path $env:JAVA_HOME "bin") + ";" + $env:Path

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Local virtual environment Python not found. Run: $repoRoot\python\runtime\python313\python.exe -m venv $repoRoot\.venv"
}

& $python -m opendataloader_pdf @args
exit $LASTEXITCODE
