param(
    [string]$Proxy = ""
)

$ErrorActionPreference = "Continue"
$targets = @("api.openai.com", "chatgpt.com")

function Get-UserEnvironment {
    param([string]$Name)
    return [Environment]::GetEnvironmentVariable($Name, "User")
}

function Test-TcpPort {
    param(
        [string]$HostName,
        [int]$Port
    )
    try {
        $result = Test-NetConnection $HostName -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        return [pscustomobject]@{
            host = $HostName
            port = $Port
            ok = [bool]$result
        }
    } catch {
        return [pscustomobject]@{
            host = $HostName
            port = $Port
            ok = $false
            error = $_.Exception.Message
        }
    }
}

function Resolve-TargetDns {
    param([string]$HostName)
    try {
        $records = Resolve-DnsName $HostName -Type A -ErrorAction Stop |
            Where-Object { $_.IPAddress } |
            ForEach-Object { $_.IPAddress }
        return [pscustomobject]@{
            host = $HostName
            addresses = @($records)
        }
    } catch {
        return [pscustomobject]@{
            host = $HostName
            addresses = @()
            error = $_.Exception.Message
        }
    }
}

function ConvertTo-ProxyUri {
    param([string]$Value)
    if (-not $Value) {
        return $null
    }
    $candidate = $Value.Trim()
    if (-not ($candidate -match "^[a-zA-Z][a-zA-Z0-9+.-]*://")) {
        $candidate = "http://$candidate"
    }
    try {
        return [Uri]$candidate
    } catch {
        return $null
    }
}

function Test-ProxyHttpHead {
    param(
        [string]$Url,
        [string]$ProxyValue
    )
    if (-not $ProxyValue) {
        return [pscustomobject]@{
            url = $Url
            skipped = $true
            reason = "proxy-not-configured"
        }
    }
    $lines = & curl.exe -I --max-time 20 --proxy $ProxyValue $Url 2>&1
    $text = ($lines | Out-String)
    $statusCodes = @()
    foreach ($line in ($text -split "`r?`n")) {
        if ($line -match "^HTTP/\S+\s+(\d+)") {
            $statusCodes += [int]$Matches[1]
        }
    }
    return [pscustomobject]@{
        url = $Url
        proxy = $ProxyValue
        ok = $statusCodes.Count -gt 0
        status_codes = $statusCodes
        first_lines = @($text -split "`r?`n" | Where-Object { $_ } | Select-Object -First 8)
    }
}

$internetSettings = Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
$userEnv = [ordered]@{}
foreach ($name in @("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy")) {
    $value = Get-UserEnvironment -Name $name
    if ($value) {
        $userEnv[$name] = $value
    }
}

$effectiveProxy = $Proxy
if (-not $effectiveProxy) {
    $effectiveProxy = Get-UserEnvironment -Name "HTTPS_PROXY"
}
if (-not $effectiveProxy -and $internetSettings.ProxyEnable -eq 1 -and $internetSettings.ProxyServer) {
    $effectiveProxy = $internetSettings.ProxyServer
}
$proxyUri = ConvertTo-ProxyUri -Value $effectiveProxy

$proxyTcp = $null
if ($proxyUri) {
    $proxyTcp = Test-TcpPort -HostName $proxyUri.Host -Port $proxyUri.Port
}

$directTcp = foreach ($target in $targets) {
    Test-TcpPort -HostName $target -Port 443
}

$dns = foreach ($target in $targets) {
    Resolve-TargetDns -HostName $target
}

$proxyHttp = @(
    Test-ProxyHttpHead -Url "https://api.openai.com/v1/models" -ProxyValue $effectiveProxy
    Test-ProxyHttpHead -Url "https://chatgpt.com/" -ProxyValue $effectiveProxy
)

$warnings = New-Object System.Collections.Generic.List[string]
if (($directTcp | Where-Object { $_.ok -eq $false }).Count -gt 0) {
    $warnings.Add("direct-openai-tcp-failed") | Out-Null
}
if ($proxyTcp -and $proxyTcp.ok -ne $true) {
    $warnings.Add("local-proxy-port-not-reachable") | Out-Null
}
if (($proxyHttp | Where-Object { $_.ok -eq $true }).Count -eq 0) {
    $warnings.Add("proxy-http-check-failed") | Out-Null
}
if (-not $userEnv.Contains("HTTPS_PROXY")) {
    $warnings.Add("user-https-proxy-env-missing") | Out-Null
}

[pscustomobject]@{
    schema_version = "codex_connectivity_diagnosis.v1"
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("s") + "Z"
    wininet = [pscustomobject]@{
        proxy_enabled = [bool]$internetSettings.ProxyEnable
        proxy_server = $internetSettings.ProxyServer
        auto_config_url = $internetSettings.AutoConfigURL
    }
    user_environment = $userEnv
    effective_proxy = $effectiveProxy
    proxy_tcp = $proxyTcp
    dns = @($dns)
    direct_tcp = @($directTcp)
    proxy_http = @($proxyHttp)
    warnings = @($warnings)
} | ConvertTo-Json -Depth 8
