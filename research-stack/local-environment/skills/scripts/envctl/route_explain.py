from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from ..path_utils import CATALOG_ROOT, REPO_ROOT, SCHEMAS_ROOT
    from .schema_validation import collect_schema_errors, load_json
except ImportError:  # pragma: no cover
    from path_utils import CATALOG_ROOT, REPO_ROOT, SCHEMAS_ROOT
    from envctl.schema_validation import collect_schema_errors, load_json


ROUTING_PATH = CATALOG_ROOT / "routing_table.json"
CONFLICT_PATH = CATALOG_ROOT / "conflict_matrix.json"
ENVIRONMENT_LAYERS_PATH = CATALOG_ROOT / "environment_layer_contract.json"
LOCAL_MEMORY_PATH = CATALOG_ROOT / "local_memory_system.json"
ROUTE_REPORT_SCHEMA_PATH = SCHEMAS_ROOT / "route_explanation_report.v1.schema.json"
STARTUP_SCHEMA_PATH = SCHEMAS_ROOT / "startup_context_summary.v1.schema.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _contains(query: str, term: str) -> bool:
    if not term:
        return False
    return term.lower() in query.lower()


def build_route_explanation(query: str, *, max_candidates: int = 5) -> dict[str, Any]:
    routing = load_json(ROUTING_PATH)
    conflicts = load_json(CONFLICT_PATH)
    candidates = []
    for route in routing.get("routes", []):
        matched_aliases = [item for item in route.get("aliases", []) if _contains(query, str(item))]
        matched_keywords = [item for item in route.get("keywords", []) if _contains(query, str(item))]
        score = len(matched_aliases) * 3 + len(matched_keywords) * 2
        if score <= 0:
            continue
        candidates.append(
            {
                "route_id": route["id"],
                "score": float(score),
                "matched_aliases": matched_aliases,
                "matched_keywords": matched_keywords,
                "profile": route.get("profile", ""),
                "quality_gates": route.get("quality_gate_required", []),
                "mcp": route.get("mcp", []),
                "helper_skills": route.get("helper_skills", []),
                "reason": route.get("rationale") or route.get("next_step") or "",
            }
        )
    candidates.sort(key=lambda item: (-item["score"], item["route_id"]))
    top_candidates = candidates[:max_candidates]
    triggered = _triggered_conflict_rules(query, conflicts)
    selected_route, clarification_required, questions = _select_route(query, top_candidates, triggered)
    return {
        "schema_version": "route_explanation_report.v1",
        "generated_at": _utc_now(),
        "source_files_written": False,
        "query": query,
        "selected_route": selected_route,
        "route_confirmation_required": True,
        "clarification_required": clarification_required,
        "top_candidates": top_candidates,
        "triggered_conflict_rules": triggered,
        "clarification_questions": questions,
    }


def _triggered_conflict_rules(query: str, conflicts: dict[str, Any]) -> list[dict[str, str]]:
    q = query.lower()
    rules = []
    trigger_map = {
        "revision-package-scope-disambiguation": ["revision package", "修改稿", "rebuttal", "response letter"],
        "replication-package-scope-disambiguation": ["复现包", "replication package", "reproducibility package"],
        "route-confirmation-before-new-chain": ["开始", "进入", "切换", "新链条", "下载", "批量", "配置"],
        "project-folder-hygiene-vs-environment-ops": ["清理项目", "整理项目", "项目文件夹", "临时文件", "死文件", "归档项目"],
        "subagent-first-for-divisible-work": ["subagent", "子智能体", "并行 agent", "并行智能体", "多智能体"],
    }
    for item in conflicts.get("rules", []):
        rule_id = str(item.get("rule", ""))
        triggers = trigger_map.get(rule_id, [])
        if triggers and any(token.lower() in q for token in triggers):
            rules.append(
                {
                    "rule": rule_id,
                    "winner": str(item.get("winner", "")),
                    "reason": str(item.get("reason", "")),
                }
            )
    return rules


def _select_route(
    query: str,
    candidates: list[dict[str, Any]],
    triggered_rules: list[dict[str, str]],
) -> tuple[str | None, bool, list[str]]:
    if not candidates:
        return (
            "general-research",
            True,
            ["当前描述没有明确命中专门路线。请确认是普通研究咨询，还是要进入文献、写作、实证、图表、审稿或环境治理链条？"],
        )
    top = candidates[0]
    near_ties = [item for item in candidates if top["score"] - item["score"] <= 1]
    disambiguation_rules = {item["rule"] for item in triggered_rules if "disambiguation" in item["rule"]}
    if disambiguation_rules and len(near_ties) > 1:
        return (
            None,
            True,
            [
                "这个任务可能进入多条路线。请确认目标是正文/回复修改、完整投稿包，还是模型/数据复现？",
                "是否已经有明确项目根目录和要冻结的交付物？",
            ],
        )
    if len(near_ties) > 1:
        return (
            None,
            True,
            [f"候选路线分数接近：{', '.join(item['route_id'] for item in near_ties)}。请确认要进入哪条链。"],
        )
    return top["route_id"], False, []


def validate_route_explanation_report(report: dict[str, Any]) -> list[str]:
    return collect_schema_errors(report, load_json(ROUTE_REPORT_SCHEMA_PATH), "route_explanation_report")


def build_startup_context_summary(route_id: str | None = None) -> dict[str, Any]:
    layers = load_json(ENVIRONMENT_LAYERS_PATH)
    memory = load_json(LOCAL_MEMORY_PATH)
    routing = load_json(ROUTING_PATH)
    route_context = None
    if route_id:
        route = next((item for item in routing.get("routes", []) if item.get("id") == route_id), None)
        if route:
            route_context = {
                "route_id": route["id"],
                "profile": route.get("profile", ""),
                "skills": route.get("skills", []),
                "helper_skills": route.get("helper_skills", []),
                "mcp": route.get("mcp", []),
                "quality_gates": route.get("quality_gate_required", []),
                "next_step": route.get("next_step", ""),
            }
    runtime_adapters = [
        {
            "id": "agentmemory",
            "role": "运行态记忆召回、候选记忆、审计和删除",
            "boundary": memory["runtime_adapter_policy"]["promotion_boundary"],
        },
        {
            "id": "codegraph",
            "role": "代码结构索引和影响范围理解",
            "boundary": "只更新忽略的 .codegraph 索引；不替代源码、validator、测试和 Git。",
        },
    ]
    return {
        "schema_version": "startup_context_summary.v1",
        "generated_at": _utc_now(),
        "source_files_written": False,
        "source_root": str(REPO_ROOT),
        "total_entry": "research-autopilot",
        "layer_order": layers.get("layer_order", []),
        "core_rules": [
            "新链条、路线切换、高成本工具、多 agent、下载链或运行态配置变更前先确认。",
            "正式引用必须有可审计证据；PDF 原文、用户来源或公开学术检索记录可作为 DOI 豁免证据。",
            "agentmemory 和 codegraph 只提供上下文候选，不覆盖本地 Git 源规则。",
            "阶段推进应主动建议，但必须等用户确认后切换路线或写入。",
        ],
        "runtime_adapters": runtime_adapters,
        "selected_route_context": route_context,
        "do_not_inject_by_default": [
            "完整 routing_table",
            "完整 conflict_matrix",
            "完整历史对话 transcript",
            "agentmemory 原始全量记忆",
            "未命中的技能说明全文",
        ],
    }


def validate_startup_context_summary(report: dict[str, Any]) -> list[str]:
    return collect_schema_errors(report, load_json(STARTUP_SCHEMA_PATH), "startup_context_summary")


def summarize_route_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": report["schema_version"],
        "selected_route": report["selected_route"],
        "route_confirmation_required": report["route_confirmation_required"],
        "clarification_required": report["clarification_required"],
        "top_candidates": [
            {
                "route_id": item["route_id"],
                "score": item["score"],
                "matched_aliases": item["matched_aliases"],
                "matched_keywords": item["matched_keywords"],
            }
            for item in report["top_candidates"]
        ],
        "triggered_conflict_rules": [item["rule"] for item in report["triggered_conflict_rules"]],
        "clarification_questions": report["clarification_questions"],
    }
