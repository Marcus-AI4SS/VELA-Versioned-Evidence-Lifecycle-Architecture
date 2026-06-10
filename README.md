<div align="center">
  <img src="./docs/assets/brand/vela-workflow-mark.png" alt="VELA layered sail mark" width="132">
  <h1>VELA</h1>
  <p><strong>Versioned Evidence Lifecycle Architecture</strong></p>
  <p><em>A portable Codex workflow package for evidence-based research projects</em></p>
  <p>
    <a href="./README.zh-CN.md">中文</a>
    · <a href="https://marcus-ai4ss.github.io/VELA/">Pages</a>
    · <a href="./docs/manual.md">Manual</a>
    · <a href="./docs/getting-started.md">Getting started</a>
    · <a href="./docs/installation.md">Install</a>
    · <a href="./docs/faq.md">FAQ</a>
  </p>
</div>

VELA gives Codex a file-based research workflow: project folders, `AGENTS.md` rules, schema-checked handoffs, evidence ledgers, claim checks, validation reports, privacy scans, and a machine-readable project context.

Use it when you want Codex to work inside a clear project boundary instead of loose chat history. VELA is not a desktop app, paper generator, citation manager, or background automation service.

The design borrows from engineering cybernetics: each research project has explicit objectives, observable state, feedback signals, validation gates, and bounded correction loops.

Optional: VELA can interoperate with HELM through explicit local files, but VELA does not require HELM.

## Visual Guide

![VELA engineering cybernetics and seven-layer structure](./docs/assets/overview/01-engineering-cybernetics-seven-layers.png)

![VELA source package, runtime, project, and tool architecture](./docs/assets/overview/02-vela-architecture.png)

![VELA memory management and self-evolution governance](./docs/assets/overview/03-memory-evolution-governance.png)

![VELA usage roadmap](./docs/assets/overview/04-vela-usage-roadmap.png)

## What You Get

| Layer | What VELA Adds |
| --- | --- |
| Project structure | `materials/`, `evidence/`, `claims/`, `methods/`, `deliverables/`, `handoffs/`, `logs/`, `.codex/`, and `.vela/context.json` |
| Codex instructions | Root and directory-level `AGENTS.md` files, command templates, and bounded handoff prompts |
| Evidence workflow | Separate material intake, evidence promotion, claim linking, and deliverable review |
| Governance model | Engineering-cybernetic loops for objectives, state, feedback, gates, and correction |
| Validation | JSON Schema checks, handoff linting, project validation, privacy scans, and sharing-readiness checks |
| Memory and evolution | Runtime logs, handoffs, evidence ledgers, and tool feedback become candidate improvements; durable rules require validation, tests, and versioned commits |
| Optional runtime | Public research skills, route profiles, validators, and `envctl` helpers installed into the user's own Codex environment |
| Machine context | `.vela/context.json` exposes current project state for documented local readers |

## Environment Map

VELA is not a single script. It is a Codex-installable research workflow environment.

| Part | Description |
| --- | --- |
| Seven-layer structure | Task boundary, tools/interfaces, context/evidence, research stage, runtime logs, reliability checks, environment governance |
| Skills | orchestration, literature, evidence, computational social science, writing/export, figures/presentation, runtime helpers, knowledge sync |
| Plugins | Native Browser, Chrome, Computer Use, GitHub, Superpowers, Zotero, Scite, Google Drive, Documents, Presentations, Spreadsheets, and related optional layers |
| MCP and adapters | OpenAlex, Semantic Scholar, Google Scholar, paper-search, Chrome DevTools, and CodeGraph are route-scoped helpers; native Browser/Chrome/Computer Use comes first for web and desktop interaction |
| Automation | doctor, runtime install, validate, privacy scan, envctl route/stack/memory/evolution checks |
| Memory governance | memory is a candidate signal; thread-level intake, reconciliation reports, durable rules, and evolution backlog all require schemas, validators, tests, and versioned commits |

See the [public manual](./docs/manual.md) for the full explanation.

## Current Runtime Updates

The current public runtime adds:

- schema-checked thread memory intake, so useful experience can become a reviewable candidate without importing full chat history
- red-blue-rainbow scientific figure presets for clearer paper figures and presentation diagrams
- stronger academic writing quality gates for direct argument flow, method-to-question continuity, contribution posture, and paragraph rhythm
- deduplicated governance assertions for memory, CodeGraph, tools, and source-rule boundaries

## Quick Start

Choose the installer for your platform:

| Platform | Command |
| --- | --- |
| Windows | `.\install.ps1 -BootstrapTools` |
| macOS | `sh ./install-macos.sh` |
| Linux / shell | `sh ./install.sh --bootstrap-tools` |

Windows example:

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

macOS example:

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install-macos.sh
~/.vela/bin/vela init ../my-research-project --skip-codex-trust
```

## Requirements

VELA works best when these public tools are available:

| Component | Why It Matters |
| --- | --- |
| Git | clone and update the package |
| Python 3.13+ | run the CLI, validators, and schema checks |
| PowerShell 7 / POSIX shell | run cross-platform helpers |
| ripgrep | fast project search and privacy scans |
| Node.js / npm | optional JavaScript-based tools |
| GitHub CLI | optional repository checks |
| CodeGraph, MCP servers, Codex plugins, Zotero, Obsidian, external memory-service patterns | checked by doctor commands or adoption reviews; user credentials and local data stay outside VELA. VELA does not install or prestart external memory services |

Installers create two normal user-side locations:

| Location | Role |
| --- | --- |
| cloned `vela/` repository | source package you can update with Git |
| `~/.vela` and `~/.codex` | local runtime shims, receipts, skills, and checks |

## Core Commands

```bash
vela init <project>
vela doctor
vela handoff new --template claim-check
vela handoff lint handoffs/H001.yaml
vela handoff render handoffs/H001.yaml --out handoffs/H001.prompt.md
vela validate <project> --repair-context
vela privacy scan <project>
```

## Repository Layout

| Path | Purpose |
| --- | --- |
| `package/` | Starter files copied into a project by `vela init` |
| `runtime/` | Optional VELA runtime: public skills, profiles, validators, schemas, and helper scripts |
| `schemas/` | Machine-readable contracts for context, handoffs, initializer, runtime, and validation |
| `scripts/` | VELA CLI and product helpers |
| `skills/` | Lightweight VELA skill entrypoints |
| `examples/` | Minimal projects and demo handoffs |
| `docs/` | Public documentation and GitHub Pages |
| `tests/` | Product contract tests |

## Read Next

- [Getting started](./docs/getting-started.md)
- [Installation](./docs/installation.md)
- [Manual](./docs/manual.md)
- [Workflow core](./docs/workflow-core.md)
- [Evidence lifecycle](./docs/evidence-lifecycle.md)
- [Handoff contract](./docs/handoff-contract.md)
