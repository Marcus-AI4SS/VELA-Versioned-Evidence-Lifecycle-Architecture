param(

    [string]$ProfilePath = "<USER_HOME>\AppData\Roaming\Zotero\Zotero\Profiles\zjkxrj29.default",

    [string]$DownloadDir,

    [string]$ZoteroExePath = "C:\zotero\zotero.exe"

)



$ErrorActionPreference = "Stop"

$skillsRoot = Split-Path -Parent $PSScriptRoot

if (-not $DownloadDir) {

    $DownloadDir = Join-Path $skillsRoot "outputs\downloads"

}



function Download-WithResume {

    param(

        [string]$Url,

        [string]$TargetPath,

        [int64]$ExpectedSize,

        [int]$MaxAttempts = 6

    )



    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetPath) | Out-Null



    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {

        if ((Test-Path -LiteralPath $TargetPath) -and ((Get-Item -LiteralPath $TargetPath).Length -ge $ExpectedSize)) {

            return

        }



        & curl.exe -L -C - $Url -o $TargetPath | Out-Null



        if ((Test-Path -LiteralPath $TargetPath) -and ((Get-Item -LiteralPath $TargetPath).Length -ge $ExpectedSize)) {

            return

        }



        Start-Sleep -Seconds 2

    }



    throw "Download failed or did not reach expected size: $TargetPath"

}



$addons = @(

    @{

        id = "better-bibtex@iris-advies.com"

        file = "zotero-better-bibtex-9.0.19.xpi"

        url = "https://github.com/retorquere/zotero-better-bibtex/releases/download/v9.0.19/zotero-better-bibtex-9.0.19.xpi"

        size = 34204005

    },

    @{

        id = "Knowledge4Zotero@windingwind.com"

        file = "better-notes-for-zotero-v3.0.4.xpi"

        url = "https://github.com/windingwind/zotero-better-notes/releases/download/v3.0.4/better-notes-for-zotero.xpi"

        size = 5190470

    },

    @{

        id = "jasminum@linxzh.com"

        file = "jasminum_1.1.35.xpi"

        url = "https://github.com/l0o0/jasminum/releases/download/v1.1.35/jasminum_1.1.35.xpi"

        size = 399781

    }

)



$extensionsDir = Join-Path $ProfilePath "extensions"

New-Item -ItemType Directory -Force -Path $extensionsDir | Out-Null



foreach ($addon in $addons) {

    $downloadTarget = Join-Path $DownloadDir $addon.file

    Download-WithResume -Url $addon.url -TargetPath $downloadTarget -ExpectedSize $addon.size

    Copy-Item -LiteralPath $downloadTarget -Destination (Join-Path $extensionsDir ("{0}.xpi" -f $addon.id)) -Force

}



$zoteroRunning = @(Get-Process zotero -ErrorAction SilentlyContinue).Count -gt 0



[pscustomobject]@{

    zotero_exe = $ZoteroExePath

    profile_path = $ProfilePath

    extensions_dir = $extensionsDir

    zotero_running = $zoteroRunning

    staged_extensions = $addons | ForEach-Object { $_.id }

    note = "Add-ons copied to profile/extensions. Restart Zotero to load them."

} | ConvertTo-Json -Depth 5
