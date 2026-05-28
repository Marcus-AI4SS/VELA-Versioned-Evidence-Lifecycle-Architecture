from __future__ import annotations

import argparse
import json
import os
import tomllib
from datetime import datetime
from pathlib import Path

try:
    from .envctl.runtime_skill_drift import inspect_installed_skill_stale_paths, inspect_research_autopilot_runtime
    from .envctl.protected_paths import protected_runtime_skill_names
    from .path_utils import CODEX_HOME, CONFIG_PATH, INSTALLED_SKILLS_DIR, PLUGIN_CACHE_ROOT, PROJECT_PLUGIN_DIR, PROFILES_ROOT, REPO_ROOT, SKILLS_ROOT
except ImportError:
    from envctl.runtime_skill_drift import inspect_installed_skill_stale_paths, inspect_research_autopilot_runtime
    from envctl.protected_paths import protected_runtime_skill_names
    from path_utils import CODEX_HOME, CONFIG_PATH, INSTALLED_SKILLS_DIR, PLUGIN_CACHE_ROOT, PROJECT_PLUGIN_DIR, PROFILES_ROOT, REPO_ROOT, SKILLS_ROOT


DEFAULT_CODEX_HOME = CODEX_HOME
ROOT = SKILLS_ROOT
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

PLUGIN_ID_OVERRIDES = {
    "browser": "browser@openai-bundled",
    "documents": "documents@openai-primary-runtime",
    "chrome": "chrome@openai-bundled",
    "presentations": "presentations@openai-primary-runtime",
    "research-autopilot": "research-autopilot@research-environment-local",
    "spreadsheets": "spreadsheets@openai-primary-runtime",
}

OFFICIAL_BUILTIN_PLUGIN_IDS = {
    "browser@openai-bundled",
    "chrome@openai-bundled",
}


def load_config(config_path: Path) -> dict:
    return tomllib.loads(config_path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def list_skills(skills_dir: Path) -> list[str]:
    if not skills_dir.exists():
        return []
    return sorted(
        entry.name
        for entry in skills_dir.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").exists()
    )


def collect_metadata_gaps(catalog: dict, routing_table: dict) -> dict:
    gates = load_json(ROOT / "catalog" / "quality_gates.json")
    stages = load_json(ROOT / "catalog" / "research_pipeline_stages.json")
    access = load_json(ROOT / "catalog" / "data_access_matrix.json")
    valid_gate_ids = {item["id"] for item in gates.get("gates", [])}
    valid_stage_ids = {item["id"] for item in stages.get("stages", [])}
    valid_access_levels = {item["id"] for item in access.get("levels", [])}

    active_skill_missing: list[str] = []
    active_skill_invalid: list[str] = []
    for name, item in catalog.get("skills", {}).items():
        if item.get("status") != "active":
            continue
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
        "route_missing_metadata": sorted(route_missing),
        "route_invalid_metadata": sorted(route_invalid),
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Research Stack Weekly Proposal Baseline",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Config file: `{payload['config_path']}`",
        f"- Skills dir: `{payload['skills_dir']}`",
        "",
        "## Active MCP Servers",
        "",
    ]
    for name in payload["active_mcp"]:
        lines.append(f"- `{name}`")

    lines.extend(["", "## Disabled MCP Servers", ""])
    for name in payload["disabled_mcp"]:
        lines.append(f"- `{name}`")

    lines.extend(["", "## Active Plugins", ""])
    for name in payload.get("active_plugins", []):
        lines.append(f"- `{name}`")

    lines.extend(["", "## Installed Skills", ""])
    for name in payload["skills"]:
        lines.append(f"- `{name}`")

    lines.extend(["", "## Research Autopilot Plugin Cache Skills", ""])
    for name in payload.get("plugin_cache_skills", []):
        lines.append(f"- `{name}`")

    lines.extend(["", "## Profiles", ""])
    for name in payload["profiles"]:
        lines.append(f"- `{name}`")

    lines.extend(["", "## Contract Assets", ""])
    for key, exists in payload.get("contract_assets", {}).items():
        lines.append(f"- `{key}`: `{'ok' if exists else 'missing'}`")

    lines.extend(["", "## Drift Checks", ""])
    drift = payload.get("drift_checks", {})
    for key, values in drift.items():
        lines.append(f"### {key}")
        if not values:
            lines.append("- none")
        elif isinstance(values, list):
            for value in values:
                if isinstance(value, dict):
                    lines.append(f"- `{json.dumps(value, ensure_ascii=False)}`")
                else:
                    lines.append(f"- `{value}`")
        else:
            lines.append(f"- `{values}`")
        lines.append("")

    lines.extend(["", "## Local Plugin", ""])
    lines.append(f"- `research-autopilot`: `{payload['plugin_path']}`")

    lines.extend(
        [
            "",
            "## Proposal Checklist",
            "",
            "- 检查总入口是否仍然只剩 `research-autopilot`；`project-retrospective-evolver`、`research-stack-manager` 只能是路线内控制器。",
            "- 检查是否有新的总控 skill 被标记成 `entry` 并破坏单一路由。",
            "- 检查活跃 MCP 是否与当前研究任务或默认 `baseline` profile 一致。",
            "- 检查 Scholar / CNKI / paper-search / 社媒读取链路是否仍保持正确分层。",
            "- 检查根级 `AGENTS.md`、阶段门控文件和 pipeline validator 是否齐全。",
            "- 检查 `manuscript_writing_workflow.json`、`writing_quality_rules.json`、`publication_style_rules.json` 与写作/图表质量门约束是否仍然存在。",
            "- 检查 harness adapter 预留接口是否仍保持 reserved-only，而没有意外接管主系统。",
            "- 检查外部体系评估总表是否仍与当前本地吸收状态一致。",
            "- 检查项目脚手架是否仍然生成 `material-passport.yaml`、`evidence-ledger.yaml` 和 pipeline status。",
            "- 检查本地插件、GUI 和 profile 管理脚本是否仍然可用。",
            "- 只输出提案，不自动修改配置或安装新组件。",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--skills-dir", type=Path, default=INSTALLED_SKILLS_DIR)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    mcp_servers = config.get("mcp_servers", {})
    catalog = load_json(ROOT / "catalog" / "skill_catalog.json")
    routing_table = load_json(ROOT / "catalog" / "routing_table.json")
    external_plugins = load_json(ROOT / "catalog" / "external_plugin_candidates.json")
    metadata_gaps = collect_metadata_gaps(catalog, routing_table)
    contract_assets = {
        "root_agents": (ROOT / "AGENTS.md").exists(),
        "project_scope_rules": (ROOT / "catalog" / "project_scope_rules.json").exists(),
        "research_team_playbooks": (ROOT / "catalog" / "research_team_playbooks.json").exists(),
        "agent_execution_modes": (ROOT / "catalog" / "agent_execution_modes.json").exists(),
        "subagent_registry": (ROOT / "catalog" / "subagent_registry.json").exists(),
        "route_mcp_activation_policy": (ROOT / "catalog" / "route_mcp_activation_policy.json").exists(),
        "prompt_catalog_lite": (ROOT / "catalog" / "prompt_catalog_lite.json").exists(),
        "citation_verification_rules": (ROOT / "catalog" / "citation_verification_rules.json").exists(),
        "reviewer_allowlist": (ROOT / "catalog" / "reviewer_allowlist.json").exists(),
        "quality_gates": (ROOT / "catalog" / "quality_gates.json").exists(),
        "publication_style_rules": (ROOT / "catalog" / "publication_style_rules.json").exists(),
        "manuscript_writing_workflow": (ROOT / "catalog" / "manuscript_writing_workflow.json").exists(),
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
        "manuscript_writing_workflow_schema": (
            ROOT / "schemas" / "manuscript_writing_workflow.v1.schema.json"
        ).exists(),
        "harness_adapter_schema": (ROOT / "schemas" / "multi_agent_harness_adapter.schema.json").exists(),
        "vela_codex_handoff_schema": (ROOT / "schemas" / "vela.codex.handoff.v1.schema.json").exists(),
        "vela_project_context_schema": (ROOT / "schemas" / "vela.project.context.v1.schema.json").exists(),
        "helm_codex_handoff_schema": (ROOT / "schemas" / "helm.codex.handoff.v1.schema.json").exists(),
        "helm_app_command_schema": (ROOT / "schemas" / "helm.app.command.v1.schema.json").exists(),
        "research_team_playbook_schema": (ROOT / "schemas" / "research_team_playbook.schema.json").exists(),
        "clarification_card_schema": (ROOT / "schemas" / "clarification_card.schema.json").exists(),
        "team_plan_result_schema": (ROOT / "schemas" / "team_plan_result.schema.json").exists(),
        "validator_result_schema": (ROOT / "schemas" / "validator_result.schema.json").exists(),
        "project_initializer_manifest_schema": (ROOT / "schemas" / "project_initializer_manifest.schema.json").exists(),
        "cybernetic_source_rule_crosswalk_schema": (ROOT / "schemas" / "cybernetic_source_rule_crosswalk.v1.schema.json").exists(),
        "project_initializer_manifest": (ROOT / "catalog" / "project_initializer_manifest.json").exists(),
        "cybernetic_source_rule_crosswalk": (ROOT / "catalog" / "cybernetic_source_rule_crosswalk.json").exists(),
        "envctl_package": (ROOT / "scripts" / "envctl" / "__main__.py").exists(),
        "envctl_apply_profile": (ROOT / "scripts" / "envctl" / "apply_profile.py").exists(),
        "envctl_apply_profile_command": (ROOT / "scripts" / "envctl" / "commands" / "apply_profile.py").exists(),
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
        "init_research_project_ps1": (ROOT / "scripts" / "init-research-project.ps1").exists(),
    }
    active_mcp: list[str] = []
    disabled_mcp: list[str] = []
    for name, value in sorted(mcp_servers.items()):
        if value.get("enabled", True):
            active_mcp.append(name)
        else:
            disabled_mcp.append(name)
    active_plugins = sorted(
        name
        for name, value in config.get("plugins", {}).items()
        if value.get("enabled", True)
    )
    known_plugin_names = {
        item.get("name")
        for item in external_plugins.get("plugins", [])
        if item.get("name")
    }
    known_plugin_ids = {
        PLUGIN_ID_OVERRIDES.get(name, f"{name}@openai-curated")
        for name in known_plugin_names
        if name not in {"obsidian-sidecar", "notion"}
    } | OFFICIAL_BUILTIN_PLUGIN_IDS

    installed_skills = list_skills(args.skills_dir)
    installed_skill_set = set(installed_skills)
    protected_runtime_skills = set(protected_runtime_skill_names(installed_skills_dir=args.skills_dir))
    catalog_skill_set = {
        name
        for name, item in catalog.get("skills", {}).items()
        if item.get("status") == "active"
    }
    plugin_cache_skill_dir = (
        PLUGIN_CACHE_ROOT
        / "research-environment-local"
        / "research-autopilot"
        / "0.1.0"
        / "skills"
    )
    plugin_cache_skills = list_skills(plugin_cache_skill_dir)
    runtime_available_skill_set = installed_skill_set | set(plugin_cache_skills)
    generated_scholar_skills = {
        name
        for name in installed_skill_set
        if name.endswith("-scholar")
    }
    known_external_skills = {"agent-browser", "codex-primary-runtime", "hatch-pet"}
    route_skill_refs: set[str] = set()
    route_mcp_refs: set[str] = set()
    for route in routing_table.get("routes", []):
        route_skill_refs.update(route.get("skills", []))
        route_skill_refs.update(route.get("helper_skills", []))
        route_skill_refs.update(route.get("project_helper_skills", []))
        route_mcp_refs.update(route.get("mcp", []))

    plugin_skill_dir = ROOT / "plugins" / "research-autopilot" / "skills"
    plugin_source_skills = sorted(
        path.name
        for path in plugin_skill_dir.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    ) if plugin_skill_dir.exists() else []
    runtime_skill_drift = inspect_research_autopilot_runtime(installed_skills_dir=args.skills_dir)
    installed_skill_stale_paths = inspect_installed_skill_stale_paths(installed_skills_dir=args.skills_dir)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config_path": str(args.config),
        "skills_dir": str(args.skills_dir),
        "active_mcp": active_mcp,
        "disabled_mcp": disabled_mcp,
        "active_plugins": active_plugins,
        "skills": installed_skills,
        "plugin_cache_skills": plugin_cache_skills,
        "protected_runtime_skills": sorted(protected_runtime_skills),
        "profiles": sorted(path.stem for path in PROFILES_ROOT.glob("*.toml")),
        "contract_assets": contract_assets,
        "plugin_path": str(PROJECT_PLUGIN_DIR),
        "repo_root": str(REPO_ROOT),
        "codex_home": str(CODEX_HOME),
        "plugin_cache_root": str(PLUGIN_CACHE_ROOT),
        "drift_checks": {
            "catalog_active_missing_from_runtime": sorted(catalog_skill_set - runtime_available_skill_set),
            "standalone_installed_not_in_catalog": sorted(
                installed_skill_set
                - catalog_skill_set
                - known_external_skills
                - protected_runtime_skills
                - generated_scholar_skills
            ),
            "distilled_scholar_runtime_skills": sorted(generated_scholar_skills),
            "route_skill_refs_missing_from_runtime": sorted(route_skill_refs - runtime_available_skill_set),
            "route_mcp_refs_missing_from_config": sorted(route_mcp_refs - set(mcp_servers)),
            "active_plugins_not_in_external_catalog": sorted(set(active_plugins) - known_plugin_ids),
            "plugin_source_skills": plugin_source_skills,
            "plugin_source_skills_missing_from_plugin_cache": sorted(set(plugin_source_skills) - set(plugin_cache_skills)),
            "plugin_source_skills_missing_from_standalone": sorted(set(plugin_source_skills) - installed_skill_set),
            "runtime_skill_drift_errors": runtime_skill_drift["errors"],
            "runtime_skill_installed_old_path_hits": runtime_skill_drift["installed_old_path_hits"],
            "runtime_skill_cache_old_path_hits": runtime_skill_drift["cache_old_path_hits"],
            "runtime_skill_installed_changed": runtime_skill_drift["installed_changed"],
            "runtime_skill_cache_changed": runtime_skill_drift["cache_changed"],
            "runtime_skill_plugin_bundle_missing": runtime_skill_drift["plugin_bundle_missing"],
            "runtime_skill_plugin_bundle_changed": runtime_skill_drift["plugin_bundle_changed"],
            "installed_skill_stale_path_errors": installed_skill_stale_paths["errors"],
            "installed_skill_stale_path_hits": installed_skill_stale_paths["old_path_hits"],
            "missing_contract_assets": sorted(key for key, exists in contract_assets.items() if not exists),
            "active_skill_missing_metadata": metadata_gaps["active_skill_missing_metadata"],
            "active_skill_invalid_metadata": metadata_gaps["active_skill_invalid_metadata"],
            "route_missing_metadata": metadata_gaps["route_missing_metadata"],
            "route_invalid_metadata": metadata_gaps["route_invalid_metadata"],
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
