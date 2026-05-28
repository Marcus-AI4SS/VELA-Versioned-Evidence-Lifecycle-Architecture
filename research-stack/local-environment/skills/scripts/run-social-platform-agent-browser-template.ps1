$skillsRoot = Split-Path -Parent $PSScriptRoot
$pluginScript = Join-Path $skillsRoot "plugins\research-autopilot\skills\social-platform-reader\scripts\run-social-platform-agent-browser-template.ps1"

if (-not (Test-Path -LiteralPath $pluginScript)) {
    throw "Template script not found: $pluginScript"
}

& $pluginScript @args
