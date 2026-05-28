param(

    [string]$AgentBrowserHome = "<USER_HOME>\.agent-browser"

)



$ErrorActionPreference = "Stop"



if (-not (Test-Path -LiteralPath $AgentBrowserHome)) {

    throw "agent-browser home was not found: $AgentBrowserHome"

}



$removed = New-Object System.Collections.Generic.List[string]



Get-ChildItem -LiteralPath $AgentBrowserHome -Filter "*.pid" -File | ForEach-Object {

    $pidFile = $_.FullName

    $sessionName = $_.BaseName

    $rawPid = (Get-Content -Raw -LiteralPath $pidFile).Trim()



    if (-not $rawPid) {

        return

    }



    $isAlive = $null -ne (Get-Process -Id ([int]$rawPid) -ErrorAction SilentlyContinue)

    if ($isAlive) {

        return

    }



    foreach ($suffix in @("engine", "pid", "port", "stream", "version")) {

        $path = Join-Path $AgentBrowserHome ($sessionName + "." + $suffix)

        if (Test-Path -LiteralPath $path) {

            Remove-Item -LiteralPath $path -Force

            $removed.Add($path) | Out-Null

        }

    }

}



[pscustomobject]@{

    removed_files = $removed

    note = "Only dead session sidecar files were removed. Saved auth state under .agent-browser\\sessions was left untouched."

} | ConvertTo-Json -Depth 5
