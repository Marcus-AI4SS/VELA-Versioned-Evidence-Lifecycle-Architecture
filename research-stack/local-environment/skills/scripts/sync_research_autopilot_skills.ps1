param(
    [string]$CodexHome,
    [string]$PluginRoot,
    [switch]$PluginCacheOnly,
    [switch]$KeepInstalledDuplicates
)

$ErrorActionPreference = "Stop"
$skillsRoot = Split-Path -Parent $PSScriptRoot
if (-not $CodexHome) {
    $CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
}
if (-not $PluginRoot) {
    $PluginRoot = Join-Path $skillsRoot "plugins\research-autopilot\skills"
}
$pluginBundleRoot = Split-Path -Parent $PluginRoot
$pluginCacheRoot = Join-Path $CodexHome "plugins\cache\research-environment-local\research-autopilot\0.1.0"
$installedSkillsRoot = Join-Path $CodexHome "skills"
$protectedRuntimeSkillDirs = @(
    (Join-Path $CodexHome "skills\scholar-nuwa")
)

$skills = @(
    "research-autopilot",
    "research-team-orchestrator",
    "academic-paper-review",
    "evidence-based-literature-workflow",
    "reference-fulltext-acquisition",
    "pdf",
    "research-figure-studio",
    "figure-table-studio",
    "research-presentation-studio",
    "manuscript-writing-studio",
    "academic-humanization-studio",
    "writing-reference-capture",
    "reviewer-response-pack",
    "social-science-submission-packager",
    "scholar-panel",
    "social-platform-reader",
    "quant-analysis",
    "desktop-app-product-blueprint",
    "desktop-app-architect",
    "desktop-ui-implementation",
    "desktop-app-qa-debug",
    "desktop-app-release-packager"
)

$standaloneSkillsSynced = @()
$installedSkillDuplicatesRemoved = @()

foreach ($skill in $skills) {
    $sourceDir = Join-Path $PluginRoot $skill

    if (-not (Test-Path -LiteralPath $sourceDir)) {
        throw "Skill source directory not found: $sourceDir"
    }

    $pluginCacheDir = Join-Path $pluginCacheRoot ("skills\" + $skill)
    if (Test-Path -LiteralPath $pluginCacheDir) {
        Remove-Item -LiteralPath $pluginCacheDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $pluginCacheDir | Out-Null
    Get-ChildItem -LiteralPath $sourceDir -Force | Copy-Item -Destination $pluginCacheDir -Recurse -Force

    $targetDir = Join-Path $installedSkillsRoot $skill
    if ($protectedRuntimeSkillDirs -contains $targetDir) {
        throw "Refusing to touch protected runtime skill directory: $targetDir"
    }

    if ($PluginCacheOnly) {
        if (-not $KeepInstalledDuplicates -and (Test-Path -LiteralPath $targetDir)) {
            Remove-Item -LiteralPath $targetDir -Recurse -Force
            $installedSkillDuplicatesRemoved += $skill
        }
    } else {
        if ($protectedRuntimeSkillDirs -contains $targetDir) {
            throw "Refusing to touch protected runtime skill directory: $targetDir"
        }
        if (Test-Path -LiteralPath $targetDir) {
            Remove-Item -LiteralPath $targetDir -Recurse -Force
        }
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        Get-ChildItem -LiteralPath $sourceDir -Force | Copy-Item -Destination $targetDir -Recurse -Force
        $standaloneSkillsSynced += $skill
    }
}

foreach ($relativePath in @(".codex-plugin", "assets", "scripts")) {
    $sourceDir = Join-Path $pluginBundleRoot $relativePath
    if (-not (Test-Path -LiteralPath $sourceDir)) {
        continue
    }
    $targetDir = Join-Path $pluginCacheRoot $relativePath
    if (Test-Path -LiteralPath $targetDir) {
        Remove-Item -LiteralPath $targetDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
    Get-ChildItem -LiteralPath $sourceDir -Force | Copy-Item -Destination $targetDir -Recurse -Force
}

[pscustomobject]@{
    synced_skills = $skills
    standalone_skills_synced = $standaloneSkillsSynced
    plugin_cache_only = [bool]$PluginCacheOnly
    installed_skill_duplicates_removed = $installedSkillDuplicatesRemoved
    codex_home = $CodexHome
    plugin_cache_root = $pluginCacheRoot
    note = "Research Autopilot skills are intentionally exposed both from the plugin cache and as standalone runtime skill mirrors. Source of truth remains this local repository. Restart Codex if updated skill text does not appear immediately."
} | ConvertTo-Json -Depth 5
