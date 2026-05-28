param(
  [string]$Python = "python",
  [switch]$BootstrapTools,
  [switch]$SkipDependencyInstall,
  [switch]$SkipLocalEnvironment,
  [switch]$ForceLocalEnvironment
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VelaHome = if ($env:VELA_HOME) { $env:VELA_HOME } else { Join-Path $HOME ".vela" }
$StateDir = Join-Path $VelaHome "state"
$BinDir = Join-Path $VelaHome "bin"
$Script = Join-Path $RepoRoot "scripts\vela.py"
New-Item -ItemType Directory -Force -Path $StateDir, $BinDir | Out-Null

function Test-VelaCommand {
  param([Parameter(Mandatory = $true)][string]$Name)
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-VelaWingetPackage {
  param(
    [Parameter(Mandatory = $true)][string]$CommandName,
    [Parameter(Mandatory = $true)][string]$PackageId,
    [Parameter(Mandatory = $true)][string]$DisplayName
  )
  if (Test-VelaCommand -Name $CommandName) {
    Write-Host "[VELA bootstrap] $DisplayName detected."
    return
  }
  if (-not (Test-VelaCommand -Name "winget")) {
    Write-Warning "[VELA bootstrap] $DisplayName is missing and winget is not available. Install manually: $PackageId"
    return
  }
  Write-Host "[VELA bootstrap] Installing $DisplayName with winget package $PackageId ..."
  & winget install --id $PackageId -e --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "[VELA bootstrap] winget could not install $DisplayName. Install manually and rerun this script."
  }
}

function Install-VelaNpmPackage {
  param(
    [Parameter(Mandatory = $true)][string]$CommandName,
    [Parameter(Mandatory = $true)][string]$PackageName,
    [Parameter(Mandatory = $true)][string]$DisplayName
  )
  if (Test-VelaCommand -Name $CommandName) {
    Write-Host "[VELA bootstrap] $DisplayName detected."
    return
  }
  if (-not (Test-VelaCommand -Name "npm")) {
    Write-Warning "[VELA bootstrap] $DisplayName is missing and npm is not available. Install Node.js first, then install $PackageName manually if you need it."
    return
  }
  Write-Host "[VELA bootstrap] Installing $DisplayName with npm package $PackageName ..."
  & npm install -g $PackageName
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "[VELA bootstrap] npm could not install $DisplayName. Install manually if you need this optional runtime."
  }
}

if ($BootstrapTools) {
  Write-Host "[VELA bootstrap] Checking public system tools. Private runtime state will not be copied."
  Install-VelaWingetPackage -CommandName "git" -PackageId "Git.Git" -DisplayName "Git"
  if (-not (Test-VelaCommand -Name $Python)) {
    Install-VelaWingetPackage -CommandName $Python -PackageId "Python.Python.3.13" -DisplayName "Python 3.13+"
  } else {
    Write-Host "[VELA bootstrap] Python command detected: $Python"
  }
  Install-VelaWingetPackage -CommandName "pwsh" -PackageId "Microsoft.PowerShell" -DisplayName "PowerShell 7"
  Install-VelaWingetPackage -CommandName "rg" -PackageId "BurntSushi.ripgrep.MSVC" -DisplayName "ripgrep"
  Install-VelaWingetPackage -CommandName "node" -PackageId "OpenJS.NodeJS.LTS" -DisplayName "Node.js LTS"
  Install-VelaWingetPackage -CommandName "gh" -PackageId "GitHub.cli" -DisplayName "GitHub CLI"
  Install-VelaNpmPackage -CommandName "agentmemory" -PackageName "agentmemory" -DisplayName "agentmemory"
  Write-Host "[VELA bootstrap] CodeGraph, MCP server vendor requirements, Codex plugins, browser/CNKI login state, Zotero, and Obsidian remain explicit doctor/manual setup."
}

$Requirements = Join-Path $RepoRoot "requirements.txt"
if (-not $SkipDependencyInstall -and (Test-Path -LiteralPath $Requirements)) {
  & $Python -m pip install -r $Requirements
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$Shim = Join-Path $BinDir "vela.cmd"
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
if ($BootstrapTools) {
  & $Python $Script local-env bootstrap-tools --include all --install --yes
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
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
