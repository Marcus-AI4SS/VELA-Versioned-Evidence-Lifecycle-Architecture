<div align="center">
  <img src="./docs/assets/brand/vela-workflow-mark.png" alt="VELA 分层帆形标志" width="132">
  <h1>VELA</h1>
  <p><strong>Versioned Evidence Lifecycle Architecture</strong></p>
  <p><em>面向 Codex 研究项目的便携式工作流包</em></p>
  <p>
    <a href="./README.md">English</a>
    · <a href="https://marcus-ai4ss.github.io/VELA/">Pages</a>
    · <a href="./docs/getting-started.md">快速开始</a>
    · <a href="./docs/installation.md">安装</a>
    · <a href="./docs/imports/vela-helm-interface.md">HELM 接口</a>
    · <a href="./docs/faq.md">FAQ</a>
  </p>
</div>

VELA 给 Codex 一个文件化的研究工作流：项目目录、`AGENTS.md` 规则、schema 校验的交接包、证据台账、主张检查、验证报告、隐私扫描，以及 HELM 可读取的本地上下文文件。

当你希望 Codex 在清楚的项目边界里工作，而不是依赖零散聊天记录时，可以使用 VELA。它不是桌面 app、论文生成器、文献管理器或后台自动化服务。

VELA 的底层方法论来自工程控制论：每个研究项目都显式记录目标、状态、反馈信号、验证门和可回滚的校正循环。

## VELA 提供什么

| 层级 | 内容 |
| --- | --- |
| 项目结构 | `materials/`、`evidence/`、`claims/`、`methods/`、`deliverables/`、`handoffs/`、`logs/`、`.codex/`、`.vela/context.json` |
| Codex 指令 | 根目录和目录级 `AGENTS.md`、命令模板、有边界的 handoff prompt |
| 证据工作流 | 材料收集、证据提升、主张链接、交付物复核分开处理 |
| 治理模型 | 工程控制论式目标、状态、反馈、验证门和校正循环 |
| 验证检查 | JSON Schema、handoff lint、项目验证、隐私扫描、分享前检查 |
| 可选运行层 | 安装到用户自己 Codex 环境里的公开 research skills、route profiles、validators 和 `envctl` 工具 |
| HELM 联动 | 写出 `vela.project.context.v1`，让 HELM 读取项目状态，但不依赖 HELM |

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
| agentmemory、CodeGraph、MCP servers、Codex plugins、Zotero、Obsidian | 可选集成；VELA 只做检测和配置提示，用户数据与凭据留在本机 |

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

## VELA 与 HELM

VELA 和 HELM 是两个独立产品，共享显式文件接口。

| 产品 | 角色 |
| --- | --- |
| VELA | 创建并验证可携带的研究工作流包 |
| HELM | 读取本地项目状态，并以桌面看板展示 |

VELA 写出 `.vela/context.json`，schema 为 `vela.project.context.v1`。HELM 可以读取它，并准备 `helm.codex.handoff.v1` 交接说明。两者可以单独使用，也可以组合使用。

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
- [工作流核心](./docs/workflow-core.md)
- [证据生命周期](./docs/evidence-lifecycle.md)
- [Handoff contract](./docs/handoff-contract.md)
- [VELA 与 HELM 接口](./docs/imports/vela-helm-interface.md)
