from __future__ import annotations



import json

from datetime import datetime

from pathlib import Path

from typing import Any



import yaml



try:

    from .agent_contracts import (

        collect_project_contract_preflight,

        extract_agent_constraints,

        load_json,

        merge_constraints,

        normalize_relative_path,

        stricter_isolation,

        stricter_mode,

        substitute_template,

        validate_project,

        validate_static_contract,

    )

    from .project_initializer import ensure_project_contract

    from .validator_envelope import build_validator_result

    from ..path_utils import CATALOG_ROOT, SKILLS_ROOT

except ImportError:  # pragma: no cover

    from envctl.agent_contracts import (

        collect_project_contract_preflight,

        extract_agent_constraints,

        load_json,

        merge_constraints,

        normalize_relative_path,

        stricter_isolation,

        stricter_mode,

        substitute_template,

        validate_project,

        validate_static_contract,

    )

    from envctl.project_initializer import ensure_project_contract

    from envctl.validator_envelope import build_validator_result

    from path_utils import CATALOG_ROOT, SKILLS_ROOT





ROOT = SKILLS_ROOT

CATALOG = CATALOG_ROOT





def read_json_if_exists(path: Path) -> dict[str, Any]:

    if not path.exists():

        return {}

    return json.loads(path.read_text(encoding="utf-8"))





def write_json(path: Path, payload: dict[str, Any]) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")





def load_route(route_id: str) -> dict[str, Any]:

    routing = load_json(CATALOG / "routing_table.json")

    for route in routing.get("routes", []):

        if route["id"] == route_id:

            return route

    raise KeyError(f"Unknown route_id: {route_id}")





def pipeline_default_stage(route_id: str) -> str:

    stages = load_json(CATALOG / "research_pipeline_stages.json")

    sequence = stages.get("route_stage_sequences", {}).get(route_id, [])

    return sequence[0] if sequence else "research_design"





def required_gates_for_stage(route_id: str, stage_id: str) -> list[str]:

    stages = load_json(CATALOG / "research_pipeline_stages.json")

    base = list(stages.get("required_stage_gates", {}).get(stage_id, []))

    override = stages.get("route_stage_gate_overrides", {}).get(route_id, {}).get(stage_id, [])

    result: list[str] = []

    for gate_id in base + list(override):

        if gate_id not in result:

            result.append(gate_id)

    return result





def sync_pipeline_files(project_root: Path, route_id: str) -> tuple[dict[str, Any], dict[str, Any]]:

    material_passport_path = project_root / "material-passport.yaml"

    pipeline_status_path = project_root / "logs" / "quality-gates" / "pipeline-status.json"

    default_stage = pipeline_default_stage(route_id)

    route_sequence = load_json(CATALOG / "research_pipeline_stages.json").get("route_stage_sequences", {}).get(route_id, [])



    material_passport = yaml.safe_load(material_passport_path.read_text(encoding="utf-8")) if material_passport_path.exists() else {}

    material_passport = material_passport or {}

    if material_passport.get("route_id") != route_id:

        material_passport["route_id"] = route_id

    if not material_passport.get("current_stage") or (route_sequence and material_passport.get("current_stage") not in route_sequence):

        material_passport["current_stage"] = default_stage

    if not material_passport.get("truth_sources"):

        material_passport["truth_sources"] = [

            "research-map.md",

            "findings-memory.md",

            "material-passport.yaml",

            "evidence-ledger.yaml",

        ]

    material_passport_path.write_text(yaml.safe_dump(material_passport, sort_keys=False, allow_unicode=True), encoding="utf-8")



    pipeline_status = read_json_if_exists(pipeline_status_path)

    if not pipeline_status:

        pipeline_status = {

            "route_id": route_id,

            "current_stage": material_passport["current_stage"],

            "completed_stages": [],

            "gate_decisions": {},

            "allowed_to_advance": False,

        }

    else:

        if pipeline_status.get("route_id") != route_id:

            pipeline_status["route_id"] = route_id

        if not pipeline_status.get("current_stage") or (route_sequence and pipeline_status.get("current_stage") not in route_sequence):

            pipeline_status["current_stage"] = material_passport["current_stage"]

        pipeline_status.setdefault("completed_stages", [])

        pipeline_status.setdefault("gate_decisions", {})

        pipeline_status.setdefault("allowed_to_advance", False)

    write_json(pipeline_status_path, pipeline_status)

    return material_passport, pipeline_status





def agent_label(agent_id: str, effective: dict[str, dict[str, Any]]) -> str:

    display_name = effective.get(agent_id, {}).get("display_name", agent_id)

    return f"{display_name}（{agent_id}）"





def build_project_state_payload(

    *,

    project_root: Path,

    route_id: str,

    project_type: str,

    run_id: str,

    dispatch_stage: str,

    selected_agents: list[str],

    review_agents: dict[str, str],

    effective: dict[str, dict[str, Any]],

    produced_types: set[str],

    merge_owner: str | None,

) -> dict[str, Any]:

    route = load_route(route_id)

    material_passport, pipeline_status = sync_pipeline_files(project_root, route_id)

    pipeline_stage = pipeline_status.get("current_stage") or material_passport.get("current_stage") or pipeline_default_stage(route_id)

    next_quality_gates = required_gates_for_stage(route_id, pipeline_stage)



    producer_agents = [agent_id for agent_id in selected_agents if effective[agent_id]["role"] != "reviewer"]

    reviewer_agents = [agent_id for agent_id in selected_agents if effective[agent_id]["role"] == "reviewer"]

    mandatory_review_targets = [

        agent_id for agent_id in producer_agents if produced_types & set(effective[agent_id]["required_review_for"])

    ]



    owner_agent_id = merge_owner if merge_owner in effective else None

    if owner_agent_id is None and "project-manager" in selected_agents:

        owner_agent_id = "project-manager"

    if owner_agent_id is None and producer_agents:

        owner_agent_id = producer_agents[0]

    if owner_agent_id is None:

        owner_agent_id = selected_agents[0]



    review_mapping_complete = all(review_agents.get(agent_id) for agent_id in mandatory_review_targets)

    payload = {

        "project_name": project_root.name,

        "route_id": route_id,

        "project_type": project_type,

        "project_scope_class": route.get("project_scope_class", "never_default_multi_agent"),

        "dispatch_run_id": run_id,

        "dispatch_stage": dispatch_stage,

        "pipeline_stage": pipeline_stage,

        "status": "planned",

        "current_owner_agent_id": owner_agent_id,

        "current_owner_display_name": effective.get(owner_agent_id, {}).get("display_name", owner_agent_id),

        "blockers": [],

        "next_quality_gates": next_quality_gates,

        "selected_agents": selected_agents,

        "selected_agent_labels": [agent_label(agent_id, effective) for agent_id in selected_agents],

        "selected_producers": producer_agents,

        "selected_reviewers": reviewer_agents,

        "review_agents": review_agents,

        "mandatory_review_targets": mandatory_review_targets,

        "milestones": [

            {

                "id": "dispatch_artifact_written",

                "label": "dispatch artifact 已落盘",

                "status": "complete",

            },

            {

                "id": "review_mapping_ready",

                "label": "target-specific review 映射",

                "status": "complete" if review_mapping_complete else "pending",

            },

            {

                "id": f"pipeline_{pipeline_stage}",

                "label": f"当前 pipeline stage：{pipeline_stage}",

                "status": "active",

            },

        ],

        "updated_at": datetime.now().isoformat(timespec="seconds"),

    }

    return payload





def build_effective_agents(project_root: Path, payload: dict) -> dict[str, dict[str, Any]]:

    registry = {

        item["agent_id"]: item for item in payload["registry"].get("agents", [])

    }

    modes = payload["modes"]["modes"]

    constraints = merge_constraints(payload["root_constraints"], extract_agent_constraints(project_root / "AGENTS.md"), {name: item["rank"] for name, item in modes.items()})

    project_agents: dict[str, dict[str, Any]] = {}

    for path in sorted((project_root / ".codex" / "agents").glob("*.json")):

        data = load_json(path)

        if data.get("enabled") is False:

            continue

        project_agents[data["agent_id"]] = data



    effective: dict[str, dict[str, Any]] = {}

    for agent_id, reg in registry.items():

        if agent_id not in project_agents:

            continue

        project = project_agents[agent_id]

        subset = project.get("allowed_skills_mcp_subset")

        write_subset = project.get("write_scope_subset")

        max_mode = project.get("max_execution_mode")



        effective_allowed = set(reg["allowed_skills_mcp"])

        if subset is not None:

            effective_allowed &= set(subset)

        effective_allowed -= set(constraints["forbid_skills_mcp"])



        effective_write_scope = set(reg["write_scope"])

        if write_subset is not None:

            effective_write_scope &= set(write_subset)

        effective_write_scope -= set(constraints["forbid_write_roots"])



        effective_mode = reg["max_execution_mode"]

        effective_mode = stricter_mode(effective_mode, max_mode, {name: item["rank"] for name, item in modes.items()})

        effective_mode = stricter_mode(effective_mode, constraints["max_execution_mode"], {name: item["rank"] for name, item in modes.items()})



        effective_required_review = set(reg["required_review_for"]) | set(constraints["require_review_for"])

        effective_isolation_method = stricter_isolation(reg.get("isolation_method"), project.get("isolation_method"))

        effective_parallel_safe = bool(reg.get("parallel_safe", False))

        if project.get("parallel_safe") is not None:

            effective_parallel_safe = effective_parallel_safe and bool(project.get("parallel_safe"))

        effective_integration_review_required = bool(reg.get("integration_review_required", False))

        if project.get("integration_review_required") is not None:

            effective_integration_review_required = effective_integration_review_required or bool(project.get("integration_review_required"))

        effective_capability_tags = set(reg.get("capability_tags", []))

        if project.get("capability_tags_subset") is not None:

            effective_capability_tags &= set(project.get("capability_tags_subset") or [])



        effective[agent_id] = {

            "display_name": (project.get("display_name") or reg.get("display_name") or agent_id),

            "role": reg["role"],

            "preferred_model": project.get("preferred_model") or reg.get("preferred_model"),

            "allowed_skills_mcp": sorted(effective_allowed),

            "write_scope": sorted(effective_write_scope),

            "max_execution_mode": effective_mode,

            "isolation_method": effective_isolation_method,

            "parallel_safe": effective_parallel_safe,

            "integration_review_required": effective_integration_review_required,

            "capability_tags": sorted(effective_capability_tags),

            "required_review_for": sorted(effective_required_review),

            "expected_outputs": project.get("expected_outputs", []),

            "required_inputs": project.get("required_inputs", []),

            "control_bindings": reg["control_bindings"],

        }

    return effective





def parse_review_pair(value: str) -> tuple[str, str]:

    if ":" not in value:

        raise ValueError(f"Invalid review pair '{value}'. Expected target:reviewer.")

    target, reviewer = value.split(":", 1)

    target = target.strip()

    reviewer = reviewer.strip()

    if not target or not reviewer:

        raise ValueError(f"Invalid review pair '{value}'.")

    return target, reviewer





def write_context_packet(path: Path, *, run_id: str, agent_id: str, display_name: str, route_id: str, stage: str, allowed_skills: list[str], required_inputs: list[str], expected_outputs: list[str], preferred_model: str | None, isolation_method: str | None, parallel_safe: bool, integration_review_required: bool, capability_tags: list[str], control_bindings: dict[str, Any]) -> None:

    text = f"""# Context Packet



- Run ID: `{run_id}`

- Agent ID: `{agent_id}`

- Agent Display Name: {display_name}

- Route ID: `{route_id}`

- Stage: `{stage}`

- Preferred Model: `{preferred_model or 'inherit'}`

- Isolation Method: `{isolation_method or 'unspecified'}`

- Parallel Safe: `{str(parallel_safe).lower()}`

- Integration Review Required: `{str(integration_review_required).lower()}`



## Task



- Fill in the concrete subtask for `{agent_id}`.



## Scope In



- Follow the selected route only.



## Scope Out



- Do not bypass formal citation, writing-capture, social evidence, reproducibility, or knowledge-sync hard chains.



## Inputs



{chr(10).join(f'- `{item}`' for item in required_inputs) if required_inputs else '- `NOT_SPECIFIED`'}



## Allowed Skills/MCP



{chr(10).join(f'- `{item}`' for item in allowed_skills) if allowed_skills else '- `NONE`'}



## Capability Tags



{chr(10).join(f'- `{item}`' for item in capability_tags) if capability_tags else '- `NONE`'}



## Control Bindings



- Control Objectives: {', '.join(f'`{item}`' for item in control_bindings.get('control_objectives', [])) or '`NONE`'}

- Controlled Variables: {', '.join(f'`{item}`' for item in control_bindings.get('controlled_variables', [])) or '`NONE`'}

- Feedback Signals: {', '.join(f'`{item}`' for item in control_bindings.get('feedback_signals', [])) or '`NONE`'}

- Stability Metrics: {', '.join(f'`{item}`' for item in control_bindings.get('stability_metrics', [])) or '`NONE`'}

- Rollback Policy: {control_bindings.get('rollback_policy', 'NOT_SPECIFIED')}



## Forbidden Actions



- Do not write outside the canonical output directory.

- Do not invent references.

- Do not change dispatch or gate artifacts directly.



## Expected Outputs



{chr(10).join(f'- `{item}`' for item in expected_outputs) if expected_outputs else '- `summary.md`'}



## Next Handoff



- To be filled after execution.

"""

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(text, encoding="utf-8")





def touch(path: Path, content: str = "") -> None:

    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():

        path.write_text(content, encoding="utf-8")





def build_dispatch_result(args: Any) -> dict[str, Any]:

    static_errors, static_warnings, payload = validate_static_contract()

    if static_errors:

        raise SystemExit(json.dumps({"ok": False, "errors": static_errors, "warnings": static_warnings}, ensure_ascii=False, indent=2))



    project_root = args.project_root.resolve()

    if not project_root.exists():

        raise SystemExit(f"Project root does not exist: {project_root}")



    preflight = collect_project_contract_preflight(project_root, require_bootstrap_dirs=False)

    if not preflight["ok"]:

        ensure_project_contract(project_root)

        preflight = collect_project_contract_preflight(project_root, require_bootstrap_dirs=False)

    if not preflight["ok"]:

        raise SystemExit(json.dumps(preflight, ensure_ascii=False, indent=2))



    effective = build_effective_agents(project_root, payload)

    scope_rules = payload["scope_rules"]

    deliverable_types = set(scope_rules["enums"]["deliverable_types"])

    review_subset = set(scope_rules["enums"]["required_review_for"])



    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")

    project_type = args.project_type or args.route_id

    selected_agents = list(dict.fromkeys(args.agents))

    missing_agents = [agent for agent in selected_agents if agent not in effective]

    if missing_agents:

        raise SystemExit(f"Missing project agent definitions for: {', '.join(missing_agents)}")



    review_agents: dict[str, str] = {}

    for item in args.review_pair:

        target, reviewer = parse_review_pair(item)

        review_agents[target] = reviewer



    for target, reviewer in review_agents.items():

        if target not in selected_agents:

            raise SystemExit(f"Review target '{target}' is not in selected agents.")

        if reviewer not in selected_agents:

            raise SystemExit(f"Reviewer '{reviewer}' is not in selected agents.")

        if effective[reviewer]["role"] != "reviewer":

            raise SystemExit(f"Agent '{reviewer}' is not a reviewer.")



    produced_types = set(args.deliverable_type)

    unknown_types = produced_types - deliverable_types

    if unknown_types:

        raise SystemExit(f"Unknown deliverable types: {sorted(unknown_types)}")



    if produced_types & review_subset:

        producer_agents = [agent for agent in selected_agents if effective[agent]["role"] != "reviewer"]

        for producer in producer_agents:

            if review_agents.get(producer) is None:

                raise SystemExit(f"Producer '{producer}' can hit mandatory review deliverables but no review-pair was provided.")



    mode_catalog = payload["modes"]

    canonical = mode_catalog["canonical_paths"]

    dispatch_rel = substitute_template(canonical["dispatch_card"], run_id=run_id)

    handoff_rel = substitute_template(canonical["handoff_log"], run_id=run_id)

    gate_log_rel = substitute_template(canonical["gate_log"], run_id=run_id)

    project_state_rel = normalize_relative_path(canonical["project_state_current"])

    project_state_history_rel = normalize_relative_path(canonical["project_state_history"])



    dispatch = {

        "run_id": run_id,

        "project_type": project_type,

        "route_id": args.route_id,

        "route_confirmation_required": bool(getattr(args, "route_confirmation_required", False)),

        "route_confirmation_question": getattr(args, "route_confirmation_question", ""),

        "user_confirmed_route": bool(getattr(args, "user_confirmed_route", False)),

        "stage": args.stage,

        "execution_mode": args.execution_mode,

        "isolation_method": "project-level-canonical-output-dirs",

        "agents": selected_agents,

        "agent_context_packet": {},

        "agent_display_names": {},

        "allowed_skills_mcp": {},

        "agent_output_path": {},

        "review_agents": review_agents,

        "quality_gate": args.quality_gate,

        "handoff_log": handoff_rel,

        "gate_log": gate_log_rel,

        "project_state_path": project_state_rel,

        "project_state_history_log": project_state_history_rel,

        "conflict_resolution": args.conflict_resolution,

        "merge_owner": args.merge_owner,

        "user_veto_window": args.user_veto_window,

    }



    for agent_id in selected_agents:

        output_rel = substitute_template(canonical["agent_output_dir"], run_id=run_id, agent_id=agent_id)

        context_rel = substitute_template(canonical["context_packet"], run_id=run_id, agent_id=agent_id)

        dispatch["agent_output_path"][agent_id] = output_rel

        dispatch["agent_context_packet"][agent_id] = context_rel

        dispatch["agent_display_names"][agent_id] = effective[agent_id]["display_name"]

        dispatch["allowed_skills_mcp"][agent_id] = effective[agent_id]["allowed_skills_mcp"]



        output_dir = project_root / output_rel

        output_dir.mkdir(parents=True, exist_ok=True)

        write_context_packet(

            project_root / context_rel,

            run_id=run_id,

            agent_id=agent_id,

            display_name=effective[agent_id]["display_name"],

            route_id=args.route_id,

            stage=args.stage,

            allowed_skills=effective[agent_id]["allowed_skills_mcp"],

            required_inputs=effective[agent_id]["required_inputs"],

            expected_outputs=effective[agent_id]["expected_outputs"],

            preferred_model=effective[agent_id]["preferred_model"],

            isolation_method=effective[agent_id]["isolation_method"],

            parallel_safe=effective[agent_id]["parallel_safe"],

            integration_review_required=effective[agent_id]["integration_review_required"],

            capability_tags=effective[agent_id]["capability_tags"],

            control_bindings=effective[agent_id]["control_bindings"],

        )



    touch(project_root / handoff_rel, "# Agent Handoffs\n\n")

    touch(project_root / gate_log_rel, "# Quality Gates\n\n")

    project_state_payload = build_project_state_payload(

        project_root=project_root,

        route_id=args.route_id,

        project_type=project_type,

        run_id=run_id,

        dispatch_stage=args.stage,

        selected_agents=selected_agents,

        review_agents=review_agents,

        effective=effective,

        produced_types=produced_types,

        merge_owner=args.merge_owner,

    )

    write_json(project_root / project_state_rel, project_state_payload)

    history_entry = [

        f"- {project_state_payload['updated_at']} | run `{run_id}` | route `{args.route_id}` | owner `{project_state_payload['current_owner_display_name']}`",

        f"  - pipeline_stage: `{project_state_payload['pipeline_stage']}`",

        f"  - next_quality_gates: {', '.join(f'`{gate}`' for gate in project_state_payload['next_quality_gates']) if project_state_payload['next_quality_gates'] else '`none`'}",

        f"  - selected_agents: {', '.join(f'`{agent}`' for agent in selected_agents)}",

        "",

    ]

    history_path = project_root / project_state_history_rel

    touch(history_path, "# Project State History\n\n")

    history_path.write_text(history_path.read_text(encoding="utf-8") + "\n".join(history_entry), encoding="utf-8")



    dispatch_path = project_root / dispatch_rel

    if dispatch_path.exists() and not args.overwrite:

        raise SystemExit(f"Dispatch already exists: {dispatch_path}")

    dispatch_path.parent.mkdir(parents=True, exist_ok=True)

    dispatch_path.write_text(yaml.safe_dump(dispatch, sort_keys=False, allow_unicode=True), encoding="utf-8")



    project_errors, project_warnings = validate_project(project_root, payload, mode="bootstrap")

    report = {

        "ok": not project_errors,

        "dispatch_path": str(dispatch_path),

        "project_errors": project_errors,

        "project_warnings": project_warnings,

        "run_id": run_id,

        "agent_display_names": dispatch["agent_display_names"],

        "review_agents": review_agents,

        "project_state_path": str(project_root / project_state_rel),

        "project_state_history_log": str(project_root / project_state_history_rel),

    }

    return build_validator_result(

        validator="bootstrap_agent_dispatch",

        scope="project",

        errors=project_errors,

        warnings=project_warnings,

        details=report,

        compatibility=report,

    )
