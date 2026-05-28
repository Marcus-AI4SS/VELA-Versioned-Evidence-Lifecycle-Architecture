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


CONTRACT_PATH = CATALOG_ROOT / "scientific_figure_workflow.json"
SCHEMA_PATH = SCHEMAS_ROOT / "scientific_figure_workflow.v1.schema.json"

REQUIRED_OPTION = "option_c_contract_first_integration"
REQUIRED_MODES = {
    "empirical_tabular_figure",
    "conceptual_mechanism_figure",
    "mixed_paper_figure_set",
    "quick_discussion_figure",
}
REQUIRED_STEPS = {
    "figure_brief",
    "configuration_block",
    "isolated_output_directory",
    "data_health_report",
    "process_data_export",
    "justified_statistics",
    "publication_rendering",
    "caption_contract",
    "report_bundle",
    "delivery_summary",
}
REQUIRED_STYLE_RULES = {
    "config_block_reproducibility",
    "data_health_before_plotting",
    "process_data_traceability",
    "justified_statistics_annotations",
    "typography_font_fallback",
    "typography_font_size_specification",
    "figure_size_resolution_contract",
    "axis_units_numeric_precision",
    "caption_what_how_so_what",
    "multi_format_export_and_editable_source",
    "renderer_selection_by_deliverable",
    "r_plot_family_output_bundle",
    "ggplot_text_export_diagnostics",
    "chart_type_selection_by_evidence_need",
    "figure_table_title_caption_plainness",
}
REQUIRED_SAFETY_RULES = {
    "no_fake_empirical_values",
    "statistics_require_design",
    "style_defaults_are_not_journal_law",
    "raw_data_not_overwritten",
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


def validate_scientific_figure_workflow() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    schema = _safe_load(SCHEMA_PATH, "scientific_figure_workflow.schema", errors)
    contract = _safe_load(CONTRACT_PATH, "scientific_figure_workflow", errors)
    if schema:
        errors.extend(collect_schema_document_errors(schema, "scientific_figure_workflow.schema"))
    if schema and contract:
        errors.extend(collect_schema_errors(contract, schema, "scientific_figure_workflow"))
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
        "step_count": len(contract.get("workflow_steps", [])) if isinstance(contract, dict) else 0,
        "style_rule_count": len(contract.get("style_rules", [])) if isinstance(contract, dict) else 0,
        "safety_rule_count": len(contract.get("safety_rules", [])) if isinstance(contract, dict) else 0,
    }
    return build_validator_result(
        validator="validate_scientific_figure_workflow",
        scope="scientific_figure_workflow",
        errors=errors,
        warnings=warnings,
        details=details,
    )


def _collect_contract_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    option_ids = [item.get("id") for item in contract.get("adoption_options", []) if isinstance(item, dict)]
    selected = [item.get("id") for item in contract.get("adoption_options", []) if item.get("decision") == "selected"]
    if contract.get("selected_strategy") != REQUIRED_OPTION:
        errors.append(f"scientific-figure-workflow:selected-strategy-mismatch:{contract.get('selected_strategy')}")
    if selected != [REQUIRED_OPTION]:
        errors.append(f"scientific-figure-workflow:selected-option-mismatch:{selected}")
    for option_id, count in Counter(option_ids).items():
        if count > 1:
            errors.append(f"scientific-figure-workflow:duplicate-option:{option_id}")

    modes = {item.get("id"): item for item in contract.get("workflow_modes", []) if isinstance(item, dict)}
    steps = {item.get("id"): item for item in contract.get("workflow_steps", []) if isinstance(item, dict)}
    style_rules = {item.get("id"): item for item in contract.get("style_rules", []) if isinstance(item, dict)}
    safety_rules = {item.get("id"): item for item in contract.get("safety_rules", []) if isinstance(item, dict)}
    errors.extend(f"scientific-figure-workflow:missing-mode:{item}" for item in sorted(REQUIRED_MODES - set(modes)))
    errors.extend(f"scientific-figure-workflow:missing-step:{item}" for item in sorted(REQUIRED_STEPS - set(steps)))
    errors.extend(
        f"scientific-figure-workflow:missing-style-rule:{item}"
        for item in sorted(REQUIRED_STYLE_RULES - set(style_rules))
    )
    errors.extend(
        f"scientific-figure-workflow:missing-safety-rule:{item}"
        for item in sorted(REQUIRED_SAFETY_RULES - set(safety_rules))
    )

    for mode_id, mode in modes.items():
        unknown_steps = sorted(set(mode.get("required_steps", [])) - set(steps))
        errors.extend(f"scientific-figure-workflow:{mode_id}:unknown-step:{item}" for item in unknown_steps)
        owner = mode.get("owner_skill")
        if mode_id == "empirical_tabular_figure" and owner != "figure-table-studio":
            errors.append("scientific-figure-workflow:empirical-mode-owner-mismatch")
        if mode_id == "conceptual_mechanism_figure" and owner != "research-figure-studio":
            errors.append("scientific-figure-workflow:conceptual-mode-owner-mismatch")

    for step_id, step in steps.items():
        unknown_modes = sorted(set(step.get("applies_to_modes", [])) - set(modes))
        errors.extend(f"scientific-figure-workflow:{step_id}:unknown-mode:{item}" for item in unknown_modes)

    output_contract = contract.get("output_contract", {})
    errors.extend(_collect_typography_errors(contract.get("typography_contract", {})))
    required_formats = set(output_contract.get("required_formats", []))
    if required_formats != {"pdf", "png", "jpg"}:
        errors.append(f"scientific-figure-workflow:output-formats-mismatch:{sorted(required_formats)}")
    required_dirs = set(output_contract.get("required_directories", []))
    for required_dir in {"figures/pdf", "figures/png", "figures/jpg", "process_data"}:
        if required_dir not in required_dirs:
            errors.append(f"scientific-figure-workflow:missing-output-dir:{required_dir}")
    if output_contract.get("report_path_template") != "logs/quality-gates/figure-table-report.json":
        errors.append("scientific-figure-workflow:report-path-mismatch")

    return errors


def _collect_typography_errors(typography: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cn_fonts = typography.get("cn_serif_fallback", [])
    en_fonts = typography.get("en_serif_fallback", [])
    if cn_fonts[:2] != ["SimSun", "Songti SC"]:
        errors.append(f"scientific-figure-workflow:cn-font-fallback-mismatch:{cn_fonts}")
    if en_fonts[:1] != ["Times New Roman"]:
        errors.append(f"scientific-figure-workflow:en-font-fallback-mismatch:{en_fonts}")
    font_sizes = typography.get("matplotlib_font_sizes_pt", {})
    expected_sizes = {
        "base": 10,
        "axes_title": 11,
        "axis_label": 10,
        "tick_label": 9,
        "legend": 9,
        "caption": 9,
        "panel_label": 10,
        "annotation": 9,
        "significance_mark": 10,
    }
    for key, expected in expected_sizes.items():
        if font_sizes.get(key) != expected:
            errors.append(f"scientific-figure-workflow:font-size-mismatch:{key}:{font_sizes.get(key)}")
    if typography.get("dpi") != 300:
        errors.append(f"scientific-figure-workflow:dpi-mismatch:{typography.get('dpi')}")
    figure_sizes = typography.get("figure_sizes_in", {})
    if figure_sizes.get("single_column") != [3.5, 2.6]:
        errors.append(f"scientific-figure-workflow:single-column-size-mismatch:{figure_sizes.get('single_column')}")
    if figure_sizes.get("double_column") != [7.2, 4.0]:
        errors.append(f"scientific-figure-workflow:double-column-size-mismatch:{figure_sizes.get('double_column')}")
    return errors
