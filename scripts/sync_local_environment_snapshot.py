from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT.parent / "skills-environment-local"
DESTINATION = REPO_ROOT / "research-stack" / "local-environment"

EXCLUDED_PATH_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "outputs",
    "manager-app",
}

EXCLUDED_NAME_PARTS = {
    "desktop-app",
    "desktop_app",
    "desktop-ui",
    "desktop_ui",
    "scholar-nuwa",
    "scholar_nuwa",
    "scholar-panel",
    "scholar_panel",
    "scholar_advisory_panel",
}

PRIVATE_PATH_REPLACEMENTS = {
    "D:\\AI environment-GITHUB": "<AI_ENV_ROOT>",
    "D:/AI environment-GITHUB": "<AI_ENV_ROOT>",
    "D:\\AI environment-GITHUB\\git-folders": "<GIT_FOLDERS_ROOT>",
    "D:/AI environment-GITHUB/git-folders": "<GIT_FOLDERS_ROOT>",
    "D:\\AI environment-GITHUB\\git-folders\\skills-environment-local": "<LOCAL_ENV_ROOT>",
    "D:/AI environment-GITHUB/git-folders/skills-environment-local": "<LOCAL_ENV_ROOT>",
    "C:\\Users\\17666\\.codex": "<CODEX_HOME>",
    "C:/Users/17666/.codex": "<CODEX_HOME>",
    "C:\\Users\\17666\\Documents\\Obsidian Vault": "<OBSIDIAN_VAULT>",
    "C:/Users/17666/Documents/Obsidian Vault": "<OBSIDIAN_VAULT>",
    "Obsidian Vault": "<OBSIDIAN_VAULT>",
    "C:\\Users\\17666\\Desktop": "<USER_DESKTOP>",
    "C:/Users/17666/Desktop": "<USER_DESKTOP>",
    "C:\\Users\\17666\\Downloads": "<USER_DOWNLOADS>",
    "C:/Users/17666/Downloads": "<USER_DOWNLOADS>",
    "C:\\Users\\17666\\Zotero": "<ZOTERO_HOME>",
    "C:/Users/17666/Zotero": "<ZOTERO_HOME>",
    "C:\\Users\\17666": "<USER_HOME>",
    "C:/Users/17666": "<USER_HOME>",
}

TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".svg",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

LINE_STRIP_SUFFIXES = {".md", ".toml", ".txt"}

ROOT_FILES = [
    "AGENTS.md",
    "README.md",
    "BUILD-LOGIC.md",
    "WORKSPACE-LOG.md",
]

SKILLS_SUBTREES = [
    "AGENTS.md",
    "README.md",
    "catalog",
    "schemas",
    "profiles",
    "scripts",
    "templates",
    "tests",
    "docs",
    "plugins/research-autopilot/skills",
]

ASSET_SUBTREES = [
    "assets/local-environment-map.png",
    "assets/local-environment-map.svg",
    "assets/environment-overview-image2",
]


def run_text(args: list[str], cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def is_excluded(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    if any(part in EXCLUDED_PATH_PARTS for part in parts):
        return True
    joined = "/".join(parts)
    return any(token in joined for token in EXCLUDED_NAME_PARTS)


def copy_filtered(src: Path, dst: Path) -> list[str]:
    copied: list[str] = []
    if not src.exists():
        return copied
    if src.is_file():
        if not is_excluded(src):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(str(dst.relative_to(DESTINATION)).replace("\\", "/"))
        return copied

    for item in src.rglob("*"):
        rel = item.relative_to(src)
        if is_excluded(rel) or is_excluded(item):
            continue
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied.append(str(target.relative_to(DESTINATION)).replace("\\", "/"))
    return copied


def contains_excluded_token(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower() if not isinstance(value, str) else value.lower()
    return any(token in text for token in EXCLUDED_NAME_PARTS)


def prune_json_value(value: Any, *, root: bool = False) -> Any:
    if isinstance(value, list):
        result = []
        for item in value:
            if contains_excluded_token(item):
                continue
            pruned = prune_json_value(item)
            if pruned is not None:
                result.append(pruned)
        return result
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if any(token in key.lower() for token in EXCLUDED_NAME_PARTS):
                continue
            pruned = prune_json_value(child)
            if pruned is not None:
                result[key] = pruned
        return result
    if isinstance(value, str) and contains_excluded_token(value) and not root:
        return None
    return value


def prune_snapshot_jsons(destination_root: Path) -> None:
    for json_path in (destination_root / "skills" / "catalog").glob("*.json"):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        json_path.write_text(
            json.dumps(prune_json_value(payload, root=True), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def scrub_text_files(destination_root: Path) -> None:
    for path in destination_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for source, replacement in sorted(PRIVATE_PATH_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
            text = text.replace(source, replacement)
        if path.suffix.lower() in LINE_STRIP_SUFFIXES:
            lines = []
            for line in text.splitlines():
                lower = line.lower()
                if any(token in lower for token in EXCLUDED_NAME_PARTS):
                    continue
                lines.append(line)
            text = "\n".join(lines) + ("\n" if lines else "")
        path.write_text(text, encoding="utf-8")


def scrub_local_settings(destination_root: Path) -> None:
    settings_path = destination_root / "skills" / "catalog" / "settings.toml"
    if not settings_path.exists():
        return
    settings_path.write_text(
        """[paths]
root = "<LOCAL_ENV_ROOT>/skills"
codex_home = "<CODEX_HOME>"
config_path = "<CODEX_HOME>/config.toml"
skills_dir = "<CODEX_HOME>/skills"
cloud_dir = "<LOCAL_ENV_ROOT>/skills/cloud"

[obsidian]
vault_path = "<OBSIDIAN_VAULT>"
vault_subdir = "Codex Research"
sync_export_dir = "<LOCAL_ENV_ROOT>/skills/outputs/reports/obsidian-sync"

[plugin_marketplace]
path = "<LOCAL_ENV_ROOT>/skills/.agents/plugins/marketplace.json"
home_path = "<AGENTS_HOME>/plugins/marketplace.json"

[global_route_rules]
language = "zh-CN"
role = "world-class-doctoral-supervisor"
require_realtime_verification = true
formal_citation_requires_doi = true
forbid_unverified_references = true
forbid_ai_hallucinated_citations = true
data_paragraph_framework = "PEEL"
""",
        encoding="utf-8",
    )


def command_version(command: str, args: list[str]) -> dict[str, Any]:
    location = run_text(["where.exe", command], REPO_ROOT)
    version = run_text([command, *args], REPO_ROOT)
    return {
        "command": command,
        "available": bool(location or version),
        "version": version.splitlines()[0] if version else None,
        "path_policy": "absolute local paths are intentionally not exported",
        "location_count": len(location.splitlines()) if location else 0,
    }


def build_toolchain_inventory() -> dict[str, Any]:
    return {
        "schema_version": "vela.local_toolchain_inventory.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tools": [
            {**command_version("git", ["--version"]), "role": "version control and rollback"},
            {**command_version("rg", ["--version"]), "role": "fast repository and text search"},
            {**command_version("python", ["--version"]), "role": "validators, envctl, scripts, tests"},
            {**command_version("node", ["--version"]), "role": "presentation validators and browser tooling"},
            {**command_version("gh", ["--version"]), "role": "GitHub inspection and publication"},
            {
                **command_version("powershell", ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]),
                "role": "Windows shell compatibility",
            },
            {
                **command_version("pwsh", ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]),
                "role": "PowerShell 7 UTF-8 friendly automation",
            },
            {**command_version("uv", ["--version"]), "role": "optional Python package/runtime manager"},
        ],
    }


def count_files(root: Path) -> int:
    return sum(1 for item in root.rglob("*") if item.is_file())


def write_manifest(source: Path, copied: list[str]) -> None:
    source_head = run_text(["git", "rev-parse", "--short", "HEAD"], source)
    source_branch = run_text(["git", "branch", "--show-current"], source)
    since_count = run_text(
        [
            "git",
            "log",
            "--since=2026-05-01 00:00:00",
            "--pretty=format:%H",
        ],
        source,
    )
    manifest = {
        "schema_version": "vela.local_environment_snapshot.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "repository": "skills-environment-local",
            "branch": source_branch,
            "head": source_head,
            "since": "2026-05-01",
            "commit_count_since": len(since_count.splitlines()) if since_count else 0,
        },
        "policy": {
            "intent": "Mirror the local research environment into VELA except explicitly excluded areas.",
            "include": [
                "research routing and workflow contracts",
                "engineering-cybernetics control kernel",
                "seven-layer environment contract",
                "memory governance",
                "literature acquisition and citation evidence workflows",
                "writing, review, figure, presentation, submission, and quantitative workflows",
                "MCP/profile/toolchain configuration templates",
                "validators, envctl modules, scripts, schemas, and tests",
            ],
            "exclude": [
                "desktop app development chain",
                "distilled scholar generation and scholar advisory panel chain",
                "runtime caches and generated outputs",
                "browser login state, cookies, credentials, and personal secrets",
                "private absolute paths; exported settings use placeholders",
            ],
        },
        "layout": {
            "root": "research-stack/local-environment",
            "runtime_mode": "snapshot; not automatically executed by VELA init",
            "settings_policy": "settings.toml is scrubbed to portable placeholders",
        },
        "copied_file_count": len(copied),
        "total_file_count": count_files(DESTINATION),
    }
    (DESTINATION / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_readme() -> None:
    (DESTINATION / "README.md").write_text(
        """# Local Research Environment Snapshot

This directory mirrors the current local Codex research environment for VELA.

It is a source snapshot, not an automatic runtime installer. VELA can read it to adopt local rules, workflows, validators, memory governance, tool profiles, and documentation. The existing VELA initializer remains stable unless a future change explicitly promotes part of this snapshot into the default package.

## Included

- engineering-cybernetics control kernel and source-rule contracts
- seven-layer environment governance: execution, tool, context, lifecycle, observability, verification, governance
- local memory system contracts and validators
- research routing, project initializer, team planning, and clarification contracts
- literature acquisition, CNKI/Google Scholar/Zotero evidence paths, citation evidence rules
- structured reading, manuscript writing, peer review, revision, figure, presentation, submission, and empirical quantitative workflows
- MCP/profile configuration templates and toolchain inventory
- envctl modules, validators, scripts, schemas, tests, and product overview assets

## Excluded

- desktop app development skills and profiles
- distilled scholar generation, scholar panel, and personal scholar-role material
- runtime caches, generated outputs, browser state, cookies, credentials, and personal secrets
- machine-specific absolute paths; `skills/catalog/settings.toml` is converted to placeholders

## How VELA Should Use It

1. Read `manifest.json` first.
2. Treat `skills/catalog` and `skills/schemas` as the contract layer.
3. Treat `skills/plugins/research-autopilot/skills` as the skill source layer.
4. Treat `skills/profiles` as MCP/profile intent, not as user config to write blindly.
5. Promote changes into VELA only through explicit schema, tests, and privacy review.

""",
        encoding="utf-8",
    )


def sync(source: Path) -> None:
    if not source.exists():
        raise SystemExit(f"source repository not found: {source}")
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    DESTINATION.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for file_name in ROOT_FILES:
        copied.extend(copy_filtered(source / file_name, DESTINATION / file_name))
    for subtree in SKILLS_SUBTREES:
        copied.extend(copy_filtered(source / "skills" / subtree, DESTINATION / "skills" / subtree))
    for subtree in ASSET_SUBTREES:
        copied.extend(copy_filtered(source / subtree, DESTINATION / subtree))

    scrub_local_settings(DESTINATION)
    prune_snapshot_jsons(DESTINATION)
    scrub_text_files(DESTINATION)
    toolchain_dir = DESTINATION / "toolchain"
    toolchain_dir.mkdir(parents=True, exist_ok=True)
    (toolchain_dir / "toolchain_inventory.json").write_text(
        json.dumps(build_toolchain_inventory(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_readme()
    write_manifest(source, copied)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync the local research environment snapshot into VELA.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Path to skills-environment-local")
    args = parser.parse_args()
    sync(args.source.resolve())


if __name__ == "__main__":
    main()
