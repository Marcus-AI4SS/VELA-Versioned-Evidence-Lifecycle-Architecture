from __future__ import annotations



import json

from pathlib import Path

from typing import Any



if __package__ in {None, ""}:

    import sys



    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from scripts import vela_contract as contract

    from scripts import vela_schema

else:

    from scripts import vela_contract as contract

    from scripts import vela_schema





SCHEMA_VERSION = "vela.project.initializer.v1"

MANIFEST_RELATIVE_PATH = Path(".vela") / "initializer-manifest.json"





def default_manifest_path() -> Path:

    return contract.package_root() / MANIFEST_RELATIVE_PATH





def load_manifest(path: Path | None = None) -> dict[str, Any]:

    manifest_path = path or default_manifest_path()

    return json.loads(manifest_path.read_text(encoding="utf-8"))





def _safe_relative_path(raw_path: str) -> Path:

    path = Path(raw_path)

    if path.is_absolute() or ".." in path.parts:

        raise ValueError(f"Initializer path must stay inside the project: {raw_path}")

    return path





def _render_value(value: Any, context: dict[str, Any]) -> Any:

    if isinstance(value, str):

        if value == "{route_hint_json}":

            return context["route_hint"]

        if value == "{generated_at_json}":

            return context["generated_at"]

        return value.format(**context)

    if isinstance(value, list):

        return [_render_value(item, context) for item in value]

    if isinstance(value, dict):

        return {key: _render_value(item, context) for key, item in value.items()}

    return value





def _write_text_if_missing(path: Path, content: str) -> bool:

    if path.exists():

        return False

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(content, encoding="utf-8")

    return True





def _write_json_if_missing(path: Path, payload: dict[str, Any]) -> bool:

    if path.exists():

        return False

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return True





def validate_manifest(manifest: dict[str, Any] | None = None) -> dict[str, Any]:

    payload = manifest if manifest is not None else load_manifest()

    scope = "inline-initializer-manifest" if manifest is not None else str(default_manifest_path())

    errors: list[str] = []

    warnings: list[str] = []

    schema_errors = vela_schema.validate_payload(payload, SCHEMA_VERSION, scope)

    errors.extend(schema_errors)



    if not isinstance(payload, dict):

        return vela_schema.validation_report(

            validator="initializer_manifest",

            scope=scope,

            errors=errors + ["initializer manifest root must be an object"],

            warnings=warnings,

            checks=[

                {"name": "schema", "passed": False},

                {"name": "path_safety", "passed": False},

            ],

            manifest_schema=None,

        )



    if payload.get("schema_version") != SCHEMA_VERSION:

        errors.append(f"schema_version must be {SCHEMA_VERSION}")



    directories = payload.get("directories")

    if not isinstance(directories, list):

        errors.append("directories must be a list")

    else:

        seen_dirs: set[str] = set()

        for item in directories:

            if not isinstance(item, str) or not item.strip():

                errors.append("directories contains a non-string or empty path")

                continue

            try:

                _safe_relative_path(item)

            except ValueError as exc:

                errors.append(str(exc))

            if item in seen_dirs:

                errors.append(f"duplicate directory entry: {item}")

            seen_dirs.add(item)



    files = payload.get("files")

    if not isinstance(files, list):

        errors.append("files must be a list")

    else:

        seen_files: set[str] = set()

        for item in files:

            if not isinstance(item, dict):

                errors.append("files contains a non-object entry")

                continue

            raw_path = item.get("path")

            if not isinstance(raw_path, str) or not raw_path.strip():

                errors.append("file entry is missing path")

                continue

            try:

                _safe_relative_path(raw_path)

            except ValueError as exc:

                errors.append(str(exc))

            if raw_path in seen_files:

                errors.append(f"duplicate file entry: {raw_path}")

            seen_files.add(raw_path)

            if item.get("kind") not in {"text", "json"}:

                errors.append(f"file entry has unsupported kind: {raw_path}")

            if "content" not in item:

                errors.append(f"file entry is missing content: {raw_path}")



    project_agents = payload.get("project_agents")

    if not isinstance(project_agents, dict):

        errors.append("project_agents must be an object")

    else:

        for file_name, agent_payload in project_agents.items():

            if not isinstance(file_name, str) or not file_name.endswith(".json"):

                errors.append(f"project agent key must be a JSON file name: {file_name}")

            if not isinstance(agent_payload, dict):

                errors.append(f"project agent payload must be an object: {file_name}")



    return vela_schema.validation_report(

        validator="initializer_manifest",

        scope=scope,

        errors=errors,

        warnings=warnings,

        checks=[

            {"name": "schema", "passed": not schema_errors},

            {"name": "path_safety", "passed": not any("inside the project" in error for error in errors)},

        ],

        manifest_schema=payload.get("schema_version") if isinstance(payload, dict) else None,

    )





def materialize_project(project_root: Path, route_hint: str | None = None, manifest_path: Path | None = None) -> dict[str, Any]:

    manifest = load_manifest(manifest_path)

    validation = validate_manifest(manifest)

    if not validation["ok"]:

        raise ValueError("Invalid VELA initializer manifest: " + "; ".join(validation["errors"]))



    project_root = project_root.expanduser().resolve()

    project_name = project_root.name

    route_hint_yaml = route_hint if route_hint else "null"

    context = {

        "project_name": project_name,

        "route_hint": route_hint,

        "route_hint_json": route_hint,

        "route_hint_yaml": route_hint_yaml,

        "generated_at": contract.utc_now(),

    }



    created_dirs: list[str] = []

    created_files: list[str] = []

    created_agents: list[str] = []



    for raw_directory in manifest.get("directories", []):

        relative = _safe_relative_path(raw_directory)

        target = project_root / relative

        if not target.exists():

            target.mkdir(parents=True, exist_ok=True)

            created_dirs.append(relative.as_posix())

        else:

            target.mkdir(parents=True, exist_ok=True)



    for item in manifest.get("files", []):

        relative = _safe_relative_path(item["path"])

        target = project_root / relative

        rendered = _render_value(item["content"], context)

        if item["kind"] == "json":

            if _write_json_if_missing(target, rendered):

                created_files.append(relative.as_posix())

        else:

            if _write_text_if_missing(target, str(rendered)):

                created_files.append(relative.as_posix())



    agents_dir = project_root / ".codex" / "agents"

    for file_name, agent_payload in manifest.get("project_agents", {}).items():

        relative = _safe_relative_path(file_name)

        target = agents_dir / relative

        rendered_payload = _render_value(agent_payload, context)

        if _write_json_if_missing(target, rendered_payload):

            created_agents.append((Path(".codex") / "agents" / relative).as_posix())



    return {

        "ok": True,

        "schema_version": manifest["schema_version"],

        "manifest_path": str(manifest_path or default_manifest_path()),

        "created_dirs": created_dirs,

        "created_files": created_files,

        "created_agents": created_agents,

    }
