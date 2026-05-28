param(
    [string]$Proxy = "http://127.0.0.1:7897",
    [string]$NoProxy = "localhost,127.0.0.1,::1",
    [switch]$Clear
)

$ErrorActionPreference = "Stop"
$backupRoot = Join-Path $env:USERPROFILE ".codex\backups\stability"
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$backupPath = Join-Path $backupRoot "proxy-env.$stamp.json"
$names = @(
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy"
)

$previous = [ordered]@{}
foreach ($name in $names) {
    $previous[$name] = [Environment]::GetEnvironmentVariable($name, "User")
}
$previous | ConvertTo-Json | Set-Content -LiteralPath $backupPath -Encoding UTF8

if ($Clear) {
    foreach ($name in $names) {
        [Environment]::SetEnvironmentVariable($name, $null, "User")
    }
} else {
    foreach ($name in @("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")) {
        [Environment]::SetEnvironmentVariable($name, $Proxy, "User")
    }
    foreach ($name in @("NO_PROXY", "no_proxy")) {
        [Environment]::SetEnvironmentVariable($name, $NoProxy, "User")
    }
}

$current = [ordered]@{}
foreach ($name in $names) {
    $current[$name] = [Environment]::GetEnvironmentVariable($name, "User")
}

[pscustomobject]@{
    schema_version = "codex_user_proxy_update.v1"
    ok = $true
    mode = $(if ($Clear) { "clear" } else { "set" })
    backup = $backupPath
    restart_required = $true
    user_environment = $current
} | ConvertTo-Json -Depth 4
