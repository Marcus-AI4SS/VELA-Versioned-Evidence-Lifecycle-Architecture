# VELA local environment project hygiene sync - 2026-05-28

## Scope

Synchronized VELA's sanitized local research environment distribution against the current D-drive `skills-environment-local` working tree after the project hygiene and subagent governance update.

The source repository was not clean at sync time. VELA records this in `research-stack/local-environment/manifest.json` through `working_tree_dirty` and `working_tree_status`, because the snapshot intentionally includes the current local working-tree update rather than only the last committed source HEAD.

## Absorbed

- Global thread constraints in `AGENTS.md` and `skills/AGENTS.md`:
  - keep project folders clean and handoff-ready;
  - prefer subagent/parallel-agent decomposition for complex work;
  - keep the main agent responsible for synthesis, review, and final decisions.
- New public skill: `project-folder-hygiene`.
- Updated catalog contracts:
  - `skill_catalog`
  - `routing_table`
  - `route_mcp_activation_policy`
  - `conflict_matrix`
  - `control_kernel`
  - `environment_layer_contract`
  - `research_pipeline_stages`
  - `data_access_matrix`
  - `research_team_playbooks`
  - `subagent_registry`
- Updated Research Autopilot and Research Team Orchestrator public skill guidance.
- Updated route explanation support for the project folder hygiene route.

## Preserved Boundaries

VELA still excludes desktop app development chains, distilled-scholar/scholar-panel material, private runtime paths, browser state, cookies, secrets, caches, and generated outputs.

The runtime manifest keeps `bootstrap.public-tools`, so future sync runs do not remove the explicit public tool bootstrap contract.

## Verification

- Source: `validate_research_stack.py --summary`
- Source: `python -m unittest discover -s skills/tests`
- VELA: `python -m unittest discover -s tests`
- VELA sandbox install: `vela local-env install-runtime --include core,automation,toolchain --commit` into a temporary D-drive sandbox, confirming 17 public skills including `project-folder-hygiene`.
