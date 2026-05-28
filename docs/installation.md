# Installation

VELA is a repository-based Codex research environment distribution and project workflow package. There is no desktop installer; the install scripts create a local `vela` shim, install the sanitized local research environment, and write receipts under `~/.vela`.

## Download

Choose the installer that matches your machine:

| Platform | Installer | Runtime layout |
| --- | --- | --- |
| Windows | `.\install.ps1 -BootstrapTools` | Source package stays in the cloned repo; runtime installs into `%USERPROFILE%\.codex` and `%USERPROFILE%\.vela` unless overridden. |
| macOS | `sh ./install-macos.sh` | Source package stays in the cloned repo; runtime installs into `~/.codex` and `~/.vela` unless overridden. |
| Linux / other shell | `sh ./install.sh --bootstrap-tools` | Source package stays in the cloned repo; runtime installs into `~/.codex` and `~/.vela`; system packages are mostly manual. |

```powershell
git clone https://github.com/Marcus-AI4SS/VELA.git vela
cd vela
.\install.ps1 -BootstrapTools
.\vela.ps1 local-env doctor
.\vela.ps1 local-env bootstrap-tools --include all
.\vela.ps1 local-env doctor-runtime --include core,automation,toolchain
```

You can also download the repository as a ZIP from GitHub and unpack it wherever your Codex environment can read it.

The installer uses `requirements.txt` to install `jsonschema` and `PyYAML` for local contract validation. By default it also runs `vela local-env install-runtime --include core,automation,toolchain --commit`, which creates the same two-layer structure for every user:

- keeps the cloned VELA repository as the source package;
- installs public research skills into `CODEX_HOME/skills`;
- copies contracts, schemas, profiles, validators, envctl modules, and toolchain metadata into `VELA_HOME/research-stack/local-environment`;
- creates an `envctl` shim under `VELA_HOME/bin`;
- writes install receipts so `vela local-env doctor-runtime` can tell what is installed and what still needs optional setup;
- excludes desktop app development, distilled-scholar material, browser state, cookies, secrets, caches, generated outputs, and private absolute paths.

Use `.\install.ps1 -SkipLocalEnvironment` when you only want the VELA CLI and project wrapper. Use `.\install.ps1 -ForceLocalEnvironment` only after reviewing conflicts; existing non-VELA skill folders are backed up before replacement.

## Tool Bootstrap

`.\install.ps1 -BootstrapTools` is the explicit Windows bootstrap layer for public machine tools. It checks and attempts safe `winget` installs for Git, Python 3.13+, PowerShell 7, ripgrep, Node.js LTS, and GitHub CLI.

`sh ./install-macos.sh` is the macOS convenience installer. It requires Homebrew, uses `brew install` for Git, Python 3.13+, PowerShell 7, ripgrep, Node.js, and GitHub CLI where missing, and then delegates to the same VELA runtime installer. If npm is available, both Windows and macOS can also install the optional `agentmemory` command.

The same state can be inspected without mutation:

```powershell
.\vela.ps1 local-env bootstrap-tools --include all
.\vela.ps1 local-env bootstrap-tools --include system --install
```

Without `--yes`, `--install` is a preview. With `--yes`, VELA may run public installer commands: `winget` on Windows, Homebrew on macOS, and npm for optional npm-backed tools. CodeGraph, MCP server vendor environments, Codex plugin installation, browser login state, CNKI sessions, Zotero databases, Obsidian vaults, and private memory stores are not copied or silently installed. VELA only reports whether they are present and what the user must configure locally.

## Use With Codex

Initialize a project and then return to Codex with a bounded handoff:

```powershell
.\vela.ps1 init ..\my-research-project --skip-codex-trust
cd ..\my-research-project
..\vela\vela.ps1 handoff new --project .
..\vela\vela.ps1 validate . --repair-context
..\vela\vela.ps1 privacy scan .
```

VELA provides `.codex/config.toml.example`, `AGENTS.md` templates, MCP/profile templates, and a runtime manifest for optional C-drive/user-runtime dependencies. It does not silently rewrite your global Codex configuration, install private browser state, copy plugin caches, or export Zotero/Obsidian/agentmemory data. To preview or apply a profile after installation, use `envctl apply-profile <profile> --dry-run` first, then `--commit` only when the diff is acceptable.

## Keep It Portable

Do not put private notes, PDFs, browser sessions, Zotero databases, Obsidian vaults, tokens, SSH keys, or machine-specific paths into files you plan to share.

## Optional HELM

HELM is a separate Hub for Evidence, Logs & Monitoring. It can make VELA project state easier to inspect, but it is not required to use VELA.
