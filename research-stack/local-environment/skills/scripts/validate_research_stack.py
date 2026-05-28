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
                findings.append(str(path.relative_to(SKILLS_ROOT)).replace("\\", "/") + ":" + token)
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
