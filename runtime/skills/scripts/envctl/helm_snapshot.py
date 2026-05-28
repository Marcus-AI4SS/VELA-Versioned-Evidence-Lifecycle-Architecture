from __future__ import annotations



from datetime import datetime, timezone

import re

from pathlib import Path

from typing import Any



from .schema_validation import collect_schema_errors, load_json

from .validator_envelope import build_validator_result



try:

    from ..path_utils import CATALOG_ROOT, PROFILES_ROOT, REPO_ROOT, SCHEMAS_ROOT

except ImportError:  # pragma: no cover

    from path_utils import CATALOG_ROOT, PROFILES_ROOT, REPO_ROOT, SCHEMAS_ROOT





PUBLIC_CATALOG_FILES = [

    "agent_execution_modes.json",

    "citation_verification_rules.json",

    "cnki_zotero_workflow.json",

    "conflict_matrix.json",

    "governance_source_rule_crosswalk.json",

    "data_access_matrix.json",

    "external_systems_research.json",

    "manuscript_writing_workflow.json",

    "multi_agent_harness_adapter.json",

    "publication_style_rules.json",

    "prompt_catalog_lite.json",

    "project_initializer_manifest.json",

    "project_scope_rules.json",

    "quality_gates.json",

    "research_pipeline_stages.json",

    "research_team_playbooks.json",

    "reviewer_allowlist.json",

    "route_mcp_activation_policy.json",

    "routing_table.json",

    "skill_catalog.json",

    "subagent_registry.json",

    "writing_quality_rules.json",

]

EXCLUDED_ROOTS = [

    ".git",

    ".venv",

    "python/downloads",

    "python/runtime",

    "skills/manager",

    "skills/outputs",

    "skills/.playwright-mcp",

    "skills/catalog/settings.toml",

    "skills/catalog/manager_distributions.json",

    "skills/catalog/external_plugin_candidates.json",

]

BLOCKED_PATTERNS = {
    "windows-user-path": re.compile(r"[A-Z]:(?:\\|/)Users(?:\\|/)[^\\/\\s]+", re.IGNORECASE),
    "named-private-workspace": re.compile(r"[A-Z]:(?:\\|/)[^\\/\n]*(?:private|workspace|environment)[^\\/\n]*", re.IGNORECASE),
    "env-file-reference": re.compile(r"(^|[\\/\s])\.env($|[\\/\s])", re.IGNORECASE),
    "token-secret-password": re.compile(r"(api[_-]?key|access[_-]?token|secret|password)", re.IGNORECASE),
    "generated-runtime-output": re.compile(r"skills/outputs/(?:[^\\/\s]*(?:desktop|release|generated)[^\\/\s]*)", re.IGNORECASE),
}




def _repo_relative(path: Path) -> str:

    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()





def _existing_schema_files() -> list[str]:

    return sorted(_repo_relative(path) for path in SCHEMAS_ROOT.glob("*.json"))





def _existing_catalog_files() -> list[str]:

    result: list[str] = []

    for name in PUBLIC_CATALOG_FILES:

        path = CATALOG_ROOT / name

        if path.exists():

            result.append(_repo_relative(path))

    return sorted(result)





def _existing_profile_files() -> list[str]:

    return sorted(_repo_relative(path) for path in PROFILES_ROOT.glob("*.toml"))





def _privacy_scan(files: list[str]) -> dict[str, Any]:

    findings: list[dict[str, str]] = []

    checked = 0

    for relative in files:

        path = REPO_ROOT / relative

        if not path.exists() or not path.is_file():

            continue

        checked += 1

        text = path.read_text(encoding="utf-8", errors="replace")

        for label, pattern in BLOCKED_PATTERNS.items():

            if pattern.search(text):

                findings.append({"file": relative, "pattern": label})

    return {

        "checked_files": checked,

        "blocked_patterns": sorted(BLOCKED_PATTERNS),

        "findings": findings,

    }





def build_helm_snapshot_manifest(*, generated_at: str | None = None) -> dict[str, Any]:

    schema_files = _existing_schema_files()

    catalog_files = _existing_catalog_files()

    profile_files = _existing_profile_files()

    checked_files = schema_files + catalog_files + profile_files

    return {

        "$schema": "../schemas/helm_snapshot_manifest.schema.json",

        "schema_version": "helm_snapshot_manifest.v1",

        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),

        "source_root": str(REPO_ROOT),

        "included_roots": [

            "skills/catalog",

            "skills/profiles",

            "skills/schemas",

        ],

        "excluded_roots": EXCLUDED_ROOTS,

        "schema_files": schema_files,

        "catalog_files": catalog_files,

        "profile_files": profile_files,

        "privacy_scan": _privacy_scan(checked_files),

    }





def collect_helm_snapshot_errors(manifest: dict[str, Any] | None = None) -> tuple[list[str], list[str], dict[str, Any]]:

    payload = manifest or build_helm_snapshot_manifest()

    errors = collect_schema_errors(payload, load_json(SCHEMAS_ROOT / "helm_snapshot_manifest.schema.json"), "helm_snapshot_manifest")

    warnings: list[str] = []

    missing_catalog_files = [

        f"skills/catalog/{name}"

        for name in PUBLIC_CATALOG_FILES

        if not (CATALOG_ROOT / name).exists()

    ]

    errors.extend(f"helm-snapshot:missing-public-catalog:{path}" for path in missing_catalog_files)

    errors.extend(

        f"helm-snapshot:privacy-finding:{item['file']}:{item['pattern']}"

        for item in payload.get("privacy_scan", {}).get("findings", [])

    )

    if "skills/outputs" not in payload.get("excluded_roots", []):

        errors.append("helm-snapshot:skills-outputs-must-be-excluded")

    return errors, warnings, payload





def validate_helm_snapshot_contract() -> dict[str, Any]:

    errors, warnings, details = collect_helm_snapshot_errors()

    return build_validator_result(

        validator="helm_snapshot",

        scope="snapshot_contract",

        errors=errors,

        warnings=warnings,

        details=details,

    )
