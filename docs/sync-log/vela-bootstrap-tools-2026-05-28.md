# VELA bootstrap tools sync - 2026-05-28

## Scope

This update adds an explicit public tool bootstrap layer to VELA. The goal is to make a clean VELA clone closer to one-command setup for a Codex research workstation while preserving the boundary between publishable source payload and private user runtime state.

## Added

- `install.ps1 -BootstrapTools` checks and attempts safe Windows public installs for Git, Python 3.13+, PowerShell 7, ripgrep, Node.js LTS, GitHub CLI, and `agentmemory` when npm is available.
- `install-macos.sh` provides the corresponding macOS entrypoint and uses Homebrew for public tool bootstrap when `brew` is available.
- `install.sh --bootstrap-tools` remains the generic shell entrypoint for Linux and advanced users.
- `vela local-env bootstrap-tools --include all` reports bootstrap readiness through `vela.local_runtime.bootstrap_tools.v1`.
- `schemas/vela.local_runtime.bootstrap_tools.v1.schema.json` defines the machine-readable bootstrap report.
- README, Pages, and runtime manifest now state the required environment configuration explicitly.

## Boundary

VELA still does not copy:

- Codex plugin cache payloads.
- Browser login state, cookies, CNKI sessions, or other credentials.
- Zotero databases or Obsidian vault content.
- agentmemory data stores.
- MCP secrets, API keys, and vendor-specific permission grants.

CodeGraph, MCP vendors, Codex plugins, Zotero, Obsidian, browser sessions, and private memory stores remain doctor/manual setup. VELA can report their status and provide next actions, but it does not redistribute another user's runtime state.

## Verification

- `python -m unittest discover -s tests`
- `vela local-env bootstrap-tools --include all`
- `git diff --check`
- tracked-file scans for private C-drive environment paths
