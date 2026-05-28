param(
    [string]$RepoPath = "<USER_DESKTOP>\zotero-obsidian-workflow-config",
    [string]$SourceRoot
)

$ErrorActionPreference = "Stop"
$SourceRoot = if ($SourceRoot) { $SourceRoot } else { Split-Path -Parent $PSScriptRoot }

function Ensure-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Git {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )
    & 'C:\Program Files\Git\cmd\git.exe' @Args
}

function Get-GitHubCredential {
    $raw = "protocol=https`nhost=github.com`n`n" | & 'C:\Program Files\Git\cmd\git.exe' credential fill 2>$null | Out-String
    if (-not ($raw -match "username=(.+)")) { return $null }
    $username = $Matches[1].Trim()
    if (-not ($raw -match "password=(.+)")) { return $null }
    $token = $Matches[1].Trim()
    return @{
        username = $username
        token = $token
    }
}

function Ensure-GitHubPrivateRepo {
    param([string]$RepoName)

    $cred = Get-GitHubCredential
    if (-not $cred) {
        return $null
    }

    $headers = @{
        Authorization = "token $($cred.token)"
        Accept = "application/vnd.github+json"
        "User-Agent" = "codex-research-workflow"
    }

    $repoApi = "https://api.github.com/repos/$($cred.username)/$RepoName"
    $repoRemote = "https://github.com/$($cred.username)/$RepoName.git"

    try {
        Invoke-RestMethod -Uri $repoApi -Headers $headers -Method Get | Out-Null
        return @{
            remote = $repoRemote
            username = $cred.username
        }
    } catch {
        $response = $_.Exception.Response
        if ($response -and $response.StatusCode.value__ -ne 404) {
            return $null
        }
    }

    $body = @{
        name = $RepoName
        private = $true
        auto_init = $false
        description = "Zotero and Obsidian workflow configuration for Codex"
    } | ConvertTo-Json

    try {
        Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Headers $headers -Method Post -Body $body | Out-Null
        return @{
            remote = $repoRemote
            username = $cred.username
        }
    } catch {
        return $null
    }
}

Ensure-Dir $RepoPath
Ensure-Dir (Join-Path $RepoPath "docs")
Ensure-Dir (Join-Path $RepoPath "guides")
Ensure-Dir (Join-Path $RepoPath "zotero")
Ensure-Dir (Join-Path $RepoPath "obsidian\example-vault\00-系统")
Ensure-Dir (Join-Path $RepoPath "obsidian\example-vault\00-模板")
Ensure-Dir (Join-Path $RepoPath "obsidian\example-vault\50-面板")
Ensure-Dir (Join-Path $RepoPath "skills\writing-reference-capture")
Ensure-Dir (Join-Path $RepoPath "scripts")

$readme = @"
# zotero-obsidian-workflow-config

这是一套面向研究工作的 `Zotero + Obsidian + Codex` 双层知识管理配置仓。

## 内容

- `docs/`：统一说明书、成熟方案复核
- `guides/`：GitHub / Bilibili / CSDN 攻略矩阵
- `zotero/`：Zotero 工作流参考
- `obsidian/example-vault/`：示例目录、模板、面板
- `skills/`：`writing-reference-capture`
- `scripts/`：自动安装与同步脚本

## 边界

本仓库只放配置、模板、说明书和示例库。
不跟踪真实 Zotero 数据库、PDF、真实 Obsidian 笔记或敏感信息。
"@

$gitignore = @"
.venv/
outputs/
cache/
*.sqlite
*.sqlite-*
*.bak
*.pdf
*.epub
*.xpi
*.zip
*.tar
*.tar.gz
obsidian/real-vault/
zotero/live-data/
secrets/
tokens/
"@

Set-Content -LiteralPath (Join-Path $RepoPath "README.md") -Value $readme -Encoding utf8
Set-Content -LiteralPath (Join-Path $RepoPath ".gitignore") -Value $gitignore -Encoding utf8

$integrationDocsRoot = Join-Path $SourceRoot "docs\30-integrations"
$operationsDocsRoot = Join-Path $SourceRoot "docs\10-operations"

$docsToCopy = @(
    "研究型Codex-统一说明书.md",
    "Codex-Zotero-Obsidian-成熟方案复核.md",
    "Zotero-Obsidian-成熟攻略矩阵.md"
)

foreach ($doc in $docsToCopy) {
    $src = if ($doc -eq "研究型Codex-统一说明书.md") {
        Join-Path $operationsDocsRoot $doc
    } else {
        Join-Path $integrationDocsRoot $doc
    }
    Copy-Item -LiteralPath $src -Destination (Join-Path $RepoPath ("docs\" + $doc)) -Force
}

Copy-Item -LiteralPath (Join-Path $integrationDocsRoot "Zotero-Obsidian-成熟攻略矩阵.md") -Destination (Join-Path $RepoPath "guides\Zotero-Obsidian-成熟攻略矩阵.md") -Force
Copy-Item -LiteralPath (Join-Path $operationsDocsRoot "研究型Codex-统一说明书.md") -Destination (Join-Path $RepoPath "zotero\研究型Codex-统一说明书.md") -Force

Copy-Item -LiteralPath (Join-Path $SourceRoot "templates\obsidian\文献笔记模板.md") -Destination (Join-Path $RepoPath "obsidian\example-vault\00-模板\文献笔记模板.md") -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "templates\obsidian\项目地图模板.md") -Destination (Join-Path $RepoPath "obsidian\example-vault\00-模板\项目地图模板.md") -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "templates\obsidian\方法卡模板.md") -Destination (Join-Path $RepoPath "obsidian\example-vault\00-模板\方法卡模板.md") -Force

Get-ChildItem -LiteralPath (Join-Path $SourceRoot "templates\obsidian\panels") -Filter *.md | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $RepoPath ("obsidian\example-vault\50-面板\" + $_.Name)) -Force
}

Copy-Item -LiteralPath (Join-Path $operationsDocsRoot "研究型Codex-统一说明书.md") -Destination (Join-Path $RepoPath "obsidian\example-vault\00-系统\研究型Codex-统一说明书.md") -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "plugins\research-autopilot\skills\writing-reference-capture\SKILL.md") -Destination (Join-Path $RepoPath "skills\writing-reference-capture\SKILL.md") -Force

$scriptsToCopy = @(
    "install_obsidian_research_plugins.ps1",
    "install_zotero_research_addons.ps1",
    "install_writing_reference_capture_skill.ps1",
    "bootstrap_zotero_obsidian_workflow.ps1"
)

foreach ($script in $scriptsToCopy) {
    Copy-Item -LiteralPath (Join-Path $SourceRoot ("scripts\" + $script)) -Destination (Join-Path $RepoPath ("scripts\" + $script)) -Force
}

if (-not (Test-Path -LiteralPath (Join-Path $RepoPath ".git"))) {
    Git -C $RepoPath init -b main | Out-Null
}

$remoteInfo = Ensure-GitHubPrivateRepo -RepoName "zotero-obsidian-workflow-config"
$remote = $null
if ($remoteInfo) {
    $remote = $remoteInfo.remote
    $hasOrigin = $true
    Git -C $RepoPath remote get-url origin 1>$null 2>$null
    if ($LASTEXITCODE -ne 0) {
        $hasOrigin = $false
    }
    if (-not $hasOrigin) {
        Git -C $RepoPath remote add origin $remote
    }

    $userName = Git -C $RepoPath config user.name 2>$null
    if (-not $userName) {
        Git -C $RepoPath config user.name $remoteInfo.username | Out-Null
    }

    $userEmail = Git -C $RepoPath config user.email 2>$null
    if (-not $userEmail) {
        Git -C $RepoPath config user.email "$($remoteInfo.username)@users.noreply.github.com" | Out-Null
    }
}

Git -C $RepoPath add . | Out-Null
$status = Git -C $RepoPath status --short
if ($status) {
    Git -C $RepoPath commit -m "初始化 Zotero 与 Obsidian 工作流配置仓" | Out-Null
}

$pushStatus = "skipped"
if ($remote) {
    try {
        Git -C $RepoPath push -u origin main | Out-Null
        $pushStatus = "success"
    } catch {
        $pushStatus = "failed"
    }
}

[pscustomobject]@{
    repo_path = $RepoPath
    remote = $remote
    initialized = $true
    push_status = $pushStatus
    note = "Configuration repo created. If remote is empty or push_status is failed, create or push the private GitHub repo manually."
} | ConvertTo-Json -Depth 5
