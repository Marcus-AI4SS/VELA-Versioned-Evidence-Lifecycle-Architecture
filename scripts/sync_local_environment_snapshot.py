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
DROP = object()

EXCLUDED_PATH_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "outputs",
    "manager-app",
}

EXCLUDED_NAME_PARTS = {
    "app-product-producer",
    "app-architect",
    "app-ui-producer",
    "app-release-producer",
    "app-qa-reviewer",
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

STATIC_PRIVATE_TEXT_REPLACEMENTS = {
    "Obsidian Vault": "<OBSIDIAN_VAULT>",
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
]

PYTHON_SUBTREES = [
    "requirements",
    "manifests",
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
            if pruned is not DROP:
                result.append(pruned)
        return result
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if any(token in key.lower() for token in EXCLUDED_NAME_PARTS):
                continue
            pruned = prune_json_value(child)
            if pruned is not DROP:
                result[key] = pruned
        return result
    if isinstance(value, str) and contains_excluded_token(value) and not root:
        return DROP
    return value


def prune_snapshot_jsons(destination_root: Path) -> None:
    for json_path in (destination_root / "skills" / "catalog").glob("*.json"):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        json_path.write_text(
            json.dumps(prune_json_value(payload, root=True), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    normalize_protected_runtime_paths(destination_root)


def normalize_protected_runtime_paths(destination_root: Path) -> None:
    protected_path = destination_root / "skills" / "catalog" / "protected_runtime_paths.json"
    if not protected_path.exists():
        return
    payload = json.loads(protected_path.read_text(encoding="utf-8"))
    if payload.get("paths"):
        return
    payload["paths"] = [
        {
            "id": "excluded-protected-runtime-boundary",
            "path": "<PROTECTED_RUNTIME_PATH>",
            "owner": "user",
            "purpose": "Placeholder for local protected runtime paths intentionally excluded from the VELA snapshot.",
            "protection_level": "no_touch",
            "allowed_operations": ["record_boundary_only"],
            "forbidden_operations": [
                "write",
                "sync",
                "clean",
                "delete",
                "rename",
                "overwrite",
                "install_dependency",
                "auto_evolve",
                "bulk_content_scan",
                "environment_automation_mutation",
            ],
            "reason": "VELA keeps the boundary contract without exporting private path names or excluded skill content.",
        }
    ]
    protected_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _path_variants(path: Path) -> set[str]:
    values = {str(path), path.as_posix()}
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    values.update({str(resolved), resolved.as_posix()})
    return {value for value in values if value}


def build_private_path_replacements(source: Path) -> dict[str, str]:
    replacements = dict(STATIC_PRIVATE_TEXT_REPLACEMENTS)
    source = source.expanduser()
    dynamic_paths = [
        (source, "<LOCAL_ENV_ROOT>"),
        (source.parent, "<GIT_FOLDERS_ROOT>"),
        (source.parent.parent, "<AI_ENV_ROOT>"),
        (REPO_ROOT, "<VELA_REPO_ROOT>"),
    ]
    home = Path.home()
    dynamic_paths.extend(
        [
            (home / ".codex", "<CODEX_HOME>"),
            (home / "Documents" / "Obsidian Vault", "<OBSIDIAN_VAULT>"),
            (home / "Desktop", "<USER_DESKTOP>"),
            (home / "Downloads", "<USER_DOWNLOADS>"),
            (home / "Zotero", "<ZOTERO_HOME>"),
            (home, "<USER_HOME>"),
        ]
    )
    for path, placeholder in dynamic_paths:
        for value in _path_variants(path):
            replacements[value] = placeholder
    return replacements


def scrub_text_files(destination_root: Path, replacements: dict[str, str]) -> None:
    for path in destination_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for source, replacement in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
            text = text.replace(source, replacement)
            text = text.replace(source.replace("\\", "\\\\"), replacement)
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


def patch_snapshot_runtime_boundaries(destination_root: Path) -> None:
    remove_distribution_only_exclusions(destination_root)
    patch_envctl_entrypoint(destination_root)
    patch_cybernetics_contract_list(destination_root)
    patch_helm_snapshot_contract(destination_root)
    patch_skill_workbench_policy(destination_root)
    patch_team_planning_modules(destination_root)
    write_distribution_stack_validator(destination_root)


def remove_distribution_only_exclusions(destination_root: Path) -> None:
    for relative in [
        "skills/scripts/generate_environment_overview.py",
        "skills/scripts/generate_environment_overview_visuals.ps1",
        "skills/scripts/sync_research_autopilot_skills.ps1",
    ]:
        path = destination_root / relative
        if path.exists():
            path.unlink()
    tests_root = destination_root / "skills" / "tests"
    if tests_root.exists():
        for path in tests_root.glob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            if any(token in text for token in EXCLUDED_NAME_PARTS):
                path.unlink()


def patch_envctl_entrypoint(destination_root: Path) -> None:
    envctl_main = destination_root / "skills" / "scripts" / "envctl" / "__main__.py"
    if not envctl_main.exists():
        return
    text = envctl_main.read_text(encoding="utf-8")
    text = text.replace(", scholar_panel, validate", ", validate")
    text = text.replace("    scholar_panel.add_parser(subparsers)\n", "")
    envctl_main.write_text(text, encoding="utf-8")


def patch_cybernetics_contract_list(destination_root: Path) -> None:
    cybernetics = destination_root / "skills" / "scripts" / "envctl" / "cybernetics.py"
    if not cybernetics.exists():
        return
    text = cybernetics.read_text(encoding="utf-8")
    text = text.replace(
        """    "scholar_advisory_panel_policy": (
        CATALOG_ROOT / "scholar_advisory_panel_policy.json",
        SCHEMAS_ROOT / "scholar_advisory_panel_policy.v1.schema.json",
    ),
""",
        "",
    )
    cybernetics.write_text(text, encoding="utf-8")


def patch_helm_snapshot_contract(destination_root: Path) -> None:
    helm_snapshot = destination_root / "skills" / "scripts" / "envctl" / "helm_snapshot.py"
    if not helm_snapshot.exists():
        return
    text = helm_snapshot.read_text(encoding="utf-8")
    text = text.replace('    "scholar_advisory_panel_policy.json",\n', "")
    helm_snapshot.write_text(text, encoding="utf-8")


def patch_skill_workbench_policy(destination_root: Path) -> None:
    policy_path = destination_root / "skills" / "catalog" / "skill_workbench_policy.json"
    if policy_path.exists():
        payload = json.loads(policy_path.read_text(encoding="utf-8"))
        boundary = payload.setdefault("local_boundaries", {})
        if isinstance(boundary, dict):
            boundary["source_of_truth"] = "<LOCAL_ENV_ROOT>"
            boundary["protected_runtime_policy"] = "skills/catalog/protected_runtime_paths.json"
        safety_rules = payload.setdefault("safety_rules", [])
        if isinstance(safety_rules, list) and not any(
            isinstance(item, dict) and item.get("id") == "no_protected_skill_mutation"
            for item in safety_rules
        ):
            safety_rules.append(
                {
                    "id": "no_protected_skill_mutation",
                    "rule": "Do not write, sync, overwrite, clean, or mutate protected runtime skill paths from the public VELA distribution.",
                    "failure_action": "Stop and report the protected runtime boundary.",
                }
            )
        policy_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    validator = destination_root / "skills" / "scripts" / "envctl" / "skill_workbench_policy.py"
    if validator.exists():
        text = validator.read_text(encoding="utf-8")
        text = text.replace(
            """        if "skills-environment-local" not in source:
            errors.append(f"skill-workbench-policy:source-of-truth-mismatch:{source}")
        protected = str(boundary.get("protected_runtime_policy", ""))
        if "scholar-nuwa" not in protected:
            errors.append("skill-workbench-policy:protected-runtime-policy-missing-scholar-nuwa")
""",
            """        if source not in {"<LOCAL_ENV_ROOT>", "skills-environment-local"} and "skills-environment-local" not in source:
            errors.append(f"skill-workbench-policy:source-of-truth-mismatch:{source}")
        protected = str(boundary.get("protected_runtime_policy", ""))
        if "protected_runtime_paths" not in protected:
            errors.append("skill-workbench-policy:protected-runtime-policy-missing")
""",
        )
        validator.write_text(text, encoding="utf-8")


def patch_team_planning_modules(destination_root: Path) -> None:
    replacements = {
        'REVIEWER_AGENT_IDS = {"reviewer", "app-qa-reviewer"}': 'REVIEWER_AGENT_IDS = {"reviewer"}',
        'reviewer_id = "app-qa-reviewer" if route_id == "desktop-app-development" else "reviewer"': 'reviewer_id = "reviewer"',
        'default_reviewer = "app-qa-reviewer" if route_id == "desktop-app-development" else "reviewer"': 'default_reviewer = "reviewer"',
    }
    for relative in [
        "skills/scripts/envctl/team_plan.py",
        "skills/scripts/envctl/team_planner.py",
    ]:
        path = destination_root / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for source, target in replacements.items():
            text = text.replace(source, target)
        lines = [
            line for line in text.splitlines()
            if not any(token in line.lower() for token in EXCLUDED_NAME_PARTS)
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_distribution_stack_validator(destination_root: Path) -> None:
    validator = destination_root / "skills" / "scripts" / "validate_research_stack.py"
    validator.write_text(
        '''from __future__ import annotations

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
]
REQUIRED_PATHS = [
    "AGENTS.md",
    "catalog/routing_table.json",
    "catalog/skill_catalog.json",
    "catalog/local_memory_system.json",
    "catalog/protected_runtime_paths.json",
    "schemas/validator_result.schema.json",
    "schemas/local_memory_system.v1.schema.json",
    "profiles/baseline.toml",
    "scripts/envctl/__main__.py",
    "plugins/research-autopilot/skills/research-autopilot/SKILL.md",
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
                findings.append(str(path.relative_to(SKILLS_ROOT)).replace("\\\\", "/") + ":" + token)
                break
    commands["excluded-token-scan"] = {"ok": not findings, "findings": findings}
    errors.extend(f"excluded-token:{item}" for item in findings)

    payload = {
        "schema_version": "validator_result.v1",
        "validator": "validate_research_stack",
        "scope": "vela_local_environment_distribution",
        "ok": not errors,
        "decision": "pass" if not errors else "fail",
        "errors": errors,
        "warnings": [],
        "details": {
            "skills_root": str(SKILLS_ROOT),
            "commands": commands,
            "distribution_policy": "near-1:1 local research environment minus desktop app, distillation, private paths, browser state, cookies, secrets, caches, and generated outputs",
        },
        "commands": commands,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
''',
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
    final_file_count = count_files(DESTINATION)
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
            "intent": "Publish a sanitized near 1:1 VELA distribution of the local research environment except explicitly excluded areas.",
            "include": [
                "research routing and workflow contracts",
                "engineering-cybernetics control kernel",
                "seven-layer environment contract",
                "memory governance",
                "literature acquisition and citation evidence workflows",
                "writing, review, figure, presentation, submission, and quantitative workflows",
                "MCP/profile/toolchain configuration templates",
                "Python requirements and toolchain manifests without vendored runtime binaries",
                "validators, envctl modules, scripts, schemas, and tests",
            ],
            "exclude": [
                "desktop app development chain",
                "distilled scholar generation and scholar advisory panel chain",
                "vendored Python/JDK/runtime binaries",
                "runtime caches and generated outputs",
                "browser login state, cookies, credentials, and personal secrets",
                "private absolute paths; exported settings use placeholders",
            ],
        },
        "layout": {
            "root": "research-stack/local-environment",
            "runtime_mode": "installable through `vela local-env install-runtime --include core,automation,toolchain --commit`; not automatically copied by `vela init`",
            "settings_policy": "settings.toml is scrubbed to portable placeholders",
        },
        "raw_copied_file_count": len(copied),
        "copied_file_count": final_file_count,
        "total_file_count": final_file_count,
    }
    (DESTINATION / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_runtime_manifest(destination_root: Path) -> None:
    runtime_dir = destination_root / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    profiles = sorted(path.stem for path in (destination_root / "skills" / "profiles").glob("*.toml"))
    manifest = {
        "schema_version": "vela.local_runtime.manifest.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary": {
            "source_authority": {
                "role": "D-drive source repository",
                "description": "The publishable source-of-truth snapshot comes from the local environment source repository. It contains contracts, schemas, scripts, profiles, tests, and public skills.",
                "public_placeholder": "<LOCAL_ENV_ROOT>",
            },
            "runtime_authority": {
                "role": "C-drive user runtime",
                "description": "The user's Codex, plugin cache, MCP config, browser state, memory service data, and application data live in the runtime layer and are install targets or health probes, not publishable source payload.",
                "public_placeholders": ["<CODEX_HOME>", "<AGENTS_HOME>", "<VELA_HOME>", "<USER_HOME>"],
            },
            "never_export": [
                "browser login state",
                "cookies",
                "tokens and secrets",
                "agentmemory data stores",
                "plugin cache payloads",
                "Zotero databases",
                "Obsidian private vault content",
                "generated outputs and runtime caches",
            ],
        },
        "components": [
            {
                "id": "core.local-environment",
                "category": "core",
                "kind": "vela_managed_payload",
                "default_action": "install",
                "installer": "vela local-env install-runtime --include core,automation,toolchain --commit",
                "description": "Public research skills, contracts, schemas, profiles, envctl modules, validators, tests, and toolchain manifests.",
            },
            {
                "id": "mcp.profile-templates",
                "category": "mcp",
                "kind": "config_template",
                "default_action": "plan",
                "profiles": profiles,
                "installer": "envctl apply-profile <profile> --dry-run|--commit",
                "description": "Profiles describe which existing MCP server config sections should be enabled for each research route.",
            },
            {
                "id": "mcp.servers",
                "category": "mcp",
                "kind": "external_runtime",
                "default_action": "doctor",
                "install_policy": "not_vendored",
                "description": "MCP server binaries and connector registrations are user runtime dependencies. VELA checks config readiness but does not copy private or cached server payloads.",
            },
            {
                "id": "plugins.codex",
                "category": "plugins",
                "kind": "external_runtime",
                "default_action": "doctor",
                "tracked_plugins": ["superpowers", "github", "browser", "research-environment-local"],
                "install_policy": "not_vendored",
                "description": "Codex plugin/cache bundles are detected in CODEX_HOME but are not redistributed by VELA.",
            },
            {
                "id": "memory.agentmemory",
                "category": "memory",
                "kind": "optional_service",
                "default_action": "doctor",
                "probe": "agentmemory status",
                "install_policy": "explicit_optional_runtime",
                "description": "agentmemory may provide runtime recall and audit. Source rules remain in Git-controlled contracts and validators.",
            },
            {
                "id": "automation.envctl",
                "category": "automation",
                "kind": "local_cli",
                "default_action": "install",
                "installer": "vela local-env install-runtime --include core,automation,toolchain --commit",
                "description": "envctl shims expose validators, profile application, route explanation, memory governance, and research workflow checks. No background service is auto-started.",
            },
            {
                "id": "external-repos.adoption-readiness",
                "category": "external-repos",
                "kind": "classified_external_input",
                "default_action": "doctor",
                "validator": "envctl validate adoption-readiness --summary",
                "description": "External repositories are classified as installed runtime, optional backend, active plugin, cross-repo contract snapshot, or pattern-only before VELA claims them as usable.",
            },
            {
                "id": "toolchain.python",
                "category": "toolchain",
                "kind": "requirements_manifest",
                "default_action": "plan",
                "artifacts": ["python/requirements/research-core.txt", "python/requirements/research-ai-extra.txt", "python/manifests/system-python-summary.json"],
                "install_policy": "requirements_only_no_vendored_runtime",
                "description": "VELA publishes requirements and manifests, not local Python/JDK runtime binaries.",
            },
        ],
    }
    (runtime_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_readme() -> None:
    (DESTINATION / "README.md").write_text(
        """# Local Research Environment Distribution

This directory is the sanitized near 1:1 VELA distribution of the current local Codex research environment.

It is installable through `vela local-env install-runtime --include core,automation,toolchain --commit`. The installer copies the public research skills into `CODEX_HOME/skills`, places contracts, schemas, profiles, validators, scripts, and toolchain metadata under `VELA_HOME/research-stack/local-environment`, creates an `envctl` shim under `VELA_HOME/bin`, and writes receipts for `doctor-runtime`.

The project initializer remains separate: `vela init` creates a VELA research project, while `vela local-env install-runtime` installs the broader Codex research environment and runtime shims.

## Included

- engineering-cybernetics control kernel and source-rule contracts
- seven-layer environment governance: execution, tool, context, lifecycle, observability, verification, governance
- local memory system contracts and validators
- research routing, project initializer, team planning, and clarification contracts
- literature acquisition, CNKI/Google Scholar/Zotero evidence paths, citation evidence rules
- structured reading, manuscript writing, peer review, revision, figure, presentation, submission, and empirical quantitative workflows
- MCP/profile configuration templates and toolchain inventory
- Python requirements and environment manifests without Python/JDK runtime binaries
- envctl modules, validators, scripts, schemas, tests, and product overview assets

## Excluded

- desktop app development skills and profiles
- distilled scholar generation, scholar panel, and personal scholar-role material
- vendored Python/JDK runtime binaries
- runtime caches, generated outputs, browser state, cookies, credentials, and personal secrets
- machine-specific absolute paths; `skills/catalog/settings.toml` is converted to placeholders

## How VELA Should Use It

1. Read `manifest.json` first.
2. Use `vela local-env install-runtime --include core,automation,toolchain --commit` for user installation.
3. Treat `skills/catalog` and `skills/schemas` as the contract layer.
4. Treat `skills/plugins/research-autopilot/skills` as the public skill source layer.
5. Treat `skills/profiles` as MCP/profile intent; apply profiles only through explicit `envctl apply-profile --commit`.
6. Treat `runtime/manifest.json` as the C-drive runtime bootstrap contract: C-drive runtime data is probed or installed into, never exported.
7. Promote future local changes into VELA only through schema, tests, and privacy review.

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
    for subtree in PYTHON_SUBTREES:
        copied.extend(copy_filtered(source / "python" / subtree, DESTINATION / "python" / subtree))

    scrub_local_settings(DESTINATION)
    prune_snapshot_jsons(DESTINATION)
    scrub_text_files(DESTINATION, build_private_path_replacements(source))
    patch_snapshot_runtime_boundaries(DESTINATION)
    toolchain_dir = DESTINATION / "toolchain"
    toolchain_dir.mkdir(parents=True, exist_ok=True)
    (toolchain_dir / "toolchain_inventory.json").write_text(
        json.dumps(build_toolchain_inventory(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_runtime_manifest(DESTINATION)
    write_readme()
    write_manifest(source, copied)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync the local research environment snapshot into VELA.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Path to skills-environment-local")
    args = parser.parse_args()
    sync(args.source.resolve())


if __name__ == "__main__":
    main()
