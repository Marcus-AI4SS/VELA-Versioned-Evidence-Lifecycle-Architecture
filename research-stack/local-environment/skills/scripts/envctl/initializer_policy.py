from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from .schema_validation import collect_schema_errors, load_json
from .validator_envelope import build_validator_result

try:
    from ..path_utils import CATALOG_ROOT, REPO_ROOT, SCHEMAS_ROOT
except ImportError:  # pragma: no cover
    from path_utils import CATALOG_ROOT, REPO_ROOT, SCHEMAS_ROOT


LOCAL_INITIALIZER_PATH = CATALOG_ROOT / "project_initializer_manifest.json"
LOCAL_INITIALIZER_SCHEMA_PATH = SCHEMAS_ROOT / "project_initializer_manifest.schema.json"
VELA_REPO_ROOT = REPO_ROOT.parent / "VELA-workflow"
VELA_INITIALIZER_PATH = VELA_REPO_ROOT / "package" / ".vela" / "initializer-manifest.json"
VELA_INITIALIZER_SCHEMA_PATH = VELA_REPO_ROOT / "schemas" / "vela.project.initializer.v1.schema.json"

PRIVATE_STRING_PATTERNS = [
    re.compile(r"\b[A-Za-z]:\\"),
    re.compile(r"<USER_HOME>", re.IGNORECASE),
    re.compile(r"C:\\Users\\17666", re.IGNORECASE),
    re.compile(r"<AI_ENV_ROOT>", re.IGNORECASE),
    re.compile(r"D:\\AI environment-GITHUB", re.IGNORECASE),
    re.compile(r"skills-app-own", re.IGNORECASE),
    re.compile(r"manager-app", re.IGNORECASE),
    re.compile(r"<OBSIDIAN_VAULT>", re.IGNORECASE),
    re.compile(r"Zotero", re.IGNORECASE),
]
APP_ONLY_AGENT_PREFIXES = ("app-", "desktop-app-")
APP_RELEASE_PATH_MARKERS = ("manager-app", "release-package", "desktop-build", "app-release")
HIDDEN_EXECUTION_KEYS = {
    "auto_execute",
    "autonomous_loop",
    "background_execution",
    "hidden_execution",
    "silent_execute",
}


def _is_safe_relative_path(path_value: str) -> bool:
    if not isinstance(path_value, str) or not path_value.strip():
        return False
    if "\\" in path_value or path_value.startswith("/") or re.match(r"^[A-Za-z]:", path_value):
        return False
    normalized = PurePosixPath(path_value)
    return str(normalized) != "." and ".." not in normalized.parts


def _walk_strings(payload: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(payload, str):
        yield path, payload
    elif isinstance(payload, dict):
        for key, value in payload.items():
            yield from _walk_strings(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            yield from _walk_strings(value, f"{path}[{index}]")


def _walk_key_values(payload: Any, path: str = "$") -> Iterable[tuple[str, Any, str]]:
    if isinstance(payload, dict):
        for key, value in payload.items():
            current_path = f"{path}.{key}"
            yield key, value, current_path
            yield from _walk_key_values(value, current_path)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            yield from _walk_key_values(value, f"{path}[{index}]")


def _validate_manifest_paths(manifest: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for path_value in manifest.get("directories", []):
        if not _is_safe_relative_path(path_value):
            errors.append(f"{label}:unsafe-directory:{path_value}")
    for item in manifest.get("files", []):
        if not isinstance(item, dict):
            continue
        path_value = item.get("path")
        if not _is_safe_relative_path(path_value):
            errors.append(f"{label}:unsafe-file:{path_value}")
    for file_name in manifest.get("project_agents", {}):
        if not _is_safe_relative_path(f".codex/agents/{file_name}"):
            errors.append(f"{label}:unsafe-agent-file:{file_name}")
    return errors


def _validate_public_initializer(local_manifest: dict[str, Any], vela_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    local_agent_ids = {
        payload.get("agent_id")
        for payload in local_manifest.get("project_agents", {}).values()
        if isinstance(payload, dict)
    }
    for file_name, payload in vela_manifest.get("project_agents", {}).items():
        if not isinstance(payload, dict):
            errors.append(f"vela-initializer:agent-not-object:{file_name}")
            continue
        agent_id = payload.get("agent_id")
        if agent_id not in local_agent_ids:
            errors.append(f"vela-initializer:agent-not-in-local-source:{agent_id}")
        if isinstance(agent_id, str) and agent_id.startswith(APP_ONLY_AGENT_PREFIXES):
            errors.append(f"vela-initializer:app-only-agent:{agent_id}")

    for path, value in _walk_strings(vela_manifest):
        for pattern in PRIVATE_STRING_PATTERNS:
            if pattern.search(value):
                errors.append(f"vela-initializer:private-string:{path}")
                break
        lowered = value.lower()
        if any(marker in lowered for marker in APP_RELEASE_PATH_MARKERS):
            errors.append(f"vela-initializer:app-release-output:{path}")

    for key, value, path in _walk_key_values(vela_manifest):
        if key in HIDDEN_EXECUTION_KEYS and value:
            errors.append(f"vela-initializer:hidden-execution-default:{path}")
    return errors


def collect_initializer_policy_errors(
    *,
    vela_repo_root: Path = VELA_REPO_ROOT,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    local_manifest = load_json(LOCAL_INITIALIZER_PATH)
    local_schema = load_json(LOCAL_INITIALIZER_SCHEMA_PATH)
    errors.extend(collect_schema_errors(local_manifest, local_schema, LOCAL_INITIALIZER_PATH.name))
    errors.extend(_validate_manifest_paths(local_manifest, "local-initializer"))

    vela_initializer_path = vela_repo_root / "package" / ".vela" / "initializer-manifest.json"
    vela_schema_path = vela_repo_root / "schemas" / "vela.project.initializer.v1.schema.json"
    details: dict[str, Any] = {
        "local_initializer_agents": len(local_manifest.get("project_agents", {})),
        "vela_repo_root": str(vela_repo_root),
        "vela_repo_present": vela_repo_root.exists(),
    }
    if not vela_repo_root.exists():
        warnings.append(f"vela-repo-missing:{vela_repo_root}")
        details["vela_initializer_agents"] = 0
        return errors, warnings, details
    if not vela_initializer_path.exists():
        errors.append(f"vela-initializer-missing:{vela_initializer_path}")
        details["vela_initializer_agents"] = 0
        return errors, warnings, details
    if not vela_schema_path.exists():
        errors.append(f"vela-initializer-schema-missing:{vela_schema_path}")
        details["vela_initializer_agents"] = 0
        return errors, warnings, details

    vela_manifest = load_json(vela_initializer_path)
    vela_schema = load_json(vela_schema_path)
    errors.extend(collect_schema_errors(vela_manifest, vela_schema, vela_initializer_path.name))
    errors.extend(_validate_manifest_paths(vela_manifest, "vela-initializer"))
    errors.extend(_validate_public_initializer(local_manifest, vela_manifest))
    details["vela_initializer_agents"] = len(vela_manifest.get("project_agents", {}))
    details["vela_initializer_files"] = len(vela_manifest.get("files", []))
    return errors, warnings, details


def validate_initializer_policy(*, vela_repo_root: Path = VELA_REPO_ROOT) -> dict[str, Any]:
    errors, warnings, details = collect_initializer_policy_errors(vela_repo_root=vela_repo_root)
    return build_validator_result(
        validator="initializer_policy",
        scope="local_to_vela",
        errors=errors,
        warnings=warnings,
        details=details,
    )
