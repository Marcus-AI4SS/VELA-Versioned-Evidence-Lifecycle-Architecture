$ErrorActionPreference = "Stop"

$envRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $envRoot ".venv\Scripts\python.exe"
$entry = Join-Path $envRoot "skills\manager\app.py"

if (-not (Test-Path $python)) {
    throw "主虚拟环境不存在：$python"
}

& $python $entry
