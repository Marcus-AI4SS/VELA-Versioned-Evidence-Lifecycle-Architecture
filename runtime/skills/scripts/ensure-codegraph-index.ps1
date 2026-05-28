param(

    [string]$ProjectRoot = (Get-Location).Path,

    [switch]$Force

)



$ErrorActionPreference = "Stop"

$resolved = (Resolve-Path -LiteralPath $ProjectRoot).Path



$command = Get-Command codegraph -ErrorAction SilentlyContinue

if (-not $command) {

    [pscustomobject]@{

        schema_version = "codegraph_index_status.v1"

        ok = $false

        project_root = $resolved

        action = "missing-codegraph-command"

        remediation = "Install CodeGraph first, then rerun this script."

    } | ConvertTo-Json -Depth 4

    exit 1

}



$statusText = & codegraph status --json $resolved 2>$null

$initialized = $false

$status = $null

try {

    if ($LASTEXITCODE -eq 0 -and $statusText) {

        $status = $statusText | ConvertFrom-Json

        $initialized = [bool]$status.initialized

    }

} catch {

    $initialized = $false

}



if ($initialized -and -not $Force) {

    [pscustomobject]@{

        schema_version = "codegraph_index_status.v1"

        ok = $true

        project_root = $resolved

        action = "already-initialized"

        file_count = $status.fileCount

        node_count = $status.nodeCount

        edge_count = $status.edgeCount

        cache = (Join-Path $resolved ".codegraph")

        note = "CodeGraph is project-local. Other project roots still need their own .codegraph index."

    } | ConvertTo-Json -Depth 4

    exit 0

}



if ($Force) {

    & codegraph index --force $resolved

} else {

    & codegraph init -i $resolved

}



if ($LASTEXITCODE -ne 0) {

    [pscustomobject]@{

        schema_version = "codegraph_index_status.v1"

        ok = $false

        project_root = $resolved

        action = $(if ($Force) { "force-index-failed" } else { "init-index-failed" })

        exit_code = $LASTEXITCODE

    } | ConvertTo-Json -Depth 4

    exit $LASTEXITCODE

}



$finalText = & codegraph status --json $resolved

$final = $finalText | ConvertFrom-Json



[pscustomobject]@{

    schema_version = "codegraph_index_status.v1"

    ok = [bool]$final.initialized

    project_root = $resolved

    action = $(if ($Force) { "force-indexed" } else { "initialized-and-indexed" })

    file_count = $final.fileCount

    node_count = $final.nodeCount

    edge_count = $final.edgeCount

    cache = (Join-Path $resolved ".codegraph")

    note = "This script writes only the project-local .codegraph cache. It does not change source rules or replace rg, validators, tests, or Git history."

} | ConvertTo-Json -Depth 4
