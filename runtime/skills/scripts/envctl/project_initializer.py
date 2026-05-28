from __future__ import annotations



import json

import re

import shutil

import subprocess

from pathlib import Path

from typing import Any



try:

    from ..path_utils import CATALOG_ROOT, REPO_ROOT, SKILLS_ROOT

except ImportError:  # pragma: no cover

    from pathlib import Path as _Path

    import sys as _sys



    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

    from path_utils import CATALOG_ROOT, REPO_ROOT, SKILLS_ROOT





MANIFEST_PATH = CATALOG_ROOT / "project_initializer_manifest.json"

PROJECT_CONTRACT_FILE_PATHS = {

    "AGENTS.md",

    "research-map.md",

    "findings-memory.md",

    "material-passport.yaml",

    "evidence-ledger.yaml",

    "logs/quality-gates/pipeline-status.json",

    "logs/quality-gates/writing-quality-report.json",

    "logs/project-state/current.json",

    "logs/project-state/history.md",

}





def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:

    return json.loads(path.read_text(encoding="utf-8"))





def write_text_if_missing(path: Path, content: str) -> bool:

    if path.exists():

        return False

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(content, encoding="utf-8")

    return True





def write_json_if_missing(path: Path, payload: dict[str, Any]) -> bool:

    if path.exists():

        return False

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return True





def ensure_codex_trust(config_path: Path, project_path: Path) -> None:

    if not config_path.exists():

        raise FileNotFoundError(f"Codex config file was not found: {config_path}")

    config_text = config_path.read_text(encoding="utf-8")

    header = f"[projects.'{project_path}']"

    escaped_header = re.escape(header)

    trust_pattern = re.compile(rf"(?ms){escaped_header}\s*\r?\ntrust_level\s*=\s*\"[^\"]*\"")

    desired_block = f"{header}\ntrust_level = \"trusted\""



    if trust_pattern.search(config_text):

        config_text = trust_pattern.sub(desired_block, config_text)

    elif re.search(escaped_header, config_text):

        config_text = re.sub(escaped_header, desired_block, config_text)

    else:

        config_text = config_text.rstrip() + "\n\n" + desired_block + "\n"

    config_path.write_text(config_text, encoding="utf-8")





def render_template(value: Any, context: dict[str, str]) -> Any:

    if isinstance(value, str):

        return value.format(**context)

    if isinstance(value, list):

        return [render_template(item, context) for item in value]

    if isinstance(value, dict):

        return {key: render_template(item, context) for key, item in value.items()}

    return value





def initialize_project(project_path: Path, *, update_trust: bool = True, manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:

    git = shutil.which("git")

    if not git:

        raise RuntimeError("Git executable was not found in PATH.")



    root_agents_path = SKILLS_ROOT / "AGENTS.md"

    if not root_agents_path.exists():

        raise FileNotFoundError(f"Root AGENTS.md was not found: {root_agents_path}")



    manifest = load_manifest(manifest_path)

    project_path = project_path.expanduser().resolve()

    project_name = project_path.name

    shared_venv = REPO_ROOT / ".venv"

    context = {

        "project_name": project_name,

        "shared_venv": str(shared_venv),

    }



    created_files: list[str] = []

    project_path.mkdir(parents=True, exist_ok=True)

    for directory in manifest.get("directories", []):

        (project_path / directory).mkdir(parents=True, exist_ok=True)



    git_initialized = False

    if not (project_path / ".git").exists():

        subprocess.run([git, "init", "-b", "main", str(project_path)], check=True)

        git_initialized = True



    for item in manifest.get("files", []):

        target = project_path / item["path"]

        content = render_template(item["content"], context)

        if item["kind"] == "json":

            if write_json_if_missing(target, content):

                created_files.append(item["path"])

        else:

            if write_text_if_missing(target, content):

                created_files.append(item["path"])



    agents_dir = project_path / ".codex" / "agents"

    for file_name, payload in manifest.get("project_agents", {}).items():

        rendered_payload = render_template(payload, context)

        if write_json_if_missing(agents_dir / file_name, rendered_payload):

            created_files.append(f".codex/agents/{file_name}")



    config_path = Path.home() / ".codex" / "config.toml"

    if update_trust:

        ensure_codex_trust(config_path, project_path)



    return {

        "ok": True,

        "project_path": str(project_path),

        "git_repo": str(project_path / ".git"),

        "git_initialized": git_initialized,

        "project_agents_dir": str(agents_dir),

        "dispatch_dir": str(project_path / ".codex" / "dispatch"),

        "codex_trust_updated": update_trust,

        "codex_config_path": str(config_path),

        "created_files": created_files,

    }





def ensure_project_contract(

    project_path: Path,

    *,

    manifest_path: Path = MANIFEST_PATH,

    enable_all_agents: bool = True,

) -> dict[str, Any]:

    """Create the project-level Codex contract files without touching git or trust config."""

    root_agents_path = SKILLS_ROOT / "AGENTS.md"

    if not root_agents_path.exists():

        raise FileNotFoundError(f"Root AGENTS.md was not found: {root_agents_path}")



    manifest = load_manifest(manifest_path)

    project_path = project_path.expanduser().resolve()

    project_name = project_path.name

    shared_venv = REPO_ROOT / ".venv"

    context = {

        "project_name": project_name,

        "shared_venv": str(shared_venv),

    }



    created_files: list[str] = []

    created_dirs: list[str] = []

    updated_files: list[str] = []

    project_path.mkdir(parents=True, exist_ok=True)

    for directory in manifest.get("directories", []):

        target_dir = project_path / directory

        existed = target_dir.exists()

        target_dir.mkdir(parents=True, exist_ok=True)

        if not existed:

            created_dirs.append(directory)



    for item in manifest.get("files", []):

        if item["path"] not in PROJECT_CONTRACT_FILE_PATHS:

            continue

        target = project_path / item["path"]

        content = render_template(item["content"], context)

        if item["kind"] == "json":

            if write_json_if_missing(target, content):

                created_files.append(item["path"])

        else:

            if write_text_if_missing(target, content):

                created_files.append(item["path"])



    agents_dir = project_path / ".codex" / "agents"

    for file_name, payload in manifest.get("project_agents", {}).items():

        rendered_payload = render_template(payload, context)

        if enable_all_agents:

            rendered_payload["enabled"] = True

        target = agents_dir / file_name

        if write_json_if_missing(target, rendered_payload):

            created_files.append(f".codex/agents/{file_name}")

        elif enable_all_agents:

            existing = json.loads(target.read_text(encoding="utf-8"))

            if existing.get("enabled") is False:

                existing["enabled"] = True

                target.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

                updated_files.append(f".codex/agents/{file_name}")



    return {

        "ok": True,

        "project_path": str(project_path),

        "project_agents_dir": str(agents_dir),

        "created_dirs": created_dirs,

        "created_files": created_files,

        "updated_files": updated_files,

        "enable_all_agents": enable_all_agents,

        "mode": "project-contract-only",

    }
