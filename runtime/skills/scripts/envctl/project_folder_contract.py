from __future__ import annotations

import fnmatch
import json
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


CONTRACT_PATH = CATALOG_ROOT / "project_folder_contract.json"
SCHEMA_PATH = SCHEMAS_ROOT / "project_folder_contract.v1.schema.json"
MANIFEST_PATH = CATALOG_ROOT / "project_initializer_manifest.json"


def _safe_load(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"{label}:missing:{path}")
        return {}
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"{label}:invalid-json:{exc}")
        return {}


def _path_exists(project_root: Path, relative_path: str) -> bool:
    return (project_root / relative_path).exists()


def _dir_exists(project_root: Path, relative_path: str) -> bool:
    return (project_root / relative_path).is_dir()


def _collect_manifest_paths(manifest: dict[str, Any]) -> set[str]:
    paths = set(manifest.get("directories", []))
    paths.update(item.get("path") for item in manifest.get("files", []) if isinstance(item, dict))
    return {item for item in paths if isinstance(item, str)}


def _collect_contract_shape_errors(contract: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    standard = contract.get("standard_tree", {})
    required_files = set(standard.get("required_files", []))
    required_dirs = set(standard.get("required_dirs", []))
    zones = contract.get("zones", [])
    zone_paths = {
        path
        for zone in zones
        if isinstance(zone, dict)
        for path in zone.get("paths", [])
        if isinstance(path, str)
    }
    for path in sorted(required_files | required_dirs):
        if not any(
            path == zone_path
            or path.startswith(f"{zone_path}/")
            or zone_path.startswith(f"{path}/")
            for zone_path in zone_paths
        ):
            errors.append(f"project_folder_contract:required-path-not-covered-by-zone:{path}")

    zone_ids = [zone.get("id") for zone in zones if isinstance(zone, dict)]
    for zone_id in sorted({item for item in zone_ids if zone_ids.count(item) > 1}):
        errors.append(f"project_folder_contract:duplicate-zone:{zone_id}")

    if manifest:
        manifest_paths = _collect_manifest_paths(manifest)
        must_create = set(contract.get("routing_integration", {}).get("project_initializer_must_create", []))
        for path in sorted(must_create - manifest_paths):
            errors.append(f"project_folder_contract:initializer-missing-required-path:{path}")

    if "outputs/" not in _gitignore_template(manifest):
        errors.append("project_folder_contract:initializer-gitignore-missing-outputs")
    return errors


def _gitignore_template(manifest: dict[str, Any]) -> str:
    for item in manifest.get("files", []):
        if isinstance(item, dict) and item.get("path") == ".gitignore":
            return str(item.get("content", ""))
    return ""


def _collect_project_root_errors(
    project_root: Path,
    contract: dict[str, Any],
    *,
    project_type: str | None = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not project_root.exists():
        return [f"project_folder_contract:project-root-missing:{project_root}"], warnings, {}
    if not project_root.is_dir():
        return [f"project_folder_contract:project-root-not-directory:{project_root}"], warnings, {}

    standard = contract.get("standard_tree", {})
    required_files = set(standard.get("required_files", []))
    required_dirs = set(standard.get("required_dirs", []))
    override = None
    for item in contract.get("project_type_overrides", []):
        if isinstance(item, dict) and item.get("project_type") == project_type:
            override = item
            required_dirs.update(item.get("add_required_dirs", []))
            break

    missing_files = sorted(path for path in required_files if not _path_exists(project_root, path))
    missing_dirs = sorted(path for path in required_dirs if not _dir_exists(project_root, path))
    errors.extend(f"project_folder_contract:missing-required-file:{path}" for path in missing_files)
    errors.extend(f"project_folder_contract:missing-required-dir:{path}" for path in missing_dirs)

    root_items = [path.name for path in project_root.iterdir()] if project_root.exists() else []
    forbidden_hits: list[dict[str, str]] = []
    for rule in contract.get("forbidden_root_patterns", []):
        if not isinstance(rule, dict):
            continue
        pattern = rule.get("pattern")
        if not isinstance(pattern, str):
            continue
        for item in root_items:
            if fnmatch.fnmatch(item, pattern):
                forbidden_hits.append(
                    {
                        "path": item,
                        "pattern": pattern,
                        "default_action": str(rule.get("default_action", "ask_user")),
                    }
                )
    warnings.extend(
        f"project_folder_contract:forbidden-root-pattern:{hit['path']}:{hit['pattern']}"
        for hit in forbidden_hits
    )

    gitignore_path = project_root / ".gitignore"
    if gitignore_path.exists():
        gitignore = gitignore_path.read_text(encoding="utf-8", errors="replace")
        for expected in ["outputs/", ".env", "__pycache__/"]:
            if expected not in gitignore:
                warnings.append(f"project_folder_contract:gitignore-missing:{expected}")

    details = {
        "project_root": str(project_root),
        "project_type": project_type,
        "override_applied": override is not None,
        "missing_files": missing_files,
        "missing_dirs": missing_dirs,
        "forbidden_root_hits": forbidden_hits,
    }
    return errors, warnings, details


def validate_project_folder_contract(
    project_root: Path | None = None,
    *,
    project_type: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    schema = _safe_load(SCHEMA_PATH, "project_folder_contract.schema", errors)
    contract = _safe_load(CONTRACT_PATH, "project_folder_contract", errors)
    manifest = _safe_load(MANIFEST_PATH, "project_initializer_manifest", errors)

    if schema:
        errors.extend(collect_schema_document_errors(schema, "project_folder_contract.schema"))
    if schema and contract:
        errors.extend(collect_schema_errors(contract, schema, "project_folder_contract"))
    if contract:
        errors.extend(_collect_contract_shape_errors(contract, manifest))

    project_details: dict[str, Any] = {}
    if project_root is not None and contract:
        project_errors, project_warnings, project_details = _collect_project_root_errors(
            project_root.expanduser().resolve(),
            contract,
            project_type=project_type,
        )
        errors.extend(project_errors)
        warnings.extend(project_warnings)

    details = {
        "contract": str(CONTRACT_PATH.relative_to(SKILLS_ROOT)),
        "schema": str(SCHEMA_PATH.relative_to(SKILLS_ROOT)),
        "initializer_manifest": str(MANIFEST_PATH.relative_to(SKILLS_ROOT)),
        "required_file_count": len(contract.get("standard_tree", {}).get("required_files", [])) if contract else 0,
        "required_dir_count": len(contract.get("standard_tree", {}).get("required_dirs", [])) if contract else 0,
        "recommended_dir_count": len(contract.get("standard_tree", {}).get("recommended_dirs", [])) if contract else 0,
        "zone_count": len(contract.get("zones", [])) if contract else 0,
        "project": project_details,
    }
    return build_validator_result(
        validator="validate_project_folder_contract",
        scope="project_folder_contract",
        errors=errors,
        warnings=warnings,
        details=details,
    )
