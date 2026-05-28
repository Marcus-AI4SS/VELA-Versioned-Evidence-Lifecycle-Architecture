$ErrorActionPreference = "Stop"



$skillsRoot = Split-Path -Parent $PSScriptRoot

$envRoot = Split-Path -Parent $skillsRoot

$venvPython = Join-Path $envRoot ".venv\Scripts\python.exe"



if (-not (Test-Path $venvPython)) {

    throw "Main virtual environment is missing. Run install-research-core.ps1 first."

}



Set-Location $envRoot

& $venvPython -m jupyter lab --notebook-dir $envRoot
