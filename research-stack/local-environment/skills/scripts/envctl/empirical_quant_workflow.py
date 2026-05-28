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


CONTRACT_PATH = CATALOG_ROOT / "empirical_quant_workflow.json"
SCHEMA_PATH = SCHEMAS_ROOT / "empirical_quant_workflow.v1.schema.json"

REQUIRED_OPTION = "option_b_contract_first_empirical_quant_integration"
REQUIRED_MODES = {
    "empirical_question_intake",
    "identification_strategy_audit",
    "full_empirical_pipeline",
    "robustness_and_sensitivity",
    "tables_figures_and_interpretation",
    "replication_package_preflight",
    "academic_humanization_surface_audit",
}
REQUIRED_DESIGN_FAMILIES = {
    "descriptive_or_correlational",
    "panel_fixed_effects",
    "difference_in_differences",
    "instrumental_variables",
    "regression_discontinuity",
    "matching_weighting_and_balance",
    "synthetic_control_and_sdid",
    "machine_learning_causal",
    "shift_share_bartik",
    "triple_difference",
    "rct_or_field_experiment",
    "dose_response_or_continuous_treatment",
    "mechanism_mediation_and_distributional_effects",
}
REQUIRED_TOOL_ECOSYSTEMS = {
    "stata_aer_replication_pipeline",
}
REQUIRED_DIAGNOSTICS = {
    "data_cleaning_merge_integrity",
    "missingness_outlier_balance",
    "measurement_validity",
    "model_assumption_check",
    "causal_identification_red_flags",
    "inference_cluster_power",
}
REQUIRED_ROBUSTNESS_STEPS = {
    "specification_gradient",
    "alternative_estimators",
    "placebo_negative_control",
    "heterogeneity_mechanism",
    "sensitivity_bounds",
    "publication_ready_output",
}
REQUIRED_SAFETY_RULES = {
    "no_causal_language_without_design",
    "no_dsl_black_box_without_audit",
    "no_generated_results_without_data",
    "no_ai_humanization_claim_or_evidence_change",
    "no_detector_evasion_guarantee",
    "no_detector_metric_as_goal",
    "no_economics_standard_as_universal_default",
    "no_naive_twfe_as_staggered_default",
    "no_stata_default_without_project_need",
    "no_stata_output_without_script_trace",
    "project_outputs_not_global_outputs",
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


def validate_empirical_quant_workflow() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    schema = _safe_load(SCHEMA_PATH, "empirical_quant_workflow.schema", errors)
    contract = _safe_load(CONTRACT_PATH, "empirical_quant_workflow", errors)
    if schema:
        errors.extend(collect_schema_document_errors(schema, "empirical_quant_workflow.schema"))
    if schema and contract:
        errors.extend(collect_schema_errors(contract, schema, "empirical_quant_workflow"))
    if contract:
        errors.extend(_collect_contract_errors(contract))

    details = {
        "contract": {
            "payload": str(CONTRACT_PATH.relative_to(SKILLS_ROOT)),
            "schema": str(SCHEMA_PATH.relative_to(SKILLS_ROOT)),
            "payload_exists": CONTRACT_PATH.exists(),
            "schema_exists": SCHEMA_PATH.exists(),
        },
        "mode_count": len(contract.get("workflow_modes", [])) if isinstance(contract, dict) else 0,
        "design_family_count": len(contract.get("design_families", [])) if isinstance(contract, dict) else 0,
        "tool_ecosystem_count": len(contract.get("tool_ecosystems", [])) if isinstance(contract, dict) else 0,
        "diagnostic_count": len(contract.get("diagnostics", [])) if isinstance(contract, dict) else 0,
        "robustness_step_count": len(contract.get("robustness_ladder", [])) if isinstance(contract, dict) else 0,
        "safety_rule_count": len(contract.get("safety_rules", [])) if isinstance(contract, dict) else 0,
    }
    return build_validator_result(
        validator="validate_empirical_quant_workflow",
        scope="empirical_quant_workflow",
        errors=errors,
        warnings=warnings,
        details=details,
    )


def _collect_contract_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    option_ids = [item.get("id") for item in contract.get("adoption_options", []) if isinstance(item, dict)]
    selected = [item.get("id") for item in contract.get("adoption_options", []) if item.get("decision") == "selected"]
    if contract.get("selected_strategy") != REQUIRED_OPTION:
        errors.append(f"empirical-quant-workflow:selected-strategy-mismatch:{contract.get('selected_strategy')}")
    if selected != [REQUIRED_OPTION]:
        errors.append(f"empirical-quant-workflow:selected-option-mismatch:{selected}")
    for option_id, count in Counter(option_ids).items():
        if count > 1:
            errors.append(f"empirical-quant-workflow:duplicate-option:{option_id}")

    modes = {item.get("id"): item for item in contract.get("workflow_modes", []) if isinstance(item, dict)}
    design_families = {item.get("id"): item for item in contract.get("design_families", []) if isinstance(item, dict)}
    tool_ecosystems = {item.get("id"): item for item in contract.get("tool_ecosystems", []) if isinstance(item, dict)}
    diagnostics = {item.get("id"): item for item in contract.get("diagnostics", []) if isinstance(item, dict)}
    robustness_steps = {item.get("id"): item for item in contract.get("robustness_ladder", []) if isinstance(item, dict)}
    safety_rules = {item.get("id"): item for item in contract.get("safety_rules", []) if isinstance(item, dict)}

    errors.extend(f"empirical-quant-workflow:missing-mode:{item}" for item in sorted(REQUIRED_MODES - set(modes)))
    errors.extend(
        f"empirical-quant-workflow:missing-design-family:{item}"
        for item in sorted(REQUIRED_DESIGN_FAMILIES - set(design_families))
    )
    errors.extend(
        f"empirical-quant-workflow:missing-tool-ecosystem:{item}"
        for item in sorted(REQUIRED_TOOL_ECOSYSTEMS - set(tool_ecosystems))
    )
    errors.extend(
        f"empirical-quant-workflow:missing-diagnostic:{item}"
        for item in sorted(REQUIRED_DIAGNOSTICS - set(diagnostics))
    )
    errors.extend(
        f"empirical-quant-workflow:missing-robustness-step:{item}"
        for item in sorted(REQUIRED_ROBUSTNESS_STEPS - set(robustness_steps))
    )
    errors.extend(
        f"empirical-quant-workflow:missing-safety-rule:{item}"
        for item in sorted(REQUIRED_SAFETY_RULES - set(safety_rules))
    )

    for family_id, family in design_families.items():
        unknown_diagnostics = sorted(set(family.get("required_diagnostics", [])) - set(diagnostics))
        errors.extend(
            f"empirical-quant-workflow:{family_id}:unknown-diagnostic:{item}"
            for item in unknown_diagnostics
        )

    valid_required_for = set(design_families) | {"all_design_families"}
    for step_id, step in robustness_steps.items():
        unknown_required_for = sorted(set(step.get("required_for", [])) - valid_required_for)
        errors.extend(
            f"empirical-quant-workflow:{step_id}:unknown-required-for:{item}"
            for item in unknown_required_for
        )

    output_contract = contract.get("output_contract", {})
    if output_contract.get("quality_gate_report") != "logs/quality-gates/empirical-quant-report.json":
        errors.append("empirical-quant-workflow:quality-report-path-mismatch")
    required_artifacts = set(output_contract.get("required_artifacts", []))
    for required in {"design family selection", "diagnostics checklist", "robustness matrix"}:
        if required not in required_artifacts:
            errors.append(f"empirical-quant-workflow:missing-required-artifact:{required}")

    did = design_families.get("difference_in_differences", {})
    did_text = " ".join(did.get("preferred_estimators", []) + did.get("red_flags", []))
    if "Callaway-Sant'Anna" not in did_text or "TWFE" not in did_text:
        errors.append("empirical-quant-workflow:did-modern-defaults-missing")

    iv = design_families.get("instrumental_variables", {})
    if "Anderson-Rubin" not in " ".join(iv.get("preferred_estimators", [])):
        errors.append("empirical-quant-workflow:iv-weak-robust-inference-missing")

    stata = tool_ecosystems.get("stata_aer_replication_pipeline", {})
    stata_text = " ".join(
        stata.get("required_conventions", [])
        + stata.get("core_packages_or_commands", [])
        + stata.get("pipeline_files", [])
        + stata.get("red_flags", [])
    )
    for token in ("reghdfe", "csdid", "ivreg2", "rdrobust", "run_all.do"):
        if token not in stata_text:
            errors.append(f"empirical-quant-workflow:stata-ecosystem-missing:{token}")

    humanization = safety_rules.get("no_ai_humanization_claim_or_evidence_change", {})
    if "citations" not in humanization.get("rule", ""):
        errors.append("empirical-quant-workflow:humanization-citation-lock-missing")

    return errors
