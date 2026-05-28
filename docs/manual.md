# VELA Manual

Updated: 2026-05-28

VELA, Versioned Evidence Lifecycle Architecture, is a portable Codex workflow package for evidence-based research projects. It gives each project readable folders, `AGENTS.md` rules, schema-checked handoffs, evidence and claim ledgers, validation reports, privacy scans, runtime logs, and governed memory/evolution loops.

VELA is not a desktop app, paper generator, citation manager, or background automation service. Its operating model is engineering cybernetics: objectives, state, feedback, validation, and correction must be visible in files, checks, and version history.

![VELA engineering cybernetics and seven-layer structure](./assets/overview/01-engineering-cybernetics-seven-layers.png)

## What VELA Does

| Problem | VELA response |
| --- | --- |
| Research context gets lost across chats and files | Project `AGENTS.md`, handoffs, logs, and `.vela/context.json` preserve bounded state |
| Raw material is mistaken for evidence | `materials/` and `evidence/` stay separate |
| Claims cannot be traced | `claims/` records support relations |
| Tools drift over time | Runtime doctor checks installed tools and optional integrations |
| Memory becomes uncontrolled | Memory is only a candidate signal; durable rules require validation, tests, and commits |

## Seven Layers

![VELA architecture](./assets/overview/02-vela-architecture.png)

| Layer | Purpose |
| --- | --- |
| 01 Task and boundary | Define objectives, scope, constraints, and review standard |
| 02 Tools and interfaces | Connect Git, Python, MCP servers, agentmemory, CodeGraph, Zotero, Obsidian, and other user-owned tools |
| 03 Context and evidence | Separate materials, evidence, claims, methods, and deliverables |
| 04 Research stage | Keep design, literature, reading, writing, figures, and review as visible stages |
| 05 Runtime logs | Capture operations, failures, checks, and repairs |
| 06 Reliability checks | Run schemas, validators, tests, privacy scans, and handoff linting |
| 07 Environment governance | Decide which rules can persist through versioned commits |

## Install

| Platform | Command |
| --- | --- |
| Windows | `.\install.ps1 -BootstrapTools` |
| macOS | `sh ./install-macos.sh` |
| Linux / shell | `sh ./install.sh --bootstrap-tools` |

Windows:

```powershell
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
.\install.ps1 -BootstrapTools
.\vela.ps1 doctor
```

macOS:

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install-macos.sh
~/.vela/bin/vela doctor
```

VELA normally has two layers: the cloned source package and the local runtime under the user's `~/.vela` and `~/.codex`. User accounts, browser sessions, credentials, Zotero libraries, and private data remain outside VELA.

## Use

![VELA usage roadmap](./assets/overview/04-vela-usage-roadmap.png)

```bash
vela init my-research-project --skip-codex-trust
cd my-research-project
vela handoff new --template claim-check
vela handoff lint handoffs/H001.yaml
vela handoff render handoffs/H001.yaml --out handoffs/H001.prompt.md
vela validate . --repair-context
vela privacy scan .
```

## Memory And Evolution

![VELA memory and self-evolution governance](./assets/overview/03-memory-evolution-governance.png)

VELA can turn runtime logs, handoffs, evidence ledgers, and tool feedback into candidate improvements. It does not allow memory to become source-of-truth by itself. Durable rules must pass schema checks, validators, tests, human review, and versioned commits.

## Project Structure

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

## Common Commands

| Goal | Command |
| --- | --- |
| Check runtime | `vela doctor` |
| Initialize project | `vela init <project>` |
| Create handoff | `vela handoff new --template claim-check` |
| Lint handoff | `vela handoff lint handoffs/H001.yaml` |
| Render Codex prompt | `vela handoff render handoffs/H001.yaml --out handoffs/H001.prompt.md` |
| Validate project | `vela validate <project> --repair-context` |
| Privacy scan | `vela privacy scan <project>` |
| Install runtime | `vela runtime install --include core,automation,toolchain` |

## Boundaries

- VELA generates structure, prompts, contracts, and checks.
- VELA does not run `codex exec` by default.
- VELA does not copy browser sessions, cookies, credentials, private libraries, or user data.
- Doctor checks distinguish installed, missing, optional, and user-configured tools.
- Memory provides candidate signals; schemas, validators, tests, and Git commits decide durable rules.
