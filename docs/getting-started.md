# Getting Started

Use VELA when you want Codex to work from a bounded project state rather than loose conversation history. VELA is the Versioned Evidence Lifecycle Architecture around Codex, not a desktop app or a hidden agent loop.

VELA also ships a sanitized near 1:1 distribution of the local Codex research environment. It includes the public research skills, routing contracts, memory governance, MCP/profile templates, envctl validators, and workflow catalogs, while excluding desktop app development, distilled-scholar material, and private runtime data.

## 1. Download VELA

Clone or download the repository you are viewing:

```powershell
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
.\install.ps1 -BootstrapTools
.\vela.ps1 local-env doctor
.\vela.ps1 local-env bootstrap-tools --include all
.\vela.ps1 local-env doctor-runtime --include core,automation,toolchain
```

On macOS or Linux:

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install.sh
~/.vela/bin/vela local-env doctor
~/.vela/bin/vela local-env doctor-runtime --include core,automation,toolchain
```

The install script configures the VELA CLI and installs the research environment into your Codex home. Restart Codex after installation so the new skills are discovered.

`-BootstrapTools` checks and, on Windows, attempts public installs for Git, Python 3.13+, PowerShell 7, ripgrep, Node.js, GitHub CLI, and agentmemory. CodeGraph, MCP server vendor setup, Codex plugins, browser/CNKI sessions, Zotero, Obsidian, and private memory databases remain explicit user-runtime setup; VELA only reports their status and gives the next action.

## 2. Initialize A Project

```powershell
.\vela.ps1 init ..\my-research-project --skip-codex-trust
```

This creates:

- `materials/`
- `evidence/`
- `claims/`
- `methods/`
- `deliverables/`
- `handoffs/`
- `logs/`
- `.codex/`
- `.vela/context.json`

Keep private data in your project folder, not in the VELA repository.

## 3. Capture Materials

Save DOI records, URLs, files, datasets, platform captures, policy documents, notes, or screenshots as materials. A material is only a source clue at this point.

## 4. Upgrade Evidence Carefully

A material becomes evidence only when the project records:

- source locator;
- access time;
- verification status;
- rights or ethics note;
- the claim it supports;
- how it supports that claim.

## 5. Ask Codex For Bounded Work

Before asking Codex to work, create a handoff:

```powershell
..\vela\vela.ps1 handoff new --project .
..\vela\vela.ps1 handoff lint handoffs\H001.yaml
..\vela\vela.ps1 handoff render handoffs\H001.yaml --out handoffs\H001.prompt.md
```

This keeps Codex work reviewable and prevents a broad prompt from silently changing the research record.

## 6. Validate, Scan, And Refresh HELM Context

```powershell
..\vela\vela.ps1 validate . --repair-context
..\vela\vela.ps1 privacy scan .
```

HELM reads `.vela/context.json` when you want a local board over the same project state.

## 7. Prepare A Public Export When Needed

```powershell
..\vela\vela.ps1 export public . --out public-export
```

The export command writes a manifest and quality report before copying public-safe project files.

## 8. Add HELM Later If Useful

HELM is optional. Use it when you want a local board for project status, evidence, deliverables, environment health, and Codex handoffs.
