param(
  [string]$Python = "python",
  [switch]$SkipDependencyInstall,
  [switch]$SkipLocalEnvironment,
  [switch]$ForceLocalEnvironment
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VelaHome = if ($env:VELA_HOME) { $env:VELA_HOME } else { Join-Path $HOME ".vela" }
$StateDir = Join-Path $VelaHome "state"
$BinDir = Join-Path $VelaHome "bin"
New-Item -ItemType Directory -Force -Path $StateDir, $BinDir | Out-Null

$Requirements = Join-Path $RepoRoot "requirements.txt"
if (-not $SkipDependencyInstall -and (Test-Path -LiteralPath $Requirements)) {
  & $Python -m pip install -r $Requirements
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$Shim = Join-Path $BinDir "vela.cmd"
$Script = Join-Path $RepoRoot "scripts\vela.py"
@"
@echo off
"$Python" "$Script" %*
"@ | Set-Content -LiteralPath $Shim -Encoding ASCII

$Receipt = @{
  schema_version = "vela.install.receipt.v1"
  installed_at = (Get-Date).ToUniversalTime().ToString("o")
  repo_root = $RepoRoot
  python = $Python
  vela_home = $VelaHome
  shim = $Shim
  codex_home = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
}
$Receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $StateDir "install.json") -Encoding UTF8

& $Python $Script doctor
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not $SkipLocalEnvironment) {
  $LocalEnvArgs = @($Script, "local-env", "install-runtime", "--include", "core,automation,toolchain", "--python", $Python, "--commit")
  if ($ForceLocalEnvironment) {
    $LocalEnvArgs += "--force-core"
  }
  & $Python @LocalEnvArgs
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Write-Host ""
Write-Host "VELA shim created: $Shim"
Write-Host "Add this directory to PATH if you want to run 'vela' directly: $BinDir"
if (-not $SkipLocalEnvironment) {
  Write-Host "VELA local research environment and runtime shims installed. Restart Codex so new skills are discovered."
}
