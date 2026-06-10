<div align="center">
  <img src="./docs/assets/brand/vela-workflow-mark.png" alt="VELA 分层帆形标志" width="132">
  <h1>VELA</h1>
  <p><strong>Versioned Evidence Lifecycle Architecture</strong></p>
  <p><em>面向 Codex 研究项目的便携式工作流包</em></p>
  <p>
    <a href="./README.md">English</a>
    · <a href="https://marcus-ai4ss.github.io/VELA/">Pages</a>
    · <a href="./docs/manual.zh-CN.md">说明书</a>
    · <a href="./docs/getting-started.md">快速开始</a>
    · <a href="./docs/installation.md">安装</a>
    · <a href="./docs/faq.md">FAQ</a>
  </p>
</div>

VELA 给 Codex 一个文件化的研究工作流：项目目录、`AGENTS.md` 规则、schema 校验的交接包、证据台账、主张检查、验证报告、隐私扫描，以及机器可读的项目上下文。

当你希望 Codex 在清楚的项目边界里工作，而不是依赖零散聊天记录时，可以使用 VELA。它不是桌面 app、论文生成器、文献管理器或后台自动化服务。

VELA 的底层方法论来自工程控制论：每个研究项目都显式记录目标、状态、反馈信号、验证门和可回滚的校正循环。

可选联动：VELA 可以通过显式本地文件与 HELM 看板配合使用，但 VELA 本身不依赖 HELM。

## 四张图看懂 VELA

![VELA 工程控制论与七层结构](./docs/assets/overview/01-engineering-cybernetics-seven-layers.png)

![VELA 源包、运行层、项目与工具架构](./docs/assets/overview/02-vela-architecture.png)

![VELA 记忆管理与自我演化治理](./docs/assets/overview/03-memory-evolution-governance.png)

![VELA 使用路线图](./docs/assets/overview/04-vela-usage-roadmap.png)

## VELA 提供什么

| 层级 | 内容 |
| --- | --- |
| 项目结构 | `materials/`、`evidence/`、`claims/`、`methods/`、`deliverables/`、`handoffs/`、`logs/`、`.codex/`、`.vela/context.json` |
| Codex 指令 | 根目录和目录级 `AGENTS.md`、命令模板、有边界的 handoff prompt |
| 证据工作流 | 材料收集、证据提升、主张链接、交付物复核分开处理 |
| 治理模型 | 工程控制论式目标、状态、反馈、验证门和校正循环 |
| 验证检查 | JSON Schema、handoff lint、项目验证、隐私扫描、分享前检查 |
| 记忆与演化 | 运行日志、交接包、证据台账和工具反馈进入候选改进；长期规则必须经过验证、测试和版本提交 |
| 可选运行层 | 安装到用户自己 Codex 环境里的公开 research skills、route profiles、validators 和 `envctl` 工具 |
| 机器上下文 | `.vela/context.json` 暴露当前项目状态，供有文档约束的本地读取器使用 |

## 环境组成一览

VELA 不是单个脚本，而是一套可安装到 Codex 的研究工作流环境。

| 组成 | 说明 |
| --- | --- |
| 七层结构 | 任务与边界、工具与接口、上下文与证据、研究阶段、运行日志、可靠性检查、环境治理 |
| Skills | 总控、文献与审稿、计算社科与分析、写作与导出、图表与演示、运行时 helper、知识沉淀 |
| 插件 | 原生 Browser、Chrome、Computer Use、GitHub、Superpowers、Zotero、Scite、Google Drive、Documents、Presentations、Spreadsheets 等按任务启用 |
| MCP 与适配器 | OpenAlex、Semantic Scholar、Google Scholar、paper-search、Chrome DevTools、CodeGraph 等按路线启用；普通浏览器和电脑操作默认优先使用原生 Browser、Chrome 和 Computer Use |
| 自动化 | doctor、runtime install、validate、privacy scan、envctl route/stack/memory/evolution 检查 |
| 记忆治理 | 记忆只作为候选线索；线程级 intake、对账报告、长期规则和演化待办都必须经过 schema、validator、测试和版本提交 |

完整解释见 [公开版说明书](./docs/manual.zh-CN.md)。

## 当前运行层更新

当前公开 runtime 已加入：

- schema 校验的线程记忆 intake，让有价值经验先成为可复核候选，而不是导入完整聊天记录
- 红蓝彩虹科研图预设，用于论文图、机制图和汇报图的统一视觉约束
- 更严格的学术写作质量门，检查论点推进、方法与问题衔接、贡献表达和段落节奏
- 去重后的环境治理断言，明确记忆、CodeGraph、工具接口和源规则边界

## 快速开始

按平台选择安装方式：

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
.\vela.ps1 init ..\my-research-project --skip-codex-trust
cd ..\my-research-project
..\vela\vela.ps1 handoff new --template claim-check
..\vela\vela.ps1 handoff lint handoffs\H001.yaml
..\vela\vela.ps1 handoff render handoffs\H001.yaml --out handoffs\H001.prompt.md
..\vela\vela.ps1 validate . --repair-context
..\vela\vela.ps1 privacy scan .
```

macOS 示例：

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install-macos.sh
~/.vela/bin/vela init ../my-research-project --skip-codex-trust
```

## 环境要求

VELA 推荐安装这些公开工具：

| 组件 | 用途 |
| --- | --- |
| Git | clone 和更新 VELA |
| Python 3.13+ | 运行 CLI、validators 和 schema checks |
| PowerShell 7 / POSIX shell | 运行跨平台辅助脚本 |
| ripgrep | 快速搜索和隐私扫描 |
| Node.js / npm | 可选 JavaScript 工具 |
| GitHub CLI | 可选仓库检查 |
| CodeGraph、MCP servers、Codex plugins、Zotero、Obsidian、外部记忆服务模式 | VELA 只做检测、审查和配置提示，用户数据与凭据留在本机；默认不安装或预启动外部记忆服务 |

安装后通常有两层：

| 位置 | 作用 |
| --- | --- |
| clone 下来的 `vela/` 仓库 | 可用 Git 更新的源包 |
| `~/.vela` 和 `~/.codex` | 本机运行入口、安装回执、skills 和检查结果 |

## 核心命令

```bash
vela init <project>
vela doctor
vela handoff new --template claim-check
vela handoff lint handoffs/H001.yaml
vela handoff render handoffs/H001.yaml --out handoffs/H001.prompt.md
vela validate <project> --repair-context
vela privacy scan <project>
```

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| `package/` | `vela init` 复制到项目里的 starter files |
| `runtime/` | 可选 VELA runtime：公开 skills、profiles、validators、schemas 和辅助脚本 |
| `schemas/` | context、handoff、initializer、runtime、validation 的机器可读契约 |
| `scripts/` | VELA CLI 和产品脚本 |
| `skills/` | 轻量 VELA skill 入口 |
| `examples/` | 最小项目和 demo handoff |
| `docs/` | 公开文档和 GitHub Pages |
| `tests/` | 产品契约测试 |

## 继续阅读

- [快速开始](./docs/getting-started.md)
- [安装说明](./docs/installation.md)
- [说明书](./docs/manual.zh-CN.md)
- [工作流核心](./docs/workflow-core.md)
- [证据生命周期](./docs/evidence-lifecycle.md)
- [Handoff contract](./docs/handoff-contract.md)
