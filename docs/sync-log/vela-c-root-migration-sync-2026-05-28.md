# VELA C-root migration sync - 2026-05-28

## Scope

Read the C-root migration handoff from the local environment runtime and updated VELA against the new source boundary.

## New Source Boundary

- Active local environment source: `<LOCAL_ENV_ROOT>`
- VELA target repository: `<VELA_REPO_ROOT>`
- Former sibling source path under `<AI_ENV_ROOT>\git-folders\skills-environment-local` is no longer the active source.

VELA remains outside the C-root workspace. The C root stays limited to the local environment source and HELM.

## Absorbed

- C-root path resolver support through `skills/scripts/path_utils.py`.
- Updated drift, initializer, adoption-readiness, runtime-skill, and workbench validators that resolve VELA/HELM from env vars, `settings.toml [repos]`, sibling paths, then fallbacks.
- Updated `startup-safe` MCP management list, including `agentmemory` and `codegraph` as managed-but-not-prestarted entries.
- Governance audit updates that keep `agentmemory` and `codegraph` as optional profile-activated context helpers rather than always-on MCP servers.
- Stack scanner updates for official OpenAI bundled `browser` / `chrome` plugins and the `presentation_design` task type.
- Stale MCP cleanup coverage for `agentmemory` MCP adapters and `codegraph serve --mcp`, while preserving the standalone `agentmemory` runtime service boundary.
- Updated evolution intake and workspace log changes from the C source.

## VELA-Specific Adjustments

- `scripts/sync_local_environment_snapshot.py` now supports `VELA_LOCAL_ENV_SOURCE` as a default source override.
- The sanitized `settings.toml` keeps portable `[repos]` placeholders:
  - `<LOCAL_ENV_ROOT>`
  - `<HELM_REPO_ROOT>`
  - `<VELA_REPO_ROOT>`
- The public snapshot manifest records source working-tree status. After the governance audit sync, the C source was clean at source HEAD `c0f6a6a`.

## Verification

Source checks passed:

- `python -B -m skills.scripts.envctl validate drift --summary`
- `python -B -m skills.scripts.envctl validate adoption-readiness --summary`
- `python -B -m skills.scripts.envctl validate initializer-policy --summary`
- `python -m unittest discover -s skills/tests`

VELA checks passed:

- `python -m unittest discover -s tests`
- `python research-stack/local-environment/skills/scripts/validate_research_stack.py`
- Private path scan across `research-stack`, `scripts`, `tests`, and `docs`
- `git diff --check`
- Sandbox runtime install and strict doctor using temporary `CODEX_HOME` / `VELA_HOME`; 17 public skills installed and no missing core/runtime shim entries remained.
