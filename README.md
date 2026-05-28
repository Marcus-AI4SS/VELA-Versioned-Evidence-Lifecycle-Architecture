<div align="center">
  <img src="./docs/assets/brand/vela-workflow-mark.png" alt="VELA layered sail mark" width="132">
  <h1>VELA</h1>
  <p><strong>Versioned Evidence Lifecycle Architecture</strong></p>
  <p><em>A portable Codex workflow package for evidence-based research projects</em></p>
  <p>
    <a href="./README.zh-CN.md">中文</a>
    · <a href="https://marcus-ai4ss.github.io/VELA/">Pages</a>
    · <a href="./docs/getting-started.md">Getting started</a>
    · <a href="./docs/installation.md">Install</a>
    · <a href="./docs/imports/vela-helm-interface.md">HELM interface</a>
    · <a href="./docs/faq.md">FAQ</a>
  </p>
</div>

VELA gives Codex a file-based research workflow: project folders, `AGENTS.md` rules, schema-checked handoffs, evidence ledgers, claim checks, validation reports, privacy scans, and a local context file that HELM can read.

Use it when you want Codex to work inside a clear project boundary instead of loose chat history. VELA is not a desktop app, paper generator, citation manager, or background automation service.

The design borrows from engineering cybernetics: each research project has explicit objectives, observable state, feedback signals, validation gates, and bounded correction loops.

## What You Get

| Layer | What VELA Adds |
| --- | --- |
| Project structure | `materials/`, `evidence/`, `claims/`, `methods/`, `deliverables/`, `handoffs/`, `logs/`, `.codex/`, and `.vela/context.json` |
| Codex instructions | Root and directory-level `AGENTS.md` files, command templates, and bounded handoff prompts |
| Evidence workflow | Separate material intake, evidence promotion, claim linking, and deliverable review |
| Governance model | Engineering-cybernetic loops for objectives, state, feedback, gates, and correction |
| Validation | JSON Schema checks, handoff linting, project validation, privacy scans, and sharing-readiness checks |
| Optional runtime | Public research skills, route profiles, validators, and `envctl` helpers installed into the user's own Codex environment |
| HELM link | `vela.project.context.v1` so HELM can read project status without controlling VELA |

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
| agentmemory, CodeGraph, MCP servers, Codex plugins, Zotero, Obsidian | optional integrations checked by doctor commands; user credentials and local data stay outside VELA |

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

## VELA And HELM

VELA and HELM are separate products with a shared interface.

| Product | Role |
| --- | --- |
| VELA | Creates and validates the portable research workflow package |
| HELM | Reads local project state and displays it as a desktop research board |

VELA writes `.vela/context.json` using `vela.project.context.v1`. HELM can read that file and prepare `helm.codex.handoff.v1` notes for Codex. Neither product requires the other to run.

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
- [Workflow core](./docs/workflow-core.md)
- [Evidence lifecycle](./docs/evidence-lifecycle.md)
- [Handoff contract](./docs/handoff-contract.md)
- [VELA and HELM interface](./docs/imports/vela-helm-interface.md)
