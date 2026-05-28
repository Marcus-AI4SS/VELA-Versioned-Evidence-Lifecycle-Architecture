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

$cli = Join-Path $repoRoot ".venv\Scripts\opendataloader-pdf.exe"
if (-not (Test-Path -LiteralPath $cli)) {
    throw "opendataloader-pdf is not installed in the D-repo virtual environment. Run: $repoRoot\.venv\Scripts\python.exe -m pip install opendataloader-pdf==2.4.6"
}

& $cli @args
exit $LASTEXITCODE
