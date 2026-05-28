from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from .envctl.cross_repo_drift import validate_cross_repo_drift
    from .envctl.runtime_skill_drift import inspect_installed_skill_stale_paths, inspect_research_autopilot_runtime
    from .envctl.validator_envelope import build_validator_result, exit_code_for_result
    from .path_utils import (
        AGENT_BROWSER_CMD,
        CODEX_HOME,
        CONFIG_PATH,
        GH_EXE,
        GIT_EXE,
        INSTALLED_SKILLS_DIR,
        LEGACY_MARKETPLACE_PATH,
        PLUGIN_CACHE_ROOT,
        PROJECT_PLUGIN_DIR,
        PYTHON_RUNTIME,
        REPO_ROOT,
        SKILLS_ROOT,
        VENV_PYTHON,
        repo_relative,
    )
except ImportError:
    from envctl.cross_repo_drift import validate_cross_repo_drift
    from envctl.runtime_skill_drift import inspect_installed_skill_stale_paths, inspect_research_autopilot_runtime
    from envctl.validator_envelope import build_validator_result, exit_code_for_result
    from path_utils import (
        AGENT_BROWSER_CMD,
        CODEX_HOME,
        CONFIG_PATH,
        GH_EXE,
        GIT_EXE,
        INSTALLED_SKILLS_DIR,
        LEGACY_MARKETPLACE_PATH,
        PLUGIN_CACHE_ROOT,
        PROJECT_PLUGIN_DIR,
        PYTHON_RUNTIME,
        REPO_ROOT,
        SKILLS_ROOT,
        VENV_PYTHON,
        repo_relative,
    )

SKILLS_DIR = INSTALLED_SKILLS_DIR
ROOT = SKILLS_ROOT
ENV_ROOT = REPO_ROOT
TASK_TYPE_ENUM = {
    "orchestration",
    "project_retrospective",
    "stack_governance",
    "paper_review",
    "literature_review",
    "citation_integrity",
    "literature_discovery",
    "quant_analysis",
    "text_analysis",
    "network_analysis",
    "research_design",
    "dataset_discovery",
    "digital_trace_capture",
    "simulation",
    "reproducibility",
    "runtime_ops",
    "figure_table",
    "social_evidence",
    "writing_export",
    "writing_capture",
    "response_revision",
    "submission_packaging",
    "presentation_design",
    "knowledge_sync",
    "cloud_routing",
    "skill_vetting",
    "environment_ops",
    "desktop_app_development",
    "computational_social_science",
    "general_research",
}

REQUIRED_SKILLS = [
    "research-autopilot",
    "research-team-orchestrator",
    "evidence-based-literature-workflow",
    "reference-fulltext-acquisition",
    "pdf",
    "cnki-research",
    "google-scholar-research",
    "openalex-landscape",
    "semantic-citation-tracer",
    "citation-verifier",
    "zotero-sync",
    "social-platform-reader",
    "quant-analysis",
    "text-analysis",
    "network-analysis",
    "research-design-studio",
    "dataset-discovery",
    "digital-trace-pipeline",
    "abm-simulation-lab",
    "reproducibility-package",
    "long-running-experiment-ops",
    "figure-table-studio",
    "research-figure-studio",
    "manuscript-writing-studio",
    "research-presentation-studio",
    "guizang-ppt-skill",
    "reviewer-response-pack",
    "social-science-submission-packager",
    "writing-reference-capture",
    "scholar-panel",
    "latex-paper-conversion",
    "obsidian-research-sync",
    "research-docx-export",
    "research-stack-manager",
    "skill-vetter",
    "project-retrospective-evolver",
    "agent-browser",
    "playwright",
    "playwright-interactive",
    "desktop-app-product-blueprint",
    "desktop-app-architect",
    "desktop-ui-implementation",
    "desktop-app-qa-debug",
    "desktop-app-release-packager",
    "scholar-nuwa",
]


def summarize_report(report: dict) -> dict:
    details = report.get("details", {})
    commands = details.get("commands", {}) if isinstance(details, dict) else {}
    failed_commands = [
        name
        for name, payload in commands.items()
        if isinstance(payload, dict) and payload.get("ok") is not True
    ]
    return {
        "schema_version": "validator_result.summary.v1",
        "validator": report.get("validator"),
        "scope": report.get("scope"),
        "ok": report.get("ok"),
        "decision": report.get("decision"),
        "error_count": len(report.get("errors", [])),
        "warning_count": len(report.get("warnings", [])),
        "errors": report.get("errors", []),
        "warnings": report.get("warnings", []),
        "failed_commands": failed_commands,
        "detail_keys": sorted(details.keys()) if isinstance(details, dict) else [],
    }

RETIRED_SKILLS = [
    "project-kickoff-router",
    "research-project-pilot",
    "computational-social-science-pilot",
    "project-ops-manager",
    "knowledge-base-curator",
]

REQUIRED_MCP = [
    "chrome-devtools",
    "social-platform-mcp",
    "xiaohongshu-mcp",
    "zotero-mcp",
    "openalex-mcp",
    "semantic-scholar-mcp",
    "google-scholar-mcp",
    "cnki-mcp",
    "paper-search-mcp",
    "playwright-mcp",
    "figma-dev-mode-mcp",
    "agentmemory",
    "codegraph",
]

PROJECT_PLUGIN_DIR = ROOT / "plugins" / "research-autopilot"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_catalog_metadata(catalog: dict, routing_table: dict) -> dict:
    gates = read_json(ROOT / "catalog" / "quality_gates.json")
    stages = read_json(ROOT / "catalog" / "research_pipeline_stages.json")
    access = read_json(ROOT / "catalog" / "data_access_matrix.json")
    valid_gate_ids = {item["id"] for item in gates.get("gates", [])}
    valid_stage_ids = {item["id"] for item in stages.get("stages", [])}
    valid_access_levels = {item["id"] for item in access.get("levels", [])}

    active_skill_missing: list[str] = []
    active_skill_invalid: list[str] = []
    active_entry_skills: list[str] = []
    for name, item in catalog.get("skills", {}).items():
        if item.get("status") != "active":
            continue
        if item.get("entry") is True or item.get("role") == "entry":
            active_entry_skills.append(name)
        for required in ("task_type", "data_access_level", "quality_gate_required", "stage_scope", "subagent_allowed"):
            if required not in item:
                active_skill_missing.append(f"{name}:{required}")
        if item.get("task_type") not in TASK_TYPE_ENUM:
            active_skill_invalid.append(f"{name}:task_type")
        if item.get("data_access_level") not in valid_access_levels:
            active_skill_invalid.append(f"{name}:data_access_level")
        if not isinstance(item.get("subagent_allowed"), bool):
            active_skill_invalid.append(f"{name}:subagent_allowed")
        if set(item.get("quality_gate_required", [])) - valid_gate_ids:
            active_skill_invalid.append(f"{name}:quality_gate_required")
        if set(item.get("stage_scope", [])) - valid_stage_ids:
            active_skill_invalid.append(f"{name}:stage_scope")

    route_missing: list[str] = []
    route_invalid: list[str] = []
    for route in routing_table.get("routes", []):
        route_id = route.get("id", "<unknown>")
        for required in ("task_type", "data_access_level", "quality_gate_required", "stage_scope", "subagent_allowed"):
            if required not in route:
                route_missing.append(f"{route_id}:{required}")
        if route.get("task_type") not in TASK_TYPE_ENUM:
            route_invalid.append(f"{route_id}:task_type")
        if route.get("data_access_level") not in valid_access_levels:
            route_invalid.append(f"{route_id}:data_access_level")
        if not isinstance(route.get("subagent_allowed"), bool):
            route_invalid.append(f"{route_id}:subagent_allowed")
        if set(route.get("quality_gate_required", [])) - valid_gate_ids:
            route_invalid.append(f"{route_id}:quality_gate_required")
        if set(route.get("stage_scope", [])) - valid_stage_ids:
            route_invalid.append(f"{route_id}:stage_scope")

    return {
        "active_skill_missing_metadata": sorted(active_skill_missing),
        "active_skill_invalid_metadata": sorted(active_skill_invalid),
        "active_total_entry_skills": sorted(active_entry_skills),
        "single_total_entry_ok": sorted(active_entry_skills) == ["research-autopilot"],
        "route_missing_metadata": sorted(route_missing),
        "route_invalid_metadata": sorted(route_invalid),
    }


def collect_route_mcp_policy_errors(routing_table: dict) -> list[str]:
    policy = read_json(ROOT / "catalog" / "route_mcp_activation_policy.json")
    routes = {route["id"]: set(route.get("mcp", [])) for route in routing_table.get("routes", [])}
    policy_routes = {item.get("route_id"): item for item in policy.get("routes", [])}
    errors: list[str] = []
    missing = sorted(set(routes) - set(policy_routes))
    extra = sorted(set(policy_routes) - set(routes))
    errors.extend(f"route-mcp-policy-missing-route:{route_id}" for route_id in missing)
    errors.extend(f"route-mcp-policy-extra-route:{route_id}" for route_id in extra)
    for route_id, item in sorted(policy_routes.items()):
        if route_id not in routes:
            continue
        required = set(item.get("required_mcp", []))
        optional = set(item.get("optional_mcp", []))
        activation_needed = set(item.get("activation_needed_mcp", []))
        if required & optional or required & activation_needed or optional & activation_needed:
            errors.append(f"route-mcp-policy-overlapping-sets:{route_id}")
        policy_union = required | optional | activation_needed
        if policy_union != routes[route_id]:
            missing_mcp = sorted(routes[route_id] - policy_union)
            extra_mcp = sorted(policy_union - routes[route_id])
            if missing_mcp:
                errors.append(f"route-mcp-policy-missing-mcp:{route_id}:{missing_mcp}")
            if extra_mcp:
                errors.append(f"route-mcp-policy-extra-mcp:{route_id}:{extra_mcp}")
    return errors


def collect_project_root_file_errors(payload: dict) -> list[str]:
    project_files = payload.get("project_root_files", {})
    return [
        f"project-root-file-missing:{name}"
        for name, exists in sorted(project_files.items())
        if exists is not True
    ]


def run_command(command: list[str], *, cwd: Path | None = ENV_ROOT, timeout: int = 30) -> dict:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": str(exc)}


def is_isolated_codex_worktree(root: Path) -> bool:
    parts = [part.lower() for part in root.resolve().parts]
    return ".codex" in parts and "worktrees" in parts


def select_stack_python() -> tuple[str, dict]:
    candidates: list[str] = []
    for candidate in [VENV_PYTHON, PYTHON_RUNTIME, Path(sys.executable) if sys.executable else None]:
        if candidate and candidate.exists():
            candidates.append(str(candidate))
    candidates.append("python")

    unique_candidates = list(dict.fromkeys(candidates))
    attempts: dict[str, dict] = {}
    probe = "import sys; import jsonschema; print(sys.executable)"
    for candidate in unique_candidates:
        result = run_command([candidate, "-c", probe], timeout=10)
        attempts[candidate] = {
            "ok": result.get("ok"),
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "error": result.get("error"),
        }
        if result.get("ok") is True:
            return candidate, {
                "selected": candidate,
                "requires": ["jsonschema"],
                "attempts": attempts,
            }

    for candidate in unique_candidates:
        result = run_command([candidate, "--version"], timeout=10)
        attempts[f"{candidate}:version"] = {
            "ok": result.get("ok"),
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "error": result.get("error"),
        }
        if result.get("ok") is True:
            return candidate, {
                "selected": candidate,
                "requires": [],
                "warning": "jsonschema-unavailable",
                "attempts": attempts,
            }

    return "python", {
        "selected": "python",
        "requires": [],
        "warning": "no-python-probe-passed",
        "attempts": attempts,
    }


def project_venv_version_probe(stack_python: str) -> dict:
    if not VENV_PYTHON.exists():
        return {
            "ok": True,
            "skipped": True,
            "reason": "venv-missing",
            "fallback_python": stack_python,
        }
    result = run_command([str(VENV_PYTHON), "--version"])
    if result.get("ok") is True:
        return result
    result["ok"] = True
    result["warning"] = "venv-version-probe-failed-using-stack-python"
    result["fallback_python"] = stack_python
    return result


def python_module_command(stack_python: str, module: str, *args: str) -> list[str]:
    return [stack_python, "-m", module, *args]


def isolated_cross_repo_warning(error: str) -> bool:
    return error.startswith("cross-repo-drift:missing-vela-repo:") or error.startswith(
        "cross-repo-drift:missing-helm-repo:"
    )


def isolated_runtime_skill_warning(error: str) -> bool:
    warning_prefixes = (
        "runtime-skill-drift:research-autopilot-runtime-installed-duplicates",
        "runtime-skill-drift:research-autopilot-runtime-cache-missing",
        "runtime-skill-drift:research-autopilot-plugin-cache-bundle-missing",
        "runtime-skill-drift:research-autopilot-installed-duplicate-old-path-hits",
        "runtime-skill-drift:research-autopilot-cache-old-path-hits",
        "runtime-skill-drift:research-autopilot-installed-duplicates-differ-from-source",
        "runtime-skill-drift:research-autopilot-cache-differs-from-source",
        "runtime-skill-drift:research-autopilot-plugin-cache-bundle-differs-from-source",
    )
    return error.startswith(warning_prefixes)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate the local research stack.")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print compact validator output for chat stability.",
    )
    args = parser.parse_args(argv)

    config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    mcp_servers = config.get("mcp_servers", {})
    home_marketplace = read_json(LEGACY_MARKETPLACE_PATH) if LEGACY_MARKETPLACE_PATH.exists() else {}
    catalog = read_json(ROOT / "catalog" / "skill_catalog.json")
    routing_table = read_json(ROOT / "catalog" / "routing_table.json")
    metadata_report = collect_catalog_metadata(catalog, routing_table)
    route_mcp_policy_errors = collect_route_mcp_policy_errors(routing_table)
    drift_report = validate_cross_repo_drift()
    runtime_skill_drift = inspect_research_autopilot_runtime()
    installed_skill_stale_paths = inspect_installed_skill_stale_paths()
    isolated_worktree = is_isolated_codex_worktree(ENV_ROOT)
    stack_python, stack_python_probe = select_stack_python()

    social_platform_runtime = None
    social_platform_command = mcp_servers.get("social-platform-mcp", {}).get("command")
    if social_platform_command:
        candidate = Path(str(social_platform_command))
        if candidate.exists():
            social_platform_runtime = candidate
    if social_platform_runtime is None:
        social_platform_runtime = Path(stack_python)
    if social_platform_runtime is None:
        social_platform_runtime = Path("python")

    def plugin_source_path(payload: dict, plugin_name: str) -> str:
        for item in payload.get("plugins", []):
            if item.get("name") == plugin_name:
                return item.get("source", {}).get("path", "")
        return ""

    def plugin_install_policy(payload: dict, plugin_name: str) -> str:
        for item in payload.get("plugins", []):
            if item.get("name") == plugin_name:
                return item.get("policy", {}).get("installation", "")
        return ""

    payload = {
        "config_exists": CONFIG_PATH.exists(),
        "skills_dir_exists": SKILLS_DIR.exists(),
        "mcp_entries": {name: name in mcp_servers for name in REQUIRED_MCP},
        "skills": {
            name: (SKILLS_DIR / name / "SKILL.md").exists()
            for name in REQUIRED_SKILLS
        },
        "retired_skills_removed": {
            name: not (SKILLS_DIR / name / "SKILL.md").exists()
            for name in RETIRED_SKILLS
        },
        "project_root_files": {
            "repo_root_readme": (ENV_ROOT / "README.md").exists(),
            "repo_root_build_logic": (ENV_ROOT / "BUILD-LOGIC.md").exists(),
            "repo_root_gitignore": (ENV_ROOT / ".gitignore").exists(),
            "workspace_log": (ENV_ROOT / "WORKSPACE-LOG.md").exists(),
            "project_venv": VENV_PYTHON.exists(),
            "project_python_runtime": (ENV_ROOT / "python" / "runtime" / "python313" / "python.exe").exists(),
            "python_core_requirements": (ENV_ROOT / "python" / "requirements" / "research-core.txt").exists(),
            "python_core_lock": (ENV_ROOT / "python" / "requirements" / "research-core-lock.txt").exists(),
            "root_agents": (ROOT / "AGENTS.md").exists(),
            "plugin_manifest": (PROJECT_PLUGIN_DIR / ".codex-plugin" / "plugin.json").exists(),
            "routing_table": (ROOT / "catalog" / "routing_table.json").exists(),
            "conflict_matrix": (ROOT / "catalog" / "conflict_matrix.json").exists(),
            "skill_catalog": (ROOT / "catalog" / "skill_catalog.json").exists(),
            "settings": (ROOT / "catalog" / "settings.toml").exists(),
            "project_scope_rules": (ROOT / "catalog" / "project_scope_rules.json").exists(),
            "research_team_playbooks": (ROOT / "catalog" / "research_team_playbooks.json").exists(),
            "agent_execution_modes": (ROOT / "catalog" / "agent_execution_modes.json").exists(),
            "subagent_registry": (ROOT / "catalog" / "subagent_registry.json").exists(),
            "route_mcp_activation_policy": (ROOT / "catalog" / "route_mcp_activation_policy.json").exists(),
            "prompt_catalog_lite": (ROOT / "catalog" / "prompt_catalog_lite.json").exists(),
            "citation_verification_rules": (ROOT / "catalog" / "citation_verification_rules.json").exists(),
            "cnki_zotero_workflow": (ROOT / "catalog" / "cnki_zotero_workflow.json").exists(),
            "scholar_browser_patterns": (ROOT / "catalog" / "scholar_browser_patterns.json").exists(),
            "scholar_advisory_panel_policy": (ROOT / "catalog" / "scholar_advisory_panel_policy.json").exists(),
            "peer_review_workflow": (ROOT / "catalog" / "peer_review_workflow.json").exists(),
            "scientific_figure_workflow": (ROOT / "catalog" / "scientific_figure_workflow.json").exists(),
            "manuscript_writing_workflow": (ROOT / "catalog" / "manuscript_writing_workflow.json").exists(),
            "research_presentation_workflow": (ROOT / "catalog" / "research_presentation_workflow.json").exists(),
            "skill_workbench_policy": (ROOT / "catalog" / "skill_workbench_policy.json").exists(),
            "empirical_quant_workflow": (ROOT / "catalog" / "empirical_quant_workflow.json").exists(),
            "reviewer_allowlist": (ROOT / "catalog" / "reviewer_allowlist.json").exists(),
            "quality_gates": (ROOT / "catalog" / "quality_gates.json").exists(),
            "publication_style_rules": (ROOT / "catalog" / "publication_style_rules.json").exists(),
            "writing_quality_rules": (ROOT / "catalog" / "writing_quality_rules.json").exists(),
            "harness_adapter_contract": (ROOT / "catalog" / "multi_agent_harness_adapter.json").exists(),
            "external_systems_research": (ROOT / "catalog" / "external_systems_research.json").exists(),
            "research_pipeline_stages": (ROOT / "catalog" / "research_pipeline_stages.json").exists(),
            "data_access_matrix": (ROOT / "catalog" / "data_access_matrix.json").exists(),
            "dispatch_schema": (ROOT / "schemas" / "agent_dispatch_card.schema.json").exists(),
            "project_agent_schema": (ROOT / "schemas" / "project_agent_definition.schema.json").exists(),
            "subagent_registry_schema": (ROOT / "schemas" / "subagent_registry.schema.json").exists(),
            "route_mcp_activation_policy_schema": (ROOT / "schemas" / "route_mcp_activation_policy.schema.json").exists(),
            "prompt_catalog_lite_schema": (ROOT / "schemas" / "prompt_catalog_lite.schema.json").exists(),
            "citation_verification_rules_schema": (ROOT / "schemas" / "citation_verification_rules.schema.json").exists(),
            "citation_verification_report_schema": (ROOT / "schemas" / "citation_verification_report.schema.json").exists(),
            "publication_style_rules_schema": (ROOT / "schemas" / "publication_style_rules.v1.schema.json").exists(),
            "harness_adapter_schema": (ROOT / "schemas" / "multi_agent_harness_adapter.schema.json").exists(),
            "vela_codex_handoff_schema": (ROOT / "schemas" / "vela.codex.handoff.v1.schema.json").exists(),
            "vela_project_context_schema": (ROOT / "schemas" / "vela.project.context.v1.schema.json").exists(),
            "helm_codex_handoff_schema": (ROOT / "schemas" / "helm.codex.handoff.v1.schema.json").exists(),
            "helm_app_command_schema": (ROOT / "schemas" / "helm.app.command.v1.schema.json").exists(),
            "research_team_playbook_schema": (ROOT / "schemas" / "research_team_playbook.schema.json").exists(),
            "clarification_card_schema": (ROOT / "schemas" / "clarification_card.schema.json").exists(),
            "team_plan_result_schema": (ROOT / "schemas" / "team_plan_result.schema.json").exists(),
            "validator_result_schema": (ROOT / "schemas" / "validator_result.schema.json").exists(),
            "helm_snapshot_manifest_schema": (ROOT / "schemas" / "helm_snapshot_manifest.schema.json").exists(),
            "project_initializer_manifest_schema": (ROOT / "schemas" / "project_initializer_manifest.schema.json").exists(),
            "cybernetic_control_kernel_schema": (ROOT / "schemas" / "cybernetic_control_kernel.v1.schema.json").exists(),
            "memory_admission_policy_schema": (ROOT / "schemas" / "memory_admission_policy.v1.schema.json").exists(),
            "local_memory_system_schema": (ROOT / "schemas" / "local_memory_system.v1.schema.json").exists(),
            "memory_reconciliation_report_schema": (
                ROOT / "schemas" / "memory_reconciliation_report.v1.schema.json"
            ).exists(),
            "environment_layer_contract_schema": (
                ROOT / "schemas" / "environment_layer_contract.v1.schema.json"
            ).exists(),
            "conflict_matrix_schema": (ROOT / "schemas" / "conflict_matrix.v1.schema.json").exists(),
            "route_explanation_report_schema": (
                ROOT / "schemas" / "route_explanation_report.v1.schema.json"
            ).exists(),
            "startup_context_summary_schema": (
                ROOT / "schemas" / "startup_context_summary.v1.schema.json"
            ).exists(),
            "memory_candidate_schema": (ROOT / "schemas" / "memory_candidate.v1.schema.json").exists(),
            "memory_status_report_schema": (ROOT / "schemas" / "memory_status_report.v1.schema.json").exists(),
            "evolution_event_schema": (ROOT / "schemas" / "evolution_event.v1.schema.json").exists(),
            "evolution_intake_policy_schema": (ROOT / "schemas" / "evolution_intake_policy.v1.schema.json").exists(),
            "evolution_intake_report_schema": (ROOT / "schemas" / "evolution_intake_report.v1.schema.json").exists(),
            "external_adoption_review_schema": (ROOT / "schemas" / "external_adoption_review.v1.schema.json").exists(),
            "protected_runtime_paths_schema": (ROOT / "schemas" / "protected_runtime_paths.v1.schema.json").exists(),
            "cybernetic_source_rule_crosswalk_schema": (ROOT / "schemas" / "cybernetic_source_rule_crosswalk.v1.schema.json").exists(),
            "cnki_zotero_workflow_schema": (ROOT / "schemas" / "cnki_zotero_workflow.v1.schema.json").exists(),
            "scholar_browser_patterns_schema": (ROOT / "schemas" / "scholar_browser_patterns.v1.schema.json").exists(),
            "scholar_advisory_panel_policy_schema": (ROOT / "schemas" / "scholar_advisory_panel_policy.v1.schema.json").exists(),
            "peer_review_workflow_schema": (ROOT / "schemas" / "peer_review_workflow.v1.schema.json").exists(),
            "scientific_figure_workflow_schema": (ROOT / "schemas" / "scientific_figure_workflow.v1.schema.json").exists(),
            "manuscript_writing_workflow_schema": (
                ROOT / "schemas" / "manuscript_writing_workflow.v1.schema.json"
            ).exists(),
            "research_presentation_workflow_schema": (
                ROOT / "schemas" / "research_presentation_workflow.v1.schema.json"
            ).exists(),
            "skill_workbench_policy_schema": (ROOT / "schemas" / "skill_workbench_policy.v1.schema.json").exists(),
            "empirical_quant_workflow_schema": (
                ROOT / "schemas" / "empirical_quant_workflow.v1.schema.json"
            ).exists(),
            "cnki_candidate_discovery_schema": (ROOT / "schemas" / "cnki_candidate_discovery.v1.schema.json").exists(),
            "cnki_search_batch_download_schema": (ROOT / "schemas" / "cnki_search_batch_download.v1.schema.json").exists(),
            "project_initializer_manifest": (ROOT / "catalog" / "project_initializer_manifest.json").exists(),
            "control_kernel": (ROOT / "catalog" / "control_kernel.json").exists(),
            "memory_admission_policy": (ROOT / "catalog" / "memory_admission_policy.json").exists(),
            "local_memory_system": (ROOT / "catalog" / "local_memory_system.json").exists(),
            "environment_layer_contract": (ROOT / "catalog" / "environment_layer_contract.json").exists(),
            "evolution_backlog": (ROOT / "catalog" / "evolution_backlog.json").exists(),
            "evolution_intake_policy": (ROOT / "catalog" / "evolution_intake_policy.json").exists(),
            "external_adoption_reviews": (ROOT / "catalog" / "external_adoption_reviews.json").exists(),
            "protected_runtime_paths": (ROOT / "catalog" / "protected_runtime_paths.json").exists(),
            "cybernetic_source_rule_crosswalk": (ROOT / "catalog" / "cybernetic_source_rule_crosswalk.json").exists(),
            "engineering_cybernetics_source_evidence": (ROOT / "catalog" / "engineering_cybernetics_source_evidence.json").exists(),
            "vela_cybernetics_handoff": (ENV_ROOT / "handoffs" / "vela" / "2026-05-09-engineering-cybernetics-local-environment-handoff.json").exists(),
            "vela_cybernetics_prompt": (ENV_ROOT / "handoffs" / "vela" / "2026-05-09-vela-iteration-prompt.txt").exists(),
            "envctl_package": (ROOT / "scripts" / "envctl" / "__main__.py").exists(),
            "envctl_apply_profile": (ROOT / "scripts" / "envctl" / "apply_profile.py").exists(),
            "envctl_apply_profile_command": (ROOT / "scripts" / "envctl" / "commands" / "apply_profile.py").exists(),
            "envctl_cybernetics": (ROOT / "scripts" / "envctl" / "cybernetics.py").exists(),
            "envctl_memory_system": (ROOT / "scripts" / "envctl" / "memory_system.py").exists(),
            "envctl_environment_layers": (ROOT / "scripts" / "envctl" / "environment_layers.py").exists(),
            "envctl_conflict_matrix": (ROOT / "scripts" / "envctl" / "conflict_matrix.py").exists(),
            "envctl_route_explain": (ROOT / "scripts" / "envctl" / "route_explain.py").exists(),
            "envctl_memory_command": (ROOT / "scripts" / "envctl" / "commands" / "memory.py").exists(),
            "envctl_route_command": (ROOT / "scripts" / "envctl" / "commands" / "route.py").exists(),
            "envctl_cnki_zotero": (ROOT / "scripts" / "envctl" / "cnki_zotero.py").exists(),
            "envctl_cnki_zotero_command": (ROOT / "scripts" / "envctl" / "commands" / "cnki_zotero.py").exists(),
            "envctl_scholar_browser_patterns": (ROOT / "scripts" / "envctl" / "scholar_browser_patterns.py").exists(),
            "envctl_peer_review_workflow": (ROOT / "scripts" / "envctl" / "peer_review_workflow.py").exists(),
            "envctl_scientific_figure_workflow": (ROOT / "scripts" / "envctl" / "scientific_figure_workflow.py").exists(),
            "envctl_manuscript_writing_workflow": (
                ROOT / "scripts" / "envctl" / "manuscript_writing_workflow.py"
            ).exists(),
            "envctl_research_presentation_workflow": (
                ROOT / "scripts" / "envctl" / "research_presentation_workflow.py"
            ).exists(),
            "envctl_skill_workbench_policy": (ROOT / "scripts" / "envctl" / "skill_workbench_policy.py").exists(),
            "envctl_empirical_quant_workflow": (
                ROOT / "scripts" / "envctl" / "empirical_quant_workflow.py"
            ).exists(),
            "envctl_scholar_panel": (ROOT / "scripts" / "envctl" / "scholar_panel.py").exists(),
            "envctl_scholar_panel_command": (ROOT / "scripts" / "envctl" / "commands" / "scholar_panel.py").exists(),
            "envctl_evolution_intake": (ROOT / "scripts" / "envctl" / "evolution_intake.py").exists(),
            "envctl_evolution_command": (ROOT / "scripts" / "envctl" / "commands" / "evolution.py").exists(),
            "envctl_protected_paths": (ROOT / "scripts" / "envctl" / "protected_paths.py").exists(),
            "envctl_agent_contracts": (ROOT / "scripts" / "envctl" / "agent_contracts.py").exists(),
            "envctl_dispatch": (ROOT / "scripts" / "envctl" / "dispatch.py").exists(),
            "envctl_pipeline_contracts": (ROOT / "scripts" / "envctl" / "pipeline_contracts.py").exists(),
            "envctl_team_plan": (ROOT / "scripts" / "envctl" / "team_plan.py").exists(),
            "envctl_team_planner": (ROOT / "scripts" / "envctl" / "team_planner.py").exists(),
            "envctl_project_initializer": (ROOT / "scripts" / "envctl" / "project_initializer.py").exists(),
            "validate_agents_contract": (ROOT / "scripts" / "validate_agents_contract.py").exists(),
            "validate_subagent_registry": (ROOT / "scripts" / "validate_subagent_registry.py").exists(),
            "validate_harness_adapter_contract": (ROOT / "scripts" / "validate_harness_adapter_contract.py").exists(),
            "validate_external_systems_research": (ROOT / "scripts" / "validate_external_systems_research.py").exists(),
            "validate_vela_contracts": (ROOT / "scripts" / "validate_vela_contracts.py").exists(),
            "validate_research_pipeline": (ROOT / "scripts" / "validate_research_pipeline.py").exists(),
            "bootstrap_agent_dispatch": (ROOT / "scripts" / "bootstrap_agent_dispatch.py").exists(),
            "plan_research_team": (ROOT / "scripts" / "plan_research_team.py").exists(),
            "init_research_project_ps1": (ROOT / "scripts" / "init-research-project.ps1").exists()
        },
        "plugin_marketplace_paths": {
            "legacy_home_marketplace_exists": LEGACY_MARKETPLACE_PATH.exists(),
            "legacy_home_marketplace_relative": plugin_source_path(home_marketplace, "research-autopilot") == "./plugins/research-autopilot",
            "legacy_home_installed_by_default": plugin_install_policy(home_marketplace, "research-autopilot") == "INSTALLED_BY_DEFAULT",
        },
        "runtime_probe_paths": {
            "codex_home": str(CODEX_HOME),
            "plugin_cache_root": str(PLUGIN_CACHE_ROOT),
            "repo_root": str(ENV_ROOT),
            "isolated_codex_worktree": isolated_worktree,
            "stack_python": stack_python,
            "stack_python_probe": stack_python_probe,
        },
        "plugin_entries": {
            name: name in config.get("plugins", {})
            for name in [
                "github@openai-curated",
                "superpowers@openai-curated",
                "research-autopilot@research-environment-local",
                "hugging-face@openai-curated",
                "scite@openai-curated",
                "google-drive@openai-curated",
                "figma@openai-curated",
                "build-macos-apps@openai-curated",
                "documents@openai-primary-runtime",
                "spreadsheets@openai-primary-runtime",
                "presentations@openai-primary-runtime",
            ]
        },
        "profiles": {
            name: (ROOT / "profiles" / f"{name}.toml").exists()
            for name in [
                "baseline",
                "startup-safe",
                "literature",
                "paper-review",
                "css-text-network",
                "social-platform",
                "writing-review",
                "cloud-batch",
                "desktop-app",
            ]
        },
        "catalog_metadata": metadata_report,
        "route_mcp_policy_errors": route_mcp_policy_errors,
        "cross_repo_drift": drift_report,
        "runtime_skill_drift": runtime_skill_drift,
        "installed_skill_stale_paths": installed_skill_stale_paths,
        "commands": {
            "zotero_mcp_version": run_command(
                [
                    r"<CODEX_HOME>\vendor\zotero-mcp\Scripts\python.exe",
                    "-m",
                    "zotero_mcp.cli",
                    "version",
                ]
            ),
            "google_scholar_import": run_command(
                [
                    r"<CODEX_HOME>\vendor\google-scholar-mcp\Scripts\python.exe",
                    "-c",
                    "import scholarly, mcp; print('google-scholar-import-ok')",
                ]
            ),
            "semantic_scholar_import": run_command(
                [
                    r"<CODEX_HOME>\vendor\semantic-scholar-mcp\Scripts\python.exe",
                    "-c",
                    "import aiohttp, mcp; print('semantic-scholar-import-ok')",
                ]
            ),
            "openalex_npx_probe": run_command(
                [
                    "cmd",
                    "/c",
                    "npx",
                    "-y",
                    "openalex-research-mcp",
                    "--help",
                ]
            ),
            "cnki_import": run_command(
                [
                    r"<CODEX_HOME>\vendor\cnki-mcp\Scripts\python.exe",
                    "-c",
                    "import selenium, fastmcp; print('cnki-import-ok')",
                ]
            ),
            "paper_search_import": run_command(
                [
                    r"<CODEX_HOME>\vendor\paper-search-mcp\Scripts\python.exe",
                    "-c",
                    "import paper_search_mcp.server; print('paper-search-import-ok')",
                ]
            ),
            "social_platform_mcp_import": run_command(
                [
                    str(social_platform_runtime),
                    "-c",
                    f"import sys; sys.path.insert(0, {str(ROOT)!r}); import scripts.social_platform_mcp_server; print('social-platform-mcp-import-ok')",
                ]
            ),
            "social_platform_mcp_child_runtime": run_command(
                [
                    str(social_platform_runtime),
                    "-c",
                    (
                        f"import json, os, sys; sys.path.insert(0, {str(ROOT)!r}); "
                        "from scripts.social_platform_mcp_server import build_runtime_probe; "
                        "base_env = dict(os.environ); base_env['PATH'] = r'C:\\Windows\\system32;C:\\Windows'; "
                        "probe = build_runtime_probe(base_env); print(json.dumps(probe, ensure_ascii=False)); "
                        "raise SystemExit(0 if probe['ok'] else 1)"
                    ),
                ]
            ),
            "agent_browser_version": run_command([str(AGENT_BROWSER_CMD), "--version"])
            if AGENT_BROWSER_CMD.exists()
            else {"ok": False, "error": "agent-browser-missing"},
            "project_venv_version": project_venv_version_probe(stack_python),
            "git_version": run_command([str(GIT_EXE), "--version"])
            if GIT_EXE.exists()
            else {"ok": False, "error": "git-missing"},
            "gh_version": run_command([str(GH_EXE), "--version"])
            if GH_EXE.exists()
            else {"ok": False, "error": "gh-missing"},
            "obsidian_sync_import": run_command(
                [
                    stack_python,
                    "-c",
                    f"import sys; sys.path.insert(0, {str(ROOT)!r}); import scripts.sync_obsidian_note; print('obsidian-sync-import-ok')",
                ]
            ),
            "validate_subagent_registry": run_command(
                python_module_command(stack_python, "skills.scripts.validate_subagent_registry")
            ),
            "validate_harness_adapter_contract": run_command(
                python_module_command(stack_python, "skills.scripts.validate_harness_adapter_contract")
            ),
            "validate_external_systems_research": run_command(
                python_module_command(stack_python, "skills.scripts.validate_external_systems_research")
            ),
            "validate_vela_contracts": run_command(
                python_module_command(stack_python, "skills.scripts.validate_vela_contracts")
            ),
            "envctl_validate_contracts": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "contracts")
            ),
            "envctl_validate_cybernetics": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "cybernetics")
            ),
            "envctl_validate_memory": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "memory")
            ),
            "envctl_validate_environment_layers": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "environment-layers")
            ),
            "envctl_validate_conflicts": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "conflicts")
            ),
            "envctl_cybernetics_audit_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "cybernetics.py"),
                    str(ROOT / "scripts" / "envctl" / "commands" / "cybernetics.py"),
                ]
            ),
            "envctl_memory_system_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "memory_system.py"),
                    str(ROOT / "scripts" / "envctl" / "commands" / "memory.py"),
                ]
            ),
            "envctl_environment_layers_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "environment_layers.py"),
                ]
            ),
            "envctl_conflict_route_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "conflict_matrix.py"),
                    str(ROOT / "scripts" / "envctl" / "route_explain.py"),
                    str(ROOT / "scripts" / "envctl" / "commands" / "route.py"),
                ]
            ),
            "agentmemory_status": run_command(["cmd", "/c", "agentmemory", "status"], timeout=30),
            "codegraph_status": run_command(["cmd", "/c", "codegraph", "status"], timeout=30),
            "envctl_memory_status_probe": run_command(
                python_module_command(
                    stack_python,
                    "skills.scripts.envctl",
                    "memory",
                    "status",
                    "--summary",
                    "--dry-run",
                )
            ),
            "envctl_memory_reconcile_probe": run_command(
                python_module_command(
                    stack_python,
                    "skills.scripts.envctl",
                    "memory",
                    "reconcile",
                    "--summary",
                    "--dry-run",
                )
            ),
            "envctl_route_explain_probe": run_command(
                python_module_command(
                    stack_python,
                    "skills.scripts.envctl",
                    "route",
                    "explain",
                    "revision package",
                    "--summary",
                )
            ),
            "envctl_startup_summary_probe": run_command(
                python_module_command(
                    stack_python,
                    "skills.scripts.envctl",
                    "route",
                    "startup-summary",
                    "--route-id",
                    "writing-export",
                    "--summary",
                )
            ),
            "envctl_cnki_zotero_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "cnki_zotero.py"),
                    str(ROOT / "scripts" / "envctl" / "commands" / "cnki_zotero.py"),
                ]
            ),
            "envctl_cnki_zotero_validate": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "cnki-zotero", "validate")
            ),
            "envctl_scholar_browser_patterns_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "scholar_browser_patterns.py"),
                ]
            ),
            "envctl_scholar_browser_patterns_validate": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "scholar-browser-patterns")
            ),
            "envctl_peer_review_workflow_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "peer_review_workflow.py"),
                ]
            ),
            "envctl_peer_review_workflow_validate": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "peer-review-workflow")
            ),
            "envctl_scientific_figure_workflow_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "scientific_figure_workflow.py"),
                ]
            ),
            "envctl_scientific_figure_workflow_validate": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "scientific-figure-workflow")
            ),
            "envctl_manuscript_writing_workflow_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "manuscript_writing_workflow.py"),
                ]
            ),
            "envctl_manuscript_writing_workflow_validate": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "manuscript-writing")
            ),
            "envctl_research_presentation_workflow_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "research_presentation_workflow.py"),
                ]
            ),
            "envctl_research_presentation_workflow_validate": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "research-presentation-workflow")
            ),
            "envctl_skill_workbench_policy_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "skill_workbench_policy.py"),
                ]
            ),
            "envctl_skill_workbench_policy_validate": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "skill-workbench")
            ),
            "envctl_empirical_quant_workflow_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "empirical_quant_workflow.py"),
                ]
            ),
            "envctl_empirical_quant_workflow_validate": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "validate", "empirical-quant-workflow")
            ),
            "envctl_evolution_intake_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "evolution_intake.py"),
                    str(ROOT / "scripts" / "envctl" / "commands" / "evolution.py"),
                    str(ROOT / "scripts" / "envctl" / "protected_paths.py"),
                ]
            ),
            "envctl_evolution_intake_probe": run_command(
                python_module_command(
                    stack_python,
                    "skills.scripts.envctl",
                    "evolution",
                    "intake",
                    "--scan-root",
                    str(ENV_ROOT),
                    "--lookback-days",
                    "1",
                )
            ),
            "envctl_apply_profile_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "apply_profile.py"),
                    str(ROOT / "scripts" / "envctl" / "commands" / "apply_profile.py"),
                ]
            ),
            "envctl_apply_profile_baseline_dry_run": run_command(
                python_module_command(stack_python, "skills.scripts.envctl", "apply-profile", "baseline", "--dry-run")
            ),
            "envctl_apply_profile_startup_safe_dry_run": run_command(
                python_module_command(
                    stack_python,
                    "skills.scripts.envctl",
                    "apply-profile",
                    "startup-safe",
                    "--dry-run",
                )
            ),
            "validate_agents_contract_static": run_command(
                python_module_command(stack_python, "skills.scripts.validate_agents_contract")
            ),
            "validate_research_pipeline_static": run_command(
                python_module_command(stack_python, "skills.scripts.validate_research_pipeline")
            ),
            "bootstrap_agent_dispatch_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "bootstrap_agent_dispatch.py"),
                ]
            ),
            "plan_research_team_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "plan_research_team.py"),
                ]
            ),
            "envctl_agent_contracts_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "agent_contracts.py"),
                ]
            ),
            "envctl_dispatch_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "dispatch.py"),
                ]
            ),
            "envctl_pipeline_contracts_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "pipeline_contracts.py"),
                ]
            ),
            "envctl_team_plan_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "team_plan.py"),
                ]
            ),
            "envctl_team_planner_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "team_planner.py"),
                ]
            ),
            "envctl_project_initializer_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "envctl" / "project_initializer.py"),
                ]
            ),
            "init_research_project_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "init-research-project.py"),
                ]
            ),
            "extract_engineering_cybernetics_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "extract_engineering_cybernetics.py"),
                    str(ROOT / "scripts" / "build_engineering_cybernetics_reading_cards.py"),
                ]
            ),
            "validate_research_pipeline_compile": run_command(
                [
                    stack_python,
                    "-m",
                    "py_compile",
                    str(ROOT / "scripts" / "validate_research_pipeline.py"),
                ]
            ),
        },
    }

    command_errors = [
        f"command-probe-failed:{name}"
        for name, item in payload.get("commands", {}).items()
        if isinstance(item, dict) and item.get("ok") is not True
    ]
    documentation_surface_errors = []
    if not (ENV_ROOT / "README.md").exists():
        documentation_surface_errors.append("documentation-surface:missing-root-readme")
    if not (ENV_ROOT / "BUILD-LOGIC.md").exists():
        documentation_surface_errors.append("documentation-surface:missing-root-build-logic")
    if (ROOT / "README.md").exists():
        documentation_surface_errors.append("documentation-surface:unexpected-skills-readme")
    if (ROOT / "docs").exists():
        documentation_surface_errors.append("documentation-surface:unexpected-skills-docs")
    drift_errors = []
    if drift_report.get("ok") is not True:
        drift_errors = [f"cross-repo-drift:{item}" for item in drift_report.get("errors", [])]
    runtime_skill_errors = [
        f"runtime-skill-drift:{item}"
        for item in runtime_skill_drift.get("errors", [])
    ]
    warnings: list[str] = []
    if isolated_worktree:
        isolated_drift_warnings = [item for item in drift_errors if isolated_cross_repo_warning(item)]
        drift_errors = [item for item in drift_errors if item not in isolated_drift_warnings]
        warnings.extend(f"isolated-worktree:{item}" for item in isolated_drift_warnings)

        isolated_runtime_warnings = [
            item for item in runtime_skill_errors if isolated_runtime_skill_warning(item)
        ]
        runtime_skill_errors = [
            item for item in runtime_skill_errors if item not in isolated_runtime_warnings
        ]
        warnings.extend(f"isolated-worktree:{item}" for item in isolated_runtime_warnings)
    installed_skill_path_errors = [
        f"installed-skill-stale-path:{item}"
        for item in installed_skill_stale_paths.get("errors", [])
    ]
    catalog_metadata_errors = [
        f"catalog-metadata:active-skill-missing:{item}"
        for item in metadata_report.get("active_skill_missing_metadata", [])
    ] + [
        f"catalog-metadata:active-skill-invalid:{item}"
        for item in metadata_report.get("active_skill_invalid_metadata", [])
    ]
    if not metadata_report.get("single_total_entry_ok"):
        catalog_metadata_errors.append(
            f"catalog-metadata:non-unique-total-entry:{metadata_report.get('active_total_entry_skills', [])}"
        )
    project_root_file_errors = collect_project_root_file_errors(payload)
    report = build_validator_result(
        validator="validate_research_stack",
        scope="stack",
        errors=command_errors
        + project_root_file_errors
        + documentation_surface_errors
        + catalog_metadata_errors
        + route_mcp_policy_errors
        + drift_errors
        + runtime_skill_errors
        + installed_skill_path_errors,
        warnings=warnings,
        details=payload,
        compatibility=payload,
    )
    if args.summary:
        print(json.dumps(summarize_report(report), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(exit_code_for_result(report))


if __name__ == "__main__":
    main()
