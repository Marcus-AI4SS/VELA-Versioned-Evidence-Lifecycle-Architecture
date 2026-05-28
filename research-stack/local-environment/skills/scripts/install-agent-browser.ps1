param(
    [string]$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe",
    [switch]$SkipChromeForTesting
)

$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists -Name "npm")) {
    throw "npm was not found. Cannot install agent-browser."
}

npm install -g agent-browser | Out-Host

$skillInstallOutput = npx -y skills add vercel-labs/agent-browser --yes --global
$skillInstallOutput | Out-Host

$syncScript = Join-Path $PSScriptRoot "sync_agent_browser_skill.ps1"
$syncResult = & $syncScript | ConvertFrom-Json

$chromeForTestingInstalled = $false
$chromeForTestingError = $null

if (-not $SkipChromeForTesting) {
    try {
        agent-browser install | Out-Host
        $chromeForTestingInstalled = $true
    }
    catch {
        $chromeForTestingError = $_.Exception.Message
    }
}

$version = (& agent-browser --version).Trim()
$localChromeExists = Test-Path -LiteralPath $ChromePath

[pscustomobject]@{
    version = $version
    local_chrome_path = $ChromePath
    local_chrome_exists = $localChromeExists
    chrome_for_testing_installed = $chromeForTestingInstalled
    chrome_for_testing_error = $chromeForTestingError
    codex_skill_path = $syncResult.target
    note = "If Chrome for Testing download fails, continue using the local Chrome installation."
} | ConvertTo-Json -Depth 5
