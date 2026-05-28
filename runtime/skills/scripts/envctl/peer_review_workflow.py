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





PAYLOAD_PATH = CATALOG_ROOT / "peer_review_workflow.json"

SCHEMA_PATH = SCHEMAS_ROOT / "peer_review_workflow.v1.schema.json"

REQUIRED_UPSTREAMS = {

    "qqfly1to19/awesome_proofreading_auto",

    "c-narcissus/research-review-skill-factory",

    "Imbad0202/academic-research-skills",

    "wanshuiyin/Auto-claude-code-research-in-sleep",

    "Yuan1z0825/nature-skills",

    "Leey21/awesome-ai-research-writing",

}

REQUIRED_ROLES = {

    "lead_integrator",

    "theory_literature_reviewer",

    "method_identification_reviewer",

    "evidence_citation_auditor",

    "writing_structure_reviewer",

    "figure_repro_reviewer",

    "review_response_reviewer",

    "adversarial_logic_reviewer",

}

REQUIRED_ISSUE_FIELDS = {

    "issue_id",

    "role_id",

    "severity",

    "manuscript_location",

    "evidence_seen",

    "diagnosis",

    "required_action",

    "confidence",

    "blocker",

}

REQUIRED_SAFETY_RULES = {

    "reviewers_must_not_modify_manuscript",

    "metadata_only_cannot_support_strong_claim",

    "response_claim_requires_real_location",

    "human_checkpoint_before_mutation",

    "social_science_standard_first",

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





def _duplicates(values: list[str]) -> list[str]:

    return sorted(value for value, count in Counter(values).items() if count > 1)





def validate_peer_review_workflow() -> dict[str, Any]:

    errors: list[str] = []

    warnings: list[str] = []



    schema = _safe_load(SCHEMA_PATH, "peer_review_workflow.schema", errors)

    payload = _safe_load(PAYLOAD_PATH, "peer_review_workflow", errors)

    if schema:

        errors.extend(collect_schema_document_errors(schema, "peer_review_workflow.v1.schema.json"))

    if schema and payload:

        errors.extend(collect_schema_errors(payload, schema, "peer_review_workflow.json"))



    if payload:

        errors.extend(_collect_link_errors(payload))



    details = {

        "contract": {

            "payload": str(PAYLOAD_PATH.relative_to(SKILLS_ROOT)),

            "schema": str(SCHEMA_PATH.relative_to(SKILLS_ROOT)),

            "payload_exists": PAYLOAD_PATH.exists(),

            "schema_exists": SCHEMA_PATH.exists(),

        },

        "mode_count": len(payload.get("modes", [])) if payload else 0,

        "role_count": len(payload.get("roles", [])) if payload else 0,

        "stage_count": len(payload.get("stage_sequence", [])) if payload else 0,

        "report_count": len(payload.get("report_contracts", [])) if payload else 0,

    }

    return build_validator_result(

        validator="validate_peer_review_workflow",

        scope="peer_review_workflow",

        errors=errors,

        warnings=warnings,

        details=details,

    )





def _collect_link_errors(payload: dict[str, Any]) -> list[str]:

    errors: list[str] = []



    upstreams = {item.get("upstream") for item in payload.get("source_review_refs", []) if isinstance(item, dict)}

    errors.extend(f"peer_review_workflow:missing-upstream:{item}" for item in sorted(REQUIRED_UPSTREAMS - upstreams))



    adoption_options = payload.get("adoption_options", [])

    option_ids = [item.get("id") for item in adoption_options if isinstance(item, dict)]

    for duplicate in _duplicates([item for item in option_ids if isinstance(item, str)]):

        errors.append(f"peer_review_workflow:duplicate-adoption-option:{duplicate}")

    selected_strategy = payload.get("selected_strategy")

    selected_options = [

        item

        for item in adoption_options

        if isinstance(item, dict) and item.get("decision") == "selected"

    ]

    if selected_strategy not in option_ids:

        errors.append(f"peer_review_workflow:selected-strategy-unknown:{selected_strategy}")

    if len(selected_options) != 1:

        errors.append("peer_review_workflow:selected-option-count-must-be-one")

    elif selected_options[0].get("id") != selected_strategy:

        errors.append("peer_review_workflow:selected-option-mismatch")



    modes = payload.get("modes", [])

    mode_ids = [item.get("id") for item in modes if isinstance(item, dict)]

    mode_set = set(mode_ids)

    for duplicate in _duplicates([item for item in mode_ids if isinstance(item, str)]):

        errors.append(f"peer_review_workflow:duplicate-mode:{duplicate}")



    stages = payload.get("stage_sequence", [])

    stage_ids = [item.get("id") for item in stages if isinstance(item, dict)]

    stage_set = set(stage_ids)

    for duplicate in _duplicates([item for item in stage_ids if isinstance(item, str)]):

        errors.append(f"peer_review_workflow:duplicate-stage:{duplicate}")



    roles = payload.get("roles", [])

    role_ids = [item.get("role_id") for item in roles if isinstance(item, dict)]

    role_set = set(role_ids)

    for duplicate in _duplicates([item for item in role_ids if isinstance(item, str)]):

        errors.append(f"peer_review_workflow:duplicate-role:{duplicate}")

    errors.extend(f"peer_review_workflow:missing-role:{item}" for item in sorted(REQUIRED_ROLES - role_set))



    for mode in modes:

        if not isinstance(mode, dict):

            continue

        mode_id = mode.get("id", "<unknown>")

        unknown_stages = set(mode.get("stage_ids", [])) - stage_set

        errors.extend(f"peer_review_workflow:mode:{mode_id}:unknown-stage:{item}" for item in sorted(unknown_stages))

        if mode_id == "standard_single_review" and mode.get("default_subagent_policy") == "always_multi_agent":

            errors.append("peer_review_workflow:standard-single-review-must-not-default-multi-agent")

        if mode_id == "submission_package_review" and mode.get("default_subagent_policy") != "always_multi_agent":

            errors.append("peer_review_workflow:submission-package-must-default-multi-agent")



    for stage in stages:

        if not isinstance(stage, dict):

            continue

        stage_id = stage.get("id", "<unknown>")

        unknown_modes = set(stage.get("applies_to_modes", [])) - mode_set

        errors.extend(f"peer_review_workflow:stage:{stage_id}:unknown-mode:{item}" for item in sorted(unknown_modes))



    for trigger in payload.get("trigger_rules", []):

        if not isinstance(trigger, dict):

            continue

        trigger_id = trigger.get("id", "<unknown>")

        if trigger.get("mode_id") not in mode_set:

            errors.append(f"peer_review_workflow:trigger:{trigger_id}:unknown-mode:{trigger.get('mode_id')}")



    issue_fields = set(payload.get("issue_contract", {}).get("required_fields", []))

    errors.extend(f"peer_review_workflow:missing-issue-field:{item}" for item in sorted(REQUIRED_ISSUE_FIELDS - issue_fields))



    report_ids = [item.get("id") for item in payload.get("report_contracts", []) if isinstance(item, dict)]

    for duplicate in _duplicates([item for item in report_ids if isinstance(item, str)]):

        errors.append(f"peer_review_workflow:duplicate-report:{duplicate}")



    safety_ids = {

        item.get("id")

        for item in payload.get("safety_rules", [])

        if isinstance(item, dict)

    }

    errors.extend(f"peer_review_workflow:missing-safety-rule:{item}" for item in sorted(REQUIRED_SAFETY_RULES - safety_ids))

    return errors
