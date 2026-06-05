param(
    [int]$MinAgeMinutes = 0,
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$now = Get-Date
# Includes retired or optional MCP server signatures so stale children can be stopped
# after profile changes. Listing a pattern here does not make it an active dependency.
$patterns = @(
    "paper_search_mcp.server",
    "social_platform_mcp_server.py",
    "Google-Scholar-MCP-Server",
    "google_scholar_server.py",
    "openalex-research-mcp",
    "@playwright\mcp",
    "@playwright/mcp",
    "chrome-devtools-mcp",
    "codegraph.cmd",
    "codegraph.js serve --mcp",
    "semantic-scholar-plugin.py",
    "cnki_mcp_server.py",
    "social-platform"
)

$processes = Get-CimInstance Win32_Process
$byParent = @{}
foreach ($process in $processes) {
    $parent = [int]$process.ParentProcessId
    if (-not $byParent.ContainsKey($parent)) {
        $byParent[$parent] = New-Object System.Collections.Generic.List[object]
    }
    $byParent[$parent].Add($process) | Out-Null
}

function Test-ManagedMcpProcess {
    param($Process)
    $commandLine = [string]$Process.CommandLine
    foreach ($pattern in $patterns) {
        if ($commandLine.IndexOf($pattern, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            return $true
        }
    }
    return $false
}

function Add-Descendants {
    param(
        [int]$ParentId,
        [System.Collections.Generic.Dictionary[int, object]]$Targets
    )
    if (-not $byParent.ContainsKey($ParentId)) {
        return
    }
    foreach ($child in $byParent[$ParentId]) {
        $childId = [int]$child.ProcessId
        if (-not $Targets.ContainsKey($childId)) {
            $Targets[$childId] = $child
            Add-Descendants -ParentId $childId -Targets $Targets
        }
    }
}

$targets = [System.Collections.Generic.Dictionary[int, object]]::new()
foreach ($process in $processes) {
    if (-not (Test-ManagedMcpProcess -Process $process)) {
        continue
    }
    $ageMinutes = (($now - $process.CreationDate).TotalMinutes)
    if ($ageMinutes -lt $MinAgeMinutes) {
        continue
    }
    $processId = [int]$process.ProcessId
    $targets[$processId] = $process
    Add-Descendants -ParentId $processId -Targets $targets
}

$orderedTargets = $targets.Values | Sort-Object CreationDate -Descending
$stopped = New-Object System.Collections.Generic.List[object]
$errors = New-Object System.Collections.Generic.List[object]

foreach ($process in $orderedTargets) {
    $processId = [int]$process.ProcessId
    $item = [pscustomobject]@{
        pid = $processId
        name = $process.Name
        parent_pid = [int]$process.ParentProcessId
        creation_time = $process.CreationDate.ToString("s")
        command_line = $process.CommandLine
    }
    if ($WhatIf) {
        $stopped.Add($item) | Out-Null
        continue
    }
    try {
        Stop-Process -Id $processId -Force -ErrorAction Stop
        $stopped.Add($item) | Out-Null
    } catch {
        $errors.Add([pscustomobject]@{
            pid = $processId
            error = $_.Exception.Message
            command_line = $process.CommandLine
        }) | Out-Null
    }
}

[pscustomobject]@{
    schema_version = "codex_mcp_cleanup.v1"
    mode = $(if ($WhatIf) { "dry-run" } else { "stop" })
    min_age_minutes = $MinAgeMinutes
    matched_count = $targets.Count
    stopped_count = $(if ($WhatIf) { 0 } else { $stopped.Count })
    candidates = $stopped
    errors = $errors
} | ConvertTo-Json -Depth 6
