from __future__ import annotations



import json

import shutil

from datetime import datetime, timezone

from pathlib import Path

from typing import Any



if __package__ in {None, ""}:

    import sys



    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from scripts import vela_schema

else:

    from scripts import vela_schema





SCHEMA_VERSION = "vela.project.context.v1"

HELM_HANDOFF_SCHEMA_VERSION = "helm.codex.handoff.v1"



RESEARCH_DIRS = ("materials", "evidence", "claims", "methods", "deliverables")

TRUTH_FILES = (

    "research-map.md",

    "findings-memory.md",

    "material-passport.yaml",

    "evidence-ledger.yaml",

)





def utc_now() -> str:

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")





def repo_root() -> Path:

    return Path(__file__).resolve().parents[1]





def package_root() -> Path:

    return repo_root() / "package"





def _safe_project_id(project_root: Path) -> str:

    raw = project_root.name.strip().lower() or "vela-project"

    slug = "".join(ch if ch.isalnum() else "-" for ch in raw)

    slug = "-".join(part for part in slug.split("-") if part)

    return slug or "vela-project"





def _relative_or_absolute(root: Path, path: Path) -> str:

    try:

        return path.resolve().relative_to(root.resolve()).as_posix()

    except ValueError:

        return str(path)





def _copy_if_missing(source: Path, target: Path) -> None:

    if source.is_dir():

        target.mkdir(parents=True, exist_ok=True)

        for child in source.iterdir():

            _copy_if_missing(child, target / child.name)

        return

    if target.exists():

        return

    target.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source, target)





def install_starter_package(project_root: Path) -> None:

    starter = package_root()

    if not starter.exists():

        raise FileNotFoundError(f"VELA starter package not found: {starter}")

    _copy_if_missing(starter, project_root)





def ensure_wrapper_dirs(project_root: Path) -> None:

    for relative in (

        *RESEARCH_DIRS,

        "handoffs",

        "handoffs/helm",

        "logs",

        "logs/codex-runs",

        "logs/quality-gates",

        "logs/privacy-scans",

        "logs/project-state",

        ".codex",

        ".codex/commands",

        ".codex/profiles",

        ".vela",

    ):

        (project_root / relative).mkdir(parents=True, exist_ok=True)





def _count_files(path: Path) -> int:

    if not path.exists():

        return 0

    return sum(1 for item in path.rglob("*") if item.is_file() and item.name != ".gitkeep")





def _file_row(project_root: Path, relative: str) -> dict[str, Any]:

    path = project_root / relative

    row: dict[str, Any] = {

        "name": Path(relative).name,

        "path": relative,

        "exists": path.exists(),

    }

    if path.exists():

        row["updated_at"] = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        row["size"] = path.stat().st_size

    return row





def _load_json(path: Path) -> dict[str, Any]:

    if not path.exists():

        return {}

    try:

        data = json.loads(path.read_text(encoding="utf-8"))

        return data if isinstance(data, dict) else {}

    except json.JSONDecodeError:

        return {}





def build_project_context(project_root: Path) -> dict[str, Any]:

    project_root = project_root.expanduser().resolve()

    state = _load_json(project_root / "logs" / "project-state" / "current.json")

    generated_at = utc_now()

    stage = str(state.get("pipeline_stage") or state.get("current_stage") or "research_design")

    route_id = state.get("route_id")

    status = str(state.get("status") or "initialized")

    blockers = [str(item) for item in state.get("blockers", []) if str(item).strip()]

    truth_files = [_file_row(project_root, name) for name in TRUTH_FILES]

    missing_truth = [row["path"] for row in truth_files if not row.get("exists")]

    warnings = [f"Missing compatibility truth file: {path}" for path in missing_truth]
    counts = {

        "materials": _count_files(project_root / "materials"),

        "evidence": _count_files(project_root / "evidence"),

        "claims": _count_files(project_root / "claims"),

        "deliverables": _count_files(project_root / "deliverables"),

        "handoffs": _count_files(project_root / "handoffs"),

    }

    context = {

        "schema_version": SCHEMA_VERSION,

        "producer": "VELA",

        "consumer": "HELM",

        "generated_at": generated_at,

        "project": {

            "id": str(state.get("project_id") or _safe_project_id(project_root)),

            "name": str(state.get("project_name") or project_root.name),

            "title": str(state.get("project_name") or project_root.name),

            "root": str(project_root),

            "route_id": route_id,

            "stage": stage,

            "status": status,

        },

        "paths": {

            "materials": "materials",

            "evidence": "evidence",

            "claims": "claims",

            "methods": "methods",

            "deliverables": "deliverables",

            "handoffs": "handoffs",

            "handoffs_helm": "handoffs/helm",

            "logs": "logs",

        },

        "status": {

            "phase": stage,

            "blocked": bool(blockers or missing_truth),

            "last_updated": generated_at,

            "label": status,

        },

        "truth_files": truth_files,

        "counts": counts,

        "evidence": {

            "items": counts["evidence"],

            "verified": 0,

            "pending": counts["evidence"],

        },

        "quality": {

            "blockers": blockers,

            "warnings": warnings,

            "validators": [],

        },

        "helm": {

            "import_ready": not bool(missing_truth),

            "handoff_dir": "handoffs/helm",

            "handoff_policy": "explicit_user_export_only",

        },

        "deliverables": [],

        "handoffs": [],

    }

    return context





def write_project_context(project_root: Path) -> dict[str, Any]:

    project_root = project_root.expanduser().resolve()

    ensure_wrapper_dirs(project_root)

    context = build_project_context(project_root)

    target = project_root / ".vela" / "context.json"

    schema_errors = vela_schema.validate_payload(context, SCHEMA_VERSION, str(target))

    if schema_errors:

        raise ValueError("Invalid VELA project context: " + "; ".join(schema_errors))

    target.parent.mkdir(parents=True, exist_ok=True)

    target.write_text(json.dumps(context, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return context





def read_project_context(project_root: Path) -> dict[str, Any] | None:

    target = project_root.expanduser().resolve() / ".vela" / "context.json"

    if not target.exists():

        return None

    data = _load_json(target)

    if data.get("schema_version") != SCHEMA_VERSION:

        return None

    if vela_schema.validate_payload(data, SCHEMA_VERSION, str(target)):

        return None

    return data





def validate_project(project_root: Path, repair_context: bool = False) -> dict[str, Any]:

    project_root = project_root.expanduser().resolve()

    if repair_context:

        write_project_context(project_root)

    required_paths = [

        *((relative, "directory") for relative in RESEARCH_DIRS),

        ("handoffs", "directory"),

        ("handoffs/helm", "directory"),

        ("logs", "directory"),

        (".codex", "directory"),

        (".vela/context.json", "file"),

        ("AGENTS.md", "file"),

    ]

    checks = []

    for relative, expected_kind in required_paths:

        path = project_root / relative

        checks.append(

            {

                "path": relative,

                "exists": path.exists(),

                "kind": expected_kind,

            }

        )

    errors = [f"Missing required path: {row['path']}" for row in checks if not row["exists"]]

    context_path = project_root / ".vela" / "context.json"

    context_payload: dict[str, Any] | None = None

    if context_path.exists():

        payload, parse_errors = vela_schema.load_json_or_yaml(context_path)

        errors.extend(parse_errors)

        if payload is None:

            context_payload = None

        elif not isinstance(payload, dict):

            errors.append(f"{context_path}:root-must-be-object")

        else:

            context_payload = payload

            errors.extend(vela_schema.validate_payload(context_payload, SCHEMA_VERSION, str(context_path)))

    return vela_schema.validation_report(

        validator="project_validate",

        scope=str(project_root),

        errors=errors,

        warnings=[],

        checks=checks,

        project_root=str(project_root),

        context_schema=context_payload.get("schema_version") if context_payload else None,

    )
