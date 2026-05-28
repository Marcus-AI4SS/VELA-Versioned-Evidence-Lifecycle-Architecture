$ErrorActionPreference = "Stop"



$skillsRoot = Split-Path -Parent $PSScriptRoot

$envRoot = Split-Path -Parent $skillsRoot

$runtime = Join-Path $envRoot "python\runtime\python313"

$runtimePython = Join-Path $runtime "python.exe"

$venv = Join-Path $envRoot ".venv"

$venvPython = Join-Path $venv "Scripts\python.exe"

$requirements = Join-Path $envRoot "python\requirements\research-core.txt"

$lockfile = Join-Path $envRoot "python\requirements\research-core-lock.txt"

$kernelName = "codex-research-main"

$kernelDisplay = "Python (VELA Research Main)"



$sourceCandidates = @(

    "$env:LOCALAPPDATA\Programs\Python\Python313"

)



function Copy-BaseRuntime {

    if (Test-Path $runtimePython) {

        return

    }



    $source = $sourceCandidates | Where-Object { Test-Path (Join-Path $_ "python.exe") } | Select-Object -First 1

    if (-not $source) {

        throw "No system Python 3.13 source was found."

    }



    New-Item -ItemType Directory -Force -Path $runtime | Out-Null

    $null = & robocopy $source $runtime /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP

    if ($LASTEXITCODE -ge 8) {

        throw "Failed to copy base Python runtime. robocopy exit code: $LASTEXITCODE"

    }

}



function Ensure-Venv {

    if (-not (Test-Path $runtimePython)) {

        throw "Project Python runtime was not found: $runtimePython"

    }



    if (-not (Test-Path $venvPython)) {

        & $runtimePython -m venv $venv

    }

}



Copy-BaseRuntime

Ensure-Venv



& $venvPython -m pip install --upgrade pip setuptools wheel

& $venvPython -m pip install -r $requirements

& $venvPython -m ipykernel install --user --name $kernelName --display-name $kernelDisplay

& $venvPython -m pip freeze | Set-Content -Encoding UTF8 $lockfile



Write-Host ""

Write-Host "Research core environment is ready." -ForegroundColor Green

Write-Host "Base interpreter: $runtimePython"

Write-Host "Virtual env: $venv"

Write-Host "Lock file: $lockfile"
