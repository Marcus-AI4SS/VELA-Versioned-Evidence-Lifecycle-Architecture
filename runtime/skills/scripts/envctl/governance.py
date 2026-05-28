from __future__ import annotations



import json

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





CONTRACTS = {

    "governance_kernel": (

        CATALOG_ROOT / "governance_kernel.json",

        SCHEMAS_ROOT / "governance_kernel.v1.schema.json",

    ),

    "memory_admission_policy": (

        CATALOG_ROOT / "memory_admission_policy.json",

        SCHEMAS_ROOT / "memory_admission_policy.v1.schema.json",

    ),

    "local_memory_system": (

        CATALOG_ROOT / "local_memory_system.json",

        SCHEMAS_ROOT / "local_memory_system.v1.schema.json",

    ),

    "evolution_backlog": (

        CATALOG_ROOT / "evolution_backlog.json",

        SCHEMAS_ROOT / "evolution_event.v1.schema.json",

    ),

    "evolution_intake_policy": (

        CATALOG_ROOT / "evolution_intake_policy.json",

        SCHEMAS_ROOT / "evolution_intake_policy.v1.schema.json",

    ),

    "external_adoption_reviews": (

        CATALOG_ROOT / "external_adoption_reviews.json",

        SCHEMAS_ROOT / "external_adoption_review.v1.schema.json",

    ),

    "governance_source_rule_crosswalk": (

        CATALOG_ROOT / "governance_source_rule_crosswalk.json",

        SCHEMAS_ROOT / "governance_source_rule_crosswalk.v1.schema.json",

    ),

    "subagent_registry": (

        CATALOG_ROOT / "subagent_registry.json",

        SCHEMAS_ROOT / "subagent_registry.schema.json",

    ),

    "citation_verification_rules": (

        CATALOG_ROOT / "citation_verification_rules.json",

        SCHEMAS_ROOT / "citation_verification_rules.schema.json",

    ),

    "route_mcp_activation_policy": (

        CATALOG_ROOT / "route_mcp_activation_policy.json",

        SCHEMAS_ROOT / "route_mcp_activation_policy.schema.json",

    ),

    "conflict_matrix": (

        CATALOG_ROOT / "conflict_matrix.json",

        SCHEMAS_ROOT / "conflict_matrix.v1.schema.json",

    ),

    "prompt_catalog_lite": (

        CATALOG_ROOT / "prompt_catalog_lite.json",

        SCHEMAS_ROOT / "prompt_catalog_lite.schema.json",

    ),

    "protected_runtime_paths": (

        CATALOG_ROOT / "protected_runtime_paths.json",

        SCHEMAS_ROOT / "protected_runtime_paths.v1.schema.json",

    ),

    "cnki_zotero_workflow": (

        CATALOG_ROOT / "cnki_zotero_workflow.json",

        SCHEMAS_ROOT / "cnki_zotero_workflow.v1.schema.json",

    ),

    "scholar_browser_patterns": (

        CATALOG_ROOT / "scholar_browser_patterns.json",

        SCHEMAS_ROOT / "scholar_browser_patterns.v1.schema.json",

    ),

    "peer_review_workflow": (

        CATALOG_ROOT / "peer_review_workflow.json",

        SCHEMAS_ROOT / "peer_review_workflow.v1.schema.json",

    ),

    "scientific_figure_workflow": (

        CATALOG_ROOT / "scientific_figure_workflow.json",

        SCHEMAS_ROOT / "scientific_figure_workflow.v1.schema.json",

    ),

    "manuscript_writing_workflow": (

        CATALOG_ROOT / "manuscript_writing_workflow.json",

        SCHEMAS_ROOT / "manuscript_writing_workflow.v1.schema.json",

    ),

    "research_presentation_workflow": (

        CATALOG_ROOT / "research_presentation_workflow.json",

        SCHEMAS_ROOT / "research_presentation_workflow.v1.schema.json",

    ),

    "environment_layer_contract": (

        CATALOG_ROOT / "environment_layer_contract.json",

        SCHEMAS_ROOT / "environment_layer_contract.v1.schema.json",

    ),

}

READING_EVIDENCE_PATH = CATALOG_ROOT / "workflow_governance_source_evidence.json"



MEMORY_DECISIONS = {"governance_kernel", "skill", "obsidian", "codex_native", "discard"}

CORE_CONTROLLERS = {"research-autopilot", "vela-runtime-manager", "project-retrospective-evolver", "envctl"}





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





def validate_governance_contracts() -> dict[str, Any]:

    errors: list[str] = []

    warnings: list[str] = []

    payloads: dict[str, dict[str, Any]] = {}



    for label, (payload_path, schema_path) in CONTRACTS.items():

        schema = _safe_load(schema_path, f"{label}.schema", errors)

        payload = _safe_load(payload_path, label, errors)

        if schema:

            errors.extend(collect_schema_document_errors(schema, f"{label}.schema"))

        if schema and payload:

            errors.extend(collect_schema_errors(payload, schema, label))

        payloads[label] = payload



    errors.extend(_collect_kernel_link_errors(payloads))

    errors.extend(_collect_memory_policy_errors(payloads.get("memory_admission_policy", {})))

    errors.extend(_collect_local_memory_system_errors(payloads.get("local_memory_system", {})))

    errors.extend(_collect_source_rule_crosswalk_errors(payloads.get("governance_source_rule_crosswalk", {})))



    details = {

        "contracts": {

            label: {

                "payload": str(paths[0].relative_to(SKILLS_ROOT)),

                "schema": str(paths[1].relative_to(SKILLS_ROOT)),

                "payload_exists": paths[0].exists(),

                "schema_exists": paths[1].exists(),

            }

            for label, paths in CONTRACTS.items()

        },

        "evolution_backlog": build_evolution_backlog_summary(),

    }

    return build_validator_result(

        validator="validate_governance",

        scope="governance_kernel",

        errors=errors,

        warnings=warnings,

        details=details,

    )





def _collect_kernel_link_errors(payloads: dict[str, dict[str, Any]]) -> list[str]:

    kernel = payloads.get("governance_kernel", {})

    errors: list[str] = []

    link_map = {

        "memory_policy_ref": CATALOG_ROOT / "memory_admission_policy.json",

        "external_adoption_policy_ref": CATALOG_ROOT / "external_adoption_reviews.json",

    }

    for key, expected in link_map.items():

        if not expected.exists():

            errors.append(f"governance_kernel:{key}:missing-target:{expected}")

        elif kernel.get(key) != str(expected.relative_to(SKILLS_ROOT.parent)).replace("\\", "/"):

            errors.append(f"governance_kernel:{key}:unexpected-ref:{kernel.get(key)}")



    controllers = {item.get("id") for item in kernel.get("controllers", []) if isinstance(item, dict)}

    missing_controllers = CORE_CONTROLLERS - controllers

    errors.extend(f"governance_kernel:missing-controller:{item}" for item in sorted(missing_controllers))

    return errors





def _collect_memory_policy_errors(policy: dict[str, Any]) -> list[str]:

    placements = policy.get("placements", [])

    labels = [item.get("decision_label") for item in placements if isinstance(item, dict)]

    found = set(labels)

    errors = [f"memory_admission_policy:missing-placement:{item}" for item in sorted(MEMORY_DECISIONS - found)]

    duplicates = [label for label, count in Counter(labels).items() if count > 1]

    errors.extend(f"memory_admission_policy:duplicate-placement:{item}" for item in sorted(duplicates))

    return errors





def _collect_local_memory_system_errors(policy: dict[str, Any]) -> list[str]:

    if not policy:

        return ["local_memory_system:missing-policy"]

    errors: list[str] = []

    forbidden_defaults = set(policy.get("storage_boundaries", {}).get("forbidden_defaults", []))

    for item in [

        "no_vector_database_by_default",

        "no_unvetted_background_service_by_default",

        "no_unvetted_vector_database_by_default",

        "no_transcript_ingestion_by_default",

        "no_external_hook_by_default",

    ]:

        if item not in forbidden_defaults:

            errors.append(f"local_memory_system:missing-lightweight-default:{item}")

    automation = policy.get("automation_policy", {})

    if automation.get("mode") != "controlled_auto_landing":

        errors.append("local_memory_system:automation-mode-not-controlled")

    if automation.get("default_execution_environment") != "local":

        errors.append("local_memory_system:automation-environment-not-local")

    if any(

        item.get("auto_promotion_allowed") is True

        for item in policy.get("memory_layers", [])

        if isinstance(item, dict)

    ):

        errors.append("local_memory_system:auto-promotion-must-remain-disabled")

    return errors





def _collect_source_rule_crosswalk_errors(crosswalk: dict[str, Any]) -> list[str]:

    sources = crosswalk.get("sources", [])

    principles = crosswalk.get("principles", [])

    source_ids = [item.get("id") for item in sources if isinstance(item, dict)]

    principle_ids = [item.get("id") for item in principles if isinstance(item, dict)]

    source_set = set(source_ids)

    errors: list[str] = []

    for source_id, count in Counter(source_ids).items():

        if count > 1:

            errors.append(f"governance_source_rule_crosswalk:duplicate-source:{source_id}")

    for principle_id, count in Counter(principle_ids).items():

        if count > 1:

            errors.append(f"governance_source_rule_crosswalk:duplicate-principle:{principle_id}")

    required_principles = {

        "technical-science-layer",

        "feedforward-constraint",

        "disturbance-uncertainty-control",

        "platform-article-19-principles",

    }

    errors.extend(

        f"governance_source_rule_crosswalk:missing-principle:{item}"

        for item in sorted(required_principles - set(principle_ids))

    )

    for principle in principles:

        if not isinstance(principle, dict):

            continue

        principle_id = principle.get("id", "<unknown>")

        unknown_sources = sorted(set(principle.get("source_ids", [])) - source_set)

        errors.extend(

            f"governance_source_rule_crosswalk:{principle_id}:unknown-source:{item}"

            for item in unknown_sources

        )

    return errors





def build_reading_status() -> dict[str, Any]:

    reading = load_json(READING_EVIDENCE_PATH)

    required = int(reading["required_passes_per_source"])

    logs = reading.get("pass_logs", [])

    completed_by_source = Counter(

        item.get("source_id")

        for item in logs

        if isinstance(item, dict) and item.get("status") == "complete"

    )

    sources = []

    for source in reading.get("source_files", []):

        source_id = source["id"]

        completed = completed_by_source[source_id]

        sources.append(

            {

                "id": source_id,

                "title": source["title"],

                "language": source["language"],

                "page_count": source["page_count"],

                "text_layer_status": source["text_layer_status"],

                "chapter_coverage_required": source["chapter_coverage_required"],

                "passes_required": required,

                "passes_complete": completed,

                "blocked_by_ocr": source["text_layer_status"] == "none_ocr_required",

            }

        )

    return {

        "schema_version": reading["schema_version"],

        "scope": reading.get("scope", "source_evidence_only"),

        "required_passes_per_source": required,

        "sources": sources,

        "article_sources": reading.get("article_sources", []),

        "all_sources_three_pass_complete": all(item["passes_complete"] >= required for item in sources),

        "ocr_required_sources": [item["id"] for item in sources if item["blocked_by_ocr"]],

    }





def build_evolution_backlog_summary() -> dict[str, Any]:

    backlog_path, _schema = CONTRACTS["evolution_backlog"]

    backlog = load_json(backlog_path)

    events = backlog.get("events", [])

    by_status = Counter(item.get("status", "<missing>") for item in events if isinstance(item, dict))

    by_target = Counter(item.get("proposed_target", "<missing>") for item in events if isinstance(item, dict))

    return {

        "schema_version": backlog["schema_version"],

        "event_count": len(events),

        "by_status": dict(sorted(by_status.items())),

        "by_target": dict(sorted(by_target.items())),

        "open_events": [

            item

            for item in events

            if isinstance(item, dict) and item.get("status") in {"observed", "proposed", "accepted"}

        ],

    }





def build_skill_audit_report() -> dict[str, Any]:

    catalog = load_json(CATALOG_ROOT / "skill_catalog.json")

    kernel = load_json(CATALOG_ROOT / "governance_kernel.json")

    active_skills = {

        name: item

        for name, item in catalog.get("skills", {}).items()

        if isinstance(item, dict) and item.get("status") == "active"

    }

    role_counts = Counter(str(item.get("role", "<missing>")) for item in active_skills.values())

    category_counts = Counter(str(item.get("category", "<missing>")) for item in active_skills.values())

    controller_ids = [item["id"] for item in kernel.get("controllers", [])]

    missing_core_skills = sorted(

        controller for controller in controller_ids if controller != "envctl" and controller not in active_skills

    )

    return {

        "schema_version": "governance_skill_audit.v1",

        "generated_at": _utc_now(),

        "mode": "controlled_auto_landing",

        "source_files_written": False,

        "active_skill_count": len(active_skills),

        "role_counts": dict(sorted(role_counts.items())),

        "category_counts": dict(sorted(category_counts.items())),

        "core_controllers": controller_ids,

        "missing_core_controller_skills": missing_core_skills,

        "memory_policy": load_json(CATALOG_ROOT / "memory_admission_policy.json"),

        "local_memory_system": load_json(CATALOG_ROOT / "local_memory_system.json"),

        "evolution_backlog": build_evolution_backlog_summary(),

        "suggested_next_checks": [

            "python -m skills.scripts.envctl validate memory",

            "python -m skills.scripts.envctl validate governance",

            "python -m skills.scripts.envctl validate stack",

            "python -m skills.scripts.envctl memory status --summary",

            "python -m skills.scripts.envctl governance evolution-backlog",

            "python -m skills.scripts.envctl evolution intake --write-report"

        ],

    }

def write_report(report: dict[str, Any], output: Path | None = None) -> Path:

    if output is None:

        date = datetime.now().strftime("%Y-%m-%d")

        output = OUTPUTS_ROOT / "reports" / "governance-daily" / f"{date}.json"

    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return output
