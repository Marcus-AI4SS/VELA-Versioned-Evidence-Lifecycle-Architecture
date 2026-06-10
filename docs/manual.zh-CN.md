# VELA 公开版说明书

更新日期：2026-06-10

VELA（Versioned Evidence Lifecycle Architecture）是一套面向 Codex 的便携式研究工作流环境。它把研究项目拆成清楚的目录、规则、证据、交接、检查、日志和可演化经验，让 Codex 在可审查的边界内协作。

它不是桌面 app，不是论文生成器，不是文献管理器，也不是后台自动化平台。VELA 的核心价值是：把研究工作从“聊天里临时推进”变成“文件里可追溯、可验证、可回滚、可交接”的工作流。

![VELA 工程控制论与七层结构](./assets/overview/01-engineering-cybernetics-seven-layers.png)

## 1. 先看一句话

VELA 给每个研究项目建立一个“操作系统式”的工作层：

- 用 `AGENTS.md` 和 handoff 说明任务边界。
- 用 `materials/`、`evidence/`、`claims/` 区分材料、证据和主张。
- 用 schema、validator、doctor、privacy scan 检查结构和风险。
- 用 route、profile、skill、MCP 和插件按任务类型选择工具。
- 用 logs、memory、evolution backlog 记录经验，但不让记忆直接改写长期规则。

更通俗地说，VELA 做三件事：

| 事情 | 具体含义 | 对用户的结果 |
| --- | --- | --- |
| 建项目秩序 | 给研究项目生成固定目录、Codex 指令、交接模板和机器可读状态 | 换一次对话、换一个协作者，也能看懂项目在哪里、做到哪一步、哪些材料可信 |
| 管工具边界 | 把 skill、插件、MCP、本地命令放进路线表和质量门 | Codex 不会因为“能调用工具”就随意开工具、改文件或跳过检查 |
| 沉淀经验 | 把日志、失败原因、修复动作和稳定做法变成可审查候选 | 环境可以演化，但长期规则必须经过验证和提交 |

VELA 的公开版尽量提供一套完整的本机研究工作流环境：研究路线、skills、MCP/profile 模板、插件协作方式、schemas、validators、tests、envctl、记忆治理和项目文件夹规则都在里面。它不会包含任何用户私有数据库、账号状态、浏览器登录态、cookies、密钥、缓存，也不会包含与公开研究工作流无关的个人定制模块。

## 2. VELA 解决什么问题

| 常见问题 | VELA 怎么处理 |
| --- | --- |
| 研究材料散在聊天、PDF、网页、笔记、代码和草稿里 | 建立固定项目结构，把材料、证据、主张、方法、交付物分开 |
| Codex 每次都要重新解释上下文 | 用 `AGENTS.md`、handoff 和 `.vela/context.json` 保存可读上下文 |
| AI 总结被误当成证据 | 只有完成来源、访问时间、核验状态和支持关系的材料才能进入 `evidence/` |
| 工具越接越多，边界不清 | 用 route/profile 决定什么时候使用哪些 skill、插件和 MCP |
| 经验沉淀靠记忆，容易越界 | 记忆只作为候选线索；长期规则必须经过检查、测试和版本提交 |
| 项目要交给别人或下次继续 | 通过 handoff、logs、schema 和 `.vela/context.json` 留下交接状态 |

VELA 面向的是“研究过程需要长期组织”的场景：文献综述、论文写作、量化分析、文本分析、网络分析、ABM 仿真、研究图表、PPT 汇报、审稿回复、复现包、项目复盘。它不追求把所有任务变成一个按钮，而是把每一步的输入、输出、工具和检查条件写清楚。

## 3. 底层逻辑：工程控制论

VELA 的骨架来自工程控制论。通俗说，就是把一个研究项目当成一个需要持续校正的系统：先定目标，再观察状态，收集反馈，通过验证门，最后做小步校正。

| 控制论概念 | 在 VELA 里是什么意思 | 你会看到什么 |
| --- | --- | --- |
| 目标 | 这次研究任务到底要完成什么 | research question、阶段目标、交付物说明、handoff task |
| 边界 | 哪些目录、材料、工具可以动，哪些不能动 | `AGENTS.md`、handoff constraints、privacy boundaries |
| 状态 | 项目当前处于什么阶段，有哪些材料、证据、阻塞和交付物 | `.vela/context.json`、logs、counts、validator report |
| 反馈 | 执行后产生的可检查信号 | doctor 结果、schema error、lint error、测试结果、引用核验结果 |
| 控制器 | 决定走哪条路线、用哪些工具、何时停下检查 | routing table、profiles、quality gates、envctl validators |
| 执行器 | 真正做事的技能、脚本、插件、MCP 和本地工具 | skills、MCP servers、Codex plugins、Python/Git/rg 等 |
| 扰动 | 可能让项目跑偏的因素 | 登录态、网络、权限、路径变动、工具缺失、未经核验的资料 |
| 稳定性 | 项目能否越做越清楚、越做越可交接 | Git 提交、测试通过、日志完整、证据链可复核 |

VELA 的规则很硬：反馈不足，不进入下一步；证据不足，不升级为结论；验证不通过，不沉淀为长期规则。

这个骨架对应到实际操作，就是一个闭环：

1. 先写清任务：研究问题、材料边界、交付物、不能碰的文件。
2. 再选择路线：文献、全文、写作、量化、文本、网络、图表、投稿、复盘或环境治理。
3. 再打开工具：只启用当前路线需要的 skill、插件、MCP 和本地命令。
4. 执行后留下状态：日志、handoff、证据台账、validator 报告、隐私扫描报告。
5. 检查是否过关：schema、引用、证据、路径、权限、文件结构、复现性。
6. 最后做小步修正：通过的规则进入提交；不稳定经验只进入候选，不直接变成全局规则。

## 4. 总体结构

![VELA 整体架构](./assets/overview/02-vela-architecture.png)

VELA 分成五块。用户可以只用最小项目结构，也可以安装完整运行层。

| 模块 | 通俗解释 | 主要内容 |
| --- | --- | --- |
| VELA 源包 | 你从 GitHub 下载或 clone 的 VELA 仓库 | `package/`、`runtime/`、`schemas/`、`scripts/`、`docs/`、`tests/` |
| 本机运行层 | 安装到你自己 Codex 环境里的运行入口 | `~/.vela`、`~/.codex/skills`、CLI、profiles、commands、安装回执 |
| 项目工作层 | 每个研究项目自己的文件结构 | `materials/`、`evidence/`、`claims/`、`methods/`、`deliverables/`、`handoffs/`、`logs/` |
| 工具接口层 | 按任务需要连接外部工具 | Git、Python、ripgrep、MCP servers、Codex plugins、Zotero、Obsidian |
| 记忆与演化层 | 保存经验，但必须经过治理 | logs、本地记忆候选、本地记忆状态报告、CodeGraph 索引、evolution backlog、validators |

安装后通常形成“两层”：

| 层 | 作用 | 能不能删除重装 |
| --- | --- | --- |
| VELA 源包 | 可用 Git 更新的公开工作流包 | 可以重新 clone |
| 本机运行层 | 安装到用户自己的 `~/.vela` 和 `~/.codex` | 可以重装，但不应混入私有凭据 |

VELA 不复制你的浏览器登录态、cookies、账号、密钥、Zotero 私有库、Obsidian 私有库或本机缓存。它只提供公开工作流、契约、检查器和安装引导。

实际使用时会形成三层：

| 层 | Windows 常见位置 | macOS / Linux 常见位置 | 说明 |
| --- | --- | --- | --- |
| 源包 | 用户自己 clone 的 `vela/` 目录 | 用户自己 clone 的 `vela/` 目录 | 用 Git 更新，适合提交 issue、查看源码、阅读 docs |
| 运行层 | `%USERPROFILE%\.vela`、`%USERPROFILE%\.codex` | `~/.vela`、`~/.codex` | 安装 CLI、skills、profiles、commands、安装回执和 doctor 结果 |
| 项目层 | 任意研究项目目录 | 任意研究项目目录 | `vela init` 生成项目结构和 `.vela/context.json` |

这意味着其他用户下载 VELA 后，也会拥有“源包 + 本机运行层 + 自己的研究项目层”。源包负责更新，运行层负责让 Codex 能调用，项目层负责保存用户自己的材料和交付物。macOS 用户不会获得 Windows 路径；安装脚本会使用 `~/.vela`、`~/.codex`、POSIX shell 和 macOS 可用的工具检测方式。

公开版包含的内容：

| 包含 | 不包含 |
| --- | --- |
| 研究路线、公开 skills、schemas、validators、tests、envctl、runtime manifest、profile 模板、MCP 启用策略、插件协作说明 | 浏览器登录态、cookies、账号、密钥、验证码状态、本地 Zotero/Obsidian 数据库、个人记忆数据、非公开个人定制模块 |

## 5. 七层结构

七层结构是 VELA 日常工作的骨架。它把“我要做什么、用什么工具、依据什么材料、处于哪个阶段、留下什么记录、怎么检查、哪些规则能长期保留”拆开。

| 层级 | 一句话解释 | 典型内容 | 主要检查 |
| --- | --- | --- | --- |
| 01 任务与边界 | 先确定任务目标和可动范围 | `AGENTS.md`、handoff、constraints、expected output | 任务是否过宽、是否缺少验收标准 |
| 02 工具与接口 | 决定是否需要外部工具 | Git、Python、rg、MCP、插件、Zotero、Obsidian | 工具是否可用、是否需要登录或权限 |
| 03 上下文与证据 | 明确当前判断依据 | materials、evidence、claims、methods、source notes | 材料是否完成核验，证据是否能支撑主张 |
| 04 研究阶段 | 判断项目处于哪一步 | 研究设计、文献、全文、分析、写作、图表、投稿、复盘 | 是否跳过了必要阶段 |
| 05 运行日志 | 留下执行痕迹 | logs、handoff render、doctor report、validation report | 是否能复盘失败原因 |
| 06 可靠性检查 | 用规则检查项目是否可信 | schema、validator、privacy scan、tests、quality gates | 是否有结构、隐私、引用或证据风险 |
| 07 环境治理 | 决定哪些经验能长期留下 | routing table、profiles、memory policy、evolution backlog、Git commit | 是否通过检查、测试和人工确认 |

七层结构不是为了复杂化，而是为了避免三类混乱：

- 把原始材料当成证据。
- 把一次性经验写成永久规则。
- 把工具连接误认为研究结论。

七层之间的关系可以这样理解：

| 上一层问的问题 | 下一层负责回答 |
| --- | --- |
| 任务到底是什么？ | 任务与边界层写清目标、范围和验收标准 |
| 需要哪些工具？ | 工具与接口层决定是否打开插件、MCP 或本地命令 |
| 凭什么判断？ | 上下文与证据层区分材料、证据、主张和方法 |
| 做到哪一步？ | 研究阶段层记录当前在设计、检索、分析、写作、投稿还是复盘 |
| 留下什么痕迹？ | 运行日志层记录 handoff、doctor、validator、失败和修复 |
| 结果可靠吗？ | 可靠性检查层运行 schema、测试、隐私扫描、引用核验和质量门 |
| 经验能不能留下？ | 环境治理层决定是否进入长期规则、profile、skill 或文档 |

这也是 VELA 与“临时 prompt 模板”的主要区别：prompt 只描述本轮怎么说，VELA 还要描述项目在哪里、证据在哪里、工具如何开、结果如何查、错误如何回滚、经验如何沉淀。

## 6. 安装方式

| 平台 | 入口 |
| --- | --- |
| Windows | `.\install.ps1 -BootstrapTools` |
| macOS | `sh ./install-macos.sh` |
| Linux / shell | `sh ./install.sh --bootstrap-tools` |

Windows 示例：

```powershell
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
.\install.ps1 -BootstrapTools
.\vela.ps1 doctor
```

macOS 示例：

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install-macos.sh
~/.vela/bin/vela doctor
```

`BootstrapTools` 会尽量检查并引导公开依赖。它不会静默复制账号、登录态、浏览器数据或私有资料。不同系统上，部分工具仍需要用户按本机权限自行安装或授权。

### Windows 与 macOS 的差异

| 项目 | Windows | macOS / Linux |
| --- | --- | --- |
| 安装入口 | `install.ps1`、`vela.ps1` | `install-macos.sh` 或 `install.sh`、`~/.vela/bin/vela` |
| 运行层位置 | `%USERPROFILE%\.vela`、`%USERPROFILE%\.codex` | `~/.vela`、`~/.codex` |
| Shell | PowerShell 7 优先 | zsh/bash |
| 工具安装 | 可提示 winget / 手动安装 | 可提示 Homebrew / 手动安装 |
| 权限模型 | 注意 PowerShell 执行策略、路径空格、Windows Defender | 注意 Gatekeeper、可执行权限、Homebrew 路径 |
| 路径写法 | `\` 和盘符路径 | `/` 和 home 路径 |

VELA 的目标不是把所有依赖强行装满，而是先给出清楚的检查结果：哪些是核心依赖，哪些是推荐依赖，哪些是可选集成，哪些需要用户自己授权。

## 7. 环境要求

| 组件 | VELA 中的作用 | 状态说明 |
| --- | --- | --- |
| Git | clone、更新、回滚、提交、发布 | 推荐安装 |
| Python 3.13+ | 运行 CLI、schema checks、validators | 核心依赖 |
| PowerShell 7 / POSIX shell | 运行跨平台安装脚本 | Windows/macOS/Linux 分开处理 |
| ripgrep (`rg`) | 快速搜索、路径审计、隐私扫描 | 推荐安装 |
| Node.js / npm | 部分插件、MCP 或展示工具可能需要 | 可选 |
| GitHub CLI | 仓库协作、发布和 CI 检查 | 可选 |
| Zotero / Obsidian | 文献库和长期笔记 | 用户自有工具，VELA 不复制数据库 |
| MCP servers | 学术检索、浏览器调试、社交证据和代码索引等接口 | 按任务启用 |
| Codex plugins | GitHub、Superpowers、文档、表格、演示等增强层 | 按任务启用 |

依赖分成三类：

| 类型 | 代表项 | 处理方式 |
| --- | --- | --- |
| 核心依赖 | Git、Python、shell、VELA CLI、schemas、validators | 安装脚本和 `vela doctor` 会重点检查 |
| 推荐依赖 | ripgrep、GitHub CLI、Node.js、PowerShell 7、Homebrew/winget | 缺失时提示，不伪装成已安装 |
| 可选集成 | Zotero、Obsidian、MCP servers、Codex plugins、外部记忆服务模式、CodeGraph | 只提供 profile、doctor 检查、adoption review 和使用说明；外部记忆服务默认不安装、不常驻 |

## 8. 初始化研究项目

![VELA 使用路线图](./assets/overview/04-vela-usage-roadmap.png)

```bash
vela init my-research-project --skip-codex-trust
cd my-research-project
vela handoff new --template claim-check
vela handoff lint handoffs/H001.yaml
vela handoff render handoffs/H001.yaml --out handoffs/H001.prompt.md
vela validate . --repair-context
vela privacy scan .
```

初始化后，一个典型项目会包含：

```text
my-research-project/
  AGENTS.md
  materials/
  evidence/
  claims/
  methods/
  deliverables/
  handoffs/
  logs/
  .codex/
  .vela/context.json
```

| 目录 | 用途 |
| --- | --- |
| `materials/` | 原始材料：PDF、网页、截图、数据、访谈、链接、笔记 |
| `evidence/` | 已核验材料：有来源、访问时间、状态、权利或伦理说明 |
| `claims/` | 候选主张、已支持主张、证据支持关系 |
| `methods/` | 方法假设、编码规则、分析计划、复现说明 |
| `deliverables/` | 报告、论文、图表、PPT、提交包、复盘 |
| `handoffs/` | 给 Codex 或协作者的有边界任务说明 |
| `logs/` | 运行记录、质量门、doctor、validation、修复记录 |
| `.vela/context.json` | 当前项目状态的机器可读摘要 |

## 9. 工作流入口

以后使用 VELA 时，不要先看一堆 skill 名称。先看“任务路线”。一条路线可以组合多个 skill、插件和 MCP；它们不是重复，而是分工不同。

路线的执行顺序通常是：

```text
用户任务 -> route 判断 -> skill 组合 -> 插件/MCP 按需开启 -> schema/validator 检查 -> logs/handoff/context 更新
```

所以同一个任务里可能同时出现 `citation-verifier`、`zotero-sync`、`openalex-mcp` 和 `writing-reference-capture`。它们不是四套互相替代的系统，而是分别负责“引用核验、文献库同步、开放学术检索、写作引用捕获”。

| 你要做什么 | 路线 | 主要能力 | 工具接口 | 边界 |
| --- | --- | --- | --- | --- |
| 不确定该走哪条研究路线 | `general-research` | 研究设计、引用核验、基础导出 | 可选浏览器、Zotero、OpenAlex、Semantic Scholar、本地记忆状态 | 用于初始分流，不替代具体路线 |
| 检查 VELA、skills、profiles、MCP、插件和配置 | `stack-governance` | `vela-runtime-manager`、`skill-vetter` | GitHub、Superpowers、本地记忆状态、CodeGraph 可选 | 管环境，不管具体研究结论 |
| 安装、修复、更新运行层 | `environment-ops` | runtime 检查、profile 应用、配置漂移检查 | 可选浏览器、Zotero、OpenAlex、本地记忆状态、CodeGraph | 不静默改用户级配置 |
| 清理项目文件夹 | `project-folder-hygiene` | 文件盘点、临时文件分类、交接前整理 | 一般不需要 MCP | 不静默删除原始材料、数据、PDF、证据 |
| 项目复盘和经验沉淀 | `project-retrospective` | 复盘、经验候选、演化待办 | 本地记忆状态、浏览器、文献工具可选 | 复盘不是自动改规则 |
| 长时间实验或后台任务 | `long-running-experiment-ops` | 进程、日志、断点、失败恢复 | 可选浏览器看仪表盘 | 以本地日志和检查点为准 |
| 文献证据总控 | `evidence-based-literature-workflow` | 结构性阅读、证据核验、引用支撑 | Zotero、OpenAlex、Semantic Scholar；浏览器/Scholar/paper-search 可选 | 发现文献不等于正式引用 |
| 文献综述和研究版图 | `literature-review` | 主题检索、引用扩展、综述表 | Zotero、OpenAlex、Semantic Scholar；Google Scholar 可选 | 综述写作前仍需引用核验 |
| 全文获取 | `reference-fulltext-acquisition` | DOI/OA 查询、PDF 获取、缺失清单 | OpenAlex、Semantic Scholar；浏览器、Zotero、Scholar 可选 | 只处理合法可访问全文 |
| 单篇论文评审 | `single-paper-review` | 贡献、方法、证据、写作问题评估 | Zotero、OpenAlex、Semantic Scholar | 不能用未核验文献做正式引用 |
| 量化实证 | `empirical-quant` | 研究设计、模型、稳健性、图表 | 文献 MCP 可选 | 结果进入正文前仍需证据链 |
| 文本与语料分析 | `text-corpus` | 语料清洗、编码、词典、主题、嵌入 | Hugging Face 可选，文献 MCP 可选 | 数据来源和伦理边界必须记录 |
| 网络分析 | `network-analysis` | 节点、边、中心性、社群、扩散 | 文献 MCP 可选 | 节点边定义必须留痕 |
| 计算社会科学综合项目 | `computational-social-science` | 研究设计、数据发现、文本、网络、图表、复现 | Hugging Face、文献 MCP 可选 | 工具只是执行器，复现包才是交付依据 |
| 科研图和结果表 | `research-figure-design` | 机制图、概念图、数据图、回归表 | 默认不需要 MCP | 不能编造数据或统计标注 |
| 研究汇报和 PPT | `research-presentation` | PPT、网页演示、图表整合 | Presentations 插件、HTML PPT 工具 | 演示不替代证据核验 |
| 正文写作和导出 | `writing-export` | 写作、引用捕获、审稿回复、DOCX/LaTeX | Zotero、OpenAlex、Semantic Scholar | 写作质量检查不能改变事实 |
| 投稿包和复现包 | `social-science-submission-package` | 版本冻结、图文一致性、复现材料、回应矩阵 | 文献 MCP | 交付前必须冻结版本和证据 |
| 平台材料和数字痕迹案例 | `social-platform-case` | 浏览器可见材料、来源台账、平台伦理 | `chrome-devtools`，文献工具可选 | VELA 不打包需要平台账号和登录态的专用后端 |

## 10. Skills 层

VELA runtime 当前公开研究包里包含 42 个 active skills，分为七类。

| 类别 | 代表 skills | 用途 |
| --- | --- | --- |
| 总控 | `research-autopilot`、`research-team-orchestrator`、`vela-runtime-manager`、`project-retrospective-evolver` | 路由、分工、环境治理、复盘 |
| 文献与审稿 | `citation-verifier`、`evidence-based-literature-workflow`、`reference-fulltext-acquisition`、`zotero-sync`、`academic-paper-review` | 文献发现、全文获取、引用核验、结构性评审 |
| 计算社科与分析 | `quant-analysis`、`text-analysis`、`network-analysis`、`dataset-discovery`、`reproducibility-package` | 数据、模型、文本、网络、复现 |
| 写作与导出 | `manuscript-writing-studio`、`writing-reference-capture`、`reviewer-response-pack`、`research-docx-export`、`latex-paper-conversion` | 写作、引用捕获、审稿回复、文档导出 |
| 图表与演示 | `research-figure-studio`、`figure-table-studio`、`research-presentation-studio`、`guizang-ppt-skill` | 科研图、结果表、PPT、网页演示 |
| 运行时 helper | `project-folder-hygiene`、`skill-vetter`、`local-cloud-router`、`agent-browser`、`playwright` | 文件整理、外部能力审查、本地/云端判断、浏览器操作 |
| 知识沉淀与平台材料 | `obsidian-research-sync`、`social-platform-reader` | 长期笔记、浏览器可见平台材料证据化 |

已经 retired 的旧入口不会作为公开主入口推荐。VELA 也不把非公开个人定制模块作为公开研究工作流的一部分。

### Skills 的四种角色

| 角色 | 说明 | 例子 |
| --- | --- | --- |
| 入口 | 接收用户任务，判断任务路线 | `research-autopilot` |
| 主控 | 组织多步流程、分配子任务、决定检查点 | `evidence-based-literature-workflow`、`social-science-submission-packager`、`research-team-orchestrator`、`vela-runtime-manager` |
| 执行 | 完成具体研究动作 | `citation-verifier`、`quant-analysis`、`text-analysis`、`research-figure-studio`、`manuscript-writing-studio` |
| helper | 支持定位、清理、浏览器操作、运行环境判断 | `project-folder-hygiene`、`skill-vetter`、`local-cloud-router`、`playwright` |

使用原则：

- 先由入口和路线表判断任务类型。
- 再由主控 skill 拆任务、列边界、指定检查点。
- 执行 skill 只做自己负责的动作，不跨界改项目结论。
- helper skill 只提供辅助，不把辅助结果直接当作研究证据。

## 11. 插件层

插件是 Codex 或相关运行环境提供的能力包。它们可以增强工作流，但不能替代 VELA 的源规则、schema、validator 和 Git 提交。

| 插件 | 公开定位 | 使用边界 |
| --- | --- | --- |
| `research-autopilot` | VELA 的研究路由插件层，承载主 skill、profile 和路线表 | 负责分流和协调，不替代具体证据核验 |
| `github` | GitHub 仓库、issue、PR、CI、发布协作 | 管代码和发布，不判断研究事实 |
| `superpowers` | 规划、调试、TDD、代码评审、分支收尾方法 | 工程治理增强层，不接管研究路线 |
| `hugging-face` | 模型、数据集、推理/训练模板增强 | 适合计算社科和文本/多模态任务，按需使用 |
| `scite` | 引用语境和支持/争议关系线索 | 只作发现增强，不替代正式引用核验 |
| `google-drive` | 外部协作文档和文件访问 | 需用户授权，不能成为证据源本身 |
| `documents` | DOCX 创建、编辑、渲染、核验 | 交付格式层，不替代写作和引用检查 |
| `presentations` | PPTX 创建、编辑、渲染、导出 | 演示交付层，不承担研究发现 |
| `spreadsheets` | 表格文件创建、编辑、分析、可视化 | 表格工件层，正式分析仍走研究路线 |
| `hyperframes` | 视频、动画、网页转视频 | 展示增强层，按需使用 |
| `browser` | Codex 原生浏览器交互层 | 普通网页、本地页面、截图、可视检查的第一入口 |
| `chrome` | 用户真实 Chrome 会话 | 需要登录态、扩展、下载目录或已有标签页时优先使用 |
| `computer-use` | 本机桌面应用操作 | 文件对话框、Office/浏览器窗口和系统级可视检查优先使用 |
| `obsidian-sidecar` | 长期研究笔记侧车 | 只沉淀笔记，不替代源规则 |

候选或非默认插件不会被写成“已安装”。涉及账号授权、云端权限或本机客户端的插件，都由用户自行启用。

插件在 VELA 里有三个边界：

1. 插件提供能力，不提供事实结论。例如 Scite 可以给出引用语境线索，但正式引用仍要走 `citation-verifier`。
2. 插件可用性必须检查。不能因为文档里写了某插件，就默认用户本机已经安装或授权。
3. 插件输出要进入项目结构。真正可交接的是 evidence、logs、handoffs、deliverables，而不是某次插件调用的临时结果。

## 12. MCP 工具接口

MCP 是把外部系统接进 Codex 的工具接口。VELA 的原则是：默认不预启动全部 MCP，只在任务需要时打开。普通浏览器和电脑操作优先使用 Codex 原生 Browser、Chrome 和 Computer Use；MCP/CLI 浏览器工具只作为调试、复现和专项采集后备。

| 接口 | 用途 | 什么时候用 |
| --- | --- | --- |
| `official Zotero plugin` | 文献条目、附件、笔记、标签、收藏夹 | 正式引用、文献入库、附件同步；它不是默认 MCP |
| `openalex-mcp` | 开放学术元数据、作者、机构、主题、引用网络 | 文献发现、综述、引用核验 |
| `semantic-scholar-mcp` | 相关论文、引用关系、语义线索 | 文献发现、引文追踪 |
| `google-scholar-mcp` | Google Scholar 检索链 | 单篇查找、右侧 PDF、引用扩展 |
| `paper-search-mcp` | 聚合论文搜索 | 补充发现，不替代正式核验 |
| `chrome-devtools` | DevTools 日志、网络、调试视角 | 原生 Browser/Chrome 不能满足调试需求时使用 |
| `external memory service pattern` | 外部记忆服务的接口思路和审查对象 | 只作 watch-only / pattern-only 线索；默认不安装、不常驻、不自动写规则 |
| `codegraph` | 项目代码结构索引 | 需要代码关系和影响范围时按项目初始化 |

重要边界：

- MCP 是传感器和执行接口，不是事实源。
- 浏览器可见内容只是材料，进入证据层前仍要记录来源、访问时间、权利和伦理说明。
- VELA 不打包需要平台账号和登录态的专用后端。
- 外部记忆服务和 CodeGraph 不能替代 schema、validator、源码审查和 Git 历史。

VELA 对 MCP 采用“启动安全”策略：

| 策略 | 含义 |
| --- | --- |
| 原生优先 | Browser、Chrome、Computer Use 先处理普通网页、登录态浏览器和本机可视操作 |
| 默认不全开 | 新任务不会预启动所有 stdio MCP，避免慢启动、资源占用和无关工具污染 |
| 按路线开启 | 文献任务优先学术检索和官方 Zotero 插件；网页材料先用原生浏览器；代码审查才用 CodeGraph |
| 先说明再调用 | 工具调用前应知道它解决什么问题、读取什么数据、会不会写文件 |
| 输出要落地 | 有价值的结果应进入 materials、evidence、logs 或 handoff，而不是留在临时聊天里 |
| 账号相关后端不随包发布 | 涉及平台账号、登录态或私有缓存的后端不会打进公开 VELA |

## 13. 记忆管理

![VELA 记忆管理与自我演化治理](./assets/overview/03-memory-evolution-governance.png)

VELA 的记忆管理不是“把所有聊天都永久存起来”。它的目标是让系统记住稳定偏好、常见路线、失败原因和项目经验，同时防止临时判断变成全局规则。

| 记忆层 | 存什么 | 默认去向 | 能否自动升级为长期规则 |
| --- | --- | --- | --- |
| 临时会话记忆 | 本轮任务路径、失败命令、网页状态、短期上下文 | 过期丢弃 | 不能 |
| 项目记忆 | 项目事实、阶段、材料边界、证据链 | 项目文件或长期笔记 | 不能 |
| 私有偏好 | 用户协作偏好、语言偏好、入口提示 | 用户本机记忆 | 不能 |
| 流程记忆 | 可复用流程、工具顺序、质量清单 | skill 或文档候选 | 必须检查 |
| 控制记忆 | 会影响总路由、权限、验证逻辑的底层规则 | control kernel 候选 | 必须严格检查 |
| 噪声 | 一次性聊天、无证据断言、过时路径、泄密风险项 | 丢弃 | 不能 |

记忆进入长期规则前，要走候选管线：

1. 捕获：记录一个可能有用的经验。
2. 规范化：去掉私有路径、账号、密钥、临时噪声。
3. 评分：看它是否重复出现、是否有证据、是否低风险。
4. 路由：决定进入项目复盘、skill 候选、schema 候选还是丢弃。
5. 复核或提升：需要用户确认、validator 和测试。
6. 衰减或遗忘：过时、低置信或冲突记忆要删除或降级。
7. 校正：如果旧规则造成错误，进入 evolution backlog 修正。

硬边界：

- 不默认导入完整聊天记录。
- 不默认做 LLM 压缩和自动上下文注入。
- 不把 secrets、tokens、cookies、账号细节或验证码状态写入记忆。
- 不让外部记忆服务成为源规则。
- 不让 CodeGraph 索引成为事实依据。

VELA 中“记忆”的四个落点：

| 落点 | 保存什么 | 适合什么时候看 |
| --- | --- | --- |
| 项目文件 | 当前项目事实、证据、阶段、方法、交付物 | 继续项目、交接项目、复盘项目 |
| 运行日志 | 命令、检查、失败、修复、handoff、validator 报告 | 排错、回滚、审计 |
| 本地记忆状态报告 | 用户确认过的偏好、常见路径、重复经验候选 | 新会话只获得可审计线索，不自动改规则 |
| 线程记忆 intake 报告 | 已完成任务里的有限经验、风险评分和建议去向 | 不导入完整聊天记录，也能形成可复核演化候选 |
| 演化待办 | 候选规则、候选 skill、候选 schema、候选自动化 | 周期性治理和版本提交 |

线程记忆 intake 的范围很窄。一个任务结束后，可以留下结构化报告：简短摘要、证据指针、可复用步骤、风险说明和建议落点。报告必须通过 `thread_memory_intake_report.v1` schema 校验；只有经过复核，才允许进入 evolution backlog。它不复制完整对话、凭据、浏览器状态或私有项目文件。

这套设计避免“记住得越多越好”的误区。研究环境真正需要的是：能解释来源、能检查风险、能回滚错误、能沉淀稳定经验。

## 14. 自动化与自我演化

VELA 的自动化不是“无人值守地改环境”。它更像巡检和对账系统：发现问题、写报告、生成候选改进，然后通过检查和提交进入长期规则。

| 自动化/命令 | 用途 | 边界 |
| --- | --- | --- |
| `vela doctor` | 检查本机工具、运行层和可选集成状态 | 只检查和提示，不冒充安装成功 |
| `vela runtime install` | 安装或更新 VELA 运行层 | 不复制用户私有数据 |
| `vela validate` | 检查项目结构、schema、context 和质量门 | 不自动替用户做研究判断 |
| `vela privacy scan` | 查找隐私、路径、账号、密钥、缓存等风险 | 发现风险后由用户确认处理 |
| `python -m skills.scripts.envctl route explain` | 解释任务应该走哪条路线 | 只给路线建议，不替代用户确认 |
| `python -m skills.scripts.envctl validate stack` | 检查技能、插件、MCP、配置一致性 | 不静默改用户配置 |
| `python -m skills.scripts.envctl validate environment-layers` | 检查七层结构是否一致 | 用于环境治理和发布前检查 |
| `python -m skills.scripts.envctl validate memory` | 检查记忆系统边界 | 记忆问题不能直接改源规则 |
| `python -m skills.scripts.envctl memory reconcile` | 对账记忆、规则和运行态状态 | 候选记忆必须经过复核 |
| `python -m skills.scripts.envctl evolution` | 管理演化候选 | 中高风险改动不能自动落地 |
| `python -m skills.scripts.envctl apply-profile` | 应用或预览 profile 配置 | 应先 dry-run、diff、backup |

允许自动做的低风险动作：

- 写入被忽略的状态报告。
- 追加去重后的演化候选。
- 生成本机健康摘要。
- 运行 validators 和 tests。
- 在通过检查后提交明确、低风险、可回滚的改动。

禁止默认自动做的动作：

- 安装外部依赖。
- 修改用户级 Codex 配置。
- 写 runtime skill cache 或 plugin cache。
- 导入完整聊天记录。
- 启动未经审查的持久向量数据库。
- 自动提升中高风险规则。
- 把外部记忆服务数据写入 VELA 源仓。
- 开启 LLM 压缩、自动上下文注入或无边界 prompt injection。

自动化的日常工作可以分成三类：

| 类型 | 目的 | 输出 |
| --- | --- | --- |
| 环境巡检 | 查工具缺口、profile 漂移、MCP 状态、schema 变化、运行层安装状态 | doctor report、stack validation report |
| 项目巡检 | 查目录结构、证据链、handoff、隐私风险、交付物完整性 | validation report、privacy report、context repair |
| 演化巡检 | 查哪些经验可复用，哪些规则冲突，哪些旧入口应 retired | evolution backlog、route conflict report、candidate patch |

低风险自动化可以帮助用户省时间，但 VELA 的默认立场是保守的：凡是会改变用户环境、启动外部服务、写用户配置、移动私有文件、提升长期规则的动作，都应先给出差异和理由。

## 15. 证据生命周期

VELA 最关键的学术边界是：材料不是证据，AI 总结也不是证据。

| 阶段 | 含义 | 是否能支持正式主张 |
| --- | --- | --- |
| 材料 | PDF、网页、截图、数据、访谈、笔记、链接 | 不能直接支持 |
| 候选证据 | 有来源线索，但核验字段不完整 | 只能作为待核验线索 |
| 已核验证据 | 记录来源、访问时间、状态、权利/伦理说明、支持关系 | 可以支持具体主张 |
| 主张 | 对现象、机制、方法或结果的陈述 | 必须链接证据 |
| 交付物 | 报告、论文、图表、PPT、提交包 | 必须能追溯到证据和方法 |

正式引用必须遵守更严格规则：作者、年份、标题、期刊/会议/出版源、DOI 或可验证替代证据。完整 PDF、用户提供来源或公开学术检索记录可以作为 DOI 缺失时的替代核验证据。

## 16. 文件整理规则

VELA 的项目整理遵循“先分类，再处理”的原则。

| 类型 | 例子 | 默认处理 |
| --- | --- | --- |
| 必须保留 | 原始数据、PDF、截图证据、用户提供材料、证据台账、方法脚本 | 不静默删除 |
| 可归档 | 旧草稿、历史导出、过期截图、旧版本报告 | 归入 archive 或 logs |
| 可再生成 | build 输出、缓存、临时转换文件 | 可清理，但先确认 |
| 风险项 | secrets、cookies、账号文件、私有路径、浏览器缓存 | 不提交，进入隐私扫描 |
| 死文件候选 | 无引用、无来源、无用临时残留 | 清理前列出报告 |

## 17. 常用命令

| 目的 | 命令 |
| --- | --- |
| 查看 VELA CLI | `vela --help` |
| 检查环境 | `vela doctor` |
| 初始化项目 | `vela init <project>` |
| 创建 handoff | `vela handoff new --template claim-check` |
| 检查 handoff | `vela handoff lint handoffs/H001.yaml` |
| 渲染 Codex prompt | `vela handoff render handoffs/H001.yaml --out handoffs/H001.prompt.md` |
| 修复项目 context | `vela validate <project> --repair-context` |
| 隐私扫描 | `vela privacy scan <project>` |
| 安装运行层 | `vela runtime install --include core,automation,toolchain` |
| 解释路线 | `python -m skills.scripts.envctl route explain "你的任务" --summary` |
| 启动摘要 | `python -m skills.scripts.envctl route startup-summary --route-id writing-export --summary` |
| 冲突检查 | `python -m skills.scripts.envctl validate conflicts --summary` |
| 七层检查 | `python -m skills.scripts.envctl validate environment-layers --summary` |
| 记忆对账 | `python -m skills.scripts.envctl memory reconcile --summary` |

## 18. 最小使用路径

第一次使用时，不需要理解所有细节。按这个顺序走：

1. clone 或下载 VELA。
2. 按系统运行安装脚本。
3. 运行 `vela doctor` 看工具缺口。
4. 用 `vela init <project>` 初始化研究项目。
5. 把原始材料放入 `materials/`。
6. 完成核验后，把材料提升到 `evidence/`。
7. 用 `vela handoff new` 给 Codex 准备小任务。
8. 用 `vela validate` 和 `vela privacy scan` 检查。
9. 把稳定交付物放入 `deliverables/`，把过程放入 `logs/`。
10. 复盘可复用经验，但先进入候选，不直接改长期规则。

如果只想快速试用，可以只做四步：

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install-macos.sh    # macOS/Linux；Windows 使用 .\install.ps1 -BootstrapTools
vela init ../my-research-project --skip-codex-trust
```

如果要接近完整运行体验，再继续：

```bash
vela doctor
vela runtime install --include core,automation,toolchain
python -m skills.scripts.envctl validate stack --summary
python -m skills.scripts.envctl validate environment-layers --summary
```

## 19. VELA 不做什么

- 不替用户判断研究结论是否成立。
- 不把未核验材料升级为证据。
- 不默认执行 `codex exec`。
- 不接管用户浏览器、Zotero、Obsidian 或本机账号。
- 不复制 cookies、tokens、密钥、验证码状态、浏览器缓存。
- 不默认安装或启动所有 MCP。
- 不把外部记忆服务、CodeGraph、插件缓存当成源规则。
- 不把非公开个人定制模块作为公开研究工作流的一部分。

## 20. 推荐阅读顺序

1. [快速开始](./getting-started.md)
2. [安装说明](./installation.md)
3. [工作流核心](./workflow-core.md)
4. [证据生命周期](./evidence-lifecycle.md)
5. [Handoff contract](./handoff-contract.md)
6. [可选集成](./integrations.md)
