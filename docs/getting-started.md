# Getting Started

Use VELA when you want Codex to work from a bounded project state instead of loose conversation history.

## 1. Install

Windows:

```powershell
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
.\install.ps1 -BootstrapTools
```

macOS:

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install-macos.sh
```

Linux or advanced shell use:

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install.sh --bootstrap-tools
```

## 2. Initialize A Project

```bash
vela init ../my-research-project --skip-codex-trust
```

The generated project contains:

- `materials/`
- `evidence/`
- `claims/`
- `methods/`
- `deliverables/`
- `handoffs/`
- `logs/`
- `.codex/`
- `.vela/context.json`

## 3. Create A Handoff

```bash
vela handoff new --template claim-check
vela handoff lint handoffs/H001.yaml
vela handoff render handoffs/H001.yaml --out handoffs/H001.prompt.md
```

Copy the rendered prompt into Codex. Keep the task small enough that the output can be reviewed.

## 4. Validate Before Sharing

```bash
vela validate . --repair-context
vela privacy scan .
```

## Optional Runtime

The installer can also place VELA's public runtime helpers under `~/.vela` and public skills under `~/.codex/skills`. Optional integrations such as MCP servers, Codex plugins, Zotero, Obsidian, CodeGraph, external memory-service patterns, and browser sessions stay in the user's own runtime and are only checked or reviewed when explicitly requested. VELA does not install or prestart external memory services.
