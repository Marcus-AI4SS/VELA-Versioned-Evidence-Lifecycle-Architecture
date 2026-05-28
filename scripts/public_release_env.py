from __future__ import annotations



import os

import sys

from pathlib import Path



def _detect_repo_root() -> Path:

    for override_name in ("VELA_ROOT",):

        override = os.environ.get(override_name)

        if not override:

            continue

        candidate = Path(override).expanduser().resolve()

        if (candidate / "docs").exists() and (candidate / "package").exists() and (candidate / "schemas").exists():

            return candidate



    if getattr(sys, "frozen", False):

        mei = getattr(sys, "_MEIPASS", "")

        if mei:

            candidate = Path(mei).resolve()

            if (candidate / "docs").exists() and (candidate / "package").exists() and (candidate / "schemas").exists():

                return candidate

        exe_root = Path(sys.executable).resolve().parent

        for candidate in [exe_root, *exe_root.parents]:

            if (candidate / "docs").exists() and (candidate / "package").exists() and (candidate / "schemas").exists():

                return candidate



    candidate = Path(__file__).resolve().parents[1]

    if (candidate / "docs").exists() and (candidate / "package").exists() and (candidate / "schemas").exists():

        return candidate

    return candidate





REPO_ROOT = _detect_repo_root()

PACKAGE_ROOT = REPO_ROOT / "package"

SCHEMAS_DIR = REPO_ROOT / "schemas"

SKILLS_ROOT = REPO_ROOT / "skills"

DOCS_DIR = REPO_ROOT / "docs"

BRAND_ASSETS_DIR = DOCS_DIR / "assets" / "brand"

EXAMPLES_DIR = REPO_ROOT / "examples"

SCRIPTS_DIR = REPO_ROOT / "scripts"



CODEX_HOME = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()

CODEX_SKILLS_DIR = CODEX_HOME / "skills"

CODEX_CONFIG_PATH = CODEX_HOME / "config.toml"

AGENTS_HOME = Path(os.environ.get("AGENTS_HOME", str(Path.home() / ".agents"))).expanduser()

HOME_MARKETPLACE = AGENTS_HOME / "plugins" / "marketplace.json"



ARTIFACTS_DIR = REPO_ROOT / "artifacts"

DOWNLOADS_DIR = ARTIFACTS_DIR / "downloads"

REPORTS_DIR = SKILLS_ROOT / "outputs" / "reports"

APP_STATE_HOME = Path(

    os.environ.get("VELA_HOME")

    or str(Path.home() / ".vela")

).expanduser()

APP_STATE_DIR = APP_STATE_HOME / "state"

APP_CACHE_DIR = APP_STATE_HOME / "cache"

APP_LOGS_DIR = APP_STATE_HOME / "logs"

APP_PROJECTS_REGISTRY = APP_STATE_DIR / "projects.json"

APP_SETTINGS_PATH = APP_STATE_DIR / "settings.json"





def repo_relative(path: Path) -> str:

    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()





def ensure_app_state_dirs() -> None:

    for path in (APP_STATE_HOME, APP_STATE_DIR, APP_CACHE_DIR, APP_LOGS_DIR):

        path.mkdir(parents=True, exist_ok=True)
