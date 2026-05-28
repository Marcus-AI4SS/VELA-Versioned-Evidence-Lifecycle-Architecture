from __future__ import annotations



import json

from collections import Counter

from pathlib import Path

from typing import Any



try:

    from ..path_utils import CATALOG_ROOT, REPO_ROOT, SCHEMAS_ROOT, SKILLS_ROOT

    from .schema_validation import collect_schema_document_errors, collect_schema_errors, load_json

    from .validator_envelope import build_validator_result

except ImportError:  # pragma: no cover

    from path_utils import CATALOG_ROOT, REPO_ROOT, SCHEMAS_ROOT, SKILLS_ROOT

    from envctl.schema_validation import collect_schema_document_errors, collect_schema_errors, load_json

    from envctl.validator_envelope import build_validator_result





CONTRACT_PATH = CATALOG_ROOT / "skill_workbench_policy.json"

SCHEMA_PATH = SCHEMAS_ROOT / "skill_workbench_policy.v1.schema.json"



REQUIRED_SELECTED_OPTION = "option_b_contract_first_local_workbench_policy"

REQUIRED_PACKAGE_CONTRACTS = {

    "research_autopilot_plugin_skill",

    "standalone_runtime_skill",

    "external_candidate_skill",

    "project_local_contract",

}

REQUIRED_BORROWED_PATTERNS = {

    "manifested_skill_inventory",

    "source_note_preservation",

    "validate_before_install",

    "public_template_scrub",

    "workbench_keyword_harvest_status_model",

    "workbench_plotting_tool_selection",

    "workbench_r_plot_micro_patterns",

    "workbench_ppt_image_wall_manifest",

    "workbench_thesis_docx_manifest_watch",

    "canonical_helper_resolution",

    "frontmatter_metadata_lint",

}

REQUIRED_SAFETY_RULES = {

    "no_runtime_first_source_edits",

    "no_protected_skill_mutation",

    "no_external_install_without_gate",

    "no_private_path_publication",

    "validate_before_runtime_sync",

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





def validate_skill_workbench_policy() -> dict[str, Any]:

    errors: list[str] = []

    warnings: list[str] = []



    schema = _safe_load(SCHEMA_PATH, "skill_workbench_policy.schema", errors)

    policy = _safe_load(CONTRACT_PATH, "skill_workbench_policy", errors)

    if schema:

        errors.extend(collect_schema_document_errors(schema, "skill_workbench_policy.schema"))

    if schema and policy:

        errors.extend(collect_schema_errors(policy, schema, "skill_workbench_policy"))

    if policy:

        errors.extend(_collect_policy_errors(policy))



    details = {

        "contract": {

            "payload": str(CONTRACT_PATH.relative_to(SKILLS_ROOT)),

            "schema": str(SCHEMA_PATH.relative_to(SKILLS_ROOT)),

            "payload_exists": CONTRACT_PATH.exists(),

            "schema_exists": SCHEMA_PATH.exists(),

        },

        "source_review_count": len(policy.get("source_review_refs", [])) if isinstance(policy, dict) else 0,

        "package_contract_count": len(policy.get("package_contracts", [])) if isinstance(policy, dict) else 0,

        "borrowed_pattern_count": len(policy.get("borrowed_patterns", [])) if isinstance(policy, dict) else 0,

        "workflow_step_count": len(policy.get("required_workflow", [])) if isinstance(policy, dict) else 0,

    }

    return build_validator_result(

        validator="validate_skill_workbench_policy",

        scope="skill_workbench_policy",

        errors=errors,

        warnings=warnings,

        details=details,

    )





def _collect_policy_errors(policy: dict[str, Any]) -> list[str]:

    errors: list[str] = []



    selected = [item.get("id") for item in policy.get("adoption_options", []) if item.get("decision") == "selected"]

    if policy.get("selected_strategy") != REQUIRED_SELECTED_OPTION:

        errors.append(f"skill-workbench-policy:selected-strategy-mismatch:{policy.get('selected_strategy')}")

    if selected != [REQUIRED_SELECTED_OPTION]:

        errors.append(f"skill-workbench-policy:selected-option-mismatch:{selected}")



    for label, items in {

        "source": [item.get("upstream") for item in policy.get("source_review_refs", []) if isinstance(item, dict)],

        "option": [item.get("id") for item in policy.get("adoption_options", []) if isinstance(item, dict)],

        "package": [item.get("id") for item in policy.get("package_contracts", []) if isinstance(item, dict)],

        "pattern": [item.get("id") for item in policy.get("borrowed_patterns", []) if isinstance(item, dict)],

        "safety": [item.get("id") for item in policy.get("safety_rules", []) if isinstance(item, dict)],

    }.items():

        for item_id, count in Counter(items).items():

            if count > 1:

                errors.append(f"skill-workbench-policy:duplicate-{label}:{item_id}")



    package_ids = {item.get("id") for item in policy.get("package_contracts", []) if isinstance(item, dict)}

    errors.extend(

        f"skill-workbench-policy:missing-package-contract:{item_id}"

        for item_id in sorted(REQUIRED_PACKAGE_CONTRACTS - package_ids)

    )

    pattern_ids = {item.get("id") for item in policy.get("borrowed_patterns", []) if isinstance(item, dict)}

    errors.extend(

        f"skill-workbench-policy:missing-borrowed-pattern:{item_id}"

        for item_id in sorted(REQUIRED_BORROWED_PATTERNS - pattern_ids)

    )

    safety_ids = {item.get("id") for item in policy.get("safety_rules", []) if isinstance(item, dict)}

    errors.extend(

        f"skill-workbench-policy:missing-safety-rule:{item_id}"

        for item_id in sorted(REQUIRED_SAFETY_RULES - safety_ids)

    )



    workflow_orders = [item.get("order") for item in policy.get("required_workflow", []) if isinstance(item, dict)]

    if workflow_orders != sorted(workflow_orders):

        errors.append(f"skill-workbench-policy:workflow-order-not-sorted:{workflow_orders}")

    if workflow_orders and workflow_orders[0] != 1:

        errors.append(f"skill-workbench-policy:workflow-order-does-not-start-at-1:{workflow_orders[0]}")



    boundary = policy.get("local_boundaries", {})

    if isinstance(boundary, dict):

        source = str(boundary.get("source_of_truth", ""))

        if source not in {"<VELA_RUNTIME_ROOT>", "skills-environment-local"} and "skills-environment-local" not in source:

            errors.append(f"skill-workbench-policy:source-of-truth-mismatch:{source}")

        protected = str(boundary.get("protected_runtime_policy", ""))

        if "protected_runtime_paths" not in protected:

            errors.append("skill-workbench-policy:protected-runtime-policy-missing")



    return errors
