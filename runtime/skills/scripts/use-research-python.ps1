$ErrorActionPreference = "Stop"



$skillsRoot = Split-Path -Parent $PSScriptRoot

$envRoot = Split-Path -Parent $skillsRoot

$activate = Join-Path $envRoot ".venv\Scripts\Activate.ps1"



if (-not (Test-Path $activate)) {

    throw "Main virtual environment is missing. Run install-research-core.ps1 first."

}



Start-Process powershell -ArgumentList @(

    "-NoExit",

    "-ExecutionPolicy",

    "Bypass",

    "-Command",

    "& '$activate'; Set-Location '$envRoot'; Write-Host 'Research Python environment is active.' -ForegroundColor Green; python -c ""import sys; print(sys.executable)"""

)
