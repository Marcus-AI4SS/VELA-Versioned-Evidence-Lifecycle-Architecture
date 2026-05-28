from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

import yaml

try:
    from .schema_validation import collect_schema_document_errors, collect_schema_errors
    from .validator_envelope import build_validator_result
    from ..path_utils import CATALOG_ROOT, SCHEMAS_ROOT, SKILLS_ROOT
    from ..validate_vela_contracts import collect_contract_errors
except ImportError:  # pragma: no cover
    from envctl.schema_validation import collect_schema_document_errors, collect_schema_errors
    from envctl.validator_envelope import build_validator_result
    from path_utils import CATALOG_ROOT, SCHEMAS_ROOT, SKILLS_ROOT
    from validate_vela_contracts import collect_contract_errors

ROOT = SKILLS_ROOT
CATALOG = CATALOG_ROOT
SCHEMAS = SCHEMAS_ROOT
ROOT_AGENTS = ROOT / "AGENTS.md"

DEFAULT_CONSTRAINTS = {
    "forbid_skills_mcp": [],
    "forbid_write_roots": [],
    "max_execution_mode": None,
    "require_review_for": [],
    "project_truth_sources": [],
}
BOOTSTRAP_PROJECT_CONTRACT_PATHS = [
    ".codex/dispatch",
    ".codex/context-packets",
    "outputs/agent-runs",
    "logs/agent-handoffs",
    "logs/quality-gates",
    "logs/project-state",
]
ISOLATION_RANKS = {
    "shared_thread_context": 0,
    "project_file_context": 1,
    "isolated_subagent_context": 2,
    "isolated_worktree_context": 3,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_project_contract_preflight(
    project_root: Path,
    *,
    require_bootstrap_dirs: bool = False,
) -> dict:
    """Return a small machine-readable readiness report for project dispatch."""
    project_root = project_root.resolve()
    missing_paths: list[str] = []
    errors: list[str] = []

    if not (project_root / "AGENTS.md").exists():
        missing_paths.append("AGENTS.md")
        errors.append("missing-project-contract:AGENTS.md")

    agents_dir = project_root / ".codex" / "agents"
    if not agents_dir.exists():
        missing_paths.append(".codex/agents/")
        errors.append("missing-project-contract:.codex/agents/")
    elif not any(agents_dir.glob("*.json")):
        missing_paths.append(".codex/agents/*.json")
        errors.append("missing-project-contract:.codex/agents/*.json")

    if require_bootstrap_dirs:
        for relative_path in BOOTSTRAP_PROJECT_CONTRACT_PATHS:
            if not (project_root / relative_path).exists():
                missing_paths.append(relative_path + ("/" if "." not in Path(relative_path).name else ""))
                errors.append(f"missing-project-contract:{relative_path}")

    return {
        "ok": not errors,
        "project_root": str(project_root),
        "missing_paths": missing_paths,
        "errors": errors,
        "why_blocked": (
            "项目级多 agent 编排必须读取真实落盘的 AGENTS.md 和 .codex/agents/*.json，"
            "否则无法计算权限收缩、审稿映射和 canonical 输出目录。"
            if errors
            else None
        ),
        "minimum_fix": (
            f'python -m skills.scripts.envctl ensure-project-contract --path "{project_root}"'
            if errors
            else None
        ),
        "forbidden_workaround": (
            "不要用临时虚拟 AGENTS.md、临时 agent JSON 或 audit 目录替代项目 contract；"
            "这会让 dispatch 与后续 quality gate 脱节。"
            if errors
            else None
        ),
    }


def collect_control_kernel_ids() -> dict[str, set[str]]:
    kernel = load_json(CATALOG / "control_kernel.json")
    return {
        "control_objectives": {item["id"] for item in kernel.get("control_objectives", [])},
        "controlled_variables": {item["id"] for item in kernel.get("controlled_variables", [])},
        "feedback_signals": {item["id"] for item in kernel.get("feedback_signals", [])},
        "stability_metrics": {item["id"] for item in kernel.get("stability_metrics", [])},
    }


def collect_control_binding_errors(agent_id: str, item: dict, kernel_ids: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    bindings = item.get("control_bindings")
    if not isinstance(bindings, dict):
        return [f"{agent_id}: missing control_bindings"]
    required = {
        "control_objectives",
        "controlled_variables",
        "feedback_signals",
        "stability_metrics",
        "rollback_policy",
    }
    missing = required - set(bindings)
    if missing:
        errors.append(f"{agent_id}: control_bindings missing fields {sorted(missing)}")
    for key in ("control_objectives", "controlled_variables", "feedback_signals", "stability_metrics"):
        values = bindings.get(key)
        if not isinstance(values, list) or not values or any(not isinstance(value, str) or not value for value in values):
            errors.append(f"{agent_id}: control_bindings.{key} must be a non-empty string list")
            continue
        unknown = set(values) - kernel_ids[key]
        if unknown:
            errors.append(f"{agent_id}: control_bindings.{key} contains unknown ids {sorted(unknown)}")
    rollback_policy = bindings.get("rollback_policy")
    if not isinstance(rollback_policy, str) or not rollback_policy.strip():
        errors.append(f"{agent_id}: control_bindings.rollback_policy must be a non-empty string")
    return errors


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def normalize_relative_path(path_value: str) -> str:
    if not isinstance(path_value, str) or not path_value.strip():
        raise ValueError("empty-path")
    if "\\" in path_value:
        raise ValueError("backslash-not-allowed")
    if path_value.startswith("/") or re.match(r"^[A-Za-z]:", path_value):
        raise ValueError("absolute-path-not-allowed")
    normalized = str(PurePosixPath(path_value))
    if normalized == "." or normalized.startswith("../") or "/../" in normalized:
        raise ValueError("parent-reference-not-allowed")
    return normalized


def normalize_template_path(path_value: str, *, allow_target: bool) -> str:
    variables = set(re.findall(r"<[^>]+>", path_value))
    allowed = {"<run_id>", "<agent_id>"}
    if allow_target:
        allowed.add("<target_agent_id>")
    unknown = variables - allowed
    if unknown:
        raise ValueError(f"unknown-template-variables:{sorted(unknown)}")
    if "<target_agent_id>" in variables and not allow_target:
        raise ValueError("target-variable-not-allowed-here")
    placeholder_path = (
        path_value.replace("<run_id>", "RUN")
        .replace("<agent_id>", "AGENT")
        .replace("<target_agent_id>", "TARGET")
    )
    normalize_relative_path(placeholder_path)
    return path_value


def substitute_template(path_value: str, *, run_id: str, agent_id: str | None = None, target_agent_id: str | None = None) -> str:
    resolved = path_value.replace("<run_id>", run_id)
    if agent_id is not None:
        resolved = resolved.replace("<agent_id>", agent_id)
    if target_agent_id is not None:
        resolved = resolved.replace("<target_agent_id>", target_agent_id)
    return normalize_relative_path(resolved)


def path_in_scope(path_value: str, scopes: list[str]) -> bool:
    normalized = normalize_relative_path(path_value)
    for scope in scopes:
        if any(token in scope for token in ("<run_id>", "<agent_id>", "<target_agent_id>")):
            placeholder_scope = (
                scope.replace("<run_id>", "RUN")
                .replace("<agent_id>", "AGENT")
                .replace("<target_agent_id>", "TARGET")
            )
            scope_normalized = normalize_relative_path(placeholder_scope)
            pattern = re.escape(scope_normalized.rstrip("/"))
            pattern = pattern.replace("RUN", "[^/]+")
            pattern = pattern.replace("AGENT", "[^/]+")
            pattern = pattern.replace("TARGET", "[^/]+")
            if re.match(rf"^{pattern}(?:/.*)?$", normalized):
                return True
            continue
        scope_normalized = normalize_relative_path(scope)
        prefix = scope_normalized.rstrip("/")
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return True
    return False


def extract_agent_constraints(path: Path) -> dict:
    if not path.exists():
        raise ValueError("missing-AGENTS.md")
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```yaml\s+(agent_constraints:\s.*?)(?:```)", text, re.DOTALL)
    if not match:
        raise ValueError("missing-agent_constraints-yaml-block")
    payload = yaml.safe_load(match.group(1)) or {}
    constraints = payload.get("agent_constraints", {})
    if not isinstance(constraints, dict):
        raise ValueError("agent_constraints-must-be-object")
    allowed_fields = {
        "forbid_skills_mcp",
        "forbid_write_roots",
        "max_execution_mode",
        "require_review_for",
        "project_truth_sources",
    }
    unknown = set(constraints) - allowed_fields
    if unknown:
        raise ValueError(f"unknown-agent-constraint-fields:{sorted(unknown)}")
    constraints.setdefault("forbid_skills_mcp", [])
    constraints.setdefault("forbid_write_roots", [])
    constraints.setdefault("max_execution_mode", None)
    constraints.setdefault("require_review_for", [])
    constraints.setdefault("project_truth_sources", [])
    return constraints


def stricter_mode(mode_a: str | None, mode_b: str | None, mode_ranks: dict[str, int]) -> str | None:
    if mode_a is None:
        return mode_b
    if mode_b is None:
        return mode_a
    return mode_a if mode_ranks[mode_a] <= mode_ranks[mode_b] else mode_b


def stricter_isolation(method_a: str | None, method_b: str | None) -> str | None:
    if method_a is None:
        return method_b
    if method_b is None:
        return method_a
    return method_a if ISOLATION_RANKS[method_a] >= ISOLATION_RANKS[method_b] else method_b


def merge_constraints(base: dict, override: dict, mode_ranks: dict[str, int]) -> dict:
    return {
        "forbid_skills_mcp": sorted(set(base["forbid_skills_mcp"]) | set(override["forbid_skills_mcp"])),
        "forbid_write_roots": sorted(set(base["forbid_write_roots"]) | set(override["forbid_write_roots"])),
        "max_execution_mode": stricter_mode(base["max_execution_mode"], override["max_execution_mode"], mode_ranks),
        "require_review_for": sorted(set(base["require_review_for"]) | set(override["require_review_for"])),
        "project_truth_sources": sorted(set(base["project_truth_sources"]) | set(override["project_truth_sources"])),
    }


def validate_static_contract() -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []

    scope_rules = load_json(CATALOG / "project_scope_rules.json")
    modes = load_json(CATALOG / "agent_execution_modes.json")
    registry = load_json(CATALOG / "subagent_registry.json")
    kernel_ids = collect_control_kernel_ids()
    reviewer_allowlist = load_json(CATALOG / "reviewer_allowlist.json")
    routing = load_json(CATALOG / "routing_table.json")
    _conflict = load_json(CATALOG / "conflict_matrix.json")
    subagent_schema = load_json(SCHEMAS / "subagent_registry.schema.json")
    dispatch_schema = load_json(SCHEMAS / "agent_dispatch_card.schema.json")
    project_agent_schema = load_json(SCHEMAS / "project_agent_definition.schema.json")
    errors.extend(collect_schema_document_errors(subagent_schema, "subagent_registry.schema.json"))
    errors.extend(collect_schema_document_errors(dispatch_schema, "agent_dispatch_card.schema.json"))
    errors.extend(collect_schema_document_errors(project_agent_schema, "project_agent_definition.schema.json"))
    errors.extend(collect_schema_errors(registry, subagent_schema, "subagent_registry.json"))
    vela_errors, vela_warnings, vela_payload = collect_contract_errors()
    errors.extend(f"vela-contract:{item}" for item in vela_errors)
    warnings.extend(f"vela-contract:{item}" for item in vela_warnings)

    route_ids = {route["id"] for route in routing.get("routes", [])}
    for item in registry.get("agents", []):
        agent_id = item.get("agent_id", "<missing-agent-id>")
        errors.extend(collect_control_binding_errors(agent_id, item, kernel_ids))

    route_scope = scope_rules.get("route_scope", {})
    partitions = {
        "always_multi_agent": set(route_scope.get("always_multi_agent", [])),
        "never_default_multi_agent": set(route_scope.get("never_default_multi_agent", [])),
        "conditional_multi_agent": set(route_scope.get("conditional_multi_agent", [])),
    }

    partition_union = set().union(*partitions.values())
    if partition_union != route_ids:
        missing = sorted(route_ids - partition_union)
        extra = sorted(partition_union - route_ids)
        if missing:
            errors.append(f"route-scope-missing-routes:{missing}")
        if extra:
            errors.append(f"route-scope-extra-routes:{extra}")
    if partitions["always_multi_agent"] & partitions["never_default_multi_agent"] or partitions["always_multi_agent"] & partitions["conditional_multi_agent"] or partitions["never_default_multi_agent"] & partitions["conditional_multi_agent"]:
        errors.append("route-scope-partitions-must-be-disjoint")

    deliverable_types = set(scope_rules["enums"]["deliverable_types"])
    review_subset = set(scope_rules["enums"]["required_review_for"])
    if not review_subset <= deliverable_types:
        errors.append("required_review_for must be subset of deliverable_types")

    if scope_rules.get("clarification_card_fields") != [
        "route_id",
        "target_item_count",
        "work_units",
        "deliverable_types",
        "sync_targets",
        "explicit_project_mode",
        "needs_clarification",
        "route_confirmation_required",
        "route_confirmation_question",
        "user_confirmed_route",
    ]:
        errors.append("clarification_card_fields do not match the approved contract")

    mode_ranks = {name: item["rank"] for name, item in modes.get("modes", {}).items()}
    if mode_ranks != {
        "multi_perspective_reasoning": 0,
        "sequential_multi_agent_execution": 1,
        "parallel_multi_agent_execution": 2,
    }:
        errors.append("agent_execution_modes ranks do not match the approved contract")

    allowed_template_variables = modes.get("allowed_template_variables", [])
    if allowed_template_variables != ["<run_id>", "<agent_id>", "<target_agent_id>"]:
        errors.append("allowed_template_variables do not match the approved contract")

    reviewer_allowed = set(reviewer_allowlist.get("allowed_skills_mcp", []))
    if reviewer_allowed != {
        "citation-verifier",
        "academic-paper-review",
        "openalex-mcp",
        "semantic-scholar-mcp",
        "desktop-app-qa-debug",
        "agent-browser",
        "chrome-devtools",
        "playwright-mcp",
        "figma-dev-mode-mcp",
    }:
        errors.append("reviewer_allowlist does not match the approved contract")

    try:
        root_constraints = extract_agent_constraints(ROOT_AGENTS)
    except ValueError as exc:
        errors.append(f"root-AGENTS.md:{exc}")
        root_constraints = dict(DEFAULT_CONSTRAINTS)

    if set(root_constraints["require_review_for"]) - deliverable_types:
        errors.append("root AGENTS require_review_for contains invalid deliverable types")
    for truth_source in root_constraints["project_truth_sources"]:
        try:
            normalize_relative_path(truth_source)
        except ValueError as exc:
            errors.append(f"root-AGENTS.md:invalid-project-truth-source:{truth_source}:{exc}")

    payload = {
        "scope_rules": scope_rules,
        "modes": modes,
        "registry": registry,
        "reviewer_allowlist": reviewer_allowlist,
        "root_constraints": root_constraints,
        "vela_contracts": vela_payload,
        "schemas": {
            "subagent_registry": subagent_schema,
            "dispatch": dispatch_schema,
            "project_agent": project_agent_schema,
        },
    }
    return errors, warnings, payload


def validate_project(project_root: Path, payload: dict, *, mode: str = "project") -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    scope_rules = payload["scope_rules"]
    modes = payload["modes"]
    schemas = payload["schemas"]
    registry = {
        item["agent_id"]: item for item in payload["registry"].get("agents", [])
    }
    reviewer_allowlist = set(payload["reviewer_allowlist"]["allowed_skills_mcp"])
    review_subset = set(scope_rules["enums"]["required_review_for"])
    deliverable_types = set(scope_rules["enums"]["deliverable_types"])
    mode_ranks = {name: item["rank"] for name, item in modes["modes"].items()}

    required_dirs = [
      project_root / ".codex" / "agents",
      project_root / ".codex" / "dispatch",
      project_root / ".codex" / "context-packets",
      project_root / "outputs" / "agent-runs",
      project_root / "logs" / "agent-handoffs",
      project_root / "logs" / "quality-gates",
      project_root / "logs" / "project-state",
    ]
    for directory in required_dirs:
        if not directory.exists():
            errors.append(f"missing-project-directory:{directory}")

    try:
        project_constraints = extract_agent_constraints(project_root / "AGENTS.md")
    except ValueError as exc:
        errors.append(f"AGENTS.md:{exc}")
        project_constraints = dict(DEFAULT_CONSTRAINTS)

    root_constraints = payload["root_constraints"]
    constraints = merge_constraints(root_constraints, project_constraints, mode_ranks)

    if set(project_constraints["require_review_for"]) - deliverable_types:
        errors.append("AGENTS require_review_for contains invalid deliverable types")
    for truth_source in project_constraints["project_truth_sources"]:
        try:
            normalize_relative_path(truth_source)
        except ValueError as exc:
            errors.append(f"AGENTS.md:invalid-project-truth-source:{truth_source}:{exc}")
    if (
        root_constraints["max_execution_mode"] is not None
        and project_constraints["max_execution_mode"] is not None
        and mode_ranks[project_constraints["max_execution_mode"]] > mode_ranks[root_constraints["max_execution_mode"]]
    ):
        errors.append("AGENTS.md:max_execution_mode expands root AGENTS constraint")

    project_agents: dict[str, dict] = {}
    agent_dir = project_root / ".codex" / "agents"
    if agent_dir.exists():
        for path in sorted(agent_dir.glob("*.json")):
            data = load_json(path)
            errors.extend(collect_schema_errors(data, schemas["project_agent"], path.name))
            agent_id = data.get("agent_id")
            if data.get("enabled") is False:
                continue
            if path.stem != agent_id:
                errors.append(f"project-agent-filename-mismatch:{path.name}")
            if agent_id in project_agents:
                errors.append(f"duplicate-project-agent:{agent_id}")
            project_agents[agent_id] = data

    effective: dict[str, dict] = {}
    for agent_id, data in project_agents.items():
        if agent_id not in registry:
            errors.append(f"project-agent-not-in-registry:{agent_id}")
            continue
        reg = registry[agent_id]
        subset = data.get("allowed_skills_mcp_subset")
        write_subset = data.get("write_scope_subset")
        max_mode = data.get("max_execution_mode")
        expected_outputs = data.get("expected_outputs")
        display_name = data.get("display_name")
        preferred_model = data.get("preferred_model")
        isolation_method = data.get("isolation_method")
        parallel_safe = data.get("parallel_safe")
        integration_review_required = data.get("integration_review_required")
        capability_tags_subset = data.get("capability_tags_subset")

        if subset is not None and (set(subset) - set(reg["allowed_skills_mcp"])):
            errors.append(f"{agent_id}: allowed_skills_mcp_subset expands registry permissions")
        if write_subset is not None and (set(write_subset) - set(reg["write_scope"])):
            errors.append(f"{agent_id}: write_scope_subset expands registry write scope")
        if max_mode is not None and modes["modes"][max_mode]["rank"] > modes["modes"][reg["max_execution_mode"]]["rank"]:
            errors.append(f"{agent_id}: max_execution_mode expands registry max_execution_mode")
        if (
            constraints["max_execution_mode"] is not None
            and max_mode is not None
            and mode_ranks[max_mode] > mode_ranks[constraints["max_execution_mode"]]
        ):
            errors.append(f"{agent_id}: max_execution_mode expands AGENTS constraint")
        if display_name is not None and (not isinstance(display_name, str) or not display_name.strip()):
            errors.append(f"{agent_id}: display_name must be a non-empty string when present")
        if preferred_model is not None and (not isinstance(preferred_model, str) or not preferred_model.strip()):
            errors.append(f"{agent_id}: preferred_model must be a non-empty string when present")
        if isolation_method is not None and isolation_method not in ISOLATION_RANKS:
            errors.append(f"{agent_id}: invalid isolation_method")
        if (
            isolation_method is not None
            and reg.get("isolation_method") in ISOLATION_RANKS
            and ISOLATION_RANKS[isolation_method] < ISOLATION_RANKS[reg["isolation_method"]]
        ):
            errors.append(f"{agent_id}: isolation_method expands registry isolation boundary")
        if parallel_safe is not None and not isinstance(parallel_safe, bool):
            errors.append(f"{agent_id}: parallel_safe must be boolean when present")
        if parallel_safe is True and not reg.get("parallel_safe", False):
            errors.append(f"{agent_id}: parallel_safe expands registry parallel boundary")
        if integration_review_required is not None and not isinstance(integration_review_required, bool):
            errors.append(f"{agent_id}: integration_review_required must be boolean when present")
        if integration_review_required is False and reg.get("integration_review_required", False):
            errors.append(f"{agent_id}: integration_review_required relaxes registry review boundary")
        if capability_tags_subset is not None:
            if not isinstance(capability_tags_subset, list) or any(not isinstance(x, str) or not x for x in capability_tags_subset):
                errors.append(f"{agent_id}: capability_tags_subset must be a string list when present")
            elif set(capability_tags_subset) - set(reg.get("capability_tags", [])):
                errors.append(f"{agent_id}: capability_tags_subset expands registry capability tags")

        effective_allowed = set(reg["allowed_skills_mcp"])
        if subset is not None:
            effective_allowed &= set(subset)
        effective_allowed -= set(constraints["forbid_skills_mcp"])

        effective_scope = set(reg["write_scope"])
        if write_subset is not None:
            effective_scope &= set(write_subset)
        effective_scope -= set(constraints["forbid_write_roots"])

        effective_required_review_for = set(reg["required_review_for"]) | set(constraints["require_review_for"])
        effective_isolation_method = stricter_isolation(reg.get("isolation_method"), isolation_method)
        effective_parallel_safe = bool(reg.get("parallel_safe", False))
        if parallel_safe is not None:
            effective_parallel_safe = effective_parallel_safe and parallel_safe
        effective_integration_review_required = bool(reg.get("integration_review_required", False))
        if integration_review_required is not None:
            effective_integration_review_required = effective_integration_review_required or integration_review_required
        effective_capability_tags = set(reg.get("capability_tags", []))
        if capability_tags_subset is not None:
            effective_capability_tags &= set(capability_tags_subset)

        if reg["role"] == "reviewer":
            if set(data.get("allowed_skills_mcp_subset") or []) - reviewer_allowlist:
                errors.append(f"{agent_id}: reviewer project subset exceeds reviewer allowlist")
            if write_subset != ["outputs/agent-runs/<run_id>/<agent_id>/"]:
                errors.append(f"{agent_id}: reviewer write_scope_subset must match canonical reviewer directory")
            if expected_outputs != [
                "review.<target_agent_id>.md",
                "gate.<target_agent_id>.json",
            ]:
                errors.append(f"{agent_id}: reviewer expected_outputs must be target-specific review/gate files")
            if effective_isolation_method is not None and ISOLATION_RANKS[effective_isolation_method] < ISOLATION_RANKS["isolated_subagent_context"]:
                errors.append(f"{agent_id}: reviewer isolation_method must be at least isolated_subagent_context")

        effective[agent_id] = {
            "display_name": (display_name or reg.get("display_name") or agent_id),
            "preferred_model": preferred_model or reg.get("preferred_model"),
            "allowed_skills_mcp": sorted(effective_allowed),
            "write_scope": sorted(effective_scope),
            "max_execution_mode": stricter_mode(
                stricter_mode(reg["max_execution_mode"], max_mode, mode_ranks),
                constraints["max_execution_mode"],
                mode_ranks,
            ),
            "isolation_method": effective_isolation_method,
            "parallel_safe": effective_parallel_safe,
            "integration_review_required": effective_integration_review_required,
            "capability_tags": sorted(effective_capability_tags),
            "required_review_for": sorted(effective_required_review_for),
            "control_bindings": reg["control_bindings"],
            "role": reg["role"],
        }

    canonical = payload["modes"]["canonical_paths"]
    dispatch_dir = project_root / ".codex" / "dispatch"
    if dispatch_dir.exists():
        for dispatch_path in sorted(dispatch_dir.glob("*.yaml")):
            dispatch = load_yaml(dispatch_path)
            errors.extend(collect_schema_errors(dispatch, schemas["dispatch"], dispatch_path.name))
            run_id = dispatch.get("run_id")
            agents = dispatch.get("agents", [])
            if not isinstance(agents, list) or not all(isinstance(x, str) for x in agents):
                errors.append(f"{dispatch_path.name}: invalid agents list")
                continue
            if substitute_template(canonical["dispatch_card"], run_id=run_id) != ".codex/dispatch/{}.yaml".format(run_id):
                warnings.append("canonical dispatch template substitution returned unexpected value")

            for field_name in ("agent_context_packet", "allowed_skills_mcp", "agent_output_path"):
                keys = set((dispatch.get(field_name) or {}).keys())
                if keys != set(agents):
                    errors.append(f"{dispatch_path.name}: {field_name} keys must equal agents[]")
            if "agent_display_names" in dispatch:
                keys = set((dispatch.get("agent_display_names") or {}).keys())
                if keys != set(agents):
                    errors.append(f"{dispatch_path.name}: agent_display_names keys must equal agents[]")

            review_agents = dispatch.get("review_agents", {})
            for target_agent_id, reviewer_agent_id in review_agents.items():
                if target_agent_id not in agents:
                    errors.append(f"{dispatch_path.name}: review_agents key {target_agent_id} not in agents")
                reviewer_effective = effective.get(reviewer_agent_id)
                if reviewer_effective is None or reviewer_effective["role"] != "reviewer":
                    errors.append(f"{dispatch_path.name}: review_agents value {reviewer_agent_id} is not a reviewer agent")

            handoff_log = dispatch.get("handoff_log")
            gate_log = dispatch.get("gate_log")
            project_state_path = dispatch.get("project_state_path")
            project_state_history_log = dispatch.get("project_state_history_log")
            try:
                if normalize_relative_path(handoff_log) != substitute_template(canonical["handoff_log"], run_id=run_id):
                    errors.append(f"{dispatch_path.name}: handoff_log must match canonical path")
                if normalize_relative_path(gate_log) != substitute_template(canonical["gate_log"], run_id=run_id):
                    errors.append(f"{dispatch_path.name}: gate_log must match canonical path")
                if project_state_path is not None and normalize_relative_path(project_state_path) != normalize_relative_path(canonical["project_state_current"]):
                    errors.append(f"{dispatch_path.name}: project_state_path must match canonical path")
                if project_state_history_log is not None and normalize_relative_path(project_state_history_log) != normalize_relative_path(canonical["project_state_history"]):
                    errors.append(f"{dispatch_path.name}: project_state_history_log must match canonical path")
            except Exception as exc:
                errors.append(f"{dispatch_path.name}: invalid log path: {exc}")

            if project_state_path is not None and not (project_root / project_state_path).exists():
                errors.append(f"{dispatch_path.name}: project_state_path file is missing")
            if project_state_history_log is not None and not (project_root / project_state_history_log).exists():
                errors.append(f"{dispatch_path.name}: project_state_history_log file is missing")

            for agent_id in agents:
                if agent_id not in effective:
                    errors.append(f"{dispatch_path.name}: agent {agent_id} missing project definition")
                    continue
                try:
                    context_path = normalize_relative_path(dispatch["agent_context_packet"][agent_id])
                    expected_context = substitute_template(canonical["context_packet"], run_id=run_id, agent_id=agent_id)
                    if context_path != expected_context:
                        errors.append(f"{dispatch_path.name}: context packet for {agent_id} must match canonical path")
                    output_path = normalize_relative_path(dispatch["agent_output_path"][agent_id])
                    expected_output = substitute_template(canonical["agent_output_dir"], run_id=run_id, agent_id=agent_id)
                    if output_path != expected_output:
                        errors.append(f"{dispatch_path.name}: output path for {agent_id} must match canonical path")
                    if not path_in_scope(output_path, effective[agent_id]["write_scope"]):
                        errors.append(f"{dispatch_path.name}: output path for {agent_id} escapes effective_write_scope")
                except Exception as exc:
                    errors.append(f"{dispatch_path.name}: invalid path for {agent_id}: {exc}")

                allowed_subset = set(dispatch["allowed_skills_mcp"][agent_id])
                if not allowed_subset <= set(effective[agent_id]["allowed_skills_mcp"]):
                    errors.append(f"{dispatch_path.name}: allowed_skills_mcp for {agent_id} exceeds effective permissions")

                output_dir = project_root / dispatch["agent_output_path"][agent_id]
                if effective[agent_id]["role"] != "reviewer":
                    summary_path = output_dir / "summary.md"
                    result_path = output_dir / "result.json"
                    if not summary_path.exists() or not result_path.exists():
                        if mode == "bootstrap":
                            continue
                        errors.append(f"{dispatch_path.name}: producer {agent_id} is missing canonical completion files")
                        continue
                    result = load_json(result_path)
                    if set(result.get("produced_deliverable_types", [])) - deliverable_types:
                        errors.append(f"{dispatch_path.name}: {agent_id} result.json has invalid deliverable types")
                    for produced_file in result.get("produced_files", []):
                        if not path_in_scope(produced_file, effective[agent_id]["write_scope"]):
                            errors.append(f"{dispatch_path.name}: {agent_id} produced file escapes effective_write_scope")
                    target_reviews = set(result.get("produced_deliverable_types", [])) & set(effective[agent_id]["required_review_for"])
                    if target_reviews:
                        reviewer_agent_id = review_agents.get(agent_id)
                        if not reviewer_agent_id:
                            errors.append(f"{dispatch_path.name}: {agent_id} requires review but has no review_agents mapping")
                            continue
                        review_output_dir = project_root / dispatch["agent_output_path"][reviewer_agent_id]
                        review_file = review_output_dir / f"review.{agent_id}.md"
                        gate_file = review_output_dir / f"gate.{agent_id}.json"
                        if not review_file.exists() or not gate_file.exists():
                            if mode == "bootstrap":
                                continue
                            errors.append(f"{dispatch_path.name}: missing target-specific review artifacts for {agent_id}")
                            continue
                        gate = load_json(gate_file)
                        if gate.get("decision") != "pass":
                            if mode == "bootstrap":
                                continue
                            errors.append(f"{dispatch_path.name}: gate for {agent_id} must pass before handoff or next stage")
                else:
                    for target_agent_id in review_agents:
                        if review_agents.get(target_agent_id) == agent_id:
                            review_file = output_dir / f"review.{target_agent_id}.md"
                            gate_file = output_dir / f"gate.{target_agent_id}.json"
                            if not review_file.exists() or not gate_file.exists():
                                if mode == "bootstrap":
                                    continue
                                errors.append(f"{dispatch_path.name}: reviewer {agent_id} missing target-specific artifacts for {target_agent_id}")

    return errors, warnings


def build_agent_contract_result(project_root: Path | None = None, *, mode: str = "project") -> dict:
    errors, warnings, payload = validate_static_contract()
    project_errors: list[str] = []
    project_warnings: list[str] = []
    project_preflight: dict | None = None

    if project_root:
        project_preflight = collect_project_contract_preflight(project_root)
        if project_preflight["ok"]:
            project_errors, project_warnings = validate_project(project_root, payload, mode=mode)
        else:
            project_errors = list(project_preflight["errors"])

    compatibility = {
        "static_errors": errors,
        "static_warnings": warnings,
        "project_errors": project_errors,
        "project_warnings": project_warnings,
    }
    if project_preflight is not None:
        compatibility["project_contract_preflight"] = project_preflight
    report = build_validator_result(
        validator="validate_agents_contract",
        scope="project" if project_root else "static",
        errors=errors + project_errors,
        warnings=warnings + project_warnings,
        details=compatibility,
        compatibility=compatibility,
    )
    return report
