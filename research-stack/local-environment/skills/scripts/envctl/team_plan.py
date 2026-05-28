from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from .agent_contracts import collect_project_contract_preflight, validate_static_contract
    from .dispatch import build_effective_agents
    from .project_initializer import ensure_project_contract
    from .team_planner import build_review_pairs as build_playbook_review_pairs
    from .team_planner import pick_producers as pick_playbook_producers
    from ..path_utils import CATALOG_ROOT, SCRIPT_ROOT, SKILLS_ROOT
except ImportError:  # pragma: no cover
    from envctl.agent_contracts import collect_project_contract_preflight, validate_static_contract
    from envctl.dispatch import build_effective_agents
    from envctl.project_initializer import ensure_project_contract
    from envctl.team_planner import build_review_pairs as build_playbook_review_pairs
    from envctl.team_planner import pick_producers as pick_playbook_producers
    from path_utils import CATALOG_ROOT, SCRIPT_ROOT, SKILLS_ROOT


ROOT = SKILLS_ROOT
CATALOG = CATALOG_ROOT
BOOTSTRAP_SCRIPT = SCRIPT_ROOT / "bootstrap_agent_dispatch.py"

REVIEWER_AGENT_IDS = {"reviewer"}
WRITING_DELIVERABLES = {"paper_draft", "revision_package", "submission_package", "docx_export", "latex_export"}
WRITING_UNITS = {"writing", "review", "export"}
ANALYSIS_UNITS = {"cleaning", "coding", "analysis", "reproducibility"}
ANALYSIS_DELIVERABLES = {"figures_tables", "reproducibility_bundle", "project_map"}
LITERATURE_DELIVERABLES = {"annotated_bibliography", "literature_synthesis"}
SOCIAL_DELIVERABLES = {"case_dataset", "comment_analysis_report"}
APP_PRODUCT_UNITS = {
    "opportunity_planning",
    "needs_discovery",
    "product_spec",
    "specification",
    "concept_generation",
    "concept_selection",
    "concept_testing",
    "visual_spec",
    "asset_generation",
    "prototyping",
    "economics",
    "preview_tuning",
}
APP_UNITS = {"design", "implementation", "testing", "packaging", "release"} | APP_PRODUCT_UNITS
APP_PRODUCT_DELIVERABLES = {
    "app_opportunity_brief",
    "user_needs_hierarchy",
    "target_specifications",
    "concept_generation_log",
    "concept_selection_matrix",
    "concept_test_report",
    "prototype_test_plan",
    "development_economics_note",
    "app_prd",
    "visual_design_spec",
    "app_screen_mockups",
    "app_icon_assets",
    "preview_tuning_report",
}
APP_DELIVERABLES = {
    *APP_PRODUCT_DELIVERABLES,
    "app_architecture",
    "ui_implementation",
    "design_system_rules",
    "test_report",
    "desktop_build",
    "release_package",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_route(route_id: str) -> dict:
    routing = load_json(CATALOG / "routing_table.json")
    for route in routing.get("routes", []):
        if route["id"] == route_id:
            return route
    raise KeyError(f"Unknown route_id: {route_id}")


def load_research_team_playbooks() -> dict:
    path = CATALOG / "research_team_playbooks.json"
    if not path.exists():
        return {"playbooks": []}
    return load_json(path)


def load_route_playbook(route_id: str) -> dict | None:
    payload = load_research_team_playbooks()
    for playbook in payload.get("playbooks", []):
        if playbook.get("route_id") == route_id:
            return playbook
    return None


def resolve_conditional_rule(route_id: str, rules: dict) -> dict:
    raw = rules["conditional_rules"].get(route_id, {})
    if "copy_of" in raw:
        return resolve_conditional_rule(raw["copy_of"], rules)
    return raw


def eval_condition(card: dict, cond: dict) -> bool:
    field = cond["field"]
    operator = cond["operator"]
    value = cond["value"]
    actual = card.get(field)

    if operator == ">=":
        return int(actual or 0) >= int(value)
    if operator == ">":
        return int(actual or 0) > int(value)
    if operator == "contains":
        return value in set(actual or [])
    if operator == "contains_any":
        return bool(set(actual or []) & set(value))
    if operator == "contains_all":
        return set(value).issubset(set(actual or []))
    if operator == "min_count":
        pool = set(cond.get("pool", []))
        return len(set(actual or []) & pool) >= int(value)
    raise ValueError(f"Unsupported operator: {operator}")


def should_plan_multi_agent(route: dict, scope_rules: dict, card: dict) -> tuple[bool, str]:
    explicit = card["explicit_project_mode"]
    scope_class = route.get("project_scope_class", "never_default_multi_agent")
    if explicit == "force_multi_agent":
        return True, "用户显式要求 force_multi_agent。"
    if explicit == "force_single_agent":
        return True, "用户显式要求 force_single_agent；producer 会压缩，但 reviewer 不取消。"
    if scope_class == "always_multi_agent":
        return True, f"路由 `{route['id']}` 属于 always_multi_agent。"
    if scope_class == "never_default_multi_agent":
        return False, f"路由 `{route['id']}` 属于 never_default_multi_agent。"

    if route["id"] == "general-research" and card["needs_clarification"]:
        return False, "general-research 缺少 clarification card，不能直接进入项目编排。"

    rule = resolve_conditional_rule(route["id"], scope_rules)
    if rule.get("requires_clarification_card") and card["needs_clarification"]:
        return False, "条件路由要求先补 clarification card。"

    matches_any = True
    matches_all = True
    if rule.get("any"):
        matches_any = any(eval_condition(card, cond) for cond in rule["any"])
    if rule.get("all"):
        matches_all = all(eval_condition(card, cond) for cond in rule["all"])

    if matches_any and matches_all:
        return True, f"路由 `{route['id']}` 命中 conditional_multi_agent 升格规则。"
    return False, f"路由 `{route['id']}` 未命中 conditional_multi_agent 升格规则。"


def pick_producers(route_id: str, card: dict, team_playbook: dict | None = None) -> list[str]:
    return pick_playbook_producers(route_id, card, team_playbook)


def build_review_pairs(route_id: str, producers: list[str], available_agents: dict[str, dict], team_playbook: dict | None = None) -> tuple[list[str], dict[str, str], list[str]]:
    if team_playbook is not None:
        return build_playbook_review_pairs(route_id, producers, available_agents, team_playbook)
    reviewers: list[str] = []
    review_pairs: dict[str, str] = {}
    excluded: list[str] = []
    reviewer_id = "reviewer"
    if reviewer_id not in available_agents:
        excluded.append(reviewer_id)
        return reviewers, review_pairs, excluded
    reviewers.append(reviewer_id)
    for producer in producers:
        review_pairs[producer] = reviewer_id
    return reviewers, review_pairs, excluded


def agent_label(agent_id: str, available_agents: dict[str, dict]) -> str:
    display_name = available_agents.get(agent_id, {}).get("display_name", agent_id)
    return f"{display_name}（{agent_id}）"


def agent_display_items(agent_ids: list[str], available_agents: dict[str, dict]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for agent_id in agent_ids:
        items.append(
            {
                "agent_id": agent_id,
                "display_name": available_agents.get(agent_id, {}).get("display_name", agent_id),
                "label": agent_label(agent_id, available_agents),
                "preferred_model": available_agents.get(agent_id, {}).get("preferred_model"),
                "isolation_method": available_agents.get(agent_id, {}).get("isolation_method"),
                "parallel_safe": available_agents.get(agent_id, {}).get("parallel_safe"),
                "integration_review_required": available_agents.get(agent_id, {}).get("integration_review_required"),
                "capability_tags": available_agents.get(agent_id, {}).get("capability_tags", []),
            }
        )
    return items


def next_quality_gates(project_root: Path, route_id: str) -> list[str]:
    passport_path = project_root / "material-passport.yaml"
    pipeline = load_json(CATALOG / "research_pipeline_stages.json")
    sequence = pipeline.get("route_stage_sequences", {}).get(route_id, [])
    stage = "research_design"
    if passport_path.exists():
        text = passport_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.strip().startswith("current_stage:"):
                _, value = line.split(":", 1)
                stage = value.strip() or stage
                break
    if sequence and stage not in sequence:
        stage = sequence[0]
    base = list(pipeline.get("required_stage_gates", {}).get(stage, []))
    override = pipeline.get("route_stage_gate_overrides", {}).get(route_id, {}).get(stage, [])
    result: list[str] = []
    for gate_id in base + list(override):
        if gate_id not in result:
            result.append(gate_id)
    return result


def project_state_preview(project_root: Path, route: dict, selected_agents: list[str], review_pairs: dict[str, str], effective_agents: dict[str, dict], merge_owner: str | None) -> dict:
    producers = [agent_id for agent_id in selected_agents if effective_agents[agent_id]["role"] != "reviewer"]
    owner_agent_id = merge_owner if merge_owner in effective_agents else None
    if owner_agent_id is None and "project-manager" in selected_agents:
        owner_agent_id = "project-manager"
    if owner_agent_id is None and producers:
        owner_agent_id = producers[0]
    if owner_agent_id is None and selected_agents:
        owner_agent_id = selected_agents[0]
    owner_display_name = effective_agents.get(owner_agent_id, {}).get("display_name", owner_agent_id) if owner_agent_id else None

    return {
        "current_owner_agent_id": owner_agent_id,
        "current_owner_display_name": owner_display_name,
        "project_state_path": str(project_root / "logs" / "project-state" / "current.json"),
        "project_state_history_log": str(project_root / "logs" / "project-state" / "history.md"),
        "project_scope_class": route.get("project_scope_class", "never_default_multi_agent"),
        "next_quality_gates": next_quality_gates(project_root, route["id"]),
        "review_mapping_ready": bool(review_pairs),
    }


def exclusion_reasons(route_id: str, selected_agents: list[str], available_agents: dict[str, dict]) -> list[dict[str, str]]:
    reasons: dict[str, str] = {
        "literature-producer": "本轮 route 不以文献发现/综述为主，或当前 deliverable 不需要单独文献 producer。",
        "social-platform-producer": "本轮 route 不以平台证据抓取为主，或 capture 单元未达到独立 producer 阈值。",
        "analysis-producer": "本轮 route 不以分析执行、图表或复现为主。",
        "writing-producer": "本轮 route 不以主稿、返修包或导出写作为主。",
        "project-manager": "本轮只有单一 producer，不需要额外 manager 做阶段编排。",
        "reviewer": "当前项目 agent 定义里没有 reviewer，或本轮被显式否决。",
    }
    items: list[dict[str, str]] = []
    for agent_id in available_agents:
        if agent_id not in selected_agents:
            items.append(
                {
                    "agent_id": agent_id,
                    "display_name": available_agents.get(agent_id, {}).get("display_name", agent_id),
                    "label": agent_label(agent_id, available_agents),
                    "reason": reasons.get(agent_id, f"`{route_id}` 当前不需要这个 agent。"),
                }
            )
    return items


def run_bootstrap(
    project_root: Path,
    args: argparse.Namespace,
    selected_agents: list[str],
    review_pairs: dict[str, str],
    execution_mode: str,
) -> dict:
    command = [
        sys.executable,
        str(BOOTSTRAP_SCRIPT),
        "--project-root",
        str(project_root),
        "--route-id",
        args.route_id,
        "--project-type",
        args.project_type or args.route_id,
        "--stage",
        args.stage,
        "--execution-mode",
        execution_mode,
    ]
    if args.run_id:
        command.extend(["--run-id", args.run_id])
    if args.quality_gate:
        command.extend(["--quality-gate", args.quality_gate])
    if getattr(args, "route_confirmation_required", False):
        command.append("--route-confirmation-required")
    if getattr(args, "route_confirmation_question", ""):
        command.extend(["--route-confirmation-question", args.route_confirmation_question])
    if getattr(args, "user_confirmed_route", False):
        command.append("--user-confirmed-route")
    if args.conflict_resolution:
        command.extend(["--conflict-resolution", args.conflict_resolution])
    if args.merge_owner:
        command.extend(["--merge-owner", args.merge_owner])
    if args.user_veto_window:
        command.extend(["--user-veto-window", args.user_veto_window])
    if args.overwrite:
        command.append("--overwrite")

    for agent_id in selected_agents:
        command.extend(["--agent", agent_id])
    for producer, reviewer in review_pairs.items():
        command.extend(["--review-pair", f"{producer}:{reviewer}"])
    for deliverable in args.deliverable_type:
        command.extend(["--deliverable-type", deliverable])

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "ok": result.returncode == 0,
    }


def build_team_plan_result(args: object) -> dict:
    static_errors, static_warnings, payload = validate_static_contract()
    if static_errors:
        return {"ok": False, "static_errors": static_errors, "static_warnings": static_warnings}

    project_root = args.project_root.resolve()
    if not project_root.exists():
        return {"ok": False, "error": f"Project root does not exist: {project_root}"}

    preflight = collect_project_contract_preflight(project_root)
    auto_init_report = None
    if not preflight["ok"] and getattr(args, "auto_init_project_contract", True):
        auto_init_report = ensure_project_contract(project_root)
        preflight = collect_project_contract_preflight(project_root)
    if not preflight["ok"]:
        return {
            "ok": False,
            "error": "project-contract-not-initialized",
            "project_contract_preflight": preflight,
            "next_step": preflight["minimum_fix"],
        }

    route = load_route(args.route_id)
    team_playbook = load_route_playbook(args.route_id)
    scope_rules = payload["scope_rules"]
    enums = scope_rules["enums"]

    work_units = list(dict.fromkeys(args.work_unit))
    deliverable_types = list(dict.fromkeys(args.deliverable_type))
    sync_targets = list(dict.fromkeys(args.sync_target))

    invalid_work_units = sorted(set(work_units) - set(enums["work_units"]))
    invalid_deliverables = sorted(set(deliverable_types) - set(enums["deliverable_types"]))
    invalid_sync_targets = sorted(set(sync_targets) - set(enums["sync_targets"]))
    if invalid_work_units or invalid_deliverables or invalid_sync_targets:
        report = {
            "ok": False,
            "invalid_work_units": invalid_work_units,
            "invalid_deliverable_types": invalid_deliverables,
            "invalid_sync_targets": invalid_sync_targets,
        }
        return report

    clarification_card = {
        "route_id": args.route_id,
        "target_item_count": args.target_item_count,
        "work_units": work_units,
        "deliverable_types": deliverable_types,
        "sync_targets": sync_targets,
        "explicit_project_mode": args.explicit_project_mode,
        "needs_clarification": args.needs_clarification,
        "route_confirmation_required": bool(getattr(args, "route_confirmation_required", False)),
        "route_confirmation_question": getattr(args, "route_confirmation_question", ""),
        "user_confirmed_route": bool(getattr(args, "user_confirmed_route", False)),
    }
    if clarification_card["route_confirmation_required"] and not clarification_card["user_confirmed_route"]:
        return {
            "ok": False,
            "error": "route-confirmation-required",
            "route_id": args.route_id,
            "clarification_card": clarification_card,
            "next_step": clarification_card["route_confirmation_question"]
            or f"请确认是否进入 `{args.route_id}` 路线，再继续生成团队计划。",
        }

    should_plan, planning_reason = should_plan_multi_agent(route, scope_rules, clarification_card)
    if should_plan and team_playbook:
        planning_reason = f"{planning_reason} 队形参考 `{team_playbook.get('squad_name', args.route_id)}`。"
    execution_mode = "sequential_multi_agent_execution" if should_plan else "multi_perspective_reasoning"

    effective_agents = build_effective_agents(project_root, payload)
    selected_producers = pick_producers(args.route_id, clarification_card, team_playbook) if should_plan else []
    selected_producers = [agent_id for agent_id in selected_producers if agent_id in effective_agents]
    if should_plan and not selected_producers and getattr(args, "auto_init_project_contract", True):
        auto_init_report = ensure_project_contract(project_root)
        effective_agents = build_effective_agents(project_root, payload)
        selected_producers = pick_producers(args.route_id, clarification_card, team_playbook)
        selected_producers = [agent_id for agent_id in selected_producers if agent_id in effective_agents]
    if should_plan and args.explicit_project_mode == "force_single_agent" and len(selected_producers) > 1:
        non_manager = [agent_id for agent_id in selected_producers if agent_id != "project-manager"]
        selected_producers = [non_manager[0] if non_manager else selected_producers[0]]
    reviewers, review_pairs, missing_reviewers = build_review_pairs(args.route_id, selected_producers, effective_agents, team_playbook) if should_plan else ([], {}, [])
    selected_agents = list(dict.fromkeys(selected_producers + reviewers))

    mandatory_review_targets = []
    if selected_producers:
        review_subset = set(scope_rules["enums"]["required_review_for"])
        if set(deliverable_types) & review_subset:
            mandatory_review_targets = list(selected_producers)

    if should_plan and not selected_producers:
        report = {
            "ok": False,
            "error": "No producers could be selected from the project agent definitions.",
            "route_id": args.route_id,
            "clarification_card": clarification_card,
        }
        return report

    bootstrap_result = None
    if getattr(args, "bootstrap", False):
        if not should_plan:
            return {
                "ok": False,
                "error": "Current clarification card does not justify multi-agent planning; bootstrap aborted.",
                "route_id": args.route_id,
                "planning_reason": planning_reason,
            }
        bootstrap_result = run_bootstrap(project_root, args, selected_agents, review_pairs, execution_mode)
        if not bootstrap_result["ok"]:
            return {
                "ok": False,
                "route_id": args.route_id,
                "clarification_card": clarification_card,
                "planning_reason": planning_reason,
                "bootstrap_result": bootstrap_result,
            }

    report = {
        "ok": True,
        "route_id": args.route_id,
        "project_scope_class": route.get("project_scope_class", "never_default_multi_agent"),
        "clarification_card": clarification_card,
        "should_plan_multi_agent": should_plan,
        "planning_reason": planning_reason,
        "team_playbook": team_playbook,
        "project_contract_auto_init": auto_init_report,
        "execution_mode": execution_mode,
        "selected_producers": selected_producers,
        "selected_producers_display": agent_display_items(selected_producers, effective_agents),
        "selected_reviewers": reviewers,
        "selected_reviewers_display": agent_display_items(reviewers, effective_agents),
        "selected_agents": selected_agents,
        "selected_agents_display": agent_display_items(selected_agents, effective_agents),
        "review_agents": review_pairs,
        "review_agents_display": [
            {
                "target_agent_id": target,
                "target_display_name": effective_agents.get(target, {}).get("display_name", target),
                "reviewer_agent_id": reviewer,
                "reviewer_display_name": effective_agents.get(reviewer, {}).get("display_name", reviewer),
            }
            for target, reviewer in review_pairs.items()
        ],
        "mandatory_review_targets": mandatory_review_targets,
        "mandatory_review_targets_display": agent_display_items(mandatory_review_targets, effective_agents),
        "excluded_agents": exclusion_reasons(args.route_id, selected_agents, effective_agents),
        "missing_reviewers": missing_reviewers,
        "agent_display_names": {agent_id: effective_agents[agent_id]["display_name"] for agent_id in selected_agents},
        "project_state_preview": project_state_preview(project_root, route, selected_agents, review_pairs, effective_agents, getattr(args, "merge_owner", None)),
        "next_step": (
            "dispatch artifact 已落盘，可以进入子 agent 执行。"
            if bootstrap_result and bootstrap_result["ok"]
            else "确认中文编排说明卡后，可加 --bootstrap 落盘 dispatch artifact。"
        ),
        "bootstrap_result": bootstrap_result,
    }
    return report
