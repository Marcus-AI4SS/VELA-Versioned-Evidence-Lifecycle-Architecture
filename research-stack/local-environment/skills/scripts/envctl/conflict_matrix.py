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


CONFLICT_PATH = CATALOG_ROOT / "conflict_matrix.json"
SCHEMA_PATH = SCHEMAS_ROOT / "conflict_matrix.v1.schema.json"
SKILL_CATALOG_PATH = CATALOG_ROOT / "skill_catalog.json"

REQUIRED_RULES = {
    "autopilot-entry",
    "route-confirmation-before-new-chain",
    "research-stage-advance-confirmation",
    "revision-package-scope-disambiguation",
    "replication-package-scope-disambiguation",
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


def validate_conflict_matrix() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    schema = _safe_load(SCHEMA_PATH, "conflict_matrix.schema", errors)
    payload = _safe_load(CONFLICT_PATH, "conflict_matrix", errors)
    skill_catalog = _safe_load(SKILL_CATALOG_PATH, "skill_catalog", errors)

    if schema:
        errors.extend(collect_schema_document_errors(schema, "conflict_matrix.schema"))
    if schema and payload:
        errors.extend(collect_schema_errors(payload, schema, "conflict_matrix"))
        errors.extend(_collect_semantic_errors(payload, skill_catalog))

    details = {
        "contract": {
            "payload": str(CONFLICT_PATH.relative_to(SKILLS_ROOT)),
            "schema": str(SCHEMA_PATH.relative_to(SKILLS_ROOT)),
            "payload_exists": CONFLICT_PATH.exists(),
            "schema_exists": SCHEMA_PATH.exists(),
        },
        "rule_count": len(payload.get("rules", [])) if payload else 0,
        "retired_skill_count": len(payload.get("retired_skills", {})) if payload else 0,
    }
    return build_validator_result(
        validator="validate_conflict_matrix",
        scope="conflict_matrix",
        errors=errors,
        warnings=warnings,
        details=details,
    )


def _collect_semantic_errors(payload: dict[str, Any], skill_catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rules = [item for item in payload.get("rules", []) if isinstance(item, dict)]
    rule_ids = [str(item.get("rule", "")) for item in rules]
    for rule_id, count in Counter(rule_ids).items():
        if count > 1:
            errors.append(f"conflict_matrix:duplicate-rule:{rule_id}")

    missing_rules = REQUIRED_RULES - set(rule_ids)
    errors.extend(f"conflict_matrix:missing-required-rule:{item}" for item in sorted(missing_rules))

    active_skills = {
        name
        for name, item in skill_catalog.get("skills", {}).items()
        if isinstance(item, dict) and item.get("status") == "active"
    }
    for retired in sorted(payload.get("retired_skills", {})):
        if retired in active_skills:
            errors.append(f"conflict_matrix:retired-skill-still-active:{retired}")

    if not any("research-autopilot" in str(item.get("winner", "")) for item in rules):
        errors.append("conflict_matrix:missing-autopilot-winner")
    if not any("必须先问用户" in str(item.get("reason", "")) for item in rules):
        errors.append("conflict_matrix:missing-clarification-language")
    return errors
