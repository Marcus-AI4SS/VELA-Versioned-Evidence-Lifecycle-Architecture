param(
    [string]$VaultPath = "<OBSIDIAN_VAULT>",
    [string]$CodexResearchPath = "<OBSIDIAN_VAULT>\Codex Research",
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"
$RepoRoot = if ($RepoRoot) { $RepoRoot } else { Split-Path -Parent $PSScriptRoot }

New-Item -ItemType Directory -Force -Path $CodexResearchPath | Out-Null

$dirs = @(
    "00-系统",
    "00-模板",
    "10-项目",
    "20-文献",
    "20-文献\_zotero-sync",
    "30-方法",
    "40-综合",
    "50-面板",
    "90-归档"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path (Join-Path $CodexResearchPath $dir) | Out-Null
}

Copy-Item -LiteralPath (Join-Path $RepoRoot "templates\obsidian\文献笔记模板.md") -Destination (Join-Path $CodexResearchPath "00-模板\文献笔记模板.md") -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "templates\obsidian\项目地图模板.md") -Destination (Join-Path $CodexResearchPath "00-模板\项目地图模板.md") -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "templates\obsidian\方法卡模板.md") -Destination (Join-Path $CodexResearchPath "00-模板\方法卡模板.md") -Force

$panelSource = Join-Path $RepoRoot "templates\obsidian\panels"
Get-ChildItem -LiteralPath $panelSource -Filter *.md | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $CodexResearchPath ("50-面板\" + $_.Name)) -Force
}

$integrationDocsRoot = Join-Path $RepoRoot "docs\30-integrations"
$operationsDocsRoot = Join-Path $RepoRoot "docs\10-operations"

$systemDocs = @(
    "研究型Codex-统一说明书.md",
    "Codex-Zotero-Obsidian-成熟方案复核.md",
    "Zotero-Obsidian-成熟攻略矩阵.md"
)

foreach ($doc in $systemDocs) {
    $src = if ($doc -eq "研究型Codex-统一说明书.md") {
        Join-Path $operationsDocsRoot $doc
    } else {
        Join-Path $integrationDocsRoot $doc
    }
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $CodexResearchPath ("00-系统\" + $doc)) -Force
    }
}

& (Join-Path $RepoRoot "scripts\install_obsidian_research_plugins.ps1") -VaultPath $VaultPath
& (Join-Path $RepoRoot "scripts\install_zotero_research_addons.ps1")
& (Join-Path $RepoRoot "scripts\sync_research_autopilot_skills.ps1")

[pscustomobject]@{
    vault = $VaultPath
    codex_research = $CodexResearchPath
    directories = $dirs
    note = "Vault bootstrap finished."
} | ConvertTo-Json -Depth 5
