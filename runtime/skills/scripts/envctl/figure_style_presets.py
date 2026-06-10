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


CONTRACT_PATH = CATALOG_ROOT / "figure_style_presets.json"
SCHEMA_PATH = SCHEMAS_ROOT / "figure_style_presets.v1.schema.json"

REQUIRED_PRESETS = {
    "social_science_nature_red_blue_rainbow",
    "nature_empirical_red_blue_rainbow",
    "minimal_review_ready_red_blue",
    "presentation_premium_red_blue_rainbow",
}
EXPECTED_DEFAULTS = {
    "formal_research_figure": "social_science_nature_red_blue_rainbow",
    "empirical_figure": "nature_empirical_red_blue_rainbow",
    "review_ready_figure": "minimal_review_ready_red_blue",
    "presentation_figure": "presentation_premium_red_blue_rainbow",
}
REQUIRED_PROMPT_TOKENS = {
    "red_blue_rainbow_palette",
    "no_internal_title",
    "no_long_caption",
    "no_overlap",
    "no_fake_data",
}
REQUIRED_QUALITY_CHECKS = {
    "figure_style_preset_selected",
    "red_blue_rainbow_palette_checked",
    "title_caption_outside_image_checked",
    "visual_overlap_checked",
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


def validate_figure_style_presets() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    schema = _safe_load(SCHEMA_PATH, "figure_style_presets.schema", errors)
    contract = _safe_load(CONTRACT_PATH, "figure_style_presets", errors)
    if schema:
        errors.extend(collect_schema_document_errors(schema, "figure_style_presets.schema"))
    if schema and contract:
        errors.extend(collect_schema_errors(contract, schema, "figure_style_presets"))
    if contract:
        errors.extend(_collect_contract_errors(contract))

    details = {
        "contract": {
            "payload": str(CONTRACT_PATH.relative_to(SKILLS_ROOT)),
            "schema": str(SCHEMA_PATH.relative_to(SKILLS_ROOT)),
            "payload_exists": CONTRACT_PATH.exists(),
            "schema_exists": SCHEMA_PATH.exists(),
        },
        "preset_count": len(contract.get("presets", [])) if isinstance(contract, dict) else 0,
        "defaults": contract.get("default_presets", {}) if isinstance(contract, dict) else {},
    }
    return build_validator_result(
        validator="validate_figure_style_presets",
        scope="figure_style_presets",
        errors=errors,
        warnings=warnings,
        details=details,
    )


def _collect_contract_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    presets = {item.get("id"): item for item in contract.get("presets", []) if isinstance(item, dict)}
    preset_ids = [item.get("id") for item in contract.get("presets", []) if isinstance(item, dict)]
    for preset_id, count in Counter(preset_ids).items():
        if count > 1:
            errors.append(f"figure-style-presets:duplicate-preset:{preset_id}")
    errors.extend(f"figure-style-presets:missing-preset:{item}" for item in sorted(REQUIRED_PRESETS - set(presets)))

    defaults = contract.get("default_presets", {})
    for key, expected in EXPECTED_DEFAULTS.items():
        actual = defaults.get(key)
        if actual != expected:
            errors.append(f"figure-style-presets:default-mismatch:{key}:{actual}")
        if actual and actual not in presets:
            errors.append(f"figure-style-presets:default-preset-missing:{key}:{actual}")

    for preset_id, preset in presets.items():
        prompt = preset.get("image2_prompt_requirements", {})
        tokens = set(prompt.get("prompt_tokens", []))
        missing_tokens = sorted(REQUIRED_PROMPT_TOKENS - tokens)
        errors.extend(f"figure-style-presets:{preset_id}:missing-prompt-token:{item}" for item in missing_tokens)

        quality_checks = set(preset.get("quality_checks", []))
        missing_checks = sorted(REQUIRED_QUALITY_CHECKS - quality_checks)
        errors.extend(f"figure-style-presets:{preset_id}:missing-quality-check:{item}" for item in missing_checks)

        forbidden = set(preset.get("forbidden_elements", []))
        if "internal formal title" not in forbidden:
            errors.append(f"figure-style-presets:{preset_id}:internal-title-not-forbidden")
        if "long internal caption" not in forbidden:
            errors.append(f"figure-style-presets:{preset_id}:internal-caption-not-forbidden")

        overlap_checks = preset.get("overlap_checks", [])
        if not any("Legend" in item or "图例" in item or "Legends" in item for item in overlap_checks):
            errors.append(f"figure-style-presets:{preset_id}:legend-overlap-check-missing")
        if not any("Text" in item or "text" in item or "文字" in item for item in overlap_checks):
            errors.append(f"figure-style-presets:{preset_id}:text-overlap-check-missing")

        palette_constraints = " ".join(preset.get("palette", {}).get("constraints", []))
        has_red_blue = "red-blue" in palette_constraints or "红蓝" in palette_constraints
        has_rainbow = "rainbow" in palette_constraints or "彩虹" in palette_constraints
        if not has_red_blue:
            errors.append(f"figure-style-presets:{preset_id}:red-blue-constraint-missing")
        if preset_id != "minimal_review_ready_red_blue" and not has_rainbow:
            errors.append(f"figure-style-presets:{preset_id}:rainbow-constraint-missing")

    return errors
