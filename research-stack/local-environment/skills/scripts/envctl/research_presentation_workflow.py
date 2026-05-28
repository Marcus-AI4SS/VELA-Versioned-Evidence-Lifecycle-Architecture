from __future__ import annotations

import json
import os
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


CONTRACT_PATH = CATALOG_ROOT / "research_presentation_workflow.json"
SCHEMA_PATH = SCHEMAS_ROOT / "research_presentation_workflow.v1.schema.json"
SKILL_ROOT = SKILLS_ROOT / "plugins" / "research-autopilot" / "skills" / "research-presentation-studio"
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
UPSTREAM_RUNTIME_SKILL_ROOT = CODEX_HOME / "skills" / "guizang-ppt-skill"

REQUIRED_VISUAL_SYSTEMS = {
    "style_a_magazine_eink",
    "style_b_swiss_international",
}
REQUIRED_STEPS = {
    "confirm_route_and_scope",
    "story_spine_and_slide_plan",
    "visual_system_selection",
    "asset_and_image_plan",
    "generate_deck",
    "preview_and_quality_review",
}
REQUIRED_OUTPUT_MODES = {
    "web_deck_html",
    "pptx_deck",
    "hybrid_html_plus_pptx",
}
REQUIRED_QUALITY_RULES = {
    "style_system_declared",
    "theme_choice_recorded",
    "slide_manifest_before_generation",
    "swiss_locked_layout_validated",
    "image_slot_and_screenshot_fidelity_checked",
    "readability_and_navigation_checked",
}
REQUIRED_SAFETY_RULES = {
    "no_presentation_as_citation_gate",
    "no_fake_data_or_claims_in_slides",
    "no_paper_figure_contract_bypass",
    "no_external_runtime_takeover",
}
REQUIRED_UPSTREAM_RUNTIME_FILES = [
    "LICENSE",
    "SKILL.md",
    "README.md",
    "assets/template.html",
    "assets/template-swiss.html",
    "assets/motion.min.js",
    "references/themes.md",
    "references/themes-swiss.md",
    "references/layouts.md",
    "references/layouts-swiss.md",
    "references/swiss-layout-lock.md",
    "references/swiss-map-component.md",
    "references/components.md",
    "references/image-prompts.md",
    "references/screenshot-framing.md",
    "references/checklist.md",
    "scripts/validate-swiss-deck.mjs",
]


def _safe_load(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"{label}:missing:{path}")
        return {}
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"{label}:invalid-json:{exc}")
        return {}


def validate_research_presentation_workflow() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    schema = _safe_load(SCHEMA_PATH, "research_presentation_workflow.schema", errors)
    contract = _safe_load(CONTRACT_PATH, "research_presentation_workflow", errors)
    if schema:
        errors.extend(collect_schema_document_errors(schema, "research_presentation_workflow.schema"))
    if schema and contract:
        errors.extend(collect_schema_errors(contract, schema, "research_presentation_workflow"))
    if contract:
        errors.extend(_collect_contract_errors(contract))
    errors.extend(_collect_runtime_skill_errors())

    details = {
        "contract": {
            "payload": str(CONTRACT_PATH.relative_to(SKILLS_ROOT)),
            "schema": str(SCHEMA_PATH.relative_to(SKILLS_ROOT)),
            "payload_exists": CONTRACT_PATH.exists(),
            "schema_exists": SCHEMA_PATH.exists(),
        },
        "skill_root": str(SKILL_ROOT.relative_to(SKILLS_ROOT)),
        "upstream_runtime_skill_root": str(UPSTREAM_RUNTIME_SKILL_ROOT),
        "upstream_runtime_skill_exists": UPSTREAM_RUNTIME_SKILL_ROOT.exists(),
        "visual_system_count": len(contract.get("visual_systems", [])) if isinstance(contract, dict) else 0,
        "workflow_step_count": len(contract.get("workflow_steps", [])) if isinstance(contract, dict) else 0,
        "output_mode_count": len(contract.get("output_modes", [])) if isinstance(contract, dict) else 0,
    }
    return build_validator_result(
        validator="validate_research_presentation_workflow",
        scope="research_presentation_workflow",
        errors=errors,
        warnings=warnings,
        details=details,
    )


def _collect_contract_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_refs = {item.get("upstream"): item for item in contract.get("source_review_refs", []) if isinstance(item, dict)}
    if "op7418/guizang-ppt-skill" not in source_refs:
        errors.append("research-presentation-workflow:missing-guizang-source-ref")
    elif source_refs["op7418/guizang-ppt-skill"].get("decision") != "install_and_delegate":
        errors.append("research-presentation-workflow:guizang-decision-not-install-and-delegate")

    visual_systems = {item.get("id"): item for item in contract.get("visual_systems", []) if isinstance(item, dict)}
    steps = {item.get("id"): item for item in contract.get("workflow_steps", []) if isinstance(item, dict)}
    modes = {item.get("id"): item for item in contract.get("output_modes", []) if isinstance(item, dict)}
    quality_rules = {item.get("id"): item for item in contract.get("quality_rules", []) if isinstance(item, dict)}
    safety_rules = {item.get("id"): item for item in contract.get("safety_rules", []) if isinstance(item, dict)}

    errors.extend(
        f"research-presentation-workflow:missing-visual-system:{item}"
        for item in sorted(REQUIRED_VISUAL_SYSTEMS - set(visual_systems))
    )
    errors.extend(
        f"research-presentation-workflow:missing-step:{item}"
        for item in sorted(REQUIRED_STEPS - set(steps))
    )
    errors.extend(
        f"research-presentation-workflow:missing-output-mode:{item}"
        for item in sorted(REQUIRED_OUTPUT_MODES - set(modes))
    )
    errors.extend(
        f"research-presentation-workflow:missing-quality-rule:{item}"
        for item in sorted(REQUIRED_QUALITY_RULES - set(quality_rules))
    )
    errors.extend(
        f"research-presentation-workflow:missing-safety-rule:{item}"
        for item in sorted(REQUIRED_SAFETY_RULES - set(safety_rules))
    )

    for collection_name in ("visual_systems", "workflow_steps", "output_modes", "quality_rules", "safety_rules"):
        ids = [item.get("id") for item in contract.get(collection_name, []) if isinstance(item, dict)]
        for item_id, count in Counter(ids).items():
            if count > 1:
                errors.append(f"research-presentation-workflow:duplicate-{collection_name}:{item_id}")

    swiss = visual_systems.get("style_b_swiss_international", {})
    if not any("validate-swiss-deck.mjs" in item for item in swiss.get("must_follow", [])):
        errors.append("research-presentation-workflow:swiss-system-missing-validator-rule")

    mapping = contract.get("local_tool_mapping", {})
    if mapping.get("owner_skill") != "research-presentation-studio":
        errors.append("research-presentation-workflow:owner-skill-mismatch")
    if mapping.get("upstream_runtime_skill") != "guizang-ppt-skill":
        errors.append("research-presentation-workflow:upstream-runtime-skill-mismatch")
    if mapping.get("official_pptx_tool") != "presentations@openai-primary-runtime":
        errors.append("research-presentation-workflow:pptx-tool-mismatch")
    if "guizang-ppt-skill" not in mapping.get("web_deck_template_root", ""):
        errors.append("research-presentation-workflow:web-deck-template-root-not-guizang")
    if "plugins/research-autopilot" in mapping.get("web_deck_template_root", "").replace("\\", "/"):
        errors.append("research-presentation-workflow:web-deck-template-root-uses-local-fork")
    if "image2" not in mapping.get("image_generation_policy", ""):
        errors.append("research-presentation-workflow:image2-policy-missing")

    return errors


def _collect_runtime_skill_errors() -> list[str]:
    errors: list[str] = []
    if not (SKILL_ROOT / "SKILL.md").exists():
        errors.append("research-presentation-workflow:missing-skill-md")
    for relative_path in REQUIRED_UPSTREAM_RUNTIME_FILES:
        if not (UPSTREAM_RUNTIME_SKILL_ROOT / relative_path).exists():
            errors.append(f"research-presentation-workflow:missing-upstream-runtime-file:{relative_path}")
    return errors
