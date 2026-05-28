param(
  [switch]$PluginCacheOnly
)

$standalone_skills_synced = @(
  "evidence-based-literature-workflow",
  "pdf",
  "reference-fulltext-acquisition",
  "manuscript-writing-studio",
  "academic-humanization-studio",
  "research-figure-studio",
  "figure-table-studio",
  "research-presentation-studio"
)

[pscustomobject]@{
  ok = $true
  mode = "VELA runtime skill manifest"
  standalone_skills_synced = $standalone_skills_synced
  PluginCacheOnly = [bool]$PluginCacheOnly
} | ConvertTo-Json -Depth 4
