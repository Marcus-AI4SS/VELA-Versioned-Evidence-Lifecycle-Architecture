from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BOOTSTRAP_SCHEMA_VERSION = "vela.local_runtime.bootstrap_tools.v1"
ALL_CATEGORIES = ("system", "optional", "runtime")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_include(include: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if include is None:
        return list(ALL_CATEGORIES)
    values: list[str] = []
    if isinstance(include, str):
        parts = include.split(",")
    else:
        parts = []
        for item in include:
            parts.extend(str(item).split(","))
    for raw in parts:
        item = raw.strip().lower()
        if not item:
            continue
        if item == "all":
            return list(ALL_CATEGORIES)
        if item not in ALL_CATEGORIES:
            raise ValueError(f"unsupported-bootstrap-category:{item}")
        if item not in values:
            values.append(item)
    return values or list(ALL_CATEGORIES)


def _run(args: list[str], *, timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": f"timeout:{timeout}s",
        }
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _probe_command(command: str, args: list[str] | None = None, *, timeout: int = 12) -> dict[str, Any]:
    found = shutil.which(command)
    if not found:
        return {"ok": False, "command": command, "path": None, "stdout_head": "", "stderr": "command-not-found"}
    command_args = args or ["--version"]
    executable = Path(found)
    if os.name == "nt" and executable.suffix.lower() in {".cmd", ".bat"}:
        run_args = ["cmd", "/c", str(executable), *command_args]
    else:
        run_args = [str(executable), *command_args]
    result = _run(run_args, timeout=timeout)
    return {
        "ok": bool(result.get("ok")),
        "command": command,
        "path": found,
        "returncode": result.get("returncode"),
        "stdout_head": "\n".join(str(result.get("stdout", "")).splitlines()[:6]),
        "stderr": result.get("stderr", ""),
    }


def _python_probe() -> dict[str, Any]:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info >= (3, 13)
    return {
        "ok": ok,
        "command": "python",
        "path": sys.executable,
        "returncode": 0,
        "stdout_head": f"Python {version}",
        "stderr": "" if ok else "python-version-below-3.13",
        "path_python": _probe_command("python", ["--version"]),
    }


def _npm_available() -> bool:
    return bool(_probe_command("npm", ["--version"]).get("ok"))


def _tool_specs() -> list[dict[str, Any]]:
    return [
        {
            "id": "git",
            "category": "system",
            "required": True,
            "command": "git",
            "args": ["--version"],
            "install_strategy": "winget",
            "winget_id": "Git.Git",
            "remediation": "Install Git, then reopen the terminal so PATH is refreshed.",
        },
        {
            "id": "python",
            "category": "system",
            "required": True,
            "command": "python",
            "args": ["--version"],
            "custom_probe": "python",
            "install_strategy": "winget",
            "winget_id": "Python.Python.3.13",
            "remediation": "Install Python 3.13+, then run install.ps1 again with the selected interpreter.",
        },
        {
            "id": "powershell",
            "category": "system",
            "required": True,
            "command": "pwsh",
            "args": ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
            "install_strategy": "winget",
            "winget_id": "Microsoft.PowerShell",
            "remediation": "Install PowerShell 7 (`pwsh`) for the cross-platform runtime scripts.",
        },
        {
            "id": "ripgrep",
            "category": "system",
            "required": True,
            "command": "rg",
            "args": ["--version"],
            "install_strategy": "winget",
            "winget_id": "BurntSushi.ripgrep.MSVC",
            "remediation": "Install ripgrep so validators and repository audits can run quickly.",
        },
        {
            "id": "node",
            "category": "system",
            "required": True,
            "command": "node",
            "args": ["--version"],
            "install_strategy": "winget",
            "winget_id": "OpenJS.NodeJS.LTS",
            "remediation": "Install Node.js LTS. npm is used for optional JavaScript-based runtime tools.",
        },
        {
            "id": "github-cli",
            "category": "system",
            "required": False,
            "command": "gh",
            "args": ["--version"],
            "install_strategy": "winget",
            "winget_id": "GitHub.cli",
            "remediation": "Install GitHub CLI if you want VELA to run repository and release checks.",
        },
        {
            "id": "agentmemory",
            "category": "optional",
            "required": False,
            "command": "agentmemory",
            "args": ["status"],
            "install_strategy": "npm-global" if _npm_available() else "manual",
            "npm_package": "agentmemory",
            "remediation": "Install and initialize agentmemory only if you want the optional memory-management runtime.",
        },
        {
            "id": "codegraph",
            "category": "optional",
            "required": False,
            "command": "codegraph",
            "args": ["--help"],
            "install_strategy": "manual",
            "remediation": "Install CodeGraph through its upstream distribution, then initialize each project index explicitly.",
        },
        {
            "id": "mcp-vendor-environment",
            "category": "runtime",
            "required": False,
            "command": "CODEX_HOME/config.toml",
            "args": [],
            "install_strategy": "manual",
            "doctor_only": True,
            "remediation": "Configure MCP server vendor requirements in CODEX_HOME/config.toml, then use VELA envctl profiles to check readiness.",
        },
        {
            "id": "codex-plugin-status",
            "category": "runtime",
            "required": False,
            "command": "CODEX_HOME/plugins/cache",
            "args": [],
            "install_strategy": "manual",
            "doctor_only": True,
            "remediation": "Install Codex plugins in the user's Codex runtime. VELA can detect plugin cache presence but cannot redistribute it.",
        },
    ]


def _protected_runtime_boundaries() -> list[dict[str, str]]:
    return [
        {
            "id": "codex-plugin-cache",
            "status": "not-redistributable",
            "install_policy": "doctor-only",
            "reason": "Codex plugin caches are runtime-managed state and may include private installation metadata.",
        },
        {
            "id": "browser-login-state",
            "status": "not-redistributable",
            "install_policy": "doctor-only",
            "reason": "Browser profiles, cookies, CNKI sessions, and platform logins are user credentials.",
        },
        {
            "id": "zotero-obsidian-private-libraries",
            "status": "not-redistributable",
            "install_policy": "doctor-only",
            "reason": "Zotero databases and Obsidian vaults can contain copyrighted PDFs, notes, and private metadata.",
        },
        {
            "id": "agentmemory-data-store",
            "status": "not-redistributable",
            "install_policy": "doctor-only",
            "reason": "VELA may install or probe the agentmemory tool, but never exports another user's memory database.",
        },
        {
            "id": "mcp-secrets-and-api-keys",
            "status": "not-redistributable",
            "install_policy": "doctor-only",
            "reason": "MCP servers often require local credentials, tokens, or service-specific permission grants.",
        },
    ]


def _probe_tool(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("doctor_only"):
        return {
            "ok": True,
            "command": spec["command"],
            "path": None,
            "returncode": None,
            "stdout_head": "",
            "stderr": "doctor-only-boundary",
        }
    if spec.get("custom_probe") == "python":
        return _python_probe()
    return _probe_command(str(spec["command"]), list(spec.get("args", [])))


def _install_with_winget(spec: dict[str, Any]) -> dict[str, Any]:
    winget = shutil.which("winget")
    if not winget:
        return {"ok": False, "status": "installer-missing", "stderr": "winget-not-found"}
    package_id = str(spec.get("winget_id", ""))
    if not package_id:
        return {"ok": False, "status": "package-id-missing", "stderr": "winget-id-missing"}
    return _run(
        [
            winget,
            "install",
            "--id",
            package_id,
            "-e",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ],
        timeout=900,
    )


def _install_with_npm(spec: dict[str, Any]) -> dict[str, Any]:
    npm = shutil.which("npm")
    if not npm:
        return {"ok": False, "status": "installer-missing", "stderr": "npm-not-found"}
    package = str(spec.get("npm_package") or spec["id"])
    executable = Path(npm)
    run_args = ["cmd", "/c", str(executable), "install", "-g", package] if os.name == "nt" and executable.suffix.lower() in {".cmd", ".bat"} else [str(executable), "install", "-g", package]
    return _run(run_args, timeout=900)


def _install_tool(spec: dict[str, Any]) -> dict[str, Any]:
    strategy = str(spec.get("install_strategy", "manual"))
    if strategy == "winget":
        if platform.system().lower() != "windows":
            return {"ok": False, "status": "manual-guidance", "stderr": "winget-bootstrap-is-windows-only"}
        return _install_with_winget(spec)
    if strategy == "npm-global":
        return _install_with_npm(spec)
    return {"ok": False, "status": "manual-guidance", "stderr": "manual-install-required"}


def _tool_payload(spec: dict[str, Any], *, install: bool, yes: bool) -> tuple[dict[str, Any], bool, list[str]]:
    probe = _probe_tool(spec)
    ok = bool(probe.get("ok"))
    warnings: list[str] = []
    mutated = False
    install_result: dict[str, Any] | None = None
    install_policy = "explicit-bootstrap" if spec.get("install_strategy") in {"winget", "npm-global"} else "manual"
    if spec.get("doctor_only"):
        install_policy = "doctor-only"

    if install and not ok and not spec.get("doctor_only"):
        if yes and spec.get("install_strategy") in {"winget", "npm-global"}:
            install_result = _install_tool(spec)
            mutated = spec.get("install_strategy") in {"winget", "npm-global"}
            probe = _probe_tool(spec)
            ok = bool(probe.get("ok"))
        else:
            warnings.append(f"bootstrap-tool-needs-install:{spec['id']}")

    status = "available" if ok else "missing"
    if spec.get("doctor_only"):
        status = "guidance-only"
    elif install_result and install_result.get("ok") and ok:
        status = "installed"
    elif install_result and not install_result.get("ok"):
        status = "install-attempt-failed"

    payload = {
        "id": spec["id"],
        "category": spec["category"],
        "required": bool(spec.get("required")),
        "ok": ok,
        "status": status,
        "command": spec["command"],
        "path": probe.get("path"),
        "install_policy": install_policy,
        "install_strategy": spec.get("install_strategy", "manual"),
        "remediation": spec["remediation"],
        "probe": probe,
    }
    if spec.get("winget_id"):
        payload["winget_id"] = spec["winget_id"]
    if spec.get("npm_package"):
        payload["npm_package"] = spec["npm_package"]
    if install_result is not None:
        payload["install_result"] = install_result
    return payload, mutated, warnings


def bootstrap_tools(
    *,
    include: str | list[str] | tuple[str, ...] | None = None,
    install: bool = False,
    yes: bool = False,
) -> dict[str, Any]:
    categories = _parse_include(include)
    tools: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    mutated = False

    for spec in _tool_specs():
        if spec["category"] not in categories:
            continue
        tool, tool_mutated, tool_warnings = _tool_payload(spec, install=install, yes=yes)
        tools.append(tool)
        mutated = mutated or tool_mutated
        warnings.extend(tool_warnings)
        if tool["status"] == "install-attempt-failed" and tool["required"]:
            errors.append(f"bootstrap-install-failed:{tool['id']}")
        elif not tool["ok"] and tool["required"]:
            warnings.append(f"bootstrap-required-tool-missing:{tool['id']}")

    required_ready = all(tool["ok"] for tool in tools if tool["required"])
    mode = "install-commit" if install and yes else "install-preview" if install else "plan"
    next_action = (
        "Run install.ps1 -BootstrapTools, then restart the terminal and run vela local-env doctor-runtime --include all."
        if not required_ready
        else "Run vela local-env doctor-runtime --include all after installing the VELA-owned runtime layer."
    )
    return {
        "schema_version": BOOTSTRAP_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "ok": not errors,
        "ready": required_ready,
        "mode": mode,
        "include": categories,
        "mutated": mutated,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "python": sys.executable,
        },
        "tools": tools,
        "protected_runtime_boundaries": _protected_runtime_boundaries(),
        "errors": errors,
        "warnings": warnings,
        "next_action": next_action,
    }


def plan_bootstrap_tools(include: str | list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
    return bootstrap_tools(include=include, install=False, yes=False)
