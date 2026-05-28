$ErrorActionPreference = "Stop"

$envRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$exePath = Join-Path $envRoot "skills\outputs\manager-app\dist\CodexResearchConsole.exe"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Codex Research Console.lnk"

if (-not (Test-Path $exePath)) {
    throw "未找到 exe：$exePath"
}

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $exePath
$Shortcut.WorkingDirectory = $envRoot
$Shortcut.IconLocation = "$exePath,0"
$Shortcut.Save()

Write-Output $shortcutPath
