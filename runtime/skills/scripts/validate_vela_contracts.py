from __future__ import annotations



import json

import re

import sys

from pathlib import Path

from typing import Any



try:

    from .envctl.validator_envelope import build_validator_result, exit_code_for_result

    from .envctl.schema_validation import collect_schema_document_errors, collect_schema_errors

    from .path_utils import CATALOG_ROOT, SCHEMAS_ROOT

except ImportError:

    from envctl.validator_envelope import build_validator_result, exit_code_for_result

    from envctl.schema_validation import collect_schema_document_errors, collect_schema_errors

    from path_utils import CATALOG_ROOT, SCHEMAS_ROOT





PLAYBOOK_PATH = CATALOG_ROOT / "research_team_playbooks.json"

PROJECT_INITIALIZER_PATH = CATALOG_ROOT / "project_initializer_manifest.json"



SCHEMA_EXPECTATIONS = {

    "vela_codex_handoff": {

        "path": SCHEMAS_ROOT / "vela.codex.handoff.v1.schema.json",

        "id": "https://marcus-ai4ss.github.io/VELA/schemas/vela.codex.handoff.v1.schema.json",

        "schema_version": "vela.codex.handoff.v1",

    },

    "vela_project_context": {

        "path": SCHEMAS_ROOT / "vela.project.context.v1.schema.json",

        "id": "https://marcus-ai4ss.github.io/VELA/schemas/vela.project.context.v1.schema.json",

        "schema_version": "vela.project.context.v1",

    },

    "helm_codex_handoff": {

        "path": SCHEMAS_ROOT / "helm.codex.handoff.v1.schema.json",

        "id": "https://marcus-ai4ss.github.io/VELA/schemas/helm.codex.handoff.v1.schema.json",

        "schema_version": "helm.codex.handoff.v1",

    },

    "helm_app_command": {

        "path": SCHEMAS_ROOT / "helm.app.command.v1.schema.json",

        "id": "https://marcus-ai4ss.github.io/VELA/schemas/helm.app.command.v1.schema.json",

        "schema_version": "helm.app.command.v1",

    },

    "research_team_playbook": {

        "path": SCHEMAS_ROOT / "research_team_playbook.schema.json",

        "id": "https://marcus-ai4ss.github.io/VELA/schemas/research_team_playbook.schema.json",

        "schema_version": "research_team_playbook.v1",

    },

    "project_initializer_manifest": {

        "path": SCHEMAS_ROOT / "project_initializer_manifest.schema.json",

        "id": "https://marcus-ai4ss.github.io/VELA/schemas/project_initializer_manifest.schema.json",

        "schema_version": "project_initializer_manifest.v1",

    },

    "clarification_card": {

        "path": SCHEMAS_ROOT / "clarification_card.schema.json",

        "id": "https://marcus-ai4ss.github.io/VELA/schemas/clarification_card.schema.json",

        "schema_version": None,

    },

    "team_plan_result": {

        "path": SCHEMAS_ROOT / "team_plan_result.schema.json",

        "id": "https://marcus-ai4ss.github.io/VELA/schemas/team_plan_result.schema.json",

        "schema_version": None,

    },

    "validator_result": {

        "path": SCHEMAS_ROOT / "validator_result.schema.json",

        "id": "https://marcus-ai4ss.github.io/VELA/schemas/validator_result.schema.json",

        "schema_version": None,

    },

    "helm_snapshot_manifest": {

        "path": SCHEMAS_ROOT / "helm_snapshot_manifest.schema.json",

        "id": "https://marcus-ai4ss.github.io/VELA/schemas/helm_snapshot_manifest.schema.json",

        "schema_version": "helm_snapshot_manifest.v1",

    },

}





def load_json(path: Path) -> dict[str, Any]:

    return json.loads(path.read_text(encoding="utf-8"))





def _schema_version_const(schema: dict[str, Any]) -> str | None:

    return schema.get("properties", {}).get("schema_version", {}).get("const")





def _validate_schema_inventory() -> tuple[list[str], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:

    errors: list[str] = []

    schema_report: dict[str, dict[str, Any]] = {}

    loaded_schemas: dict[str, dict[str, Any]] = {}



    for name, expectation in SCHEMA_EXPECTATIONS.items():

        path = expectation["path"]

        if not path.exists():

            errors.append(f"missing-schema:{path.name}")

            schema_report[name] = {"exists": False}

            continue

        schema = load_json(path)

        loaded_schemas[name] = schema

        errors.extend(collect_schema_document_errors(schema, path.name))

        if schema.get("$id") != expectation["id"]:

            errors.append(f"{path.name}:unexpected-$id")

        expected_version = expectation["schema_version"]

        actual_version = _schema_version_const(schema)

        if expected_version is not None and actual_version != expected_version:

            errors.append(f"{path.name}:unexpected-schema_version-const")

        if schema.get("type") != "object":

            errors.append(f"{path.name}:root-type-must-be-object")

        schema_report[name] = {

            "exists": True,

            "id": schema.get("$id"),

            "schema_version": actual_version,

        }

    return errors, schema_report, loaded_schemas





def _is_safe_relative_path(path_value: str) -> bool:

    if not isinstance(path_value, str) or not path_value.strip():

        return False

    if "\\" in path_value or path_value.startswith("/") or re.match(r"^[A-Za-z]:", path_value):

        return False

    parts = [part for part in path_value.split("/") if part]

    return bool(parts) and all(part not in {".", ".."} for part in parts)





def _condition_values(group: dict[str, Any], field: str) -> set[str]:

    return set(group.get(field) or [])





def _validate_playbooks(

    schemas: dict[str, dict[str, Any]],

    routing: dict[str, Any],

    registry: dict[str, Any],

    scope_rules: dict[str, Any],

) -> tuple[list[str], list[str], dict[str, Any]]:

    errors: list[str] = []

    warnings: list[str] = []

    if not PLAYBOOK_PATH.exists():

        return ["missing-catalog:research_team_playbooks.json"], warnings, {"playbook_count": 0, "playbook_routes": []}



    playbooks = load_json(PLAYBOOK_PATH)

    schema = schemas.get("research_team_playbook")

    if schema:

        errors.extend(collect_schema_errors(playbooks, schema, PLAYBOOK_PATH.name))



    route_ids = {route.get("id") for route in routing.get("routes", [])}

    agent_ids = {agent.get("agent_id") for agent in registry.get("agents", [])}

    enums = scope_rules.get("enums", {})

    deliverable_types = set(enums.get("deliverable_types", []))

    work_units = set(enums.get("work_units", []))

    sync_targets = set(enums.get("sync_targets", []))

    explicit_modes = set(enums.get("explicit_project_mode", []))

    project_routes = set(scope_rules.get("route_scope", {}).get("always_multi_agent", [])) | set(

        scope_rules.get("route_scope", {}).get("conditional_multi_agent", [])

    )



    seen_routes: set[str] = set()

    items = playbooks.get("playbooks", [])

    if not isinstance(items, list):

        items = []



    for index, playbook in enumerate(items):

        if not isinstance(playbook, dict):

            continue

        route_id = playbook.get("route_id")

        if not isinstance(route_id, str):

            errors.append(f"playbook-missing-route_id:{index}")

            continue

        if route_id in seen_routes:

            errors.append(f"duplicate-playbook-route:{route_id}")

        seen_routes.add(route_id)

        if route_id not in route_ids:

            errors.append(f"{route_id}:route-not-in-routing-table")



        default_agents = playbook.get("default_agents", [])

        optional_agents = [item.get("agent_id") for item in playbook.get("optional_agents", []) if isinstance(item, dict)]

        known_playbook_agents = set(default_agents) | set(optional_agents)

        unknown_agents = sorted(known_playbook_agents - agent_ids)

        if unknown_agents:

            errors.append(f"{route_id}:unknown-agents:{unknown_agents}")



        unknown_outputs = sorted(set(playbook.get("primary_outputs", [])) - deliverable_types)

        if unknown_outputs:

            errors.append(f"{route_id}:unknown-primary-outputs:{unknown_outputs}")



        for optional_agent in playbook.get("optional_agents", []):

            if not isinstance(optional_agent, dict):

                continue

            for group in optional_agent.get("include_when", {}).get("any_of", []):

                unknown_route_ids = sorted(_condition_values(group, "route_id_is") - route_ids)

                unknown_work_units = sorted(_condition_values(group, "work_units_contains_any") - work_units)

                unknown_deliverables = sorted(_condition_values(group, "deliverable_types_contains_any") - deliverable_types)

                unknown_sync_targets = sorted(_condition_values(group, "sync_targets_contains_any") - sync_targets)

                unknown_modes = sorted(_condition_values(group, "explicit_project_mode_is") - explicit_modes)

                if unknown_route_ids:

                    errors.append(f"{route_id}:{optional_agent.get('agent_id')}:unknown-route-conditions:{unknown_route_ids}")

                if unknown_work_units:

                    errors.append(f"{route_id}:{optional_agent.get('agent_id')}:unknown-work-unit-conditions:{unknown_work_units}")

                if unknown_deliverables:

                    errors.append(f"{route_id}:{optional_agent.get('agent_id')}:unknown-deliverable-conditions:{unknown_deliverables}")

                if unknown_sync_targets:

                    errors.append(f"{route_id}:{optional_agent.get('agent_id')}:unknown-sync-target-conditions:{unknown_sync_targets}")

                if unknown_modes:

                    errors.append(f"{route_id}:{optional_agent.get('agent_id')}:unknown-explicit-mode-conditions:{unknown_modes}")



        for item in playbook.get("review_chain", []):

            if not isinstance(item, dict):

                continue

            producer = item.get("producer")

            reviewer = item.get("reviewer")

            if producer not in known_playbook_agents or reviewer not in known_playbook_agents:

                errors.append(f"{route_id}:review-chain-agent-outside-playbook:{producer}->{reviewer}")



    missing_project_routes = sorted(project_routes - seen_routes)

    if missing_project_routes:

        errors.append(f"project-routes-missing-playbooks:{missing_project_routes}")



    return errors, warnings, {"playbook_count": len(items), "playbook_routes": sorted(seen_routes)}





def _validate_project_initializer_manifest(schemas: dict[str, dict[str, Any]], registry: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:

    errors: list[str] = []

    warnings: list[str] = []

    if not PROJECT_INITIALIZER_PATH.exists():

        return ["missing-catalog:project_initializer_manifest.json"], warnings, {"project_initializer_files": 0, "project_initializer_agents": 0}



    manifest = load_json(PROJECT_INITIALIZER_PATH)

    manifest_schema = schemas.get("project_initializer_manifest")

    project_agent_schema = load_json(SCHEMAS_ROOT / "project_agent_definition.schema.json")

    if manifest_schema:

        errors.extend(collect_schema_errors(manifest, manifest_schema, PROJECT_INITIALIZER_PATH.name))



    for path_value in manifest.get("directories", []):

        if not _is_safe_relative_path(path_value):

            errors.append(f"project-initializer:unsafe-directory:{path_value}")

    for item in manifest.get("files", []):

        if not isinstance(item, dict):

            continue

        path_value = item.get("path")

        if not _is_safe_relative_path(path_value):

            errors.append(f"project-initializer:unsafe-file:{path_value}")



    agent_ids = {agent.get("agent_id") for agent in registry.get("agents", [])}

    for file_name, payload in manifest.get("project_agents", {}).items():

        if not _is_safe_relative_path(f".codex/agents/{file_name}"):

            errors.append(f"project-initializer:unsafe-agent-file:{file_name}")

        errors.extend(collect_schema_errors(payload, project_agent_schema, f"project_initializer:{file_name}"))

        agent_id = payload.get("agent_id")

        if file_name != f"{agent_id}.json":

            errors.append(f"project-initializer:agent-filename-mismatch:{file_name}")

        if agent_id not in agent_ids:

            errors.append(f"project-initializer:unknown-agent:{agent_id}")



    return errors, warnings, {

        "project_initializer_files": len(manifest.get("files", [])),

        "project_initializer_agents": len(manifest.get("project_agents", {})),

    }





def collect_contract_errors() -> tuple[list[str], list[str], dict[str, Any]]:

    errors: list[str] = []

    warnings: list[str] = []



    schema_errors, schema_report, schemas = _validate_schema_inventory()

    errors.extend(schema_errors)



    routing = load_json(CATALOG_ROOT / "routing_table.json")

    registry = load_json(CATALOG_ROOT / "subagent_registry.json")

    scope_rules = load_json(CATALOG_ROOT / "project_scope_rules.json")



    playbook_errors, playbook_warnings, playbook_report = _validate_playbooks(schemas, routing, registry, scope_rules)

    initializer_errors, initializer_warnings, initializer_report = _validate_project_initializer_manifest(schemas, registry)

    errors.extend(playbook_errors)

    warnings.extend(playbook_warnings)

    errors.extend(initializer_errors)

    warnings.extend(initializer_warnings)



    report = {

        "schemas": schema_report,

        **playbook_report,

        **initializer_report,

    }

    return errors, warnings, report





def main() -> None:

    errors, warnings, payload = collect_contract_errors()

    report = build_validator_result(

        validator="validate_vela_contracts",

        scope="contracts",

        errors=errors,

        warnings=warnings,

        details=payload,

        compatibility=payload,

    )

    print(json.dumps(report, ensure_ascii=False, indent=2))

    sys.exit(exit_code_for_result(report))





if __name__ == "__main__":

    main()
