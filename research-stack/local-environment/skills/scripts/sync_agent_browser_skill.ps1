param(
    [string]$AgentsSkillPath = "$env:USERPROFILE\.agents\skills\agent-browser\SKILL.md",
    [string]$CodexHome = "$env:USERPROFILE\.codex"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $AgentsSkillPath)) {
    throw "Missing agent-browser skill stub: $AgentsSkillPath"
}

$targetDir = Join-Path $CodexHome "skills\agent-browser"
$targetPath = Join-Path $targetDir "SKILL.md"

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
Copy-Item -LiteralPath $AgentsSkillPath -Destination $targetPath -Force

[pscustomobject]@{
    source = $AgentsSkillPath
    target = $targetPath
    note = "agent-browser skill synced to Codex local skills directory. Restart Codex if it does not appear immediately."
} | ConvertTo-Json -Depth 4
