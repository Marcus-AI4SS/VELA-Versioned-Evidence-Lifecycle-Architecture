# VELA 介绍资料与使用说明书

更新日期：2026-05-28

VELA（Versioned Evidence Lifecycle Architecture）是一套面向 Codex 的便携式研究工作流包。它把研究项目拆成可读目录、显式规则、证据台账、schema 契约、验证检查、运行日志和可演化规则，让 Codex 在清楚边界内协作，而不是依赖零散聊天记录。

VELA 不是桌面 app、论文生成器、文献管理器或后台自动化服务。它的核心是工程控制论：目标、状态、反馈、验证和校正都必须落到项目文件、检查结果和版本记录里。

![VELA 工程控制论与七层结构](./assets/overview/01-engineering-cybernetics-seven-layers.png)

## 1. VELA 解决什么问题

研究项目很容易分散在聊天、PDF、网页、Zotero、笔记、数据、脚本和草稿里。VELA 的目标不是替用户“自动做研究”，而是把研究过程变成可追溯、可验证、可回滚、可交接的文件系统。

| 问题 | VELA 的处理方式 |
| --- | --- |
| 聊天上下文丢失 | 用 `AGENTS.md`、handoff 和 `.vela/context.json` 固化任务边界 |
| 材料与证据混在一起 | `materials/` 先收集，核验后才进入 `evidence/` |
| 结论无法追溯 | `claims/` 记录主张及其证据来源 |
| 工具越开越乱 | 运行层按需连接工具，doctor 检查可用性 |
| 经验沉淀不可控 | 记忆只提供候选线索，长期规则必须检查、测试和提交 |

## 2. 工程控制论框架

VELA 把每个研究项目看成一个受控系统：

| 控制论概念 | 在 VELA 中的含义 |
| --- | --- |
| 目标 | 当前研究任务、阶段目标和预期交付物 |
| 状态 | 项目目录、证据计数、阻塞项、日志和 `.vela/context.json` |
| 反馈 | validator 输出、doctor 报告、失败日志、handoff lint 结果 |
| 验证 | schema、隐私扫描、结构检查、证据核验和测试 |
| 校正 | 修复上下文、调整路线、补齐证据、回滚错误规则 |

## 3. 七层结构

![VELA 整体架构](./assets/overview/02-vela-architecture.png)

| 层级 | 作用 | 常见文件或能力 |
| --- | --- | --- |
| 01 任务与边界 | 明确研究目标、可动范围、约束和验收标准 | `AGENTS.md`、handoff、项目说明 |
| 02 工具与接口 | 接入 Git、Python、MCP、agentmemory、CodeGraph、Zotero、Obsidian 等外部能力 | `vela doctor`、profiles、runtime receipts |
| 03 上下文与证据 | 区分材料、证据、主张、方法和交付物 | `materials/`、`evidence/`、`claims/`、`methods/` |
| 04 研究阶段 | 组织研究设计、文献、阅读、写作、图表、复盘等阶段 | workflow templates、command templates |
| 05 运行日志 | 留下操作、检查、失败和修复记录 | `logs/`、handoff render 输出 |
| 06 可靠性检查 | 判断结构、schema、证据和隐私边界是否可靠 | validators、tests、privacy scan |
| 07 环境治理 | 决定哪些规则能长期保留，哪些只能作为候选 | Git commit、evolution backlog、runtime install |

## 4. 源包与运行层

用户安装 VELA 后通常形成两层结构：

| 层 | 作用 |
| --- | --- |
| VELA 源包 | 通过 Git clone 或下载得到，包含 `package/`、`runtime/`、`schemas/`、`scripts/`、`docs/` 和 `tests/` |
| 本机运行层 | 安装到用户自己的 `~/.vela` 和 `~/.codex`，提供 CLI、skills、profiles、commands、安装回执和 doctor 检查 |

源包负责更新和审查；运行层负责在当前机器上执行。运行层可以重装，源包可以用 Git 更新。用户自己的账号、凭据、浏览器登录态、Zotero 库和私有数据不属于 VELA 包，也不会被复制进公开仓库。

## 5. 安装

| 平台 | 命令 |
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

`-BootstrapTools` 或 `--bootstrap-tools` 会尽量检查并引导安装公开依赖。某些工具仍需要用户按本机权限、网络、账号和软件来源自行确认。

## 6. 初始化一个研究项目

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

初始化后，项目会包含：

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

## 7. 证据生命周期

VELA 强制区分“材料”和“证据”：

| 阶段 | 含义 |
| --- | --- |
| `materials/` | 原始收集物：PDF、网页、截图、数据、访谈、笔记、链接 |
| `evidence/` | 已记录来源、访问时间、核验状态、权利或伦理说明的材料 |
| `claims/` | 候选主张及其证据支撑关系 |
| `deliverables/` | 报告、论文草稿、图表、复盘、提交包 |

未经核验的材料不能被当成正式证据。Codex 生成的总结、解释和建议也不能自动升级为证据。

## 8. 记忆管理与自我演化

![VELA 记忆管理与自我演化治理](./assets/overview/03-memory-evolution-governance.png)

VELA 支持把运行日志、项目交接、证据台账和工具反馈变成候选改进，但它不允许记忆直接覆盖长期规则。

| 来源 | 可用于什么 | 不能做什么 |
| --- | --- | --- |
| 运行日志 | 发现重复失败、路径漂移、工具缺失 | 不能静默改写项目证据 |
| handoff | 复用任务边界和验收标准 | 不能替用户确认新任务范围 |
| 证据台账 | 追溯材料来源和证据状态 | 不能把未核验材料变成证据 |
| agentmemory | 召回偏好、路线线索和历史经验 | 不能作为源规则 |
| CodeGraph | 辅助理解代码结构和影响范围 | 不能替代测试和源码审查 |

长期演化必须经过：

1. 召回经验。
2. 生成候选规则。
3. 运行 schema、validator 和测试。
4. 人工确认边界。
5. 版本提交。

## 9. 外部工具与可选集成

VELA 可以检查或引导接入这些工具，但不把用户私有数据打包进仓库：

| 工具 | 作用 |
| --- | --- |
| Git | 版本控制、回滚、审查和发布 |
| Python | CLI、validators、schema checks |
| ripgrep | 快速搜索、隐私扫描、路径审计 |
| MCP servers | 按需接入浏览器、学术检索、Zotero、记忆、代码索引等能力 |
| agentmemory | 运行态记忆召回 |
| CodeGraph | 项目级代码结构索引 |
| Zotero / Obsidian | 文献库和长期笔记，由用户本机管理 |

## 10. 常用命令

| 目的 | 命令 |
| --- | --- |
| 查看环境状态 | `vela doctor` |
| 初始化项目 | `vela init <project>` |
| 创建 handoff | `vela handoff new --template claim-check` |
| 检查 handoff | `vela handoff lint handoffs/H001.yaml` |
| 渲染 Codex prompt | `vela handoff render handoffs/H001.yaml --out handoffs/H001.prompt.md` |
| 验证项目 | `vela validate <project> --repair-context` |
| 隐私扫描 | `vela privacy scan <project>` |
| 安装运行层 | `vela runtime install --include core,automation,toolchain` |

## 11. 边界

- VELA 默认只生成结构、提示、契约和检查。
- VELA 不默认执行 `codex exec`。
- VELA 不接管浏览器登录态、账号、cookies、密钥、缓存或 Zotero 私有库。
- VELA 不把工具可用性说成已经安装；doctor 会区分“可用、缺失、可选、需要用户配置”。
- VELA 的记忆系统只提供候选线索；长期规则以 schema、validator、测试和 Git 提交为准。

## 12. 推荐阅读顺序

1. [快速开始](./getting-started.md)
2. [安装说明](./installation.md)
3. [工作流核心](./workflow-core.md)
4. [证据生命周期](./evidence-lifecycle.md)
5. [Handoff contract](./handoff-contract.md)
