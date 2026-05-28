param(

  [Parameter(ValueFromRemainingArguments = $true)]

  [string[]]$Args

)



$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$Python = if ($env:VELA_PYTHON) { $env:VELA_PYTHON } else { $null }

if (-not $Python) {

  $VelaHome = if ($env:VELA_HOME) { $env:VELA_HOME } else { Join-Path $HOME ".vela" }

  $Receipt = Join-Path (Join-Path $VelaHome "state") "install.json"

  if (Test-Path -LiteralPath $Receipt) {

    try {

      $InstallReceipt = Get-Content -LiteralPath $Receipt -Raw | ConvertFrom-Json

      if ($InstallReceipt.python) {

        $Python = [string]$InstallReceipt.python

      }

    } catch {

      $Python = $null

    }

  }

}

if (-not $Python) { $Python = "python" }

& $Python (Join-Path $RepoRoot "scripts\vela.py") @Args
