from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback.
    tomllib = None  # type: ignore[assignment]


SCRIPT_ROOT = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPT_ROOT.parent
REPO_ROOT = SKILLS_ROOT.parent
CATALOG_ROOT = SKILLS_ROOT / "catalog"
SCHEMAS_ROOT = SKILLS_ROOT / "schemas"
PROFILES_ROOT = SKILLS_ROOT / "profiles"
PLUGINS_ROOT = SKILLS_ROOT / "plugins"
OUTPUTS_ROOT = SKILLS_ROOT / "outputs"
SETTINGS_PATH = CATALOG_ROOT / "settings.toml"

CODEX_HOME = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
CONFIG_PATH = CODEX_HOME / "config.toml"
INSTALLED_SKILLS_DIR = CODEX_HOME / "skills"
PROJECT_PLUGIN_DIR = PLUGINS_ROOT / "research-autopilot"
PROJECT_PLUGIN_MANIFEST = PROJECT_PLUGIN_DIR / ".codex-plugin" / "plugin.json"
PLUGIN_CACHE_ROOT = CODEX_HOME / "plugins" / "cache"
LEGACY_AGENTS_HOME = Path.home() / ".agents"
LEGACY_MARKETPLACE_PATH = LEGACY_AGENTS_HOME / "plugins" / "marketplace.json"

VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
PYTHON_RUNTIME = REPO_ROOT / "python" / "runtime" / "python313" / "python.exe"


def resolve_executable(*names: str, preferred_paths: list[str] | None = None) -> Path | None:
    for candidate in preferred_paths or []:
        path = Path(candidate)
        if path.exists():
            return path
    for name in names:
        discovered = shutil.which(name)
        if discovered:
            return Path(discovered)
    return None


GIT_EXE = resolve_executable(
    "git",
    preferred_paths=[r"C:\Program Files\Git\cmd\git.exe"],
)
GH_EXE = resolve_executable(
    "gh",
    preferred_paths=[r"C:\Program Files\GitHub CLI\gh.exe"],
)
AGENT_BROWSER_CMD = resolve_executable(
    "agent-browser.cmd",
    "agent-browser",
    preferred_paths=[rf"{Path.home()}\AppData\Roaming\npm\agent-browser.cmd"],
)


def _load_settings() -> dict[str, Any]:
    if tomllib is None or not SETTINGS_PATH.exists():
        return {}
    try:
        return tomllib.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _configured_path(value: str) -> Path:
    path = Path(os.path.expandvars(value)).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def resolve_external_repo_root(
    *,
    env_var: str,
    settings_key: str,
    sibling_name: str,
    fallback_paths: list[str] | None = None,
) -> Path:
    """Resolve a peer repository without assuming it is always a sibling."""

    env_value = os.environ.get(env_var)
    if env_value:
        return _configured_path(env_value)

    repos = _load_settings().get("repos", {})
    if isinstance(repos, dict):
        settings_value = repos.get(settings_key)
        if isinstance(settings_value, str) and settings_value.strip():
            return _configured_path(settings_value)

    sibling = (REPO_ROOT.parent / sibling_name).resolve()
    if sibling.exists():
        return sibling

    for fallback in fallback_paths or []:
        fallback_path = _configured_path(fallback)
        if fallback_path.exists():
            return fallback_path
    return sibling


VELA_REPO_ROOT = resolve_external_repo_root(
    env_var="VELA_REPO_ROOT",
    settings_key="vela_repo_root",
    sibling_name="VELA-workflow",
    fallback_paths=[r"<VELA_REPO_ROOT>"],
)
HELM_REPO_ROOT = resolve_external_repo_root(
    env_var="HELM_REPO_ROOT",
    settings_key="helm_repo_root",
    sibling_name="HELM",
    fallback_paths=[],
)


def repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))
