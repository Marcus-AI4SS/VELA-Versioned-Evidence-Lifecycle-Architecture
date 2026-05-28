# VELA Runtime

This directory contains the optional VELA runtime package.

It can install public research skills into `CODEX_HOME/skills`, copy VELA contracts and validators into `VELA_HOME/runtime`, and create `envctl` shims under `VELA_HOME/bin`.

The runtime does not include account credentials, browser sessions, Zotero databases, Obsidian vaults, plugin caches, generated outputs, or private project data.

## Contents

| Path | Purpose |
| --- | --- |
| `skills/` | Public research skills, route profiles, validators, schemas, and helper scripts |
| `runtime/manifest.json` | Runtime component manifest |
| `python/requirements/` | Python dependency lists |
| `toolchain/` | Toolchain inventory |
| `manifest.json` | Package manifest |

## Install

```bash
vela runtime enable --include core,automation,toolchain --commit
```

The installed payload is the VELA runtime.
