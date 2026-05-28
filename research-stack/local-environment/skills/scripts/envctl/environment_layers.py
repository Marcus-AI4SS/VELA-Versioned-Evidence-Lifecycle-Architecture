from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from ..path_utils import CATALOG_ROOT, SCHEMAS_ROOT, SKILLS_ROOT
    from .schema_validation import collect_schema_document_errors, collect_schema_errors, load_json
    from .validator_envelope import build_validator_result
except ImportError:  # pragma: no cover
    from path_utils import CATALOG_ROOT, SCHEMAS_ROOT, SKILLS_ROOT
    from envctl.schema_validation import collect_schema_document_errors, collect_schema_errors, load_json
    from envctl.validator_envelope import build_validator_result


CONTRACT_PATH = CATALOG_ROOT / "environment_layer_contract.json"
SCHEMA_PATH = SCHEMAS_ROOT / "environment_layer_contract.v1.schema.json"
ROUTING_PATH = CATALOG_ROOT / "routing_table.json"
SKILL_CATALOG_PATH = CATALOG_ROOT / "skill_catalog.json"
ROUTE_MCP_POLICY_PATH = CATALOG_ROOT / "route_mcp_activation_policy.json"
CONFLICT_MATRIX_PATH = CATALOG_ROOT / "conflict_matrix.json"
LOCAL_MEMORY_PATH = CATALOG_ROOT / "local_memory_system.json"
CONTROL_KERNEL_PATH = CATALOG_ROOT / "control_kernel.json"

LAYER_ORDER = [
    "execution",
    "tool",
    "context",
    "lifecycle",
    "observability",
    "verification",
    "governance",
]
REQUIRED_MEMORY_INTERFACES = {
    "keyword_search",
    "semantic_search_optional_dry_run",
    "cross_session_context_injection_gated",
    "confidence_evaluation",
    "decision_archive",
    "task_tracking",
    "memory_cleanup",
    "conversation_snapshot",
    "task_status",
    "memory_list_delete",
    "agentmemory_smart_search",
    "agentmemory_session_history",
    "agentmemory_governance_delete",
    "codegraph_context_index",
}
RUNTIME_TOOL_SAFETY_TERMS = {
    "agentmemory": {
        "write_scope": [".agentmemory"],
        "forbidden": ["source rules", "auto-promote", "secrets"],
        "delete_policy": ["confirmation", "audit"],
        "source_policy": ["runtime recall", "source of truth"],
    },
    "codegraph": {
        "write_scope": [".codegraph"],
        "forbidden": ["change source files", "replace rg", "source-of-truth"],
        "delete_policy": [".codegraph", "source files"],
        "source_policy": ["index", "authoritative"],
    },
}


def _safe_load(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"{label}:missing:{path}")
        return {}
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"{label}:invalid-json:{exc}")
        return {}


def validate_environment_layer_contract() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    schema = _safe_load(SCHEMA_PATH, "environment_layer_contract.schema", errors)
    contract = _safe_load(CONTRACT_PATH, "environment_layer_contract", errors)
    routing = _safe_load(ROUTING_PATH, "routing_table", errors)
    skill_catalog = _safe_load(SKILL_CATALOG_PATH, "skill_catalog", errors)
    route_mcp_policy = _safe_load(ROUTE_MCP_POLICY_PATH, "route_mcp_activation_policy", errors)
    conflict_matrix = _safe_load(CONFLICT_MATRIX_PATH, "conflict_matrix", errors)
    memory = _safe_load(LOCAL_MEMORY_PATH, "local_memory_system", errors)
    kernel = _safe_load(CONTROL_KERNEL_PATH, "control_kernel", errors)

    if schema:
        errors.extend(collect_schema_document_errors(schema, "environment_layer_contract.schema"))
    if schema and contract:
        errors.extend(collect_schema_errors(contract, schema, "environment_layer_contract"))
    if contract:
        errors.extend(_collect_layer_contract_errors(contract, routing, skill_catalog))
        errors.extend(_collect_tool_contract_errors(contract, routing, route_mcp_policy))
        errors.extend(_collect_memory_contract_errors(contract, memory))
        errors.extend(_collect_governance_contract_errors(contract, conflict_matrix, kernel))

    details = {
        "contract": str(CONTRACT_PATH.relative_to(SKILLS_ROOT)),
        "schema": str(SCHEMA_PATH.relative_to(SKILLS_ROOT)),
        "layer_order": contract.get("layer_order", []),
        "route_count": len(contract.get("route_layer_map", [])),
        "skill_count": len(contract.get("skill_layer_map", [])),
        "tool_count": len(contract.get("tool_inventory", [])),
        "memory_adapter": memory.get("runtime_adapter_policy", {}).get("selected_adapter"),
        "agentmemory_enabled": _agentmemory_enabled(memory),
        "codegraph_listed": any(
            item.get("id") == "codegraph"
            for item in contract.get("tool_inventory", [])
            if isinstance(item, dict)
        ),
    }
    return build_validator_result(
        validator="validate_environment_layer_contract",
        scope="environment_layers",
        errors=errors,
        warnings=warnings,
        details=details,
    )


def _collect_layer_contract_errors(
    contract: dict[str, Any],
    routing: dict[str, Any],
    skill_catalog: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if contract.get("layer_order") != LAYER_ORDER:
        errors.append(f"environment_layers:unexpected-layer-order:{contract.get('layer_order')}")
    layer_ids = [item.get("id") for item in contract.get("layers", []) if isinstance(item, dict)]
    for layer_id, count in Counter(layer_ids).items():
        if count > 1:
            errors.append(f"environment_layers:duplicate-layer:{layer_id}")
    missing_layers = set(LAYER_ORDER) - set(layer_ids)
    errors.extend(f"environment_layers:missing-layer:{item}" for item in sorted(missing_layers))

    routes = {route.get("id") for route in routing.get("routes", []) if isinstance(route, dict)}
    route_maps = {
        item.get("route_id"): item
        for item in contract.get("route_layer_map", [])
        if isinstance(item, dict)
    }
    errors.extend(
        f"environment_layers:missing-route-map:{item}"
        for item in sorted(routes - set(route_maps))
    )
    errors.extend(
        f"environment_layers:extra-route-map:{item}"
        for item in sorted(set(route_maps) - routes)
    )
    for route_id, item in sorted(route_maps.items()):
        required_layers = set(item.get("required_layers", []))
        missing_required = set(LAYER_ORDER) - required_layers
        errors.extend(
            f"environment_layers:{route_id}:missing-required-layer:{layer_id}"
            for layer_id in sorted(missing_required)
        )

    active_skills = {
        name
        for name, item in skill_catalog.get("skills", {}).items()
        if isinstance(item, dict) and item.get("status") == "active"
    }
    entry_skills = sorted(
        name
        for name, item in skill_catalog.get("skills", {}).items()
        if isinstance(item, dict)
        and item.get("status") == "active"
        and (item.get("entry") is True or item.get("role") == "entry")
    )
    if entry_skills != ["research-autopilot"]:
        errors.append(f"environment_layers:non-unique-total-entry:{entry_skills}")
    skill_maps = {
        item.get("skill_id"): item
        for item in contract.get("skill_layer_map", [])
        if isinstance(item, dict)
    }
    errors.extend(
        f"environment_layers:missing-skill-map:{item}"
        for item in sorted(active_skills - set(skill_maps))
    )
    errors.extend(
        f"environment_layers:extra-skill-map:{item}"
        for item in sorted(set(skill_maps) - active_skills)
    )
    for skill_id, item in sorted(skill_maps.items()):
        all_layers = {item.get("primary_layer")} | set(item.get("secondary_layers", []))
        unknown = sorted(all_layers - set(LAYER_ORDER))
        errors.extend(f"environment_layers:{skill_id}:unknown-layer:{layer_id}" for layer_id in unknown)
        if item.get("role") == "entry" and skill_id != "research-autopilot":
            errors.append(f"environment_layers:non-autopilot-entry-skill-map:{skill_id}")
    return errors


def _collect_tool_contract_errors(
    contract: dict[str, Any],
    routing: dict[str, Any],
    route_mcp_policy: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    tool_ids = [
        item.get("id")
        for item in contract.get("tool_inventory", [])
        if isinstance(item, dict)
    ]
    tools = {
        item.get("id"): item
        for item in contract.get("tool_inventory", [])
        if isinstance(item, dict)
    }
    for tool_id, count in Counter(tool_ids).items():
        if count > 1:
            errors.append(f"environment_layers:duplicate-tool:{tool_id}")
    route_mcp = {
        mcp
        for route in routing.get("routes", [])
        if isinstance(route, dict)
        for mcp in route.get("mcp", [])
    }
    errors.extend(
        f"environment_layers:route-mcp-missing-from-tool-inventory:{item}"
        for item in sorted(route_mcp - set(tools))
    )
    for expected in ["agentmemory", "codegraph"]:
        if expected not in tools:
            errors.append(f"environment_layers:missing-runtime-tool:{expected}")
            continue
        controls = tools[expected].get("safety_controls")
        if not isinstance(controls, dict):
            errors.append(f"environment_layers:{expected}:missing-safety-controls")
            continue
        allowed_scope = " ".join(controls.get("allowed_write_scope", []))
        forbidden = " ".join(controls.get("forbidden_actions", []))
        delete_policy = str(controls.get("delete_policy", ""))
        source_policy = str(controls.get("source_of_truth_policy", ""))
        for phrase in RUNTIME_TOOL_SAFETY_TERMS[expected]["write_scope"]:
            if phrase not in allowed_scope:
                errors.append(f"environment_layers:{expected}:missing-write-scope:{phrase}")
        for phrase in RUNTIME_TOOL_SAFETY_TERMS[expected]["forbidden"]:
            if phrase not in forbidden:
                errors.append(f"environment_layers:{expected}:missing-forbidden-action:{phrase}")
        for phrase in RUNTIME_TOOL_SAFETY_TERMS[expected]["delete_policy"]:
            if phrase not in delete_policy:
                errors.append(f"environment_layers:{expected}:missing-delete-policy:{phrase}")
        for phrase in RUNTIME_TOOL_SAFETY_TERMS[expected]["source_policy"]:
            if phrase not in source_policy:
                errors.append(f"environment_layers:{expected}:missing-source-policy:{phrase}")
    policy_mcp = {
        mcp
        for route in route_mcp_policy.get("routes", [])
        if isinstance(route, dict)
        for field in ["required_mcp", "optional_mcp", "activation_needed_mcp"]
        for mcp in route.get(field, [])
    }
    errors.extend(
        f"environment_layers:policy-mcp-missing-from-tool-inventory:{item}"
        for item in sorted(policy_mcp - set(tools))
    )
    return errors


def _collect_memory_contract_errors(contract: dict[str, Any], memory: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    mem = contract.get("memory_optimization", {})
    if mem.get("decision") != "adopt_runtime_adapter":
        errors.append(f"environment_layers:memory-decision-not-runtime-adapter:{mem.get('decision')}")
    missing_interfaces = REQUIRED_MEMORY_INTERFACES - set(mem.get("required_interfaces", []))
    errors.extend(
        f"environment_layers:memory-missing-required-interface:{item}"
        for item in sorted(missing_interfaces)
    )
    local_retrieval = set(memory.get("retrieval_policy", {}).get("enabled_interfaces", []))
    missing_local = REQUIRED_MEMORY_INTERFACES - local_retrieval
    errors.extend(
        f"environment_layers:local-memory-missing-required-interface:{item}"
        for item in sorted(missing_local)
    )
    runtime = memory.get("runtime_adapter_policy", {})
    if runtime.get("selected_adapter") != "agentmemory":
        errors.append(f"environment_layers:runtime-adapter-not-agentmemory:{runtime.get('selected_adapter')}")
    if runtime.get("status") != "enabled":
        errors.append(f"environment_layers:runtime-adapter-not-enabled:{runtime.get('status')}")
    data_root = str(runtime.get("data_root", "")).replace("\\", "/").lower()
    if "skills-environment-local" in data_root:
        errors.append(f"environment_layers:agentmemory-data-inside-source-tree:{runtime.get('data_root')}")
    runtime_text = " ".join(runtime.get("forbidden_actions", []))
    for phrase in ["auto-promote runtime memory", "full transcript import", "secrets"]:
        if phrase not in runtime_text:
            errors.append(f"environment_layers:runtime-missing-forbidden-action:{phrase}")
    return errors


def _collect_governance_contract_errors(
    contract: dict[str, Any],
    conflict_matrix: dict[str, Any],
    kernel: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected_ref = "skills/catalog/control_kernel.json"
    if contract.get("core_methodology_ref") != expected_ref:
        errors.append(f"environment_layers:unexpected-control-kernel-ref:{contract.get('core_methodology_ref')}")
    controller_ids = {
        item.get("id")
        for item in kernel.get("controllers", [])
        if isinstance(item, dict)
    }
    if "research-autopilot" not in controller_ids:
        errors.append("environment_layers:missing-research-autopilot-controller")
    serialized_conflicts = json.dumps(conflict_matrix, ensure_ascii=False)
    if "route-confirmation-before-new-chain" not in serialized_conflicts:
        errors.append("environment_layers:missing-route-confirmation-conflict-rule")
    assertions = set(contract.get("governance_assertions", []))
    for item in [
        "research-autopilot remains the only total router",
        "engineering cybernetics remains the core methodology and control kernel",
        "agentmemory recall candidates must be scored, reviewed, and routed before becoming durable rules",
        "codegraph is a code-context cache and not a governance authority",
    ]:
        if item not in assertions:
            errors.append(f"environment_layers:missing-governance-assertion:{item}")
    return errors


def _agentmemory_enabled(memory: dict[str, Any]) -> bool:
    runtime = memory.get("runtime_adapter_policy", {})
    return runtime.get("selected_adapter") == "agentmemory" and runtime.get("status") == "enabled"
