from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .schema_validation import load_json
from .validator_envelope import build_validator_result

try:
    from ..path_utils import CONFIG_PATH, HELM_REPO_ROOT, REPO_ROOT, SCHEMAS_ROOT, VELA_REPO_ROOT
except ImportError:  # pragma: no cover
    from path_utils import CONFIG_PATH, HELM_REPO_ROOT, REPO_ROOT, SCHEMAS_ROOT, VELA_REPO_ROOT


PUBLIC_SCHEMA_FILES = [
    "vela.codex.handoff.v1.schema.json",
    "vela.project.context.v1.schema.json",
    "helm.codex.handoff.v1.schema.json",
]
OLD_ACTIVE_PATH_PATTERNS = [
    re.compile(r"<GIT_FOLDERS_ROOT>\\git-folders", re.IGNORECASE),
    re.compile(r"<GIT_FOLDERS_ROOT>/git-folders", re.IGNORECASE),
    re.compile(r"public-release[\\/]codex-research-stack", re.IGNORECASE),
]
OLD_VELA_EXPANSIONS = [
    "Versatile Experiment Lab & Automation",
    "Visual Evidence Literacy",
]


def _schema_version_const(schema: dict[str, Any]) -> str | None:
    return schema.get("properties", {}).get("schema_version", {}).get("const")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _scan_text_files(root: Path, patterns: list[str]) -> list[str]:
    hits: list[str] = []
    if not root.exists():
        return hits
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".toml", ".html", ".txt"}:
            continue
        try:
            text = _read_text(path)
        except OSError:
            continue
        for pattern in patterns:
            if pattern in text:
                hits.append(str(path.relative_to(root)).replace("\\", "/"))
                break
    return hits


def collect_cross_repo_drift_errors(
    *,
    vela_repo_root: Path = VELA_REPO_ROOT,
    helm_repo_root: Path = HELM_REPO_ROOT,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {
        "vela_repo_root": str(vela_repo_root),
        "helm_repo_root": str(helm_repo_root),
        "vela_repo_present": vela_repo_root.exists(),
        "helm_repo_present": helm_repo_root.exists(),
        "schema_checks": {},
        "helm_interface": {},
        "active_path_scan": {},
    }

    if not vela_repo_root.exists():
        errors.append(f"missing-vela-repo:{vela_repo_root}")
    if not helm_repo_root.exists():
        errors.append(f"missing-helm-repo:{helm_repo_root}")

    if vela_repo_root.exists():
        for schema_name in PUBLIC_SCHEMA_FILES:
            local_path = SCHEMAS_ROOT / schema_name
            vela_path = vela_repo_root / "schemas" / schema_name
            check: dict[str, Any] = {
                "local_exists": local_path.exists(),
                "vela_exists": vela_path.exists(),
            }
            if not local_path.exists() or not vela_path.exists():
                errors.append(f"schema-missing:{schema_name}")
                details["schema_checks"][schema_name] = check
                continue
            local_schema = load_json(local_path)
            vela_schema = load_json(vela_path)
            check.update(
                {
                    "local_id": local_schema.get("$id"),
                    "vela_id": vela_schema.get("$id"),
                    "local_schema_version": _schema_version_const(local_schema),
                    "vela_schema_version": _schema_version_const(vela_schema),
                }
            )
            if check["local_id"] != check["vela_id"]:
                errors.append(f"schema-id-drift:{schema_name}")
            if check["local_schema_version"] != check["vela_schema_version"]:
                errors.append(f"schema-version-drift:{schema_name}")
            details["schema_checks"][schema_name] = check

    if helm_repo_root.exists():
        interface_schema_path = helm_repo_root / "docs" / "imports" / "vela-helm-interface.schema.json"
        if not interface_schema_path.exists():
            errors.append("helm-interface-schema-missing")
        else:
            interface_schema = load_json(interface_schema_path)
            defs = interface_schema.get("$defs", {})
            project_context_version = (
                defs.get("velaProjectContext", {})
                .get("properties", {})
                .get("schema_version", {})
                .get("const")
            )
            helm_handoff_version = (
                defs.get("helmCodexHandoff", {})
                .get("properties", {})
                .get("schema_version", {})
                .get("const")
            )
            details["helm_interface"] = {
                "path": "docs/imports/vela-helm-interface.schema.json",
                "vela_project_context": project_context_version,
                "helm_codex_handoff": helm_handoff_version,
            }
            if project_context_version != "vela.project.context.v1":
                errors.append("helm-interface-vela-project-context-version-drift")
            if helm_handoff_version != "helm.codex.handoff.v1":
                errors.append("helm-interface-handoff-version-drift")
        old_expansion_hits = _scan_text_files(helm_repo_root / "docs", OLD_VELA_EXPANSIONS)
        details["helm_old_vela_expansion_hits"] = old_expansion_hits
        errors.extend(f"helm-old-vela-expansion:{item}" for item in old_expansion_hits)

    active_paths = {
        "settings": REPO_ROOT / "skills" / "catalog" / "settings.toml",
        "codex_config": CONFIG_PATH,
    }
    for label, path in active_paths.items():
        if not path.exists():
            warnings.append(f"active-path-scan-missing:{label}:{path}")
            continue
        text = _read_text(path)
        hits = [pattern.pattern for pattern in OLD_ACTIVE_PATH_PATTERNS if pattern.search(text)]
        details["active_path_scan"][label] = {"path": str(path), "hits": hits}
        errors.extend(f"old-active-path:{label}:{pattern}" for pattern in hits)

    return errors, warnings, details


def validate_cross_repo_drift(
    *,
    vela_repo_root: Path = VELA_REPO_ROOT,
    helm_repo_root: Path = HELM_REPO_ROOT,
) -> dict[str, Any]:
    errors, warnings, details = collect_cross_repo_drift_errors(
        vela_repo_root=vela_repo_root,
        helm_repo_root=helm_repo_root,
    )
    return build_validator_result(
        validator="cross_repo_drift",
        scope="local_vela_helm",
        errors=errors,
        warnings=warnings,
        details=details,
    )
