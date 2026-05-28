from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from ..path_utils import CATALOG_ROOT, REPO_ROOT, SCHEMAS_ROOT
    from .schema_validation import collect_schema_document_errors, collect_schema_errors, load_json
    from .validator_envelope import build_validator_result
except ImportError:  # pragma: no cover
    from path_utils import CATALOG_ROOT, REPO_ROOT, SCHEMAS_ROOT
    from envctl.schema_validation import collect_schema_document_errors, collect_schema_errors, load_json
    from envctl.validator_envelope import build_validator_result


PATTERNS_PATH = CATALOG_ROOT / "scholar_browser_patterns.json"
SCHEMA_PATH = SCHEMAS_ROOT / "scholar_browser_patterns.v1.schema.json"
REQUIRED_SYSTEMS = {"cnki", "google_scholar"}


def load_scholar_browser_patterns() -> dict[str, Any]:
    return load_json(PATTERNS_PATH)


def validate_scholar_browser_patterns() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    schema = _safe_load(SCHEMA_PATH, "scholar_browser_patterns.schema", errors)
    payload = _safe_load(PATTERNS_PATH, "scholar_browser_patterns", errors)

    if schema:
        errors.extend(collect_schema_document_errors(schema, "scholar_browser_patterns.schema"))
    if schema and payload:
        errors.extend(collect_schema_errors(payload, schema, "scholar_browser_patterns"))
        errors.extend(_collect_semantic_errors(payload))

    return build_validator_result(
        validator="validate_scholar_browser_patterns",
        scope="scholar_browser_patterns",
        errors=errors,
        warnings=warnings,
        details={
            "catalog": str(PATTERNS_PATH.relative_to(REPO_ROOT)),
            "schema": str(SCHEMA_PATH.relative_to(REPO_ROOT)),
            "systems": _system_ids(payload),
            "efficiency_estimate": estimate_browser_pattern_efficiency(item_count=10),
        },
    )


def estimate_browser_pattern_efficiency(*, item_count: int = 10) -> dict[str, Any]:
    count = max(1, int(item_count))
    estimates = [
        _estimate(
            workflow="cnki_batch_metadata_export",
            item_count=count,
            baseline_browser_steps=2 + count * 3,
            adapted_browser_steps=3,
            usability_gain=(
                "Result-page checkbox IDs and batch export avoid opening every detail page before "
                "Zotero import planning."
            ),
        ),
        _estimate(
            workflow="google_scholar_data_cid_followup",
            item_count=count,
            baseline_browser_steps=count * 4,
            adapted_browser_steps=count * 2,
            usability_gain=(
                "Keeping data-cid from the first visible Scholar pass avoids title re-search when "
                "opening cited-by, versions, or BibTeX follow-ups."
            ),
        ),
        _estimate(
            workflow="captcha_or_access_stop_policy",
            item_count=count,
            baseline_browser_steps=count * 3,
            adapted_browser_steps=count + 1,
            usability_gain=(
                "Explicit stop conditions prevent repeated failed retries after captcha, login, "
                "or institution-access challenges."
            ),
        ),
    ]
    return {
        "schema_version": "scholar_browser_pattern_efficiency.v1",
        "item_count": count,
        "measurement_mode": "static_step_model",
        "assumptions": [
            "One browser step means one navigation, one visible-browser script evaluation, or one manual stop event.",
            "The model checks relative workflow cost; it does not benchmark network latency or database response time.",
            "Safety gates are counted as usability improvements when they prevent repeated failed automation.",
        ],
        "estimates": estimates,
        "decision": "more_efficient_and_more_auditable"
        if all(item["adapted_browser_steps"] < item["baseline_browser_steps"] for item in estimates)
        else "needs_review",
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


def _system_ids(payload: dict[str, Any]) -> list[str]:
    return [
        item.get("system_id", "<missing>")
        for item in payload.get("systems", [])
        if isinstance(item, dict)
    ]


def _system_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("system_id")): item
        for item in payload.get("systems", [])
        if isinstance(item, dict) and item.get("system_id")
    }


def _collect_semantic_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    systems = _system_map(payload)
    missing = sorted(REQUIRED_SYSTEMS - set(systems))
    errors.extend(f"scholar_browser_patterns:missing-system:{item}" for item in missing)

    policy_text = " ".join(
        str(payload.get("policy", {}).get(key, ""))
        for key in ("allowed_role", "forbidden_role")
    ).lower()
    if "reference-fulltext-acquisition" not in str(payload.get("policy", {}).get("default_route", "")):
        errors.append("scholar_browser_patterns:policy-default-route-must-be-reference-fulltext-acquisition")
    if "independent citation verifier" not in policy_text:
        errors.append("scholar_browser_patterns:policy-must-forbid-independent-citation-verifier")
    if "captcha" not in " ".join(payload.get("policy", {}).get("must_stop_for", [])).lower():
        errors.append("scholar_browser_patterns:policy-must-stop-for-captcha")

    if "cnki" in systems:
        errors.extend(_collect_cnki_errors(systems["cnki"]))
    if "google_scholar" in systems:
        errors.extend(_collect_google_scholar_errors(systems["google_scholar"]))
    return errors


def _collect_cnki_errors(system: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    accepted = _joined(system.get("accepted_patterns", []))
    rejected = _joined(system.get("rejected_patterns", []))
    params = _joined(_all_action_params(system))
    fields = _joined(_field_selectors(system))

    required_fragments = {
        "author-affiliation-pattern": ["author", "affiliation"],
        "batch-export-pattern": ["batch", "export"],
        "journal-index-pattern": ["journal", "index"],
    }
    for label, fragments in required_fragments.items():
        if not all(fragment in accepted for fragment in fragments):
            errors.append(f"scholar_browser_patterns:cnki:missing-accepted-{label}")

    for fragment in ("cookie", "captcha", "login"):
        if fragment not in rejected:
            errors.append(f"scholar_browser_patterns:cnki:missing-rejected-{fragment}")

    for selector in ("#au_1_value2", "#cssci", "#pdfdown", "input.cbitem"):
        if selector not in params and selector not in fields:
            errors.append(f"scholar_browser_patterns:cnki:missing-selector:{selector}")

    actions = {item.get("id") for item in system.get("actions", []) if isinstance(item, dict)}
    for action in ("advanced_search_with_source_category", "batch_export_metadata", "authorized_download"):
        if action not in actions:
            errors.append(f"scholar_browser_patterns:cnki:missing-action:{action}")
    return errors


def _collect_google_scholar_errors(system: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    accepted = _joined(system.get("accepted_patterns", []))
    rejected = _joined(system.get("rejected_patterns", []))
    primary_keys = _joined(system.get("primary_keys", []))
    params = _joined(_all_action_params(system))
    fields = _joined(_field_selectors(system))
    captcha = _joined(system.get("captcha_detection", []))

    if "data-cid" not in accepted and "data-cid" not in primary_keys:
        errors.append("scholar_browser_patterns:google_scholar:missing-data-cid-primary-key")
    if "sci-hub" not in rejected:
        errors.append("scholar_browser_patterns:google_scholar:must-reject-sci-hub")
    if "captcha" not in accepted and "#gs_captcha_ccl" not in captcha:
        errors.append("scholar_browser_patterns:google_scholar:missing-captcha-stop-policy")

    for selector in (".gs_ggs", "cites={data_cid}", "#gs_captcha_ccl"):
        if selector not in params and selector not in fields and selector not in captcha:
            errors.append(f"scholar_browser_patterns:google_scholar:missing-selector-or-param:{selector}")

    actions = {item.get("id") for item in system.get("actions", []) if isinstance(item, dict)}
    for action in ("right_pdf_candidate", "cited_by", "bibtex_metadata", "captcha_stop_and_resume"):
        if action not in actions:
            errors.append(f"scholar_browser_patterns:google_scholar:missing-action:{action}")
    return errors


def _all_action_params(system: dict[str, Any]) -> list[str]:
    params: list[str] = []
    for action in system.get("actions", []):
        if isinstance(action, dict):
            params.extend(str(item) for item in action.get("selectors_or_params", []))
            params.extend(str(item) for item in action.get("notes", []))
    return params


def _field_selectors(system: dict[str, Any]) -> list[str]:
    return [
        str(item.get("selector"))
        for item in system.get("result_fields", [])
        if isinstance(item, dict)
    ]


def _joined(values: list[str] | Any) -> str:
    if not isinstance(values, list):
        return str(values).lower()
    return " ".join(str(item) for item in values).lower()


def _estimate(
    *,
    workflow: str,
    item_count: int,
    baseline_browser_steps: int,
    adapted_browser_steps: int,
    usability_gain: str,
) -> dict[str, Any]:
    saved = baseline_browser_steps - adapted_browser_steps
    reduction = saved / baseline_browser_steps if baseline_browser_steps else 0
    return {
        "workflow": workflow,
        "item_count": item_count,
        "baseline_browser_steps": baseline_browser_steps,
        "adapted_browser_steps": adapted_browser_steps,
        "saved_browser_steps": saved,
        "reduction_ratio": round(reduction, 3),
        "usability_gain": usability_gain,
        "verdict": "more_efficient" if saved > 0 else "not_more_efficient",
    }
