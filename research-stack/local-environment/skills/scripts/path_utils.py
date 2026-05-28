from __future__ import annotations

import os
import shutil
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPT_ROOT.parent
REPO_ROOT = SKILLS_ROOT.parent
CATALOG_ROOT = SKILLS_ROOT / "catalog"
SCHEMAS_ROOT = SKILLS_ROOT / "schemas"
PROFILES_ROOT = SKILLS_ROOT / "profiles"
PLUGINS_ROOT = SKILLS_ROOT / "plugins"
OUTPUTS_ROOT = SKILLS_ROOT / "outputs"

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


def repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))
