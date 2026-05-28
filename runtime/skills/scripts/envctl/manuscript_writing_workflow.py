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





CONTRACT_PATH = CATALOG_ROOT / "manuscript_writing_workflow.json"

SCHEMA_PATH = SCHEMAS_ROOT / "manuscript_writing_workflow.v1.schema.json"



REQUIRED_OPTION = "option_b_contract_first_social_science_integration"

REQUIRED_LANGUAGE_TARGETS = {

    "cn_humanities_social_science",

    "en_high_impact_journal",

    "bilingual_transition",

}

REQUIRED_DISCIPLINE_TARGETS = {

    "humanities_social_science",

    "computational_social_science_or_method",

    "traditional_quantitative_social_science",

    "qualitative_or_interpretive_social_science",

}

REQUIRED_MODES = {

    "draft_section",

    "rewrite_structure",

    "polish_language",

    "translate_rebuild",

    "format_sensitive_translation",

    "micro_revision",

    "humanized_surface_check",

    "venue_migration",

    "final_quality_audit",

    "humanities_thesis_problem_framing",

    "target_journal_adaptation",

}

REQUIRED_SECTIONS = {

    "title",

    "abstract",

    "introduction",

    "literature_review",

    "methods",

    "results",

    "discussion",

    "conclusion",

    "humanities_thesis_chapter",

}

REQUIRED_POLISHING_LEVELS = {

    "level_1_argument_repair",

    "level_2_paragraph_flow",

    "level_3_sentence_style",

    "level_4_submission_surface",

}

REQUIRED_SAFETY_RULES = {

    "no_fabricated_evidence_or_references",

    "no_universal_nature_default",

    "no_stem_default_for_social_science",

    "no_sentence_polish_over_broken_logic",

    "citation_capture_when_references_touched",

    "no_auto_thesis_studio_for_ordinary_papers",

    "no_prompt_template_overrides_contracts",

    "no_theory_material_forced_fit",

    "no_metadata_only_literature_analysis",

    "no_unread_corpus_style_extraction",

    "no_journal_style_over_claim_integrity",

    "no_detector_metric_as_goal",

    "no_fake_human_noise",

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





def validate_manuscript_writing_workflow() -> dict[str, Any]:

    errors: list[str] = []

    warnings: list[str] = []



    schema = _safe_load(SCHEMA_PATH, "manuscript_writing_workflow.schema", errors)

    contract = _safe_load(CONTRACT_PATH, "manuscript_writing_workflow", errors)

    if schema:

        errors.extend(collect_schema_document_errors(schema, "manuscript_writing_workflow.schema"))

    if schema and contract:

        errors.extend(collect_schema_errors(contract, schema, "manuscript_writing_workflow"))

    if contract:

        errors.extend(_collect_contract_errors(contract))



    details = {

        "contract": {

            "payload": str(CONTRACT_PATH.relative_to(SKILLS_ROOT)),

            "schema": str(SCHEMA_PATH.relative_to(SKILLS_ROOT)),

            "payload_exists": CONTRACT_PATH.exists(),

            "schema_exists": SCHEMA_PATH.exists(),

        },

        "language_target_count": len(contract.get("language_targets", [])) if isinstance(contract, dict) else 0,

        "discipline_target_count": len(contract.get("discipline_targets", [])) if isinstance(contract, dict) else 0,

        "workflow_mode_count": len(contract.get("workflow_modes", [])) if isinstance(contract, dict) else 0,

        "section_contract_count": len(contract.get("section_contracts", [])) if isinstance(contract, dict) else 0,

        "safety_rule_count": len(contract.get("safety_rules", [])) if isinstance(contract, dict) else 0,

    }

    return build_validator_result(

        validator="validate_manuscript_writing_workflow",

        scope="manuscript_writing_workflow",

        errors=errors,

        warnings=warnings,

        details=details,

    )





def _collect_contract_errors(contract: dict[str, Any]) -> list[str]:

    errors: list[str] = []

    option_ids = [item.get("id") for item in contract.get("adoption_options", []) if isinstance(item, dict)]

    selected = [item.get("id") for item in contract.get("adoption_options", []) if item.get("decision") == "selected"]

    if contract.get("selected_strategy") != REQUIRED_OPTION:

        errors.append(f"manuscript-writing-workflow:selected-strategy-mismatch:{contract.get('selected_strategy')}")

    if selected != [REQUIRED_OPTION]:

        errors.append(f"manuscript-writing-workflow:selected-option-mismatch:{selected}")

    for option_id, count in Counter(option_ids).items():

        if count > 1:

            errors.append(f"manuscript-writing-workflow:duplicate-option:{option_id}")



    language_targets = {item.get("id"): item for item in contract.get("language_targets", []) if isinstance(item, dict)}

    discipline_targets = {item.get("id"): item for item in contract.get("discipline_targets", []) if isinstance(item, dict)}

    modes = {item.get("id"): item for item in contract.get("workflow_modes", []) if isinstance(item, dict)}

    sections = {item.get("id"): item for item in contract.get("section_contracts", []) if isinstance(item, dict)}

    polishing_levels = {item.get("id"): item for item in contract.get("polishing_levels", []) if isinstance(item, dict)}

    safety_rules = {item.get("id"): item for item in contract.get("safety_rules", []) if isinstance(item, dict)}



    errors.extend(

        f"manuscript-writing-workflow:missing-language-target:{item}"

        for item in sorted(REQUIRED_LANGUAGE_TARGETS - set(language_targets))

    )

    errors.extend(

        f"manuscript-writing-workflow:missing-discipline-target:{item}"

        for item in sorted(REQUIRED_DISCIPLINE_TARGETS - set(discipline_targets))

    )

    errors.extend(f"manuscript-writing-workflow:missing-mode:{item}" for item in sorted(REQUIRED_MODES - set(modes)))

    errors.extend(

        f"manuscript-writing-workflow:missing-section:{item}" for item in sorted(REQUIRED_SECTIONS - set(sections))

    )

    errors.extend(

        f"manuscript-writing-workflow:missing-polishing-level:{item}"

        for item in sorted(REQUIRED_POLISHING_LEVELS - set(polishing_levels))

    )

    errors.extend(

        f"manuscript-writing-workflow:missing-safety-rule:{item}"

        for item in sorted(REQUIRED_SAFETY_RULES - set(safety_rules))

    )



    cn_target = language_targets.get("cn_humanities_social_science", {})

    en_target = language_targets.get("en_high_impact_journal", {})

    if "英文期刊" not in "".join(cn_target.get("reject_when", [])):

        errors.append("manuscript-writing-workflow:cn-target-does-not-reject-english-journal-default")

    if "中文期刊" not in "".join(en_target.get("reject_when", [])):

        errors.append("manuscript-writing-workflow:en-target-does-not-reject-chinese-journal-default")



    css = discipline_targets.get("computational_social_science_or_method", {})

    if "pipeline" not in " ".join(css.get("adapted_from_nature", [])):

        errors.append("manuscript-writing-workflow:css-target-missing-technical-pipeline-adaptation")

    traditional = discipline_targets.get("traditional_quantitative_social_science", {})

    if "STEM" not in " ".join(traditional.get("do_not_import", [])):

        errors.append("manuscript-writing-workflow:traditional-quantitative-missing-stem-rejection")

    qualitative = discipline_targets.get("qualitative_or_interpretive_social_science", {})

    if "statistical significance" not in " ".join(qualitative.get("do_not_import", [])):

        errors.append("manuscript-writing-workflow:qualitative-target-missing-significance-rejection")



    output_contract = contract.get("output_contract", {})

    if output_contract.get("quality_gate_report") != "logs/quality-gates/writing-quality-report.json":

        errors.append("manuscript-writing-workflow:quality-report-path-mismatch")

    default_outputs = set(output_contract.get("default_outputs", []))

    for required in {"revised or drafted manuscript text", "claim-evidence-boundary notes"}:

        if required not in default_outputs:

            errors.append(f"manuscript-writing-workflow:missing-default-output:{required}")



    return errors
