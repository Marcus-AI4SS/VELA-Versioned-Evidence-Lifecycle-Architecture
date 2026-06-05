# Installation

VELA is installed from a Git repository. It creates a local `vela` command, installs Python dependencies, and can install the optional VELA runtime into the user's own Codex environment.

## Windows

```powershell
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
.\install.ps1 -BootstrapTools
```

`-BootstrapTools` checks public tools and uses `winget` where possible for Git, Python 3.13+, PowerShell 7, ripgrep, Node.js, and GitHub CLI.

## macOS

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install-macos.sh
```

The macOS installer expects Homebrew and uses it for public tool bootstrap.

## Linux / Shell

```bash
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
sh ./install.sh --bootstrap-tools
```

## Runtime Locations

| Location | Role |
| --- | --- |
| cloned `vela/` repository | source package |
| `~/.vela` | VELA command shim, runtime files, install receipts |
| `~/.codex/skills` | public VELA-managed skills |

VELA does not copy account credentials, browser sessions, plugin caches, Zotero databases, Obsidian vaults, generated outputs, or private project data.

## Verify

```bash
vela doctor
vela runtime check --include core,automation,toolchain
```

The `runtime` command group installs and checks VELA's optional runtime layer. The project workflow itself starts with `vela init`.
