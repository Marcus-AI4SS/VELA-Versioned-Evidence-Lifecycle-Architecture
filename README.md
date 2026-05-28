<div align="center">
  <img src="./docs/assets/brand/vela-workflow-mark.png" alt="VELA layered sail mark" width="132">
  <h1>VELA</h1>
  <p><strong>Versioned Evidence Lifecycle Architecture</strong></p>
  <p><em>Portable project workflow package for Codex-based research</em></p>
  <p>
    <a href="./README.zh-CN.md">中文</a>
    · <a href="https://marcus-ai4ss.github.io/VELA/">Pages</a>
    · <a href="./docs/getting-started.md">Getting started</a>
    · <a href="./docs/imports/vela-helm-interface.md">HELM interface</a>
    · <a href="./docs/workflow-core.md">Workflow core</a>
    · <a href="./docs/evidence-lifecycle.md">Evidence lifecycle</a>
    · <a href="./docs/quality-checks.md">Quality checks</a>
  </p>
</div>

VELA = **Versioned Evidence Lifecycle Architecture**. It gives Codex a bounded, evidence-aware operating layer for research work. It packages project scaffolds, `AGENTS.md` instructions, Codex handoff contracts, evidence ledgers, claim checks, validation reports, and HELM-readable local state.

VELA is not a desktop app, chat interface, paper generator, citation manager, hidden autonomous agent, or private memory store. VELA prepares bounded work for Codex; Codex performs the task; people review the result. [HELM](https://github.com/Marcus-AI4SS/HELM) is the optional Hub for Evidence, Logs & Monitoring that can read the same project state.

## Local Research Environment Distribution

This repository now includes `research-stack/local-environment/`, a sanitized near 1:1 distribution of the local Codex research environment after the May 2026 governance updates. It carries the research routing contracts, engineering-cybernetics control kernel, seven-layer governance model, memory rules, workflow catalogs, MCP/profile templates, validators, tests, envctl modules, public research skills, and toolchain inventory.

The distribution deliberately excludes desktop app development and distilled-scholar skill chains. It also redacts private absolute paths and never includes browser login state, cookies, secrets, caches, or generated outputs. `install.ps1` and `install.sh` run `vela local-env install-runtime --include core,automation,toolchain --commit`: this installs the public research skills into `CODEX_HOME/skills`, copies the contracts and envctl runtime into `VELA_HOME/research-stack/local-environment`, creates an `envctl` shim, and records a runtime receipt. Optional MCP servers, Codex plugins, browser login state, Zotero, Obsidian, agentmemory, and CodeGraph are checked or guided through doctor commands, not copied from another user's machine. `vela init` remains the project initializer and does not copy the broader environment into each project.

## Environment Requirements

VELA is closest to a one-command setup when the public toolchain is already present. For a fresh Windows machine, run `.\install.ps1 -BootstrapTools` first; it checks the toolchain and attempts safe public installs through `winget` where VELA knows a stable package. On macOS, run `sh ./install-macos.sh`; it uses Homebrew when `brew` is available and otherwise reports manual setup steps.

| Component | Required For | VELA Setup Behavior |
| --- | --- | --- |
| Git | clone, repo audit, release workflow | Windows: `winget`; macOS: Homebrew |
| Python 3.13+ | VELA CLI, validators, envctl, schema checks | required before the Python installer can run; Windows: `winget`; macOS: Homebrew |
| PowerShell 7 (`pwsh`) | cross-platform runtime scripts | Windows: `winget`; macOS: Homebrew |
| ripgrep (`rg`) | fast repository and privacy scans | Windows: `winget`; macOS: Homebrew |
| Node.js LTS / npm | optional JavaScript-based tools and agentmemory install path | Windows: `winget`; macOS: Homebrew |
| GitHub CLI (`gh`) | optional GitHub release and repo checks | Windows: `winget`; macOS: Homebrew |
| agentmemory | optional local memory-management runtime | checked and optionally installed with npm; VELA never exports memory data |
| CodeGraph | optional project-local code index | checked/guided only; initialize each target project explicitly |
| MCP servers | optional Codex tool profiles | profile and doctor checks only; server credentials remain user-local |
| Codex plugins | optional plugin capabilities such as Browser, GitHub, Superpowers, Research Autopilot | install in the user's Codex runtime; VELA never redistributes plugin cache |
| Zotero / Obsidian / browser logins / CNKI sessions | optional external research workflows | never copied; VELA only documents and checks the boundary |

`.\install.ps1` or `sh ./install.sh` without bootstrap installs only the VELA-owned workflow/runtime layer: public research skills, contracts, schemas, catalogs, profiles, validators, tests, envctl modules, toolchain manifests, and shims.

VELA intentionally creates a two-layer setup for every user. The cloned VELA repository is the source package and can be updated with Git. The user's runtime layer lives under `CODEX_HOME` and `VELA_HOME`, defaulting to `~/.codex` and `~/.vela` on Windows, macOS, and Linux. Runtime receipts, installed public skills, envctl shims, MCP profile checks, and optional tool probes live there; private account state and caches stay user-local.

## Start In Five Minutes

Choose the installer for your machine:

| Platform | Use This | What It Does |
| --- | --- | --- |
| Windows | `install.ps1 -BootstrapTools` | Uses `winget` where possible, then installs the VELA runtime into your own `CODEX_HOME` and `VELA_HOME`. |
| macOS | `sh ./install-macos.sh` | Uses Homebrew where possible, then installs the VELA runtime into your own `~/.codex` and `~/.vela`. |
| Linux / advanced shell use | `sh ./install.sh --bootstrap-tools` | Checks public tools, installs the VELA runtime, and leaves system package installation to the user. |

```powershell
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
.\install.ps1 -BootstrapTools
.\vela.ps1 local-env doctor
.\vela.ps1 local-env bootstrap-tools --include all
.\vela.ps1 local-env doctor-runtime --include core,automation,toolchain
.\vela.ps1 init ..\my-research-project --skip-codex-trust
cd ..\my-research-project
..\vela\vela.ps1 handoff new --template claim-check
..\vela\vela.ps1 handoff lint handoffs\H001.yaml
..\vela\vela.ps1 handoff render handoffs\H001.yaml --out handoffs\H001.prompt.md
..\vela\vela.ps1 validate . --repair-context
..\vela\vela.ps1 privacy scan .
```

On macOS:

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install-macos.sh
~/.vela/bin/vela local-env doctor-runtime --include core,automation,toolchain
```

The generated project contains `materials/`, `evidence/`, `claims/`, `methods/`, `deliverables/`, `handoffs/`, `logs/`, `.codex/`, and `.vela/context.json`.

## What VELA Helps You Do

| Need | What VELA Gives You |
| --- | --- |
| Start a project without losing structure | A clear place for question, scope, sources, and expected deliverables |
| Keep evidence honest | A lifecycle that separates collected material from verified evidence |
| Work with Codex safely | Handoff packets that name the task, files, constraints, expected output, and review standard |
| Connect to HELM | `.vela/context.json` using `vela.project.context.v1` |
| Prepare shareable outputs | Checks that reveal unsupported claims and private material before a deliverable leaves the project |

## The Workflow

| Layer | Keep Here | Do Not Confuse It With |
| --- | --- | --- |
| Materials | DOI records, URLs, files, datasets, notes, captures | Evidence |
| Evidence | Verified materials with source, access time, status, and ethics or rights notes | A broad reading list |
| Claims | Candidate and supported statements | Final findings |
| Methods | Assumptions, coding rules, analysis plans, reproducibility notes | Results |
| Deliverables | Reports, briefs, figures, tables, status notes | Raw project state |
| Handoffs | Bounded tasks for Codex or collaborators | Whole-project delegation |

## A Good Codex Handoff

```yaml
schema_version: vela.codex.handoff.v1
handoff_id: H001
created_at: "2026-05-05T00:00:00Z"
created_by: human
surface: cli
mode: review_only
scope:
  task: Check whether a claim is supported by named evidence.
  relevant_files:
    - claims/C001.md
    - evidence/E001.yaml
constraints:
  - Do not add new claims.
expected_output:
  format: markdown
  path: logs/codex-runs/H001-result.md
review_standard:
  - Every support judgment must cite an evidence_id.
completion:
  validation_commands:
    - vela handoff lint handoffs/H001.yaml
  human_review_required: true
```

The handoff is intentionally small and schema-validated. Codex should receive enough context to do the task, not an unbounded invitation to rewrite the project.

## VELA And HELM

| Product | Role | Can Stand Alone? |
| --- | --- | --- |
| **VELA** = Versioned Evidence Lifecycle Architecture | Portable project lab, workflow boundary, and Codex workflow package | Yes |
| **HELM** = Hub for Evidence, Logs & Monitoring | Local board for status, evidence, logs, files, checks, and Codex notes | Yes |

Use VELA by itself when you want a portable workflow. Add HELM when you want a visual local board over the same project state.

The shared import contract has two directions:

- `vela.project.context.v1`: VELA exposes project state that HELM can read.
- `helm.codex.handoff.v1`: HELM prepares a bounded Codex handoff packet for the user to copy back into Codex; VELA should only store it after an explicit user save or export action.

See [VELA and HELM import interface](./docs/imports/vela-helm-interface.md).

## Read Next

- [Getting started](./docs/getting-started.md)
- [Codex wrapper contract](./docs/codex-wrapper.md)
- [Workflow core](./docs/workflow-core.md)
- [Project structure](./docs/architecture.md)
- [Evidence lifecycle](./docs/evidence-lifecycle.md)
- [Quality checks](./docs/quality-checks.md)
- [Handoff contract](./docs/handoff-contract.md)
- [Public export](./docs/public-export.md)
- [VELA and HELM import interface](./docs/imports/vela-helm-interface.md)
- [Use cases](./docs/use-cases.md)
- [Integrations](./docs/integrations.md)
- [FAQ](./docs/faq.md)

## Repository Layout

| Path | Purpose |
| --- | --- |
| `docs/` | Public documentation, GitHub Pages, and approved visual assets |
| `docs/imports/` | VELA and HELM import contracts |
| `docs/sync-log/` | Local cross-repository synchronization notes |
| `research-stack/local-environment/` | Sanitized near 1:1 local research environment distribution, excluding desktop app and distilled-scholar chains |
| `archive/legacy-research-stack/` | Historical private environment assets, kept out of VELA runtime |
| `examples/` | Minimal project and quick demo for inspection |
| `package/` | Starter package copied into a research project by `vela init` |
| `package/.vela/initializer-manifest.json` | Schema-driven initializer manifest for default project directories and files |
| `schemas/` | Machine-readable context, handoff, initializer, and validation schemas |
| `scripts/` | CLI, schema-driven initializer, validation, and local maintenance helpers |
| `skills/` | Public VELA Codex skill entrypoints |
| `tests/` | Runtime contract tests |
