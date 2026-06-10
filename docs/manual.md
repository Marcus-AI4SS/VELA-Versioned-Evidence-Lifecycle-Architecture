# VELA Public Manual

Updated: 2026-06-10

VELA, Versioned Evidence Lifecycle Architecture, is a portable research workflow environment for Codex. It gives each research project a readable operating layer: project folders, `AGENTS.md` rules, handoffs, evidence ledgers, schemas, validators, runtime logs, memory governance, and controlled evolution.

VELA is not a desktop app, paper generator, citation manager, or background automation platform. It helps Codex work inside clear project boundaries instead of relying on loose chat history.

![VELA engineering cybernetics and seven-layer structure](./assets/overview/01-engineering-cybernetics-seven-layers.png)

## 1. What VELA Gives You

| Problem | VELA response |
| --- | --- |
| Research context is scattered across chats, PDFs, notes, code, and drafts | A stable project structure with separated materials, evidence, claims, methods, deliverables, handoffs, and logs |
| Codex needs the same context repeatedly | `AGENTS.md`, handoff packets, and `.vela/context.json` preserve bounded project state |
| Raw material is treated as evidence too early | Materials only become evidence after source, access time, verification status, and support relation are recorded |
| Tooling becomes hard to govern | Routes and profiles decide which skills, plugins, and MCP tools are relevant |
| Memory becomes uncontrolled | Memory is a candidate signal; durable rules require validation, tests, review, and commits |

VELA does three practical jobs:

| Job | Meaning | Result |
| --- | --- | --- |
| Creates project order | Generates stable folders, Codex rules, handoff templates, and machine-readable state | A future Codex thread or collaborator can see where the project is and what evidence is usable |
| Governs tool use | Routes skills, plugins, MCP servers, and local commands through task profiles and quality gates | Tools are opened because the route needs them, not just because they are available |
| Preserves usable experience | Logs failures, fixes, and reusable procedures as reviewable candidates | The environment can evolve without letting temporary memory rewrite durable rules |

The public package includes research routes, public skills, MCP/profile templates, plugin coordination notes, schemas, validators, tests, envctl helpers, memory governance, and project folder hygiene. It does not include private databases, account state, browser sessions, cookies, tokens, caches, or personal custom modules outside the public research workflow.

## 2. Engineering-Cybernetic Backbone

VELA treats a research project as a controlled system:

| Concept | In VELA |
| --- | --- |
| Objective | The research task, stage goal, and expected deliverable |
| Boundary | Files, materials, tools, and actions that are allowed or forbidden |
| State | Project folders, evidence counts, blockers, logs, and `.vela/context.json` |
| Feedback | Doctor reports, schema errors, lint errors, tests, citation checks, and validation reports |
| Controller | Routing table, profiles, quality gates, and envctl validators |
| Actuator | Skills, scripts, plugins, MCP servers, and local tools |
| Disturbance | Login state, network limits, permissions, path drift, missing tools, and unverified material |
| Stability | Clean logs, passing checks, versioned rules, and reviewable evidence paths |

The loop is:

1. Define the task, expected output, and protected files.
2. Pick the route: literature, full text, writing, quant, text, network, figures, submission, retrospective, or environment governance.
3. Open only the skills, plugins, MCP servers, and local commands needed by that route.
4. Leave state behind: logs, handoffs, evidence ledgers, validator reports, and privacy reports.
5. Check the work through schemas, citation checks, path checks, permission checks, and quality gates.
6. Promote only validated experience into durable rules.

## 3. System Structure

![VELA architecture](./assets/overview/02-vela-architecture.png)

| Module | Plain meaning | Contents |
| --- | --- | --- |
| Source package | The VELA repository cloned from GitHub | `package/`, `runtime/`, `schemas/`, `scripts/`, `docs/`, `tests/` |
| Local runtime | User-side runtime installed into Codex | `~/.vela`, `~/.codex/skills`, CLI, profiles, commands, receipts |
| Project layer | Each research project's files | `materials/`, `evidence/`, `claims/`, `methods/`, `deliverables/`, `handoffs/`, `logs/` |
| Tool interface | Optional connectors to user-owned tools | Git, Python, ripgrep, MCP servers, Codex plugins, Zotero, Obsidian |
| Memory and evolution | Candidate memory and governed rule promotion | logs, local memory candidates, memory status reports, CodeGraph index, evolution backlog, validators |

VELA does not copy browser sessions, cookies, credentials, Zotero libraries, Obsidian vaults, or private local caches.

Users normally get three layers:

| Layer | Windows | macOS / Linux | Role |
| --- | --- | --- | --- |
| Source package | cloned `vela/` directory | cloned `vela/` directory | Git-updated source, docs, schemas, tests, runtime package |
| Local runtime | `%USERPROFILE%\.vela`, `%USERPROFILE%\.codex` | `~/.vela`, `~/.codex` | CLI shims, skills, profiles, commands, receipts, doctor reports |
| Project layer | any research project folder | any research project folder | `vela init` project scaffold and `.vela/context.json` |

This source/runtime/project separation is intentional. The source package can be recloned, the runtime can be reinstalled, and project files remain owned by the user.

## 4. Seven Layers

| Layer | Purpose |
| --- | --- |
| 01 Task and boundary | Define objectives, scope, constraints, and review standard |
| 02 Tools and interfaces | Decide which local tools, plugins, and MCP servers are needed |
| 03 Context and evidence | Separate materials, evidence, claims, methods, and source notes |
| 04 Research stage | Track design, literature, full text, analysis, writing, figures, submission, and retrospective stages |
| 05 Runtime logs | Preserve handoffs, rendered prompts, doctor reports, validation reports, failures, and repairs |
| 06 Reliability checks | Run schemas, validators, privacy scans, tests, and quality gates |
| 07 Environment governance | Decide which reusable rules can persist through commits |

The seven layers answer different questions:

| Question | Layer That Answers It |
| --- | --- |
| What is the task? | Task and boundary |
| Which tools are needed? | Tools and interfaces |
| What supports the decision? | Context and evidence |
| Which research stage is this? | Research stage |
| What happened? | Runtime logs |
| Is it reliable? | Reliability checks |
| Can this experience persist? | Environment governance |

## 5. Install

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

`BootstrapTools` checks and guides public dependencies. It does not copy account state, browser data, credentials, or private material.

Platform differences:

| Item | Windows | macOS / Linux |
| --- | --- | --- |
| Entry | `install.ps1`, `vela.ps1` | `install-macos.sh` / `install.sh`, `~/.vela/bin/vela` |
| Shell | PowerShell 7 preferred | zsh/bash |
| Tool guidance | winget/manual prompts | Homebrew/manual prompts |
| Permission notes | execution policy, path spaces, Defender | Gatekeeper, executable bits, Homebrew paths |

## 6. Environment Requirements

| Component | Role | Status |
| --- | --- | --- |
| Git | Clone, update, rollback, commit, publish | Recommended |
| Python 3.13+ | Run the CLI, schema checks, and validators | Core |
| PowerShell 7 / POSIX shell | Run platform-specific installers and helpers | Core |
| ripgrep | Fast search, path audit, privacy scan | Recommended |
| Node.js / npm | Optional JavaScript-based tooling | Optional |
| GitHub CLI | Repository collaboration and CI checks | Optional |
| Zotero / Obsidian | User-owned bibliography and notes | Optional; VELA does not copy databases |
| MCP servers | academic lookup, browser diagnostics, social evidence, and code-index interfaces | Route-specific |
| Codex plugins | GitHub, Superpowers, documents, spreadsheets, presentations, browser, and other enhancement layers | Route-specific |

Dependencies are grouped as:

| Type | Examples | How VELA Treats Them |
| --- | --- | --- |
| Core | Git, Python, shell, VELA CLI, schemas, validators | installers and `vela doctor` check them directly |
| Recommended | ripgrep, GitHub CLI, Node.js, PowerShell 7, Homebrew/winget | missing tools are reported, not faked |
| Optional integrations | Zotero, Obsidian, MCP servers, Codex plugins, external memory-service patterns, CodeGraph | profiles, doctor checks, and adoption reviews are provided; user authorization is required. External memory services are not installed or prestarted by VELA |

## 7. Project Structure

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

## 8. Workflow Routes

VELA starts from routes, not isolated tool names. A route can combine skills, plugins, MCP tools, and validators.

Typical flow:

```text
user task -> route selection -> skill bundle -> optional plugins/MCP -> schemas/validators -> logs/handoff/context
```

| Route | Use it for | Boundary |
| --- | --- | --- |
| `general-research` | Initial research triage | Does not replace specialized routes |
| `stack-governance` / `environment-ops` | Runtime, skills, plugins, MCP, profiles, and configuration checks | Does not decide research facts |
| `project-folder-hygiene` | Project folder cleanup and handoff preparation | Does not silently delete raw material, data, PDFs, or evidence |
| `evidence-based-literature-workflow` | Structured reading and citation evidence control | Discovery is not formal citation |
| `literature-review` | Literature landscape and synthesis | Writing still needs citation checks |
| `reference-fulltext-acquisition` | Legal full-text lookup and PDF status tracking | Only handles accessible sources |
| `single-paper-review` | One-paper review and pre-submission critique | Requires verified references |
| `empirical-quant`, `text-corpus`, `network-analysis`, `computational-social-science` | Data, models, text, network, and reproducibility workflows | Tools are actuators; evidence and reproducibility are the deliverables |
| `research-figure-design` / `research-presentation` | Figures, tables, presentations, web decks | No invented data or statistics |
| `writing-export` / `social-science-submission-package` | Writing, reviewer response, DOCX/LaTeX, version freeze | Language polish must not change facts |
| `social-platform-case` | Browser-visible platform material and digital trace cases | VELA does not ship account/session-bound platform backends |

## 9. Skills, Plugins, And MCP

VELA's public runtime contains active skills for orchestration, literature, evidence, computational social science, writing, export, figures, presentation, project hygiene, and knowledge sync.

Skill roles:

| Role | Meaning | Examples |
| --- | --- | --- |
| Entry | Receives the task and selects a route | `research-autopilot` |
| Controller | Runs multi-step workflows and checkpoints | `evidence-based-literature-workflow`, `research-team-orchestrator`, `vela-runtime-manager` |
| Executor | Performs concrete research actions | `citation-verifier`, `quant-analysis`, `text-analysis`, `research-figure-studio` |
| Helper | Supports cleanup, browser work, routing, or environment checks | `project-folder-hygiene`, `skill-vetter`, `local-cloud-router`, `playwright` |

Plugins are optional enhancement layers. Native Browser, Chrome, and Computer Use are the first choice for ordinary web pages, authenticated Chrome sessions, downloads, visible desktop apps, screenshots, and file dialogs. GitHub, Superpowers, Zotero, Scite, Google Drive, Documents, Presentations, Spreadsheets, and similar plugins may help when available. They do not replace schemas, validators, or source rules.

MCP servers are sensors and interfaces. Common examples are OpenAlex, Semantic Scholar, Google Scholar, paper-search, Chrome DevTools, and CodeGraph. Zotero is handled through the official plugin rather than a required MCP server. Platform and browser-visible material starts with native Browser, Chrome, and Computer Use; Browser MCP/CLI tools are reserved for debugging or reproducible page-structure checks after the native surfaces are insufficient. Their outputs must still pass project evidence and validation rules.

MCP startup policy:

| Policy | Meaning |
| --- | --- |
| Native first | Browser, Chrome, and Computer Use handle ordinary web and desktop interaction before MCP fallback |
| Do not open everything by default | avoids slow startup, resource waste, and unrelated tool state |
| Open by route | literature uses academic lookup and the official Zotero plugin; web evidence starts with native browser tools; code review uses CodeGraph only when code structure is needed |
| Explain before use | the agent should know what the server reads and whether it writes files |
| Persist useful output | useful results should land in materials, evidence, logs, or handoffs |

## 10. Memory And Evolution

![VELA memory and self-evolution governance](./assets/overview/03-memory-evolution-governance.png)

VELA does not treat memory as source-of-truth. Memory is a candidate signal.

| Memory layer | Stores | Boundary |
| --- | --- | --- |
| Ephemeral session | Temporary paths, failed commands, short-term context | Expires unless reviewed |
| Project memory | Project facts, stages, material boundaries, evidence paths | Stays project-scoped |
| Private preference | User collaboration preferences | Cannot become global rules automatically |
| Procedural memory | Reusable process and tool order | Needs tests or review |
| Control memory | Routing, permission, validator, or governance rules | Requires strict validation and commits |

No full transcript import, secret storage, cookie storage, automatic prompt injection, or automatic rule promotion is enabled by default.

Memory has four public landing zones:

| Landing Zone | Stores | Used For |
| --- | --- | --- |
| Project files | project facts, evidence, stage, methods, deliverables | continuation, handoff, review |
| Runtime logs | commands, checks, failures, repairs, handoffs, validation reports | debugging, rollback, audit |
| Local memory status reports | approved preferences and repeated-pattern candidates | auditable context recovery without automatic rule changes |
| Thread memory intake reports | bounded lessons from a finished task, with risk score and routing recommendation | reviewable evolution candidates without full transcript import |
| Evolution backlog | candidate rules, skills, schemas, automations | periodic governance and commits |

Thread memory intake is deliberately narrow. A finished task can leave a structured report with a summary, evidence pointers, reusable procedure, risk notes, and a recommended landing zone. The report is validated against `thread_memory_intake_report.v1`; it can feed the evolution backlog only after review. It does not copy full conversations, credentials, browser state, or private project files.

## 11. Automation

VELA automation is controlled auditing, not unattended mutation.

| Command or ability | Purpose | Boundary |
| --- | --- | --- |
| `vela doctor` | Check local tools and optional integrations | Reports status, does not fake installation |
| `vela runtime install` | Install or update VELA runtime | Does not copy private data |
| `vela validate` | Check project structure, schemas, context, and gates | Does not make research judgments |
| `vela privacy scan` | Detect private paths, credentials, caches, and sensitive files | User decides how to handle findings |
| `envctl route explain` | Explain the recommended route | Does not override user intent |
| `envctl validate stack` | Check skills, plugins, MCP, and config consistency | Does not silently rewrite user config |
| `envctl memory reconcile` | Compare memory, rules, and runtime state | Candidate memories need review |

Automation categories:

| Type | Purpose | Output |
| --- | --- | --- |
| Environment audit | tool gaps, profile drift, MCP state, schema changes, runtime install state | doctor report, stack validation report |
| Project audit | project structure, evidence chain, handoffs, privacy risk, deliverables | validation report, privacy report, context repair |
| Evolution audit | reusable experience, conflicting rules, retired routes | evolution backlog, route conflict report, candidate patch |

## 12. Common Commands

| Goal | Command |
| --- | --- |
| Check runtime | `vela doctor` |
| Initialize project | `vela init <project>` |
| Create handoff | `vela handoff new --template claim-check` |
| Lint handoff | `vela handoff lint handoffs/H001.yaml` |
| Render prompt | `vela handoff render handoffs/H001.yaml --out handoffs/H001.prompt.md` |
| Validate project | `vela validate <project> --repair-context` |
| Privacy scan | `vela privacy scan <project>` |
| Install runtime | `vela runtime install --include core,automation,toolchain` |

## 13. What VELA Does Not Do

- It does not decide research conclusions for the user.
- It does not upgrade unverified material into evidence.
- It does not run `codex exec` by default.
- It does not copy cookies, credentials, browser state, private libraries, or local caches.
- It does not start every MCP server by default.
- It does not treat external memory services, CodeGraph, or plugin caches as source rules.
- It does not include personal custom modules outside the public research workflow.
