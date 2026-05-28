# Workspace Cleanup Sync Log

Date: 2026-05-05

This repository is the current public VELA workflow package source.

Cleanup completed in the surrounding local workspace:

- Removed legacy `public-release/codex-research-stack` clones from both the D drive workspace and the C drive reference copy.
- Removed legacy `git-folders/skills-environment-release` clones from both locations.
- Removed old `CodexResearchConsole` / manager app build outputs from the root environment and local environment copies.
- Removed obsolete `workspace-control` scripts that still pointed to the old four-workspace split.

Current source-of-truth mapping:

- VELA workflow package: `<GIT_FOLDERS_ROOT>\VELA-workflow`
- HELM public dashboard: `<GIT_FOLDERS_ROOT>\HELM`
- Local research environment: `<LOCAL_ENV_ROOT>`
- Private local app: `<GIT_FOLDERS_ROOT>\skills-app-own`

Do not restore `codex-research-stack`, `skills-environment-release`, or `skills-app-github` as active workspaces unless a later migration explicitly reopens them.
