# AGENTS

This directory contains the public Codex skill runtime that VELA can install into a user's `CODEX_HOME/skills`.

## Operating Rules

- Keep every skill useful without private accounts, private paths, hidden caches, or unpublished project state.
- Treat `research-autopilot` as the main router for research work; helper skills must stay scoped to their stated task.
- Formal academic references require verifiable metadata: author, year, title, venue or source, and an auditable lookup path. Verify DOI when a DOI is present.
- Separate collected material, verified evidence, claims, deliverables, and handoffs. Do not turn raw material into a claim without an evidence record.
- Use project files as the source of truth. Conversation context can explain intent, but durable project state must be written into the VELA project structure.
- Keep generated outputs inside the active project unless the user explicitly selects another target.
- For multi-step research work, prefer scoped subagents or staged handoffs where that makes review easier; the main agent remains responsible for integration and final checks.
- Do not install, copy, or vendor plugin caches, browser sessions, cookies, secrets, private memory stores, Zotero databases, or Obsidian vaults.

## Project Inheritance

Project-level `AGENTS.md` files may add stricter rules for sources, methods, privacy, deliverables, and write boundaries. They must not relax the evidence, citation, privacy, or project-boundary rules above.

```yaml
agent_constraints:
  forbid_skills_mcp: []
  forbid_write_roots: []
  max_execution_mode: null
  require_review_for:
    - paper_draft
    - revision_package
    - submission_package
    - figures_tables
    - reproducibility_bundle
    - literature_synthesis
    - case_dataset
    - project_map
  project_truth_sources:
    - research-map.md
    - findings-memory.md
    - material-passport.yaml
    - evidence-ledger.yaml
```
