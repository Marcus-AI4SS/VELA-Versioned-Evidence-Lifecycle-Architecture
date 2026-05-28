# AGENTS

This repository is the private `skills环境管理` workspace.

## Scope

- Manage the local Codex research environment.
- Work only inside this repository root.
- Main areas: `skills/`, `python/`, local validators, local docs, local environment scripts.

## Cross-Repo Boundary

- You may read, call, compare against, or copy content from `skills-environment-release`, `skills-app-own`, and `skills-app-github`.
- Do not modify any of those three repositories unless the user has explicitly approved that cross-repo change in the current thread.
- Do not publish private machine-specific material from this repository into public repositories.

## Thread Rule

- The `skills环境管理` thread should only work in this repository.
- Cross-repo reading and copying are allowed.
- Cross-repo writes require explicit user approval first; without that approval, stop and switch to the corresponding repository thread instead of editing across boundaries.

## Codex App Stability Rule

- Default to the `startup-safe` profile for ordinary environment maintenance threads. This keeps stdio MCP servers from prestarting during new conversation setup.
- Prefer validator summary output in chat: use `python -m skills.scripts.envctl validate <target> --summary` and `python .\skills\scripts\validate_research_stack.py --summary` for routine checks.
- Do not paste full validator JSON or long generated reports into chat unless the user explicitly asks for the raw output. Write large reports to files and summarize the result.
- If new Codex conversations repeatedly reconnect, run `python -m skills.scripts.envctl apply-profile startup-safe --commit`, restart Codex, then clean old MCP child processes with `skills/scripts/cleanup-stale-codex-mcp-processes.ps1` if needed.
- If chat streams repeatedly disconnect with transport/network errors, run `skills/scripts/diagnose-codex-connectivity.ps1`. When browser proxy is available but Codex child processes are not inheriting it, use `skills/scripts/set-codex-user-proxy.ps1` and restart Codex.

## Automation Worktree Rule

- Codex automation worktrees under `<CODEX_HOME>\worktrees\*\skills-environment-local` are isolated scratch checkouts.
- In those worktrees, missing sibling VELA/HELM repositories and runtime skill cache differences are diagnostic warnings, not source-contract failures.
- `WORKSPACE-LOG.md` can change when hooks run after checkout or branch switches. Treat a lone `WORKSPACE-LOG.md` diff as hook-generated state, not as a source change to review or promote.
- If an automation worktree captures valid feedback in `skills/catalog/evolution_backlog.json`, merge the event into the main local repository and then clean the scratch worktree.

## Project Contract Rule

- Project-level multi-agent work must use real files in the target project: `AGENTS.md` and `.codex/agents/*.json`.
- Do not emulate those files from conversation context, temporary JSON, or an `audit/` folder.
- If a project is missing them, use `python -m skills.scripts.envctl ensure-project-contract --path "<project_root>"` or the equivalent `plan-team` auto-initialization before dispatch.
- The local environment's `skills/AGENTS.md` and initializer catalog are templates and validators; they do not replace project-local contracts at runtime.

## Project Folder Hygiene Rule

- Every thread must keep its own target project folder organized and free of avoidable temporary files, dead files, dead code, duplicate scratch exports, empty throwaway folders, and stale intermediate artifacts.
- Use `project-folder-hygiene` when the user asks to clean, organize, hand off, archive, close, or audit a project folder, and before ending substantial file-generating work when the target folder may have accumulated scratch artifacts.
- Classify before deleting: keep source, evidence, data, schemas, scripts, tests, configs, final deliverables, logs, and user-provided materials; remove only clearly safe temporary/cache artifacts; ask before deleting tracked files, ambiguous data, PDFs, notebooks, evidence ledgers, Zotero/Obsidian files, or user-authored material.
- Destructive cleanup must stay inside the confirmed project root. Verify resolved paths before recursive removal, and report removed, moved, retained, and needs-user-decision items.

## Subagent Delegation Rule

- For substantial research, coding, review, environment audit, literature, figure, writing, or multi-file execution tasks with separable work units, prefer subagent-style decomposition and parallel agents when available.
- Each delegated agent must receive a concrete mission, project root, permitted files/sources, forbidden writes, required tools/skills, iteration expectation, validation method, and expected report format.
- Subagents should do context-heavy discovery, comparison, testing, reading, and draft review in their own context windows, then return concise but deep reports with evidence, decisions, failures, risks, and recommended next actions.
- The main agent remains accountable for route choice, integration, critique, follow-up assignment, final edits, validation, and user-facing summary. Do not delegate unsafe writes, secret handling, or irreversible operations without explicit guardrails.
- Tiny one-step tasks may stay single-agent; otherwise the default bias is to offload context-heavy work and keep the main context focused on the clean project line.

## External Adoption Readiness Rule

- When an external repository is described as installed, enabled, indexed, or delegated to, verify it with `python -m skills.scripts.envctl validate adoption-readiness --summary` before relying on it.
- When an external repository is described as pattern-only or not installed, do not claim its runtime is available. Use only the local schema, catalog, skill, or validator that absorbed the pattern.
- CodeGraph is project-local. If a target project reports `Not initialized`, run `skills/scripts/ensure-codegraph-index.ps1 -ProjectRoot "<project_root>"` or `codegraph init -i "<project_root>"` before using CodeGraph context. Do not treat another project's missing `.codegraph` cache as evidence that the local environment is broken.
- CodeGraph, agentmemory, and other runtime adapters provide context evidence only; they never replace `rg`, source files, validators, tests, and Git history.

## Protected Runtime Skill Rule

- Local environment management and automations must not write, sync, clean, rename, overwrite, delete, install dependencies into, or auto-evolve that folder.
- Treat it as an external protected runtime path. At most, record that it exists; do not scan its content for drift or fold it into local environment governance.
- The machine-readable protection list is `skills/catalog/protected_runtime_paths.json`.
