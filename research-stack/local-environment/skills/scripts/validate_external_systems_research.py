from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from .path_utils import CATALOG_ROOT, SKILLS_ROOT
except ImportError:
    from path_utils import CATALOG_ROOT, SKILLS_ROOT

ROOT = SKILLS_ROOT
TARGET = CATALOG_ROOT / "external_systems_research.json"
VALID_LABELS = {
    "adopted_as_standard",
    "adapted_as_pattern",
    "retained_as_plugin_and_methodology",
    "optional_watch_layer",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def main() -> None:
    payload = load_json(TARGET)
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload.get("generated_at"), str) or not payload["generated_at"].strip():
        errors.append("missing-generated_at")
    if not isinstance(payload.get("source_scope"), str) or not payload["source_scope"].strip():
        errors.append("missing-source_scope")

    policy = payload.get("policy", {})
    if not isinstance(policy, dict):
        errors.append("policy-must-be-object")
        policy = {}
    if not isinstance(policy.get("default_rule"), str) or not policy.get("default_rule", "").strip():
        errors.append("missing-policy-default-rule")
    labels = policy.get("adoption_labels", [])
    if set(labels) != VALID_LABELS:
        errors.append("policy-adoption-labels-mismatch")

    systems = payload.get("systems", [])
    if not isinstance(systems, list) or not systems:
        errors.append("systems-must-be-non-empty-list")
        systems = []

    seen_names: set[str] = set()
    for item in systems:
        if not isinstance(item, dict):
            errors.append("system-entry-must-be-object")
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append("system-entry-missing-name")
            continue
        if name in seen_names:
            errors.append(f"duplicate-system-name:{name}")
        seen_names.add(name)

        for field in ("repo_url", "category", "adoption_label", "current_status", "notes"):
            if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                errors.append(f"{name}:missing-{field}")

        if item.get("adoption_label") not in VALID_LABELS:
            errors.append(f"{name}:invalid-adoption-label")

        for field in ("absorbed_into_local_stack", "not_adopted_by_default", "watch_items"):
            if not ensure_string_list(item.get(field, [])):
                errors.append(f"{name}:{field}-must-be-string-list")

    report = {
        "ok": not errors,
        "systems": len(systems),
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
