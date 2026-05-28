from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from ..path_utils import CATALOG_ROOT, OUTPUTS_ROOT, SCHEMAS_ROOT, SKILLS_ROOT
    from .schema_validation import collect_schema_document_errors, collect_schema_errors, load_json
    from .validator_envelope import build_validator_result
except ImportError:  # pragma: no cover
    from path_utils import CATALOG_ROOT, OUTPUTS_ROOT, SCHEMAS_ROOT, SKILLS_ROOT
    from envctl.schema_validation import collect_schema_document_errors, collect_schema_errors, load_json
    from envctl.validator_envelope import build_validator_result


POLICY_PATH = CATALOG_ROOT / "local_memory_system.json"
POLICY_SCHEMA_PATH = SCHEMAS_ROOT / "local_memory_system.v1.schema.json"
CANDIDATE_SCHEMA_PATH = SCHEMAS_ROOT / "memory_candidate.v1.schema.json"
STATUS_SCHEMA_PATH = SCHEMAS_ROOT / "memory_status_report.v1.schema.json"
RECONCILIATION_SCHEMA_PATH = SCHEMAS_ROOT / "memory_reconciliation_report.v1.schema.json"
PROTECTED_PATHS_PATH = CATALOG_ROOT / "protected_runtime_paths.json"
EVOLUTION_BACKLOG_PATH = CATALOG_ROOT / "evolution_backlog.json"

SCORE_KEYS = {
    "evidence",
    "recurrence",
    "actionability",
    "stability",
    "scope_fit",
    "validator_support",
    "privacy_risk",
    "conflict_risk",
    "staleness",
}
POSITIVE_SCORE_KEYS = {
    "evidence",
    "recurrence",
    "actionability",
    "stability",
    "scope_fit",
    "validator_support",
}
RISK_SCORE_KEYS = {"privacy_risk", "conflict_risk", "staleness"}
REQUIRED_INTERFACE_CONTROLS = {
    "confidence_evaluation": {
        "source_ref",
        "confidence_band",
        "conflict_status",
    },
    "decision_archive": {
        "decision_id",
        "route_id",
        "decision",
        "validator_gate",
    },
    "task_tracking": {
        "task_id",
        "route_id",
        "current_stage",
        "event",
        "timestamp",
        "next_action",
    },
    "task_status": {
        "route_id",
        "lifecycle_stage",
        "last_verified_gate",
        "open_blockers",
        "next_recommended_stage",
    },
    "memory_cleanup": {
        "memory_id",
        "scope",
        "user_confirmation",
        "protected_path_check",
        "audit_log_ref",
    },
    "agentmemory_governance_delete": {
        "agentmemory_id",
        "operation",
        "scope",
        "user_confirmation",
        "audit_log_ref",
    },
    "codegraph_context_index": {
        "query",
        "source_path",
        "result_scope",
        "index_status",
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_load(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"{label}:missing:{path}")
        return {}
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"{label}:invalid-json:{exc}")
        return {}


def load_memory_policy(path: Path | None = None) -> dict[str, Any]:
    return load_json(path or POLICY_PATH)


def validate_local_memory_system() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    policy_schema = _safe_load(POLICY_SCHEMA_PATH, "local_memory_system.schema", errors)
    candidate_schema = _safe_load(CANDIDATE_SCHEMA_PATH, "memory_candidate.schema", errors)
    status_schema = _safe_load(STATUS_SCHEMA_PATH, "memory_status_report.schema", errors)
    reconciliation_schema = _safe_load(RECONCILIATION_SCHEMA_PATH, "memory_reconciliation_report.schema", errors)
    policy = _safe_load(POLICY_PATH, "local_memory_system", errors)

    for label, schema in [
        ("local_memory_system.schema", policy_schema),
        ("memory_candidate.schema", candidate_schema),
        ("memory_status_report.schema", status_schema),
        ("memory_reconciliation_report.schema", reconciliation_schema),
    ]:
        if schema:
            errors.extend(collect_schema_document_errors(schema, label))
    if policy_schema and policy:
        errors.extend(collect_schema_errors(policy, policy_schema, "local_memory_system"))
        errors.extend(_collect_policy_consistency_errors(policy))

    details = {
        "policy": str(POLICY_PATH.relative_to(SKILLS_ROOT)),
        "schemas": [
            str(POLICY_SCHEMA_PATH.relative_to(SKILLS_ROOT)),
            str(CANDIDATE_SCHEMA_PATH.relative_to(SKILLS_ROOT)),
            str(STATUS_SCHEMA_PATH.relative_to(SKILLS_ROOT)),
            str(RECONCILIATION_SCHEMA_PATH.relative_to(SKILLS_ROOT)),
        ],
        "selected_plan": policy.get("selected_plan", {}),
        "automation_mode": policy.get("automation_policy", {}).get("mode"),
        "memory_layers": [
            item.get("id")
            for item in policy.get("memory_layers", [])
            if isinstance(item, dict)
        ],
    }
    return build_validator_result(
        validator="validate_local_memory_system",
        scope="memory",
        errors=errors,
        warnings=warnings,
        details=details,
    )


def _collect_policy_consistency_errors(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    layers = policy.get("memory_layers", [])
    layer_ids = [item.get("id") for item in layers if isinstance(item, dict)]
    required_layers = {
        "ephemeral_session",
        "project_memory",
        "private_preference",
        "procedural_memory",
        "control_memory",
        "discarded_noise",
    }
    missing_layers = required_layers - set(layer_ids)
    errors.extend(f"local_memory_system:missing-layer:{item}" for item in sorted(missing_layers))
    if any(item.get("auto_promotion_allowed") is True for item in layers if isinstance(item, dict)):
        errors.append("local_memory_system:auto-promotion-must-remain-disabled")
    retrieval = policy.get("retrieval_policy", {})
    enabled_interfaces = set(retrieval.get("enabled_interfaces", []))
    required_interfaces = {
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
        "codegraph_context_index",
    }
    errors.extend(
        f"local_memory_system:missing-retrieval-interface:{item}"
        for item in sorted(required_interfaces - enabled_interfaces)
    )
    controls = {
        item.get("interface"): item
        for item in retrieval.get("interface_controls", [])
        if isinstance(item, dict)
    }
    for interface, required_fields in sorted(REQUIRED_INTERFACE_CONTROLS.items()):
        if interface not in controls:
            errors.append(f"local_memory_system:missing-interface-control:{interface}")
            continue
        fields = set(controls[interface].get("required_fields", []))
        missing_fields = required_fields - fields
        errors.extend(
            f"local_memory_system:{interface}:missing-required-field:{field}"
            for field in sorted(missing_fields)
        )
        safety_text = " ".join(controls[interface].get("safety_rules", []))
        delete_safety_phrases = {
            "memory_cleanup": ["confirmation", "protected"],
            "agentmemory_governance_delete": ["source rules", "secrets"],
        }.get(interface, [])
        for phrase in delete_safety_phrases:
            if phrase not in safety_text and phrase not in " ".join(fields):
                errors.append(f"local_memory_system:{interface}:missing-delete-safety:{phrase}")
    runtime_adapter = policy.get("runtime_adapter_policy", {})
    agentmemory_enabled = (
        runtime_adapter.get("selected_adapter") == "agentmemory"
        and runtime_adapter.get("status") in {"enabled", "trial"}
    )
    semantic = retrieval.get("optional_semantic_search", {})
    allowed_semantic_states = {"dry_run_only", "watch_only"}
    if agentmemory_enabled:
        allowed_semantic_states.add("enabled_read_only")
    if semantic.get("status") not in allowed_semantic_states:
        errors.append(f"local_memory_system:semantic-search-default-too-strong:{semantic.get('status')}")
    semantic_limits = set(semantic.get("hard_limits", []))
    required_semantic_limits = [
        "no full transcript ingestion by default",
        "semantic hits are candidates, not source-of-truth rules",
    ]
    if agentmemory_enabled:
        required_semantic_limits.extend(
            [
                "no unvetted vector database by default",
                "no unvetted background service by default",
                "agentmemory recall cannot silently switch route or mutate source rules",
            ]
        )
    else:
        required_semantic_limits.extend(
            [
                "no vector database by default",
                "no background service by default",
            ]
        )
    for item in required_semantic_limits:
        if item not in semantic_limits:
            errors.append(f"local_memory_system:missing-semantic-hard-limit:{item}")
    if agentmemory_enabled:
        for item in [
            "agentmemory_smart_search",
            "agentmemory_session_history",
            "agentmemory_governance_delete",
        ]:
            if item not in enabled_interfaces:
                errors.append(f"local_memory_system:missing-agentmemory-interface:{item}")
        runtime_text = " ".join(runtime_adapter.get("forbidden_actions", []))
        for phrase in ["auto-promote runtime memory", "full transcript import", "secrets"]:
            if phrase not in runtime_text:
                errors.append(f"local_memory_system:missing-agentmemory-forbidden-action:{phrase}")
    automation = policy.get("automation_policy", {})
    if automation.get("mode") != "controlled_auto_landing":
        errors.append("local_memory_system:automation-mode-not-controlled")
    if automation.get("default_execution_environment") != "local":
        errors.append("local_memory_system:automation-environment-not-local")
    forbidden_defaults = set(policy.get("storage_boundaries", {}).get("forbidden_defaults", []))
    for item in [
        "no_vector_database_by_default",
        "no_unvetted_background_service_by_default",
        "no_transcript_ingestion_by_default",
        "no_external_hook_by_default",
        "no_unvetted_vector_database_by_default",
    ]:
        if item not in forbidden_defaults:
            errors.append(f"local_memory_system:missing-lightweight-default:{item}")
    required_gates = set(automation.get("required_gates", []))
    for gate in [
        "python -m skills.scripts.envctl validate memory",
        "python -m skills.scripts.envctl validate cybernetics",
        "python -m skills.scripts.envctl validate stack",
        "python -m skills.scripts.envctl validate environment-layers",
    ]:
        if gate not in required_gates:
            errors.append(f"local_memory_system:missing-required-gate:{gate}")
    protected_ref = automation.get("protected_runtime_paths_ref")
    if protected_ref != "skills/catalog/protected_runtime_paths.json":
        errors.append(f"local_memory_system:unexpected-protected-path-ref:{protected_ref}")
    return errors


def admission_score(candidate: dict[str, Any], policy: dict[str, Any] | None = None) -> float:
    active_policy = policy or load_memory_policy()
    components = candidate.get("score_components", {})
    weights = active_policy["scoring_policy"]["weights"]
    penalties = active_policy["scoring_policy"]["risk_penalties"]
    score = 0.0
    for key in POSITIVE_SCORE_KEYS:
        score += float(components.get(key, 0)) * float(weights.get(key, 0))
    for key in RISK_SCORE_KEYS:
        score -= float(components.get(key, 0)) * float(penalties.get(key, 0))
    return max(0.0, min(1.0, round(score, 4)))


def decide_candidate(candidate: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    active_policy = policy or load_memory_policy()
    schema_errors = collect_schema_errors(candidate, load_json(CANDIDATE_SCHEMA_PATH), "memory_candidate")
    hard_blocks = _collect_candidate_hard_blocks(candidate)
    score = admission_score(candidate, active_policy) if not schema_errors else 0.0
    thresholds = active_policy["scoring_policy"]
    if schema_errors or hard_blocks:
        decision = "rejected"
        reason = "schema_or_hard_block"
    elif score < float(thresholds["manual_review_threshold"]):
        decision = "discard_or_ephemeral"
        reason = "low_score"
    elif score < float(thresholds["promotion_threshold"]):
        decision = "needs_review"
        reason = "manual_review_band"
    else:
        decision = "promotion_plan"
        reason = "promotion_threshold_met"
    return {
        "id": candidate.get("id"),
        "admission_score": score,
        "decision": decision,
        "reason": reason,
        "schema_errors": schema_errors,
        "hard_blocks": hard_blocks,
        "proposed_target": candidate.get("proposed_target"),
    }


def _collect_candidate_hard_blocks(candidate: dict[str, Any]) -> list[str]:
    blocks: list[str] = []
    claim = str(candidate.get("normalized_claim", ""))
    source_ref = str(candidate.get("source_ref", ""))
    combined = f"{claim}\n{source_ref}".lower()
    if re.search(r"(secret|token|cookie|password|api[_ -]?key|验证码|账号|密码)", combined):
        blocks.append("contains-secret-or-account-signal")
    if candidate.get("privacy_scope") in {"local_private", "session_only"} and candidate.get("proposed_target") in {
        "control_kernel",
        "skill",
        "evolution_backlog",
    }:
        blocks.append("private-scope-targets-git-source")
    if "doi" in combined or "citation" in combined or "引用" in combined:
        if "citation gate" not in " ".join(candidate.get("evidence_refs", [])).lower():
            blocks.append("citation-like-memory-without-citation-gate")
    return blocks


def build_memory_status_report() -> dict[str, Any]:
    policy = load_memory_policy()
    protected_paths = _load_protected_path_strings()
    return {
        "schema_version": "memory_status_report.v1",
        "generated_at": _utc_now(),
        "mode": policy["automation_policy"]["mode"],
        "source_files_written": False,
        "selected_plan": policy["selected_plan"]["id"],
        "lightweight_constraints": policy["storage_boundaries"]["forbidden_defaults"],
        "external_inputs": [
            {
                "repo": item["repo"],
                "decision": item["decision"],
                "absorbed_count": len(item["absorbed_patterns"]),
                "rejected_count": len(item["rejected_patterns"]),
            }
            for item in policy["external_inputs"]
        ],
        "memory_layers": [
            {
                "id": item["id"],
                "default_target": item["default_target"],
                "auto_promotion_allowed": item["auto_promotion_allowed"],
            }
            for item in policy["memory_layers"]
        ],
        "automation": {
            "default_execution_environment": policy["automation_policy"]["default_execution_environment"],
            "allowed_auto_actions": policy["automation_policy"]["allowed_auto_actions"],
            "allowed_source_write_scope": policy["automation_policy"]["allowed_source_write_scope"],
            "required_gates": policy["automation_policy"]["required_gates"],
            "run_ledger_output_dir": policy["automation_policy"]["run_ledger_output_dir"],
            "weekly_review_scope": policy["automation_policy"]["weekly_review_scope"],
        },
        "health_checks": policy["health_policy"]["startup_checks"],
        "protected_runtime_paths": protected_paths,
        "next_actions": [
            "Keep daily automation local to the active D drive repository.",
            "Write only deduplicated backlog entries and ignored reports unless weekly low-risk gates pass.",
            "Use memory score/dry-run before turning repeated user corrections into source rules.",
        ],
    }


def validate_memory_status_report(report: dict[str, Any]) -> list[str]:
    return collect_schema_errors(report, load_json(STATUS_SCHEMA_PATH), "memory_status_report")


def write_memory_status_report(report: dict[str, Any], output: Path | None = None) -> Path:
    if output is None:
        date = datetime.now().strftime("%Y-%m-%d")
        output = OUTPUTS_ROOT / "reports" / "local-memory-system" / f"{date}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def build_memory_reconciliation_report(*, probe_agentmemory: bool = False) -> dict[str, Any]:
    policy = load_memory_policy()
    agentmemory = _agentmemory_status(probe_agentmemory)
    daily_reports = _report_inventory(OUTPUTS_ROOT / "reports" / "cybernetics-daily")
    evolution_reports = _report_inventory(OUTPUTS_ROOT / "reports" / "evolution-intake")
    backlog = _evolution_backlog_summary()
    reconciliation = [
        "local Git contracts remain the source of truth; runtime memory is recall and candidate evidence only",
        "daily automation reports are read as signals; durable changes still require validators and Git commits",
    ]
    if agentmemory["checked"] and agentmemory["healthy"] is not True:
        reconciliation.append("agentmemory is not healthy; do not rely on runtime recall until fixed")
    if backlog["open_count"]:
        reconciliation.append("open evolution backlog items require review before promotion")
    if not daily_reports["count"]:
        reconciliation.append("no cybernetics daily report found; daily automation has no recent local evidence")
    return {
        "schema_version": "memory_reconciliation_report.v1",
        "generated_at": _utc_now(),
        "source_files_written": False,
        "mode": policy["automation_policy"]["mode"],
        "source_of_truth": "skills/catalog, skills/schemas, skills/plugins, skills/scripts, skills/tests, and Git commits",
        "agentmemory": agentmemory,
        "automation_reports": {
            "cybernetics_daily_count": daily_reports["count"],
            "latest_cybernetics_daily": daily_reports["latest"],
            "evolution_intake_count": evolution_reports["count"],
            "latest_evolution_intake": evolution_reports["latest"],
        },
        "evolution_backlog": backlog,
        "reconciliation": reconciliation,
        "next_actions": [
            "Use envctl memory score before promoting repeated runtime memories.",
            "Use project-retrospective-evolver for project lessons and research-stack-manager for governed source changes.",
            "Keep agentmemory LLM compression, automatic injection, and full transcript import disabled unless explicitly approved.",
        ],
    }


def validate_memory_reconciliation_report(report: dict[str, Any]) -> list[str]:
    return collect_schema_errors(report, load_json(RECONCILIATION_SCHEMA_PATH), "memory_reconciliation_report")


def write_memory_reconciliation_report(report: dict[str, Any], output: Path | None = None) -> Path:
    if output is None:
        date = datetime.now().strftime("%Y-%m-%d")
        output = OUTPUTS_ROOT / "reports" / "local-memory-system" / f"{date}-reconciliation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def _agentmemory_status(probe: bool) -> dict[str, Any]:
    configured = load_memory_policy().get("runtime_adapter_policy", {}).get("selected_adapter") == "agentmemory"
    if not probe:
        return {"configured": configured, "checked": False, "healthy": None, "summary": "not probed"}
    result = subprocess.run(
        ["cmd", "/c", "agentmemory", "status"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    text = f"{result.stdout}\n{result.stderr}".strip()
    healthy = result.returncode == 0 and "healthy" in text.lower()
    summary = "healthy" if healthy else (text[:300] if text else f"exit:{result.returncode}")
    return {"configured": configured, "checked": True, "healthy": healthy, "summary": summary}


def _report_inventory(root: Path) -> dict[str, Any]:
    if not root.exists():
        return {"count": 0, "latest": None}
    files = [item for item in root.rglob("*") if item.is_file()]
    files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    latest = str(files[0].relative_to(SKILLS_ROOT)) if files else None
    return {"count": len(files), "latest": latest}


def _evolution_backlog_summary() -> dict[str, Any]:
    if not EVOLUTION_BACKLOG_PATH.exists():
        return {"event_count": 0, "open_count": 0, "implemented_count": 0, "by_status": {}}
    payload = load_json(EVOLUTION_BACKLOG_PATH)
    events = [item for item in payload.get("events", []) if isinstance(item, dict)]
    counts = Counter(str(item.get("status", "<missing>")) for item in events)
    open_count = sum(count for status, count in counts.items() if status not in {"implemented", "rejected", "closed"})
    return {
        "event_count": len(events),
        "open_count": open_count,
        "implemented_count": counts.get("implemented", 0),
        "by_status": dict(sorted(counts.items())),
    }


def candidate_from_text(
    *,
    text: str,
    source_type: str,
    source_ref: str,
    memory_layer: str,
    privacy_scope: str,
    proposed_target: str,
    occurrence_count: int = 1,
    user_confirmed: bool = False,
) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", text.strip())
    digest = hashlib.sha256(f"{source_ref}\n{normalized}".encode("utf-8", errors="replace")).hexdigest()
    now = _utc_now()
    components = _default_score_components(
        normalized_claim=normalized,
        source_type=source_type,
        occurrence_count=occurrence_count,
        user_confirmed=user_confirmed,
        privacy_scope=privacy_scope,
        proposed_target=proposed_target,
    )
    candidate: dict[str, Any] = {
        "schema_version": "memory_candidate.v1",
        "id": f"memcand-{digest[:12]}",
        "observed_at": now,
        "source_type": source_type,
        "source_ref": source_ref,
        "source_hash": digest,
        "normalized_claim": normalized,
        "memory_layer": memory_layer,
        "privacy_scope": privacy_scope,
        "evidence_refs": [source_ref],
        "occurrence_count": occurrence_count,
        "first_seen_at": now,
        "last_seen_at": now,
        "score_components": components,
        "decay_class": "protected" if user_confirmed else "normal",
        "conflict_refs": [],
        "proposed_target": proposed_target,
        "status": "candidate",
        "review_after": None,
        "expires_at": None,
        "user_confirmed": user_confirmed,
    }
    return candidate


def _default_score_components(
    *,
    normalized_claim: str,
    source_type: str,
    occurrence_count: int,
    user_confirmed: bool,
    privacy_scope: str,
    proposed_target: str,
) -> dict[str, float]:
    text_len = len(normalized_claim)
    evidence = 0.95 if user_confirmed else 0.45
    recurrence = min(1.0, occurrence_count / 3)
    actionability = 0.9 if user_confirmed else 0.7 if source_type in {"user_correction", "route_override", "explicit_preference"} else 0.55
    stability = 0.95 if user_confirmed else 0.8 if occurrence_count >= 2 else 0.45
    if privacy_scope in {"public_repo", "project_private"}:
        scope_fit = 0.95 if user_confirmed else 0.8
    elif privacy_scope == "local_private" and proposed_target == "codex_native":
        scope_fit = 0.8
    elif privacy_scope == "local_private" and proposed_target == "obsidian":
        scope_fit = 0.65
    else:
        scope_fit = 0.35
    validator_support = 0.8 if user_confirmed else 0.6 if source_type in {"validator_failure", "daily_audit", "weekly_review"} else 0.3
    if privacy_scope == "session_only":
        privacy_risk = 0.7
    elif privacy_scope == "local_private" and proposed_target in {"control_kernel", "skill", "evolution_backlog"}:
        privacy_risk = 0.8
    elif privacy_scope == "local_private" and proposed_target == "obsidian":
        privacy_risk = 0.1
    else:
        privacy_risk = 0.0
    conflict_risk = 0.0
    staleness = 0.0 if source_type in {"explicit_preference", "user_correction"} or text_len >= 20 else 0.3
    return {
        "evidence": evidence,
        "recurrence": recurrence,
        "actionability": actionability,
        "stability": stability,
        "scope_fit": scope_fit,
        "validator_support": validator_support,
        "privacy_risk": privacy_risk,
        "conflict_risk": conflict_risk,
        "staleness": staleness,
    }


def _load_protected_path_strings() -> list[str]:
    if not PROTECTED_PATHS_PATH.exists():
        return []
    payload = load_json(PROTECTED_PATHS_PATH)
    paths: list[str] = []
    for key in ["protected_paths", "paths"]:
        for item in payload.get(key, []):
            if isinstance(item, dict):
                value = item.get("path") or item.get("root")
                if value:
                    paths.append(str(value))
            elif isinstance(item, str):
                paths.append(item)
    return sorted(set(paths))
