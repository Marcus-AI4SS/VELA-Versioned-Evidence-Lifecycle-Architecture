from __future__ import annotations



import difflib

import json

import re

import shutil

import tomllib

from datetime import datetime, timezone

from pathlib import Path

from typing import Any



try:

    from ..path_utils import CONFIG_PATH, PROFILES_ROOT

except ImportError:  # pragma: no cover

    from path_utils import CONFIG_PATH, PROFILES_ROOT





DEFAULT_BACKUP_ROOT = CONFIG_PATH.parent / "backups" / "envctl-apply-profile"





def _utc_stamp() -> str:

    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")





def _load_toml(path: Path) -> dict[str, Any]:

    return tomllib.loads(path.read_text(encoding="utf-8"))





def _profile_path(profile_name: str, profiles_root: Path) -> Path:

    if not re.match(r"^[A-Za-z0-9_.-]+$", profile_name):

        raise ValueError("profile-name-must-be-simple-id")

    return profiles_root / f"{profile_name}.toml"





def _load_profile(profile_name: str, profiles_root: Path) -> tuple[dict[str, Any], Path]:

    path = _profile_path(profile_name, profiles_root)

    if not path.exists():

        raise FileNotFoundError(f"profile-not-found:{path}")

    profile = _load_toml(path)

    managed = profile.get("managed_mcp", [])

    enabled = profile.get("enabled_mcp", [])

    if not isinstance(managed, list) or any(not isinstance(item, str) or not item for item in managed):

        raise ValueError("profile-managed_mcp-must-be-string-list")

    if not isinstance(enabled, list) or any(not isinstance(item, str) or not item for item in enabled):

        raise ValueError("profile-enabled_mcp-must-be-string-list")

    if len(set(managed)) != len(managed):

        raise ValueError("profile-managed_mcp-contains-duplicates")

    if len(set(enabled)) != len(enabled):

        raise ValueError("profile-enabled_mcp-contains-duplicates")

    unknown_enabled = sorted(set(enabled) - set(managed))

    if unknown_enabled:

        raise ValueError(f"profile-enabled_mcp-not-managed:{unknown_enabled}")

    return profile, path





def _mcp_enabled_map(config: dict[str, Any]) -> dict[str, bool]:

    servers = config.get("mcp_servers", {})

    if not isinstance(servers, dict):

        return {}

    result: dict[str, bool] = {}

    for name, payload in servers.items():

        if isinstance(payload, dict):

            result[name] = bool(payload.get("enabled", True))

    return result





def _replace_enabled_line(section_lines: list[str], enabled: bool) -> list[str]:

    value = "true" if enabled else "false"

    pattern = re.compile(r"^(\s*enabled\s*=\s*)(true|false)([ \t]*(?:#.*)?)(\r?\n?)$", re.IGNORECASE)

    for index, line in enumerate(section_lines):

        match = pattern.match(line)

        if match:

            ending = match.group(4) or "\n"

            section_lines[index] = f"{match.group(1)}{value}{match.group(3)}{ending}"

            return section_lines

    insert_at = len(section_lines)

    section_lines.insert(insert_at, f"enabled = {value}\n")

    return section_lines





def _set_mcp_enabled(text: str, mcp_name: str, enabled: bool) -> str:

    lines = text.splitlines(keepends=True)

    header = re.compile(rf"^\s*\[mcp_servers\.{re.escape(mcp_name)}\]\s*(?:#.*)?(?:\r?\n)?$", re.IGNORECASE)

    start: int | None = None

    for index, line in enumerate(lines):

        if header.match(line):

            start = index

            break

    if start is None:

        raise ValueError(f"config-missing-mcp-section:{mcp_name}")



    end = len(lines)

    for index in range(start + 1, len(lines)):

        if re.match(r"^\s*\[", lines[index]):

            end = index

            break



    updated_section = [lines[start], *_replace_enabled_line(lines[start + 1 : end], enabled)]

    return "".join([*lines[:start], *updated_section, *lines[end:]])





def _build_diff(before: str, after: str, config_path: Path) -> list[str]:

    return list(

        difflib.unified_diff(

            before.splitlines(),

            after.splitlines(),

            fromfile=f"{config_path}:before",

            tofile=f"{config_path}:after",

            lineterm="",

        )

    )





def _next_backup_path(backup_root: Path, profile_name: str) -> Path:

    backup_root.mkdir(parents=True, exist_ok=True)

    base = backup_root / f"config.{_utc_stamp()}.{profile_name}.toml"

    if not base.exists():

        return base

    for index in range(1, 100):

        candidate = backup_root / f"{base.stem}.{index}.toml"

        if not candidate.exists():

            return candidate

    raise RuntimeError("unable-to-allocate-backup-path")





def _find_backup(backup_root: Path, backup_id: str) -> Path:

    backup_root = backup_root.resolve()

    if backup_id == "latest":

        candidates = sorted(backup_root.glob("config.*.toml"), key=lambda item: item.name)

        if not candidates:

            raise FileNotFoundError(f"backup-not-found:{backup_root}")

        return candidates[-1]

    candidate = Path(backup_id)

    if not candidate.is_absolute():

        candidate = backup_root / backup_id

    candidate = candidate.resolve()

    if not candidate.is_relative_to(backup_root):

        raise ValueError(f"backup-outside-backup-root:{candidate}")

    if not candidate.exists():

        raise FileNotFoundError(f"backup-not-found:{candidate}")

    return candidate





def _error_result(action: str, error: Exception) -> dict[str, Any]:

    return {

        "ok": False,

        "mode": action,

        "errors": [str(error)],

        "warnings": [],

        "source_files_written": False,

        "config_written": False,

    }





def apply_profile(

    profile_name: str,

    *,

    config_path: Path = CONFIG_PATH,

    profiles_root: Path = PROFILES_ROOT,

    backup_root: Path = DEFAULT_BACKUP_ROOT,

    dry_run: bool = False,

    commit: bool = False,

) -> dict[str, Any]:

    if dry_run == commit:

        return _error_result("apply-profile", ValueError("choose-exactly-one-of-dry-run-or-commit"))

    try:

        profile, profile_path = _load_profile(profile_name, profiles_root)

        if not config_path.exists():

            raise FileNotFoundError(f"config-not-found:{config_path}")

        before = config_path.read_text(encoding="utf-8")

        config = tomllib.loads(before)

        enabled_map = _mcp_enabled_map(config)

        managed = list(profile["managed_mcp"])

        enabled = set(profile["enabled_mcp"])

        missing = sorted(set(managed) - set(enabled_map))

        if missing:

            raise ValueError(f"profile-managed-mcp-missing-from-config:{missing}")



        changes: list[dict[str, Any]] = []

        after = before

        for name in managed:

            current = enabled_map[name]

            target = name in enabled

            if current != target:

                changes.append({"mcp": name, "from": current, "to": target})

            after = _set_mcp_enabled(after, name, target)



        diff = _build_diff(before, after, config_path)

        result: dict[str, Any] = {

            "ok": True,

            "mode": "dry-run" if dry_run else "commit",

            "profile": profile_name,

            "profile_path": str(profile_path),

            "config_path": str(config_path),

            "backup_path": None,

            "changes": changes,

            "diff": diff,

            "restart_required": bool(changes),

            "source_files_written": False,

            "config_written": False,

            "errors": [],

            "warnings": [],

        }

        if dry_run:

            return result



        backup_path = _next_backup_path(backup_root, profile_name)

        shutil.copyfile(config_path, backup_path)

        config_path.write_text(after, encoding="utf-8")

        metadata_path = backup_path.with_suffix(".json")

        metadata_path.write_text(

            json.dumps(

                {

                    "schema_version": "envctl_apply_profile_backup.v1",

                    "created_at": datetime.now(timezone.utc).isoformat(),

                    "profile": profile_name,

                    "config_path": str(config_path),

                    "backup_path": str(backup_path),

                    "changes": changes,

                },

                ensure_ascii=False,

                indent=2,

            )

            + "\n",

            encoding="utf-8",

        )

        result["backup_path"] = str(backup_path)

        result["backup_metadata_path"] = str(metadata_path)

        result["config_written"] = True

        return result

    except Exception as exc:

        return _error_result("apply-profile", exc)





def rollback_profile(

    *,

    config_path: Path = CONFIG_PATH,

    backup_root: Path = DEFAULT_BACKUP_ROOT,

    backup_id: str = "latest",

) -> dict[str, Any]:

    try:

        backup_path = _find_backup(backup_root, backup_id)

        if not config_path.exists():

            raise FileNotFoundError(f"config-not-found:{config_path}")

        before = config_path.read_text(encoding="utf-8")

        after = backup_path.read_text(encoding="utf-8")

        diff = _build_diff(before, after, config_path)

        shutil.copyfile(backup_path, config_path)

        return {

            "ok": True,

            "mode": "rollback",

            "config_path": str(config_path),

            "backup_path": str(backup_path),

            "diff": diff,

            "restart_required": before != after,

            "source_files_written": False,

            "config_written": True,

            "errors": [],

            "warnings": [],

        }

    except Exception as exc:

        return _error_result("rollback", exc)
