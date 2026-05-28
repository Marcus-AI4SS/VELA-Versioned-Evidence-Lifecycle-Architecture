from __future__ import annotations



import json

import shutil

from pathlib import Path

from typing import Any



if __package__ in {None, ""}:

    import sys



    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from scripts import vela_contract as contract

    from scripts import vela_privacy

    from scripts import vela_schema

else:

    from scripts import vela_contract as contract

    from scripts import vela_privacy

    from scripts import vela_schema





PUBLIC_EXPORT_SCHEMA = "vela.public_export.manifest.v1"

INCLUDE_FILES = (

    "README.md",

    "research-map.md",

    "findings-memory.md",

    "material-passport.yaml",

    "evidence-ledger.yaml",

)

INCLUDE_DIRS = ("claims", "evidence", "methods", "deliverables", "handoffs")

SKIP_NAMES = {".gitkeep", ".env", ".env.local", "credentials.json", "secrets.json"}

SKIP_DIRS = {".git", ".venv", "__pycache__", "private-notes", "credentials", "secrets", "helm"}





def _relative(root: Path, path: Path) -> str:

    try:

        return path.resolve().relative_to(root.resolve()).as_posix()

    except ValueError:

        return str(path)





def _copy_file(project_root: Path, output_root: Path, source: Path, included: list[str], excluded: list[str]) -> None:

    relative = _relative(project_root, source)

    if source.name in SKIP_NAMES or any(part in SKIP_DIRS for part in Path(relative).parts):

        excluded.append(relative)

        return

    target = output_root / relative

    target.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source, target)

    included.append(relative)





def _copy_dir(project_root: Path, output_root: Path, source_dir: Path, included: list[str], excluded: list[str]) -> None:

    if not source_dir.exists():

        return

    for source in source_dir.rglob("*"):

        if source.is_file():

            _copy_file(project_root, output_root, source, included, excluded)





def _project_summary(project_root: Path) -> dict[str, Any]:

    context = contract.read_project_context(project_root)

    if context:

        project = context.get("project", {})

        return {

            "id": project.get("id"),

            "name": project.get("name") or project_root.name,

            "stage": project.get("stage"),

            "status": project.get("status"),

        }

    return {"id": None, "name": project_root.name}





def _safe_report_for_export(report: dict[str, Any]) -> dict[str, Any]:

    safe = dict(report)

    safe["scope"] = "."

    return safe





def build_public_export(project_root: Path, output_root: Path, *, force: bool = False) -> dict[str, Any]:

    project_root = project_root.expanduser().resolve()

    output_root = output_root.expanduser().resolve()

    if project_root == output_root:

        raise ValueError("Public export output must not be the project root.")



    privacy_report = vela_privacy.scan_project(project_root, scope_label=".")

    if privacy_report["errors"] and not force:

        return {

            "ok": False,

            "exported": False,

            "reason": "privacy_scan_failed",

            "validation": privacy_report,

        }



    output_root.mkdir(parents=True, exist_ok=True)

    included: list[str] = []

    excluded: list[str] = []



    for relative in INCLUDE_FILES:

        source = project_root / relative

        if source.exists() and source.is_file():

            _copy_file(project_root, output_root, source, included, excluded)



    for relative in INCLUDE_DIRS:

        _copy_dir(project_root, output_root, project_root / relative, included, excluded)



    safe_report = _safe_report_for_export(privacy_report)

    manifest = {

        "schema_version": PUBLIC_EXPORT_SCHEMA,

        "generated_at": contract.utc_now(),

        "project": _project_summary(project_root),

        "source_root": "<local-project-root>",

        "output_root": ".",

        "included_paths": sorted(set(included)),

        "excluded_paths": sorted(set(excluded)),

        "validation_report": safe_report,

    }

    schema_errors = vela_schema.validate_payload(manifest, PUBLIC_EXPORT_SCHEMA, "public-export-manifest")

    if schema_errors:

        raise ValueError("Invalid public export manifest: " + "; ".join(schema_errors))



    (output_root / "VELA-PUBLIC-EXPORT-MANIFEST.json").write_text(

        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",

        encoding="utf-8",

    )

    (output_root / "EXPORT-QUALITY-REPORT.json").write_text(

        json.dumps(safe_report, ensure_ascii=False, indent=2) + "\n",

        encoding="utf-8",

    )

    (output_root / "REDACTION-MANIFEST.md").write_text(

        "\n".join(

            [

                "# Redaction Manifest",

                "",

                "VELA created this export from public-safe project surfaces.",

                "",

                "Excluded paths:",

                *(f"- `{path}`" for path in sorted(set(excluded)) or ["None recorded"]),

                "",

                "Human review is still required before publishing.",

                "",

            ]

        ),

        encoding="utf-8",

    )

    return {

        "ok": True,

        "exported": True,

        "output": str(output_root),

        "manifest": str(output_root / "VELA-PUBLIC-EXPORT-MANIFEST.json"),

        "included_paths": sorted(set(included)),

        "excluded_paths": sorted(set(excluded)),

        "validation": safe_report,

    }
