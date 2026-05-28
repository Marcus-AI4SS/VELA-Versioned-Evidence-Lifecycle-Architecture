from __future__ import annotations



import argparse

import json

import re

import shutil

import subprocess

import sys

from pathlib import Path

from typing import Any



if __package__ in {None, ""}:

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from scripts import public_release_env as pre

    from scripts import vela_contract as contract

    from scripts import vela_initializer as initializer

else:

    from scripts import public_release_env as pre

    from scripts import vela_contract as contract

    from scripts import vela_initializer as initializer





def _ensure_git_repo(project_root: Path) -> bool:

    if (project_root / ".git").exists():

        return True

    git = shutil.which("git")

    if not git:

        return False

    result = subprocess.run([git, "init", "-b", "main", str(project_root)], capture_output=True, text=True)

    return result.returncode == 0





def _append_codex_trust(project_root: Path) -> bool:

    if not pre.CODEX_CONFIG_PATH.exists():

        return False

    pre.CODEX_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    project_key = f"[projects.'{project_root.as_posix()}']"

    desired_block = f'{project_key}\ntrust_level = "trusted"'

    config_text = pre.CODEX_CONFIG_PATH.read_text(encoding="utf-8")

    escaped_key = re.escape(project_key)

    trust_pattern = re.compile(rf"(?ms){escaped_key}\s*\r?\ntrust_level\s*=\s*\"[^\"]*\"")

    if trust_pattern.search(config_text):

        updated = trust_pattern.sub(desired_block, config_text)

    elif re.search(escaped_key, config_text):

        updated = re.sub(escaped_key, desired_block, config_text)

    else:

        updated = config_text.rstrip() + "\n\n" + desired_block + "\n"

    pre.CODEX_CONFIG_PATH.write_text(updated, encoding="utf-8")

    return True





def _load_registry() -> dict[str, Any]:

    pre.ensure_app_state_dirs()

    if not pre.APP_PROJECTS_REGISTRY.exists():

        return {"projects": []}

    try:

        return json.loads(pre.APP_PROJECTS_REGISTRY.read_text(encoding="utf-8"))

    except json.JSONDecodeError:

        return {"projects": []}





def _save_registry(payload: dict[str, Any]) -> None:

    pre.ensure_app_state_dirs()

    pre.APP_PROJECTS_REGISTRY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")





def register_project(project_root: Path, route_hint: str | None = None) -> None:

    registry = _load_registry()

    rows = registry.setdefault("projects", [])

    normalized = str(project_root.resolve())

    existing = [row for row in rows if row.get("path") == normalized]

    if existing:

        if route_hint:

            existing[0]["route_hint"] = route_hint

        existing[0]["source"] = "vela"

        _save_registry(registry)

        return

    rows.append(

        {

            "name": project_root.name,

            "path": normalized,

            "route_hint": route_hint,

            "source": "vela",

        }

    )

    _save_registry(registry)





def initialize_project(project_root: Path, skip_codex_trust: bool = False, route_hint: str | None = None) -> dict[str, Any]:

    project_root = project_root.expanduser().resolve()

    project_name = project_root.name

    project_root.mkdir(parents=True, exist_ok=True)



    root_agents_path = contract.package_root() / "AGENTS.md"

    if not root_agents_path.exists():

        raise FileNotFoundError(f"VELA package AGENTS.md was not found: {root_agents_path}")



    manifest_report = initializer.validate_manifest()

    if not manifest_report["ok"]:

        raise ValueError("Invalid VELA initializer manifest: " + "; ".join(manifest_report["errors"]))



    contract.ensure_wrapper_dirs(project_root)

    git_initialized = _ensure_git_repo(project_root)

    manifest_result = initializer.materialize_project(project_root, route_hint=route_hint)

    contract.install_starter_package(project_root)



    trust_updated = False

    if not skip_codex_trust:

        trust_updated = _append_codex_trust(project_root)



    register_project(project_root, route_hint=route_hint)

    context = contract.write_project_context(project_root)



    return {

        "ok": True,

        "project_root": str(project_root),

        "project_name": project_name,

        "context_schema": context["schema_version"],

        "context_path": str(project_root / ".vela" / "context.json"),

        "initializer_schema": manifest_result["schema_version"],

        "initializer_manifest": manifest_result["manifest_path"],

        "created_files": manifest_result["created_files"],

        "created_agents": manifest_result["created_agents"],

        "git_initialized": git_initialized,

        "codex_trust_updated": trust_updated,

        "route_hint": route_hint,

        "paths": {

            "codex_commands_dir": str(project_root / ".codex" / "commands"),

            "codex_profiles_dir": str(project_root / ".codex" / "profiles"),

            "helm_handoffs_dir": str(project_root / "handoffs" / "helm"),

            "gate_logs_dir": str(project_root / "logs" / "quality-gates"),

            "project_state_dir": str(project_root / "logs" / "project-state"),

        },

    }





def main() -> None:

    parser = argparse.ArgumentParser(description="Initialize a public VELA project scaffold.")

    parser.add_argument("--path", required=True, help="Project root path.")

    parser.add_argument("--route-hint", default=None, help="Optional route hint.")

    parser.add_argument("--skip-codex-trust", action="store_true", help="Do not write Codex trust config.")

    args = parser.parse_args()

    result = initialize_project(Path(args.path), skip_codex_trust=args.skip_codex_trust, route_hint=args.route_hint)

    print(json.dumps(result, ensure_ascii=False, indent=2))





if __name__ == "__main__":

    main()
