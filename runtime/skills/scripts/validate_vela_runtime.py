from __future__ import annotations



import json

import sys

from pathlib import Path





SKILLS_ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_TOKENS = [

    "app-" + "product-producer",

    "app-" + "architect",

    "app-" + "ui-producer",

    "app-" + "release-producer",

    "app-" + "qa-reviewer",

    "desktop-" + "app-development",

    "scholar-" + "nuwa",

    "scholar-" + "panel",

    "scholar" + "_panel",

    "scholar" + "_advisory_panel",

    "zotero-" + "mcp",

    "xiao" + "hongshu",

    "小" + "红书",

    "c:" + "\\users\\" + "17" + "666",

    "c:" + "/users/" + "17" + "666",

    "d:" + "\\ai environment-github",

]

REQUIRED_PATHS = [
    "AGENTS.md",

    "catalog/routing_table.json",

    "catalog/skill_catalog.json",

    "catalog/local_memory_system.json",

    "catalog/project_folder_contract.json",

    "catalog/figure_style_presets.json",

    "catalog/route_mcp_activation_policy.json",

    "catalog/protected_runtime_paths.json",

    "schemas/validator_result.schema.json",

    "schemas/local_memory_system.v1.schema.json",

    "schemas/project_folder_contract.v1.schema.json",

    "schemas/figure_style_presets.v1.schema.json",

    "profiles/baseline.toml",

    "profiles/startup-safe.toml",

    "scripts/envctl/__main__.py",

    "scripts/envctl/project_folder_contract.py",

    "scripts/envctl/figure_style_presets.py",

    "plugins/research-autopilot/skills/research-autopilot/SKILL.md",

]


def is_isolated_codex_worktree(root: Path) -> bool:
    normalized = str(root).replace("\\", "/").lower()
    return "/.codex/worktrees/" in normalized or "/codex/worktrees/" in normalized or "<codex_home>/worktrees/" in normalized


def isolated_cross_repo_warning(error: str) -> bool:
    return error.startswith("cross-repo-drift:missing-vela-repo:") or error.startswith(
        "cross-repo-drift:missing-helm-repo:"
    )


def isolated_runtime_skill_warning(error: str) -> bool:
    return error.startswith("runtime-skill-drift:research-autopilot-cache-differs-from-source:")


def python_module_command(python_executable: str, module: str, *args: str) -> list[str]:
    return [python_executable, "-m", module, *args]


def collect_project_root_file_errors(details: dict) -> list[str]:
    project_root_files = details.get("project_root_files", {})
    if not isinstance(project_root_files, dict):
        return []
    return [
        f"project-root-file-missing:{name}"
        for name, present in project_root_files.items()
        if present is not True
    ]


def main() -> int:
    errors: list[str] = []

    commands: dict[str, dict[str, object]] = {}

    for relative in REQUIRED_PATHS:

        exists = (SKILLS_ROOT / relative).exists()

        commands[f"path:{relative}"] = {"ok": exists}

        if not exists:

            errors.append(f"path-missing:{relative}")



    text_suffixes = {".json", ".md", ".ps1", ".py", ".toml", ".txt", ".yaml", ".yml"}

    findings: list[str] = []

    for path in SKILLS_ROOT.rglob("*"):

        if not path.is_file() or path.suffix.lower() not in text_suffixes:

            continue

        if "__pycache__" in path.parts:

            continue

        text = path.read_text(encoding="utf-8", errors="replace").lower()

        for token in EXCLUDED_TOKENS:

            if token in text:

                findings.append(str(path.relative_to(SKILLS_ROOT)).replace("\\", "/") + ":" + token)

                break

    commands["excluded-token-scan"] = {"ok": not findings, "findings": findings}

    errors.extend(f"excluded-token:{item}" for item in findings)



    payload = {

        "schema_version": "validator_result.v1",

        "validator": "validate_vela_runtime",

        "scope": "vela_runtime_distribution",

        "ok": not errors,

        "decision": "pass" if not errors else "fail",

        "errors": errors,

        "warnings": [],

        "details": {

            "skills_root": str(SKILLS_ROOT),

            "commands": commands,

            "distribution_policy": "VELA runtime package without account state, credentials, private paths, browser state, caches, or generated outputs",
        },

        "commands": commands,

    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0 if not errors else 1





if __name__ == "__main__":

    raise SystemExit(main())
