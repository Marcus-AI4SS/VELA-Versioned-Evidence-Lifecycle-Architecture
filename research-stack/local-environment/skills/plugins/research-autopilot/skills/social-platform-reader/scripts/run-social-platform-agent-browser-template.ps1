param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("douyin", "bilibili", "wechat")]
    [string]$Platform,

    [Parameter(Mandatory = $true)]
    [string]$Url,

    [string]$ArtifactType = "page",
    [string]$SessionName = "research-social",
    [string]$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe",
    [string]$OutputRoot,
    [switch]$AutoConnect,
    [switch]$Headed,
    [switch]$SaveState,
    [switch]$KeepSessionAlive,
    [switch]$JsonOnly
)

$ErrorActionPreference = "Stop"
$skillsRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $skillsRoot "outputs\social-platform-reader\agent-browser"
}

function Resolve-AgentBrowserExe {
    $candidates = New-Object System.Collections.Generic.List[string]
    if ($env:AGENT_BROWSER_EXE) {
        $candidates.Add($env:AGENT_BROWSER_EXE) | Out-Null
    }
    if ($env:AGENT_BROWSER_CMD) {
        $cmdBase = Split-Path -Parent $env:AGENT_BROWSER_CMD
        $candidates.Add((Join-Path $cmdBase "node_modules\agent-browser\bin\agent-browser-win32-x64.exe")) | Out-Null
    }

    $agentBrowser = Get-Command agent-browser -ErrorAction SilentlyContinue
    if ($agentBrowser) {
        $agentBrowserBaseDir = Split-Path -Parent $agentBrowser.Source
        $candidates.Add((Join-Path $agentBrowserBaseDir "node_modules\agent-browser\bin\agent-browser-win32-x64.exe")) | Out-Null
    }

    $npmRoot = Join-Path $env:APPDATA "npm"
    $candidates.Add((Join-Path $npmRoot "node_modules\agent-browser\bin\agent-browser-win32-x64.exe")) | Out-Null

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    throw "agent-browser executable not found. Checked: $($candidates -join '; ')"
}

$agentBrowserExe = Resolve-AgentBrowserExe

$platformConfig = @{
    douyin = @{
        allowed_domains = "douyin.com,*.douyin.com,*.amemv.com,*.douyinvod.com,*.byteimg.com,*.bytedance.com"
        wait_ms = "2200"
    }
    bilibili = @{
        allowed_domains = "bilibili.com,*.bilibili.com,*.hdslb.com"
        wait_ms = "1800"
    }
    wechat = @{
        allowed_domains = "mp.weixin.qq.com,weixin.qq.com,*.qq.com"
        wait_ms = "1500"
    }
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputDir = Join-Path $OutputRoot (Join-Path $Platform $timestamp)
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$metadataPath = Join-Path $outputDir "metadata.json"
$snapshotPath = Join-Path $outputDir "snapshot-interactive.json"
$screenshotPath = Join-Path $outputDir "screenshot.png"
$statePath = Join-Path $outputDir "state.json"
$titleTempPath = Join-Path $env:TEMP ("social-platform-reader-title-" + [guid]::NewGuid().ToString() + ".txt")
$urlTempPath = Join-Path $env:TEMP ("social-platform-reader-url-" + [guid]::NewGuid().ToString() + ".txt")

$commonArgs = @()
if ($AutoConnect) {
    $commonArgs += "--auto-connect"
} elseif (Test-Path -LiteralPath $ChromePath) {
    $commonArgs += "--executable-path"
    $commonArgs += $ChromePath
}

if ($Headed) {
    $commonArgs += "--headed"
}

if ($SessionName) {
    $commonArgs += "--session"
    $commonArgs += $SessionName
    $commonArgs += "--session-name"
    $commonArgs += $SessionName
}

$commonArgs += "--content-boundaries"
$commonArgs += "--max-output"
$commonArgs += "50000"
$commonArgs += "--allowed-domains"
$commonArgs += $platformConfig[$Platform].allowed_domains
$escapedUrl = $Url.Replace("\", "\\").Replace("'", "\'")

try {
    if ($JsonOnly) {
        & $agentBrowserExe @commonArgs open "about:blank" > $null
        & $agentBrowserExe @commonArgs eval "location.href = '$escapedUrl'" > $null
        & $agentBrowserExe @commonArgs wait $platformConfig[$Platform].wait_ms > $null
    } else {
        & $agentBrowserExe @commonArgs open "about:blank"
        & $agentBrowserExe @commonArgs eval "location.href = '$escapedUrl'"
        & $agentBrowserExe @commonArgs wait $platformConfig[$Platform].wait_ms
    }

    & $agentBrowserExe @commonArgs get title > $titleTempPath
    & $agentBrowserExe @commonArgs get url > $urlTempPath
    & $agentBrowserExe @commonArgs snapshot -i --json > $snapshotPath
    if ($JsonOnly) {
        & $agentBrowserExe @commonArgs screenshot $screenshotPath > $null
    } else {
        & $agentBrowserExe @commonArgs screenshot $screenshotPath
    }

    $title = (Get-Content -Raw -LiteralPath $titleTempPath).Trim()
    $finalUrl = (Get-Content -Raw -LiteralPath $urlTempPath).Trim()

    if ($SaveState) {
        if ($JsonOnly) {
            & $agentBrowserExe @commonArgs state save $statePath > $null
        } else {
            & $agentBrowserExe @commonArgs state save $statePath
        }
    }

    $metadata = [pscustomobject]@{
        platform = $Platform
        artifact_type = $ArtifactType
        url_requested = $Url
        url_final = $finalUrl
        title = $title
        session_name = $SessionName
        output_dir = $outputDir
        snapshot_interactive = $snapshotPath
        screenshot = $screenshotPath
        state_file = $(if ($SaveState) { $statePath } else { $null })
        captured_at = (Get-Date).ToString("s")
    }

    $metadata | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $metadataPath -Encoding UTF8
    $metadata | ConvertTo-Json -Depth 4
}
finally {
    if (-not $KeepSessionAlive) {
        if ($JsonOnly) {
            & $agentBrowserExe @commonArgs close > $null
        } else {
            & $agentBrowserExe @commonArgs close
        }
    }

    foreach ($tempPath in @($titleTempPath, $urlTempPath)) {
        if (Test-Path -LiteralPath $tempPath) {
            Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
        }
    }
}
