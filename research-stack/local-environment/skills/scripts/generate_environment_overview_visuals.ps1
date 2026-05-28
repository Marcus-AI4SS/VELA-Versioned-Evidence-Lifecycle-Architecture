param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"

$outputRoot = Join-Path $RepoRoot "outputs\environment-overview"
$imageRoot = Join-Path $outputRoot "images"
$assetRoot = Join-Path $RepoRoot "assets"
$pptxPath = Join-Path $outputRoot "local-research-environment-overview.pptx"
New-Item -ItemType Directory -Force -Path $outputRoot, $imageRoot, $assetRoot | Out-Null

function RgbInt([string]$hex) {
  $h = $hex.TrimStart("#")
  $r = [Convert]::ToInt32($h.Substring(0, 2), 16)
  $g = [Convert]::ToInt32($h.Substring(2, 2), 16)
  $b = [Convert]::ToInt32($h.Substring(4, 2), 16)
  return $r + ($g * 256) + ($b * 65536)
}

function Add-Text($slide, [double]$x, [double]$y, [double]$w, [double]$h, [string]$value, [int]$size, [string]$color = "0A0A0A", [bool]$bold = $false, [string]$align = "left") {
  $shape = $slide.Shapes.AddTextbox(1, $x, $y, $w, $h)
  $shape.TextFrame2.MarginLeft = 0
  $shape.TextFrame2.MarginRight = 0
  $shape.TextFrame2.MarginTop = 0
  $shape.TextFrame2.MarginBottom = 0
  $shape.TextFrame2.WordWrap = -1
  $shape.TextFrame2.TextRange.Text = $value
  $shape.TextFrame2.TextRange.Font.Name = "Microsoft YaHei"
  $shape.TextFrame2.TextRange.Font.NameFarEast = "Microsoft YaHei"
  $shape.TextFrame2.TextRange.Font.Size = $size
  $shape.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = RgbInt $color
  if ($bold) { $shape.TextFrame2.TextRange.Font.Bold = -1 }
  if ($align -eq "center") { $shape.TextFrame2.TextRange.ParagraphFormat.Alignment = 2 }
  return $shape
}

function Add-Box($slide, [double]$x, [double]$y, [double]$w, [double]$h, [string]$fill = "FFFFFF", [string]$line = "DCDCDC", [double]$lineWidth = 1) {
  $shape = $slide.Shapes.AddShape(1, $x, $y, $w, $h)
  $shape.Fill.ForeColor.RGB = RgbInt $fill
  $shape.Line.ForeColor.RGB = RgbInt $line
  $shape.Line.Weight = $lineWidth
  return $shape
}

function Add-Chip($slide, [double]$x, [double]$y, [double]$w, [double]$h, [string]$label, [string]$fill = "F0F0EE", [string]$color = "0A0A0A") {
  Add-Box $slide $x $y $w $h $fill "DCDCDC" 0.75 | Out-Null
  Add-Text $slide ($x + 8) ($y + 6) ($w - 16) ($h - 10) $label 10 $color $true "center" | Out-Null
}

function Add-Arrow($slide, [double]$x1, [double]$y1, [double]$x2, [double]$y2, [string]$color = "002FA7", [double]$weight = 2.25) {
  $line = $slide.Shapes.AddLine($x1, $y1, $x2, $y2)
  $line.Line.ForeColor.RGB = RgbInt $color
  $line.Line.Weight = $weight
  $line.Line.EndArrowheadStyle = 3
  return $line
}

function Add-Header($slide, [string]$section, [string]$page) {
  Add-Text $slide 36 18 460 16 $section 7 "737373" $false | Out-Null
  Add-Text $slide 880 18 40 16 $page 7 "737373" $false "right" | Out-Null
}

$skillCatalog = Get-Content (Join-Path $RepoRoot "skills\catalog\skill_catalog.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$routingTable = Get-Content (Join-Path $RepoRoot "skills\catalog\routing_table.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$qualityGates = Get-Content (Join-Path $RepoRoot "skills\catalog\quality_gates.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$mcpPolicy = Get-Content (Join-Path $RepoRoot "skills\catalog\route_mcp_activation_policy.json") -Raw -Encoding UTF8 | ConvertFrom-Json

$skillCount = ($skillCatalog.skills.PSObject.Properties | Where-Object { $_.Value.status -eq "active" }).Count
$routeCount = $routingTable.routes.Count
$gateCount = $qualityGates.gates.Count
$mcpCount = (($mcpPolicy.routes | ForEach-Object { $_.required_mcp + $_.optional_mcp }) | Where-Object { $_ } | Sort-Object -Unique).Count

$ppt = $null
$presentation = $null
try {
  $ppt = New-Object -ComObject PowerPoint.Application
  $ppt.Visible = -1
  $presentation = $ppt.Presentations.Add()
  $presentation.PageSetup.SlideWidth = 960
  $presentation.PageSetup.SlideHeight = 540

  # Slide 1
  $s = $presentation.Slides.Add(1, 12)
  Add-Box $s 0 0 960 540 "002FA7" "002FA7" 0 | Out-Null
  Add-Text $s 54 100 720 145 "本地研究环境`n可治理的研究工作台" 44 "FFFFFF" $false | Out-Null
  Add-Text $s 58 365 620 44 "Engineering Cybernetics · Seven Layers · Controlled Evolution" 15 "FFFFFF" $false | Out-Null
  Add-Text $s 58 420 760 34 "先判断路线，再调用工具；先留下证据，再沉淀经验。" 22 "FFFFFF" $false | Out-Null

  # Slide 2
  $s = $presentation.Slides.Add(2, 12)
  Add-Header $s "SECTION 01 · OVERVIEW" "02 / 09"
  Add-Text $s 52 78 760 82 "不是工具箱，`n而是一套研究控制系统。" 38 "0A0A0A" $false | Out-Null
  Add-Text $s 56 205 760 52 "用户只需要说清楚任务。系统负责判断路线、选择工具、检查证据、记录过程，并在项目结束后把稳定经验沉淀下来。" 20 "4B5563" $false | Out-Null
  $metricLabels = @("技能", "任务路线", "工具接口", "检查点")
  $metricNums = @($skillCount, $routeCount, $mcpCount, $gateCount)
  for ($i = 0; $i -lt 4; $i++) {
    $x = 62 + $i * 205
    Add-Box $s $x 340 165 90 "F0F0EE" "D4D4D2" 0.75 | Out-Null
    Add-Text $s ($x + 18) 358 120 34 ([string]$metricNums[$i]) 30 "002FA7" $false | Out-Null
    Add-Text $s ($x + 20) 400 120 22 $metricLabels[$i] 13 "737373" $true | Out-Null
  }

  # Slide 3 main map
  $s = $presentation.Slides.Add(3, 12)
  Add-Header $s "SECTION 02 · ARCHITECTURE" "03 / 09"
  Add-Text $s 42 52 410 40 "本地研究环境" 26 "0A0A0A" $true | Out-Null
  Add-Text $s 44 88 510 22 "以工程控制论组织研究、工具、证据和长期演化" 13 "737373" $false | Out-Null
  Add-Box $s 54 145 210 72 "FFFFFF" "D4DCE8" 1 | Out-Null
  Add-Text $s 76 164 160 24 "用户任务" 18 "0A0A0A" $true | Out-Null
  Add-Text $s 76 192 165 30 "研究 / 文献 / 写作 / 绘图 / 环境维护" 10 "737373" $false | Out-Null
  Add-Arrow $s 264 181 330 181
  Add-Box $s 330 128 250 106 "002FA7" "002FA7" 0 | Out-Null
  Add-Text $s 356 154 190 28 "总入口：先判断路线" 20 "FFFFFF" $true | Out-Null
  Add-Text $s 356 188 190 30 "新链条、路线切换或语义模糊时先确认。" 11 "EAF1FF" $false | Out-Null
  Add-Arrow $s 580 181 650 181
  Add-Box $s 650 145 240 72 "F0FBF8" "8BD5C8" 1 | Out-Null
  Add-Text $s 672 164 170 24 "控制核与规则" 18 "0A0A0A" $true | Out-Null
  Add-Text $s 672 192 180 26 "目标、边界、反馈、稳定性、记忆准入。" 10 "737373" $false | Out-Null
  Add-Arrow $s 812 235 505 270 "002FA7" 1.6 | Out-Null
  Add-Text $s 595 242 160 16 "闭环反馈与纠偏" 10 "002FA7" $true | Out-Null

  $layers = @(
    @("执行动作","运行命令、写文件、生成结果","002FA7"),
    @("工具接口","浏览器、Zotero、学术检索","F59E0B"),
    @("上下文与证据","材料、引用、项目事实","0F9F8F"),
    @("研究阶段","从设计到投稿和复盘","6E56CF"),
    @("运行日志","日报、状态、失败原因","64748B"),
    @("可靠性检查","结构规则、测试、检查点","7C3AED"),
    @("环境治理","权限、回滚、外部吸收","17A673")
  )
  for ($i = 0; $i -lt $layers.Count; $i++) {
    $x = 62 + ($i % 4) * 218
    $y = 275 + [math]::Floor($i / 4) * 76
    Add-Box $s $x $y 190 52 "FFFFFF" "D7DDE8" 0.75 | Out-Null
    Add-Box $s $x $y 6 52 $layers[$i][2] $layers[$i][2] 0 | Out-Null
    Add-Text $s ($x + 18) ($y + 10) 130 16 $layers[$i][0] 13 "0A0A0A" $true | Out-Null
    Add-Text $s ($x + 18) ($y + 30) 145 14 $layers[$i][1] 8 "737373" $false | Out-Null
  }
  $work = @("找文献","结构性阅读","分析与图表","写作与审稿","PPT 与交付")
  for ($i = 0; $i -lt $work.Count; $i++) {
    $x = 62 + $i * 170
    Add-Box $s $x 445 135 46 "FFFDF7" "E7D29C" 0.75 | Out-Null
    Add-Text $s ($x + 14) 458 100 18 $work[$i] 13 "0A0A0A" $true | Out-Null
  }

  # Slide 4 stage map
  $s = $presentation.Slides.Add(4, 12)
  Add-Header $s "SECTION 03 · RESEARCH CHAIN" "04 / 09"
  Add-Text $s 42 54 720 36 "研究工作从哪里开始，下一步去哪里" 25 "0A0A0A" $true | Out-Null
  Add-Text $s 44 90 720 22 "AI 可以主动建议进入下一阶段，但切换路线、下载和写入前必须先确认。" 12 "737373" $false | Out-Null
  $stages = @(
    @("研究设计","问题、对象、材料边界"),
    @("候选文献","约 50 篇，优先高被引"),
    @("获取全文","开放来源、Scholar、CNKI"),
    @("结构性阅读","证据句、变量、理论基础"),
    @("引文核验","PDF 标注、支撑正文"),
    @("正文写作","PEEL、章节职责"),
    @("图表与 PPT","论文图、表格、汇报"),
    @("审稿修改","问题账本、回复矩阵"),
    @("润色定稿","目标期刊适配"),
    @("投稿复盘","冻结材料、经验沉淀")
  )
  for ($i = 0; $i -lt $stages.Count; $i++) {
    $row = [math]::Floor($i / 5)
    $col = $i % 5
    $x = 58 + $col * 178
    $y = 150 + $row * 155
    Add-Box $s $x $y 150 62 ($(if ($i % 2 -eq 0) { "FFFFFF" } else { "F4F7FF" })) "CFD7E6" 0.9 | Out-Null
    Add-Box $s ($x + 10) ($y + 16) 30 30 ($(if ($i -lt 6) { "002FA7" } else { "0F9F8F" })) ($(if ($i -lt 6) { "002FA7" } else { "0F9F8F" })) 0 | Out-Null
    Add-Text $s ($x + 17) ($y + 19) 18 16 ([string]($i + 1)) 12 "FFFFFF" $true "center" | Out-Null
    Add-Text $s ($x + 50) ($y + 14) 88 16 $stages[$i][0] 12 "0A0A0A" $true | Out-Null
    Add-Text $s ($x + 50) ($y + 34) 88 16 $stages[$i][1] 8 "737373" $false | Out-Null
    if ($row -eq 0 -and $col -lt 4) { Add-Arrow $s ($x + 150) ($y + 31) ($x + 174) ($y + 31) "64748B" 1.3 | Out-Null }
    if ($row -eq 1 -and $col -gt 0) { Add-Arrow $s $x ($y + 31) ($x - 24) ($y + 31) "64748B" 1.3 | Out-Null }
  }
  Add-Arrow $s 828 214 828 305 "64748B" 1.3 | Out-Null
  Add-Box $s 140 438 680 54 "F0FBF8" "9FDCD1" 0.9 | Out-Null
  Add-Text $s 170 452 220 18 "每个阶段都不是自动跳过去" 14 "0A0A0A" $true | Out-Null
  Add-Text $s 170 474 560 12 "系统只提出建议；是否下载、写文件、切换路线、调用多角色或改变项目状态，必须等用户确认。" 9 "737373" $false | Out-Null

  # Slide 5 memory governance
  $s = $presentation.Slides.Add(5, 12)
  Add-Header $s "SECTION 04 · MEMORY & AUTOMATION" "05 / 09"
  Add-Text $s 42 54 720 36 "记忆、自动化与自我演化怎么管" 25 "0A0A0A" $true | Out-Null
  Add-Text $s 44 90 760 22 "运行态记忆可以让系统更顺手，但源规则仍由本地 Git 仓、schema、校验器和提交记录决定。" 12 "737373" $false | Out-Null
  Add-Box $s 58 165 210 80 "FFFFFF" "CFD7E6" 0.9 | Out-Null
  Add-Text $s 86 188 130 18 "运行态记忆" 15 "0A0A0A" $true | Out-Null
  Add-Text $s 86 214 130 18 "agentmemory：召回经验和显式保存偏好" 9 "737373" $false | Out-Null
  Add-Box $s 58 315 210 80 "FFFFFF" "CFD7E6" 0.9 | Out-Null
  Add-Text $s 86 338 130 18 "代码结构索引" 15 "0A0A0A" $true | Out-Null
  Add-Text $s 86 364 130 18 "codegraph：理解文件关系和影响范围" 9 "737373" $false | Out-Null
  Add-Box $s 370 215 250 145 "F4F7FF" "B9C9EC" 0.9 | Out-Null
  Add-Text $s 408 245 170 24 "本地源规则层" 21 "0A0A0A" $true | Out-Null
  $chips = @("控制核","路线表","冲突矩阵","数据格式","校验器","测试","提交记录")
  for ($i = 0; $i -lt $chips.Count; $i++) {
    $x = 405 + ($i % 2) * 105
    $y = 292 + [math]::Floor($i / 2) * 24
    Add-Chip $s $x $y 92 17 $chips[$i] "FFFFFF" "002FA7"
  }
  Add-Arrow $s 268 205 370 260 "002FA7" 1.7 | Out-Null
  Add-Arrow $s 268 355 370 312 "002FA7" 1.7 | Out-Null
  Add-Box $s 720 165 190 80 "FFFDF7" "E7D29C" 0.9 | Out-Null
  Add-Text $s 748 188 120 18 "每日检查" 15 "0A0A0A" $true | Out-Null
  Add-Text $s 748 214 130 18 "路线冲突、七层漂移、记忆对账" 9 "737373" $false | Out-Null
  Add-Box $s 720 315 190 80 "F0FBF8" "9FDCD1" 0.9 | Out-Null
  Add-Text $s 748 338 120 18 "低风险演化" 15 "0A0A0A" $true | Out-Null
  Add-Text $s 748 364 130 18 "可回滚、有日志、能通过校验" 9 "737373" $false | Out-Null
  Add-Arrow $s 620 260 720 205 "F59E0B" 1.7 | Out-Null
  Add-Arrow $s 620 312 720 355 "0F9F8F" 1.7 | Out-Null
  Add-Box $s 180 455 600 46 "FFFFFF" "D7DDE8" 0.9 | Out-Null
  Add-Text $s 210 466 90 14 "硬边界" 12 "0A0A0A" $true | Out-Null
  Add-Text $s 300 466 430 16 "记忆召回只提供候选线索；所有持久规则必须经过 envctl 校验和 Git 提交。" 9 "737373" $false | Out-Null

  # Slide 6
  $s = $presentation.Slides.Add(6, 12)
  Add-Header $s "SECTION 05 · ROUTING" "06 / 09"
  Add-Text $s 52 70 600 72 "新增增强：`n先解释，再进入链条。" 32 "0A0A0A" $false | Out-Null
  $items = @("conflict_matrix：记录路线和工具冲突","route explain：解释为什么命中某条路线","startup-summary：新线程只带紧凑上下文","memory reconcile：对账自动化、待办和运行态记忆")
  for ($i = 0; $i -lt $items.Count; $i++) {
    Add-Box $s 72 (210 + $i * 55) 690 34 "F0F0EE" "D4D4D2" 0.5 | Out-Null
    Add-Text $s 92 (219 + $i * 55) 610 14 $items[$i] 12 "0A0A0A" $false | Out-Null
  }

  # Slide 7
  $s = $presentation.Slides.Add(7, 12)
  Add-Header $s "SECTION 06 · DAILY USE" "07 / 09"
  Add-Text $s 52 70 520 40 "日常只记四个入口" 28 "0A0A0A" $true | Out-Null
  $entries = @(
    @("research-autopilot","总入口"),
    @("evidence-based-literature-workflow","文献证据"),
    @("manuscript / figure / presentation","写作图表PPT"),
    @("research-stack-manager","环境治理")
  )
  for ($i = 0; $i -lt 4; $i++) {
    $x = 70 + $i * 215
    Add-Box $s $x 190 170 160 ($(if ($i -eq 0) { "002FA7" } else { "FFFFFF" })) ($(if ($i -eq 0) { "002FA7" } else { "D4D4D2" })) 0.8 | Out-Null
    Add-Text $s ($x + 18) 220 125 22 $entries[$i][1] 17 ($(if ($i -eq 0) { "FFFFFF" } else { "0A0A0A" })) $true | Out-Null
    Add-Text $s ($x + 18) 268 128 38 $entries[$i][0] 11 ($(if ($i -eq 0) { "EAF1FF" } else { "737373" })) $false | Out-Null
  }

  # Slide 8
  $s = $presentation.Slides.Add(8, 12)
  Add-Header $s "SECTION 07 · BOUNDARIES" "08 / 09"
  Add-Text $s 52 78 760 54 "能自动，但不能乱自动。" 38 "0A0A0A" $false | Out-Null
  Add-Text $s 58 190 720 170 "正式引用必须可核验。`n新链条和高成本工具先确认。`nagentmemory 与 codegraph 只是辅助层。`nscholar-nuwa 是受保护知识蒸馏目录。`n所有持久改动必须留下校验和 Git 痕迹。" 20 "002FA7" $true | Out-Null

  # Slide 9
  $s = $presentation.Slides.Add(9, 12)
  Add-Box $s 0 0 960 540 "0A0A0A" "0A0A0A" 0 | Out-Null
  Add-Text $s 56 90 720 110 "Open in blue.`nClose in blue." 44 "FFFFFF" $false | Out-Null
  Add-Text $s 60 425 760 42 "研究环境的目标不是多装工具，而是让每一步都可解释、可验证、可回滚。" 20 "FFFFFF" $false | Out-Null

  $presentation.SaveAs($pptxPath)
  $presentation.Slides.Item(3).Export((Join-Path $imageRoot "00-local-environment-main-map.png"), "PNG", 2400, 1350)
  $presentation.Slides.Item(4).Export((Join-Path $imageRoot "01-research-stage-roadmap.png"), "PNG", 2400, 1350)
  $presentation.Slides.Item(5).Export((Join-Path $imageRoot "02-memory-automation-governance.png"), "PNG", 2400, 1350)
  Copy-Item -LiteralPath (Join-Path $imageRoot "00-local-environment-main-map.png") -Destination (Join-Path $assetRoot "local-environment-map.png") -Force

  Write-Output "PowerPoint visuals exported: $pptxPath"
}
finally {
  if ($presentation) { $presentation.Close() | Out-Null }
  if ($ppt) { $ppt.Quit() | Out-Null }
}
