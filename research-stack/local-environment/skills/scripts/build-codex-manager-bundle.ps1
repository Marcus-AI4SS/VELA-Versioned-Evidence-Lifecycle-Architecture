param(
    [switch]$SkipExeBuild
)

$ErrorActionPreference = "Stop"

function Write-Utf8Lf {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $normalized = $Content -replace "`r`n", "`n"
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $normalized, $encoding)
}

function Replace-TextInFiles {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [hashtable]$Replacements,
        [string[]]$Extensions = @(".md", ".txt", ".json", ".toml")
    )

    if (-not (Test-Path -LiteralPath $Root)) {
        return
    }

    Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object { $Extensions -contains $_.Extension.ToLowerInvariant() } | ForEach-Object {
        $content = Get-Content -Raw -LiteralPath $_.FullName
        foreach ($key in $Replacements.Keys) {
            $content = $content.Replace($key, $Replacements[$key])
        }
        Set-Content -LiteralPath $_.FullName -Value $content -Encoding UTF8
    }
}

$envRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$bundleRoot = Join-Path $envRoot "skills\outputs\manager-app\friend-macos\CodexResearchConsole-macOS"
$bundleArchive = Join-Path $envRoot "skills\outputs\manager-app\friend-macos\CodexResearchConsole-macOS.tar.gz"
$bundleSetupScriptName = "Install-CodexResearchConsole-macOS.sh"
$bundleSetupScriptSource = Join-Path $envRoot "skills\scripts\setup-codex-console-macos.sh"
$bundleSetupScriptPath = Join-Path $bundleRoot "scripts\$bundleSetupScriptName"
$bundleLauncherName = "Install Codex Research Console.command"
$bundleLauncherPath = Join-Path $bundleRoot $bundleLauncherName
$bundleManifestName = "package-manifest.json"
$bundleReadmeName = "README.md"
$bundleQuickstartName = "Quick Start.txt"
$tarCommand = Get-Command tar -ErrorAction SilentlyContinue

if (-not (Test-Path -LiteralPath $bundleSetupScriptSource)) {
    throw "Missing macOS setup script template: $bundleSetupScriptSource"
}

if (Test-Path -LiteralPath $bundleRoot) {
    Remove-Item -Recurse -Force -LiteralPath $bundleRoot
}
New-Item -ItemType Directory -Force -Path $bundleRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bundleRoot "payload\skills") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bundleRoot "scripts") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bundleRoot "docs") | Out-Null

$copyRoots = @(
    "AGENTS.md",
    "catalog",
    "manager",
    "plugins",
    "profiles",
    "schemas",
    "scripts",
    "templates",
    "tests"
)

foreach ($item in $copyRoots) {
    $source = Join-Path $envRoot "skills\$item"
    if (Test-Path -LiteralPath $source) {
        Copy-Item -Recurse -Force -LiteralPath $source -Destination (Join-Path $bundleRoot "payload\skills")
    }
}

$excludePaths = @(
    (Join-Path $bundleRoot "payload\skills\scripts\cleanup-windows-powershell51-modules.ps1"),
    (Join-Path $bundleRoot "payload\skills\scripts\set-codex-shell-defaults.ps1"),
    (Join-Path $bundleRoot "payload\skills\scripts\setup_omx_wsl.ps1"),
    (Join-Path $bundleRoot "payload\skills\scripts\sync-git-proxy.ps1"),
    (Join-Path $bundleRoot "payload\skills\scripts\setup-local-codex-console.ps1"),
    (Join-Path $bundleRoot "payload\skills\scripts\build-codex-manager-exe.ps1"),
    (Join-Path $bundleRoot "payload\skills\outputs")
)

foreach ($path in $excludePaths) {
    if (Test-Path -LiteralPath $path) {
        Remove-Item -Recurse -Force -LiteralPath $path
    }
}

Copy-Item -Force -LiteralPath $bundleSetupScriptSource -Destination $bundleSetupScriptPath

$launcher = @"
#!/bin/zsh
set -euo pipefail
DIR="`$(cd "`$(dirname "`$0")" && pwd)"
/bin/zsh "`$DIR/scripts/$bundleSetupScriptName"
"@
Write-Utf8Lf -Path $bundleLauncherPath -Content $launcher

$manifest = @"
{
  "package_name": "Codex Research Console",
  "edition": "macos-arm64",
  "platform": "darwin",
  "arch": "arm64",
  "delivery_mode": "guided_install",
  "launch_entry": "$bundleLauncherName",
  "setup_script": "scripts/$bundleSetupScriptName"
}
"@
Write-Utf8Lf -Path (Join-Path $bundleRoot $bundleManifestName) -Content $manifest

$readme = @'
# Codex Research Console

This package is prepared for Apple Silicon Mac.

## Before you start

- Codex App is already installed
- If Python, Git, Node, Zotero, or Obsidian is missing, the installer will tell you what to install next

## Install

1. After extracting, double-click `Install Codex Research Console.command`
2. If macOS does not execute it directly, run this first in Terminal:
   `chmod +x "Install Codex Research Console.command"`
3. The installer will deploy the console to `~/Desktop/Codex Research Console`
4. After installation, `Codex Research Console.command` will appear on the desktop

## Notes

- The first launch may require a macOS confirmation
- If a dependency is missing, finish that installation and run this installer again
'@
Write-Utf8Lf -Path (Join-Path $bundleRoot $bundleReadmeName) -Content $readme

$quickstart = @'
Codex Research Console macOS Quick Start
=======================================

1. Double-click Install Codex Research Console.command
2. If the system blocks direct execution, run this first in Terminal:
   chmod +x "Install Codex Research Console.command"
3. The installer checks Python, Git, Node, Zotero, Obsidian, and Codex App
4. If something is missing, it tells you what to install next
5. After installation, double-click Codex Research Console.command on the desktop
'@
Write-Utf8Lf -Path (Join-Path $bundleRoot "docs\$bundleQuickstartName") -Content $quickstart

$payloadDistributionsPath = Join-Path $bundleRoot "payload\skills\catalog\manager_distributions.json"
if (Test-Path -LiteralPath $payloadDistributionsPath) {
    $payloadDistributions = Get-Content -Raw -LiteralPath $payloadDistributionsPath | ConvertFrom-Json
    if ($payloadDistributions.friend_macos_console) {
        $friendOnly = [ordered]@{
            friend_macos_console = [ordered]@{
                platform = $payloadDistributions.friend_macos_console.platform
                delivery_mode = "guided_install"
                workspace_mode = "bundled_environment_workspace"
                environment_source = "bundle_payload/skills"
                bundle_dir = $payloadDistributions.friend_macos_console.bundle_dir
                bundle_output = $payloadDistributions.friend_macos_console.bundle_output
                install_entry = $payloadDistributions.friend_macos_console.install_entry
                setup_script = $payloadDistributions.friend_macos_console.setup_script
                privacy_mode = "light_redaction"
            }
        }
        ($friendOnly | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $payloadDistributionsPath -Encoding UTF8
    }
}

$payloadSkillsRoot = Join-Path $bundleRoot "payload\skills"
$sourceSkillsRoot = Join-Path $envRoot "skills"
$localUserHome = [Environment]::GetFolderPath("UserProfile")
$codexHome = Join-Path $localUserHome ".codex"
$sharedReplacements = @{}
$sharedReplacements[$sourceSkillsRoot] = "<SKILLS_ROOT>"
$sharedReplacements[$envRoot] = "<ENV_ROOT>"
$sharedReplacements[$codexHome] = "<CODEX_HOME>"
$sharedReplacements[$localUserHome] = "<LOCAL_USER_HOME>"
$sharedReplacements[($sourceSkillsRoot -replace "\\", "/")] = "<SKILLS_ROOT>"
$sharedReplacements[($envRoot -replace "\\", "/")] = "<ENV_ROOT>"
$sharedReplacements[($codexHome -replace "\\", "/")] = "<CODEX_HOME>"
$sharedReplacements[($localUserHome -replace "\\", "/")] = "<LOCAL_USER_HOME>"
Replace-TextInFiles -Root (Join-Path $payloadSkillsRoot "catalog") -Replacements $sharedReplacements

if (Test-Path -LiteralPath $bundleArchive) {
    Remove-Item -Force -LiteralPath $bundleArchive
}

if (-not $tarCommand) {
    throw "tar command not found; cannot create the macOS bundle archive."
}

Push-Location $bundleRoot
try {
    & $tarCommand.Source -czf $bundleArchive *
}
finally {
    Pop-Location
}

Write-Output $bundleRoot
