param(

    [string]$VaultPath = "<OBSIDIAN_VAULT>",

    [string]$DownloadDir

)



$ErrorActionPreference = "Stop"

$skillsRoot = Split-Path -Parent $PSScriptRoot

if (-not $DownloadDir) {

    $DownloadDir = Join-Path $skillsRoot "outputs\downloads"

}



function Read-JsonFile {

    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {

        return [pscustomobject]@{}

    }

    $raw = Get-Content -LiteralPath $Path -Raw -Encoding utf8

    if ([string]::IsNullOrWhiteSpace($raw)) {

        return [pscustomobject]@{}

    }

    return ($raw | ConvertFrom-Json)

}



function Write-JsonFile {

    param([string]$Path, $Data)

    $dir = Split-Path -Parent $Path

    if ($dir) {

        New-Item -ItemType Directory -Force -Path $dir | Out-Null

    }

    $json = $Data | ConvertTo-Json -Depth 20

    Set-Content -LiteralPath $Path -Value $json -Encoding utf8

}



function Set-JsonProperty {

    param(

        [Parameter(Mandatory = $true)]$Object,

        [Parameter(Mandatory = $true)][string]$Name,

        [Parameter(Mandatory = $true)]$Value

    )

    $prop = $Object.PSObject.Properties[$Name]

    if ($null -ne $prop) {

        $Object.$Name = $Value

    } else {

        $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value

    }

}



function Ensure-Plugin {

    param(

        [string]$PluginId,

        [string]$MainJs,

        [string]$Manifest,

        [string]$StylesCss

    )

    $targetDir = Join-Path $pluginsDir $PluginId

    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

    Copy-Item -LiteralPath $MainJs -Destination (Join-Path $targetDir "main.js") -Force

    Copy-Item -LiteralPath $Manifest -Destination (Join-Path $targetDir "manifest.json") -Force

    Copy-Item -LiteralPath $StylesCss -Destination (Join-Path $targetDir "styles.css") -Force

}



$obsidianDir = Join-Path $VaultPath ".obsidian"

$pluginsDir = Join-Path $obsidianDir "plugins"

New-Item -ItemType Directory -Force -Path $pluginsDir | Out-Null



Ensure-Plugin `

    -PluginId "dataview" `

    -MainJs (Join-Path $DownloadDir "dataview-main.js") `

    -Manifest (Join-Path $DownloadDir "dataview-manifest.json") `

    -StylesCss (Join-Path $DownloadDir "dataview-styles.css")



Ensure-Plugin `

    -PluginId "obsidian-zotero-desktop-connector" `

    -MainJs (Join-Path $DownloadDir "obsidian-zotero-integration-main.js") `

    -Manifest (Join-Path $DownloadDir "obsidian-zotero-integration-manifest.json") `

    -StylesCss (Join-Path $DownloadDir "obsidian-zotero-integration-styles.css")



$appJsonPath = Join-Path $obsidianDir "app.json"

$appJson = Read-JsonFile -Path $appJsonPath

Set-JsonProperty -Object $appJson -Name "communityPluginSafeMode" -Value $false

Write-JsonFile -Path $appJsonPath -Data $appJson



$corePluginsPath = Join-Path $obsidianDir "core-plugins.json"

$corePlugins = Read-JsonFile -Path $corePluginsPath

Set-JsonProperty -Object $corePlugins -Name "templates" -Value $true

Set-JsonProperty -Object $corePlugins -Name "properties" -Value $true

Write-JsonFile -Path $corePluginsPath -Data $corePlugins



$templatesPath = Join-Path $obsidianDir "templates.json"

$templatesConfig = [pscustomobject]@{

    folder = "VELA Research/00-模板"

}

Write-JsonFile -Path $templatesPath -Data $templatesConfig



$communityPath = Join-Path $obsidianDir "community-plugins.json"

$currentPlugins = @()

if (Test-Path -LiteralPath $communityPath) {

    $existing = Get-Content -LiteralPath $communityPath -Raw -Encoding utf8 | ConvertFrom-Json

    if ($existing) {

        $currentPlugins = @($existing)

    }

}

$targetPlugins = @($currentPlugins + @("dataview", "obsidian-zotero-desktop-connector")) | Select-Object -Unique

$targetPlugins | ConvertTo-Json | Set-Content -LiteralPath $communityPath -Encoding utf8



[pscustomobject]@{

    vault_path = $VaultPath

    templates_folder = "VELA Research/00-模板"

    community_plugins = $targetPlugins

    properties_enabled = $true

    templates_enabled = $true

} | ConvertTo-Json -Depth 5
