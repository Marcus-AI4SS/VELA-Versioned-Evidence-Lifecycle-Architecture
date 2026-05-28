# VELA Local Environment Sync - 2026-05-28

## Scope

This sync updates VELA from the local `skills-environment-local` repository after the May 2026 local research-environment work.

Source baseline:

- source repository: `skills-environment-local`
- source branch: `codex/cleanup-handoff`
- source head: `41481fa`
- change window: since `2026-05-01`
- local commit count in window: 65

## User Policy

The user requested a near one-to-one transfer into VELA, except:

- desktop app development workflows and their related skills/profiles
- distilled scholar generation, scholar panels, and related personal scholar-role material

The user also requested that environment configuration be included, including memory governance, installed toolchain information, Git, ripgrep, Python, Node, PowerShell, and related support pieces.

## Implementation

Added `research-stack/local-environment/` as a sanitized current snapshot. It contains:

- root local environment docs and rules
- `skills/catalog`
- `skills/schemas`
- `skills/profiles`
- `skills/scripts`
- `skills/templates`
- `skills/tests`
- `skills/docs`
- selected `research-autopilot` skill source directories
- environment overview assets
- `toolchain/toolchain_inventory.json`
- `manifest.json`

The snapshot is not automatically run by `vela init`. VELA can inspect and selectively promote pieces from it through schema, test, and privacy review.

## Redaction And Exclusion

The sync script:

- excludes desktop app skill directories and the `desktop-app` profile
- excludes `scholar-panel` and distilled-scholar policy files
- excludes generated outputs, caches, `.venv`, and runtime blobs
- redacts local absolute paths into placeholders such as `<LOCAL_ENV_ROOT>`, `<CODEX_HOME>`, `<OBSIDIAN_VAULT>`, and `<USER_HOME>`
- keeps installed tool versions but does not export executable absolute paths

## New Sync Tool

Added:

```powershell
python .\scripts\sync_local_environment_snapshot.py --source ..\skills-environment-local
```

The tool can refresh the snapshot from the local environment while preserving the same exclusion and redaction rules.

## Verification

Added `tests/test_local_environment_snapshot.py` to verify:

- the snapshot manifest records the May update window
- excluded skill folders are absent
- private paths are not exported
- toolchain inventory includes required commands without executable paths
- `settings.toml` uses portable placeholders

