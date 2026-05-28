# VELA

VELA = **Versioned Evidence Lifecycle Architecture**. It is a portable project lab, Codex workflow boundary, and sanitized near 1:1 distribution of the local Codex research environment. It gives each project a readable structure before work spreads across files, notes, citations, datasets, and handoffs, and it can install the public research skills, contracts, profiles, validators, and envctl runtime into a user's own Codex environment.

## Start Here

- [Getting started](./getting-started.md)
- [Installation](./installation.md)
- [Workflow core](./workflow-core.md)
- [Evidence lifecycle](./evidence-lifecycle.md)
- [Quality checks](./quality-checks.md)
- [Handoff contract](./handoff-contract.md)
- [Skills layer](./skills-layer.md)
- [Public export](./public-export.md)
- [Use cases](./use-cases.md)
- [Integrations](./integrations.md)
- [FAQ](./faq.md)

## Local Research Environment

Run the installer for your platform from the repository root:

- Windows: `.\install.ps1 -BootstrapTools`
- macOS: `sh ./install-macos.sh`
- Linux or generic shell: `sh ./install.sh --bootstrap-tools`

Windows bootstrap uses `winget` where possible. macOS bootstrap uses Homebrew where possible. Both install the public VELA runtime into the user's own `CODEX_HOME` and `VELA_HOME`, normally `~/.codex` and `~/.vela`. CodeGraph, MCP server vendors, Codex plugins, browser/CNKI sessions, Zotero, Obsidian, and private memory stores are doctor/manual setup only.

The distribution excludes desktop app development, distilled-scholar material, browser state, cookies, secrets, caches, generated outputs, and private absolute paths.

## Relationship To HELM

VELA is the portable project workflow package. HELM = **Hub for Evidence, Logs & Monitoring**, the optional local board. You can use VELA without HELM; HELM can later make the same project state easier to inspect.
