from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

try:
    from .path_utils import OUTPUTS_ROOT, SCRIPT_ROOT, SKILLS_ROOT
except ImportError:
    from path_utils import OUTPUTS_ROOT, SCRIPT_ROOT, SKILLS_ROOT

ROOT = SKILLS_ROOT
CAPTURE_SCRIPT = SCRIPT_ROOT / "run-social-platform-agent-browser-template.ps1"
CLEANUP_SCRIPT = SCRIPT_ROOT / "cleanup-stale-agent-browser-sessions.ps1"
OUTPUT_ROOT = OUTPUTS_ROOT / "social-platform-reader" / "agent-browser"

SUPPORTED_PLATFORMS: dict[str, dict[str, str]] = {
    "douyin": {
        "label": "抖音",
        "default_artifact_type": "video",
        "mode": "browser-visible",
    },
    "bilibili": {
        "label": "B站",
        "default_artifact_type": "video",
        "mode": "browser-visible",
    },
    "wechat": {
        "label": "微信公众号文章",
        "default_artifact_type": "article",
        "mode": "browser-visible",
    },
}


mcp = FastMCP(
    "social-platform-mcp",
    instructions=(
        "Generic social-platform capture facade for Douyin, Bilibili, and WeChat public articles. "
        "This server only returns browser-visible evidence artifacts and does not invent hidden content."
    ),
)


def _path_entry(path: Path) -> str:
    return str(path.expanduser())


def _existing_path(path: str | Path | None) -> Path | None:
    if not path:
        return None
    candidate = Path(path).expanduser()
    return candidate if candidate.exists() else None


def _resolve_powershell_command(env: dict[str, str] | None = None) -> str:
    active_env = env or os.environ
    candidates = [
        _existing_path(active_env.get("PWSH_EXE")),
        _existing_path(active_env.get("PWSH")),
        _existing_path(shutil.which("pwsh", path=active_env.get("PATH"))),
        _existing_path(shutil.which("powershell", path=active_env.get("PATH"))),
        _existing_path(Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps" / "pwsh.exe"),
        _existing_path(r"C:\Program Files\PowerShell\7\pwsh.exe"),
        _existing_path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"),
    ]
    for candidate in candidates:
        if candidate is not None:
            return str(candidate)
    return "pwsh"


def _resolve_agent_browser_exe(env: dict[str, str] | None = None) -> Path | None:
    active_env = env or os.environ
    candidates: list[Path | None] = [
        _existing_path(active_env.get("AGENT_BROWSER_EXE")),
    ]

    command = active_env.get("AGENT_BROWSER_CMD") or shutil.which("agent-browser", path=active_env.get("PATH"))
    if command:
        command_path = Path(command)
        candidates.append(command_path.parent / "node_modules" / "agent-browser" / "bin" / "agent-browser-win32-x64.exe")

    npm_root = Path(active_env.get("APPDATA") or (Path.home() / "AppData" / "Roaming")) / "npm"
    candidates.extend(
        [
            npm_root / "node_modules" / "agent-browser" / "bin" / "agent-browser-win32-x64.exe",
            Path.home()
            / "AppData"
            / "Roaming"
            / "npm"
            / "node_modules"
            / "agent-browser"
            / "bin"
            / "agent-browser-win32-x64.exe",
        ]
    )

    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate
    return None


def _build_child_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    extra_paths = [
        Path.home() / "AppData" / "Roaming" / "npm",
        Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps",
        Path(r"C:\Windows\System32\WindowsPowerShell\v1.0"),
        Path(r"C:\Program Files\PowerShell\7"),
        Path(r"C:\Program Files\nodejs"),
    ]
    current_path = env.get("PATH", "")
    path_parts = [_path_entry(path) for path in extra_paths if path.exists()]
    path_parts.extend(part for part in current_path.split(os.pathsep) if part)
    env["PATH"] = os.pathsep.join(dict.fromkeys(path_parts))
    agent_browser_exe = _resolve_agent_browser_exe(env)
    if agent_browser_exe is not None:
        env["AGENT_BROWSER_EXE"] = str(agent_browser_exe)
    return env


def _probe_command(command: list[str], env: dict[str, str], timeout: int = 15) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": "timeout",
        }
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
    }


def build_runtime_probe(base_env: dict[str, str] | None = None) -> dict[str, Any]:
    child_env = _build_child_env(base_env)
    powershell_command = _resolve_powershell_command(child_env)
    agent_browser_exe = _resolve_agent_browser_exe(child_env)
    powershell_exists = Path(powershell_command).exists()
    agent_browser_exists = bool(agent_browser_exe and agent_browser_exe.exists())
    powershell_launch = _probe_command(
        [powershell_command, "-NoLogo", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
        child_env,
    )
    agent_browser_version = (
        _probe_command([str(agent_browser_exe), "--version"], child_env) if agent_browser_exe else {"ok": False}
    )
    return {
        "ok": all(
            [
                powershell_exists,
                powershell_launch["ok"],
                agent_browser_exists,
                agent_browser_version["ok"],
                CAPTURE_SCRIPT.exists(),
                CLEANUP_SCRIPT.exists(),
            ]
        ),
        "powershell_command": powershell_command,
        "powershell_exists": powershell_exists,
        "powershell_launch": powershell_launch,
        "agent_browser_exe": str(agent_browser_exe) if agent_browser_exe else None,
        "agent_browser_exe_exists": agent_browser_exists,
        "agent_browser_version": agent_browser_version,
        "capture_script": str(CAPTURE_SCRIPT),
        "capture_script_exists": CAPTURE_SCRIPT.exists(),
        "cleanup_script": str(CLEANUP_SCRIPT),
        "cleanup_script_exists": CLEANUP_SCRIPT.exists(),
    }


def _run_powershell_json(script_path: Path, args: list[str], timeout: int = 600) -> dict[str, Any]:
    child_env = _build_child_env()
    command = [
        _resolve_powershell_command(child_env),
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        *args,
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=child_env,
        timeout=timeout,
        check=False,
    )

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    if result.returncode != 0:
        raise RuntimeError(
            f"PowerShell script failed: {script_path.name}\nstdout:\n{stdout}\nstderr:\n{stderr}"
        )

    if not stdout:
        return {"stdout": "", "stderr": stderr}

    payload = _extract_json_payload(stdout)
    if payload is None:
        raise RuntimeError(
            f"Expected a JSON payload from {script_path.name}, but none could be extracted.\nstdout:\n{stdout}\nstderr:\n{stderr}"
        )

    if stderr:
        payload["_stderr"] = stderr
    return payload


def _extract_json_payload(stdout: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    matches: list[dict[str, Any]] = []

    for index, char in enumerate(stdout):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stdout[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            matches.append(value)

    if not matches:
        return None

    for candidate in reversed(matches):
        if "platform" in candidate or "removed_files" in candidate or "platforms" in candidate:
            return candidate

    return matches[-1]


def _read_metadata(output_dir: Path) -> dict[str, Any]:
    metadata_path = output_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json not found under {output_dir}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def list_supported_social_platforms_impl() -> dict[str, Any]:
    return {
        "platforms": SUPPORTED_PLATFORMS,
        "output_root": str(OUTPUT_ROOT),
        "evidence_boundary": "Only browser-visible content and generated evidence artifacts are returned.",
    }


def capture_visible_social_page_impl(
    platform: str,
    url: str,
    artifact_type: str | None = None,
    session_name: str = "research-social",
    auto_connect: bool = False,
    headed: bool = False,
    save_state: bool = False,
    keep_session_alive: bool = False,
) -> dict[str, Any]:
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")

    if not CAPTURE_SCRIPT.exists():
        raise FileNotFoundError(f"Capture script not found: {CAPTURE_SCRIPT}")

    resolved_artifact_type = artifact_type or SUPPORTED_PLATFORMS[platform]["default_artifact_type"]
    args = [
        "-Platform",
        platform,
        "-ArtifactType",
        resolved_artifact_type,
        "-Url",
        url,
        "-SessionName",
        session_name,
    ]

    if auto_connect:
        args.append("-AutoConnect")
    if headed:
        args.append("-Headed")
    if save_state:
        args.append("-SaveState")
    if keep_session_alive:
        args.append("-KeepSessionAlive")

    payload = _run_powershell_json(CAPTURE_SCRIPT, args)
    output_dir = Path(payload["output_dir"])
    metadata = _read_metadata(output_dir)

    return {
        "platform": platform,
        "artifact_type": resolved_artifact_type,
        "requested_url": url,
        "output_dir": str(output_dir),
        "metadata": metadata,
        "artifacts": {
            "metadata_json": str(output_dir / "metadata.json"),
            "snapshot_json": str(output_dir / "snapshot-interactive.json"),
            "screenshot": str(output_dir / "screenshot.png"),
            "state_file": str(output_dir / "state.json") if save_state else None,
        },
        "warnings": payload.get("_stderr", ""),
        "evidence_boundary": "Only browser-visible content was captured.",
    }


def get_latest_social_capture_impl(platform: str) -> dict[str, Any]:
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f"Unsupported platform: {platform}")

    platform_dir = OUTPUT_ROOT / platform
    if not platform_dir.exists():
        raise FileNotFoundError(f"No capture directory exists yet for platform: {platform}")

    candidates = [path for path in platform_dir.iterdir() if path.is_dir()]
    if not candidates:
        raise FileNotFoundError(f"No capture runs were found yet for platform: {platform}")

    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    metadata = _read_metadata(latest)
    return {
        "platform": platform,
        "latest_output_dir": str(latest),
        "metadata": metadata,
    }


def read_social_capture_metadata_impl(output_dir: str) -> dict[str, Any]:
    path = Path(output_dir)
    metadata = _read_metadata(path)
    return {
        "output_dir": str(path),
        "metadata": metadata,
    }


def cleanup_stale_social_sessions_impl() -> dict[str, Any]:
    if not CLEANUP_SCRIPT.exists():
        raise FileNotFoundError(f"Cleanup script not found: {CLEANUP_SCRIPT}")
    return _run_powershell_json(CLEANUP_SCRIPT, [])


@mcp.tool(
    name="list_supported_social_platforms",
    description="List supported social platforms, default artifact types, and the browser-visible evidence boundary.",
)
def list_supported_social_platforms() -> dict[str, Any]:
    return list_supported_social_platforms_impl()


@mcp.tool(
    name="capture_visible_social_page",
    description=(
        "Capture a social-platform page through the local browser-evidence workflow. "
        "Returns structured metadata plus artifact paths for metadata.json, snapshot-interactive.json, and screenshot.png."
    ),
)
def capture_visible_social_page(
    platform: str,
    url: str,
    artifact_type: str | None = None,
    session_name: str = "research-social",
    auto_connect: bool = False,
    headed: bool = False,
    save_state: bool = False,
    keep_session_alive: bool = False,
) -> dict[str, Any]:
    return capture_visible_social_page_impl(
        platform=platform,
        url=url,
        artifact_type=artifact_type,
        session_name=session_name,
        auto_connect=auto_connect,
        headed=headed,
        save_state=save_state,
        keep_session_alive=keep_session_alive,
    )


@mcp.tool(
    name="get_latest_social_capture",
    description="Return the metadata.json payload for the latest saved capture of a supported platform.",
)
def get_latest_social_capture(platform: str) -> dict[str, Any]:
    return get_latest_social_capture_impl(platform)


@mcp.tool(
    name="read_social_capture_metadata",
    description="Read metadata.json from an existing social-platform capture output directory.",
)
def read_social_capture_metadata(output_dir: str) -> dict[str, Any]:
    return read_social_capture_metadata_impl(output_dir)


@mcp.tool(
    name="cleanup_stale_social_sessions",
    description="Remove dead agent-browser session sidecar files while preserving saved auth-state files.",
)
def cleanup_stale_social_sessions() -> dict[str, Any]:
    return cleanup_stale_social_sessions_impl()


if __name__ == "__main__":
    mcp.run(transport="stdio")
