param(
    [string]$CodexHome = "<CODEX_HOME>"
)

$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "sync_research_autopilot_skills.ps1") `
    -CodexHome $CodexHome
