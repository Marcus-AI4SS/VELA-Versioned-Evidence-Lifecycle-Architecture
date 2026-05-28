from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import public_release_env as pre
else:
    from scripts import public_release_env as pre


SNAPSHOT_ROOT = pre.REPO_ROOT / "research-stack" / "local-environment"
SNAPSHOT_SKILLS_ROOT = SNAPSHOT_ROOT / "skills"
SNAPSHOT_PUBLIC_SKILLS = SNAPSHOT_SKILLS_ROOT / "plugins" / "research-autopilot" / "skills"
MANAGED_MARKER = ".vela-managed.json"
INSTALL_RECEIPT_NAME = "local-environment-install.json"
INSTALL_SCHEMA_VERSION = "vela.local_environment.install.receipt.v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _copytree_clean(src: Path, dst: Path, *, managed_root: Path) -> None:
    resolved_dst = dst.resolve()
    resolved_root = managed_root.resolve()
    if not _is_relative_to(resolved_dst, resolved_root):
        raise ValueError(f"refusing to replace unmanaged path: {dst}")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _skill_names() -> list[str]:
    if not SNAPSHOT_PUBLIC_SKILLS.exists():
        return []
    return sorted(item.name for item in SNAPSHOT_PUBLIC_SKILLS.iterdir() if (item / "SKILL.md").exists())


def _is_vela_managed_skill(path: Path) -> bool:
    marker = path / MANAGED_MARKER
    if not marker.exists():
        return False
    try:
        payload = _load_json(marker)
    except json.JSONDecodeError:
        return False
    return payload.get("manager") == "VELA" and payload.get("schema_version") == "vela.managed_skill.v1"


def _write_skill_marker(path: Path, *, skill_name: str, snapshot_head: str | None) -> None:
    _write_json(
        path / MANAGED_MARKER,
        {
            "schema_version": "vela.managed_skill.v1",
            "manager": "VELA",
            "installed_at": _utc_now(),
            "skill": skill_name,
            "source": {
                "snapshot_root": "research-stack/local-environment",
                "snapshot_head": snapshot_head,
            },
        },
    )


def _write_envctl_shims(bin_dir: Path, local_stack: Path, python_executable: str) -> dict[str, str]:
    bin_dir.mkdir(parents=True, exist_ok=True)
    scripts_root = local_stack / "skills" / "scripts"

    cmd_path = bin_dir / "envctl.cmd"
    cmd_path.write_text(
        f"""@echo off
set "PYTHONPATH={scripts_root};%PYTHONPATH%"
"{python_executable}" -m envctl %*
""",
        encoding="ascii",
    )

    sh_path = bin_dir / "envctl"
    sh_path.write_text(
        f"""#!/usr/bin/env sh
PYTHONPATH="{scripts_root}:$PYTHONPATH" exec "{python_executable}" -m envctl "$@"
""",
        encoding="utf-8",
    )
    try:
        sh_path.chmod(0o755)
    except OSError:
        pass
    return {"windows": str(cmd_path), "posix": str(sh_path)}


def install_local_environment(
    *,
    codex_home: Path | None = None,
    vela_home: Path | None = None,
    python_executable: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    codex_home = (codex_home or pre.CODEX_HOME).expanduser()
    vela_home = (vela_home or pre.APP_STATE_HOME).expanduser()
    python_executable = python_executable or sys.executable
    manifest_path = SNAPSHOT_ROOT / "manifest.json"
    errors: list[str] = []
    warnings: list[str] = []

    if not manifest_path.exists():
        return {
            "schema_version": INSTALL_SCHEMA_VERSION,
            "ok": False,
            "errors": [f"snapshot-manifest-missing:{manifest_path}"],
            "warnings": [],
        }
    manifest = _load_json(manifest_path)
    skill_names = _skill_names()
    if not skill_names:
        errors.append("snapshot-skills-missing")

    codex_skills = codex_home / "skills"
    local_stack = vela_home / "research-stack" / "local-environment"
    bin_dir = vela_home / "bin"
    state_dir = vela_home / "state"

    conflicts = []
    installed = []
    backups: list[dict[str, str]] = []
    for skill_name in skill_names:
        target = codex_skills / skill_name
        if target.exists() and not _is_vela_managed_skill(target):
            conflicts.append(skill_name)
    if conflicts and not force:
        errors.append("codex-skill-conflicts:" + ",".join(conflicts))

    if dry_run or errors:
        return {
            "schema_version": INSTALL_SCHEMA_VERSION,
            "ok": not errors,
            "dry_run": dry_run,
            "snapshot": manifest,
            "codex_home": str(codex_home),
            "vela_home": str(vela_home),
            "skill_count": len(skill_names),
            "installed_skills": [],
            "conflicts": conflicts,
            "force": force,
            "errors": errors,
            "warnings": warnings,
            "next_action": (
                "Resolve conflicts or rerun in a clean CODEX_HOME."
                if errors
                else "Rerun without --dry-run to install the VELA local research environment."
            ),
        }

    codex_skills.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    _copytree_clean(SNAPSHOT_ROOT, local_stack, managed_root=vela_home)

    snapshot_head = manifest.get("source", {}).get("head") if isinstance(manifest.get("source"), dict) else None
    backup_root = vela_home / "backups" / "skills" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for skill_name in skill_names:
        source = SNAPSHOT_PUBLIC_SKILLS / skill_name
        target = codex_skills / skill_name
        if target.exists() and _is_vela_managed_skill(target):
            shutil.rmtree(target)
        elif target.exists() and force:
            backup_root.mkdir(parents=True, exist_ok=True)
            backup_target = backup_root / skill_name
            shutil.move(str(target), str(backup_target))
            backups.append({"skill": skill_name, "backup": str(backup_target)})
        shutil.copytree(source, target)
        _write_skill_marker(target, skill_name=skill_name, snapshot_head=snapshot_head)
        installed.append(skill_name)

    shims = _write_envctl_shims(bin_dir, local_stack, python_executable)
    receipt = {
        "schema_version": INSTALL_SCHEMA_VERSION,
        "ok": True,
        "installed_at": _utc_now(),
        "snapshot": {
            "schema_version": manifest.get("schema_version"),
            "source": manifest.get("source"),
            "policy": manifest.get("policy"),
        },
        "codex_home": str(codex_home),
        "codex_skills_dir": str(codex_skills),
        "vela_home": str(vela_home),
        "local_stack": str(local_stack),
        "envctl_shims": shims,
        "installed_skills": installed,
        "installed_skill_count": len(installed),
        "backups": backups,
        "force": force,
        "excluded": manifest.get("policy", {}).get("exclude", []),
        "errors": [],
        "warnings": warnings,
        "next_action": "Run `vela local-env doctor` and restart Codex so newly installed skills are discovered.",
    }
    _write_json(state_dir / INSTALL_RECEIPT_NAME, receipt)
    return receipt


def doctor_local_environment(*, codex_home: Path | None = None, vela_home: Path | None = None) -> dict[str, Any]:
    codex_home = (codex_home or pre.CODEX_HOME).expanduser()
    vela_home = (vela_home or pre.APP_STATE_HOME).expanduser()
    codex_skills = codex_home / "skills"
    local_stack = vela_home / "research-stack" / "local-environment"
    receipt_path = vela_home / "state" / INSTALL_RECEIPT_NAME
    expected_skills = _skill_names()
    missing_skills = [name for name in expected_skills if not (codex_skills / name / "SKILL.md").exists()]
    unmanaged_installed = [
        name for name in expected_skills if (codex_skills / name).exists() and not _is_vela_managed_skill(codex_skills / name)
    ]
    errors: list[str] = []
    if not (local_stack / "manifest.json").exists():
        errors.append(f"local-stack-missing:{local_stack}")
    if not receipt_path.exists():
        errors.append(f"install-receipt-missing:{receipt_path}")
    errors.extend(f"skill-missing:{name}" for name in missing_skills)
    errors.extend(f"skill-not-vela-managed:{name}" for name in unmanaged_installed)
    for shim in (vela_home / "bin" / "envctl.cmd", vela_home / "bin" / "envctl"):
        if not shim.exists():
            errors.append(f"envctl-shim-missing:{shim}")
    return {
        "schema_version": "vela.local_environment.doctor.v1",
        "ok": not errors,
        "codex_home": str(codex_home),
        "vela_home": str(vela_home),
        "expected_skill_count": len(expected_skills),
        "missing_skills": missing_skills,
        "unmanaged_installed_skills": unmanaged_installed,
        "local_stack": str(local_stack),
        "install_receipt": str(receipt_path),
        "errors": errors,
        "warnings": [],
        "next_action": "Run `vela local-env install-runtime --include core,automation,toolchain --commit` from the VELA repository." if errors else "Restart Codex if these skills were installed during the current session.",
    }
