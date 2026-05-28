param(
    [string]$Name = "research-default",
    [string]$OutputDir,
    [string]$SessionName = "research-social",
    [string]$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe",
    [switch]$AutoConnect
)

$ErrorActionPreference = "Stop"
$skillsRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDir) {
    $OutputDir = Join-Path $skillsRoot "outputs\agent-browser\state"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$statePath = Join-Path $OutputDir ($Name + ".json")

$agentBrowser = (Get-Command agent-browser -ErrorAction Stop).Source
$agentBrowserBaseDir = Split-Path -Parent $agentBrowser
$agentBrowserExe = Join-Path $agentBrowserBaseDir "node_modules\agent-browser\bin\agent-browser-win32-x64.exe"
if (-not (Test-Path -LiteralPath $agentBrowserExe)) {
    throw "agent-browser executable not found: $agentBrowserExe"
}

$args = @()

if ($AutoConnect) {
    $args += "--auto-connect"
}
elseif ($SessionName) {
    $args += "--session"
    $args += $SessionName
    $args += "--session-name"
    $args += $SessionName
}
elseif (Test-Path -LiteralPath $ChromePath) {
    $args += "--executable-path"
    $args += $ChromePath
}

$args += "state"
$args += "save"
$args += $statePath

& $agentBrowserExe @args

if (-not (Test-Path -LiteralPath $statePath)) {
    throw "State file was not created. Use -AutoConnect for a running Chrome session or provide the active agent-browser session name."
}

[pscustomobject]@{
    state_path = $statePath
    note = "State files contain plaintext session tokens and should remain under skills/outputs/. Do not commit them to Git."
} | ConvertTo-Json -Depth 4
