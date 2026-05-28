param(
    [int]$Port = 9333,
    [string]$ProfileDir = "$env:USERPROFILE\.codex\browser-profiles\cnki-controlled",
    [string]$Url = "https://www.cnki.net/"
)

$ErrorActionPreference = "Stop"

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path -LiteralPath $chromePath)) {
    throw "Chrome not found: $chromePath"
}

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if ($listener) {
    Start-Process -FilePath $chromePath -ArgumentList $Url
} else {
    $argString = @(
        "--remote-debugging-port=$Port",
        "--remote-allow-origins=*",
        "--user-data-dir=`"$ProfileDir`"",
        "--profile-directory=`"Default`"",
        "--no-first-run",
        "--no-default-browser-check",
        $Url
    ) -join " "
    Start-Process -FilePath $chromePath -ArgumentList $argString
}

Start-Sleep -Seconds 3

$versionUrl = "http://127.0.0.1:$Port/json/version"
try {
    $version = Invoke-WebRequest -UseBasicParsing $versionUrl -TimeoutSec 5
    [pscustomobject]@{
        ok = $true
        port = $Port
        profile_dir = (Resolve-Path -LiteralPath $ProfileDir).Path
        version_url = $versionUrl
        note = "Use this Chrome window for CNKI login and captcha. Do not store this profile in git."
    } | ConvertTo-Json -Depth 4
} catch {
    [pscustomobject]@{
        ok = $false
        port = $Port
        profile_dir = $ProfileDir
        version_url = $versionUrl
        error = $_.Exception.Message
    } | ConvertTo-Json -Depth 4
    exit 1
}
