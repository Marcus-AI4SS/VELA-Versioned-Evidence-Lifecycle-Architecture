param(
    [Parameter(Mandatory = $true)]
    [string]$Url,
    [ValidateSet("generic", "douyin", "bilibili", "wechat")]
    [string]$Platform = "generic",
    [string]$SessionName = "research-social",
    [string]$ProfileName,
    [string]$StatePath,
    [string]$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe",
    [switch]$AutoConnect,
    [switch]$Headed,
    [switch]$NoAllowedDomains
)

$ErrorActionPreference = "Stop"

$platformDomains = @{
    generic = $null
    douyin = "douyin.com,*.douyin.com,*.amemv.com,*.douyinvod.com,*.byteimg.com,*.bytedance.com"
    bilibili = "bilibili.com,*.bilibili.com,*.hdslb.com"
    wechat = "mp.weixin.qq.com,weixin.qq.com,*.qq.com"
}

$platformWaitMs = @{
    generic = "1200"
    douyin = "2200"
    bilibili = "1800"
    wechat = "1500"
}

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
elseif (Test-Path -LiteralPath $ChromePath) {
    $args += "--executable-path"
    $args += $ChromePath
}

if ($Headed) {
    $args += "--headed"
}

if ($SessionName) {
    $args += "--session"
    $args += $SessionName
    $args += "--session-name"
    $args += $SessionName
}

if ($ProfileName) {
    $args += "--profile"
    $args += $ProfileName
}

if ($StatePath) {
    $args += "--state"
    $args += $StatePath
}

$args += "--content-boundaries"
$args += "--max-output"
$args += "50000"

if (-not $NoAllowedDomains -and $platformDomains[$Platform]) {
    $args += "--allowed-domains"
    $args += $platformDomains[$Platform]
}

$escapedUrl = $Url.Replace("\", "\\").Replace("'", "\'")

& $agentBrowserExe @args open "about:blank"
& $agentBrowserExe @args eval "location.href = '$escapedUrl'"
& $agentBrowserExe @args wait $platformWaitMs[$Platform]
