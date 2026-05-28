from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

try:
    from ..path_utils import INSTALLED_SKILLS_DIR, PLUGIN_CACHE_ROOT, PROJECT_PLUGIN_DIR
    from .protected_paths import protected_runtime_skill_names
except ImportError:  # pragma: no cover
    from path_utils import INSTALLED_SKILLS_DIR, PLUGIN_CACHE_ROOT, PROJECT_PLUGIN_DIR
    from envctl.protected_paths import protected_runtime_skill_names


PLUGIN_CACHE_SKILLS_DIR = (
    PLUGIN_CACHE_ROOT
    / "research-environment-local"
    / "research-autopilot"
    / "0.1.0"
    / "skills"
)
PLUGIN_CACHE_BUNDLE_ROOT = PLUGIN_CACHE_SKILLS_DIR.parent
PLUGIN_BUNDLE_RUNTIME_DIRS = (".codex-plugin", "assets", "scripts")

STALE_LOCAL_ROOT_PATTERNS = [
    re.compile(r"<LEGACY_RUNTIME_ROOT>", re.IGNORECASE),
    re.compile(r"<LEGACY_RUNTIME_ROOT>", re.IGNORECASE),
]

TEXT_FILE_SUFFIXES = {
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def _source_skill_dirs(source_root: Path) -> list[Path]:
    if not source_root.exists():
        return []
    return sorted(
        path
        for path in source_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    )


def _iter_text_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix.lower() in TEXT_FILE_SUFFIXES
    )


def _iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix.lower() not in {".pyc", ".pyo"}
    )


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_digest(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): _file_digest(path)
        for path in _iter_files(root)
    }


def _stale_path_hits(root: Path) -> list[str]:
    hits: list[str] = []
    for path in _iter_text_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for index, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in STALE_LOCAL_ROOT_PATTERNS):
                hits.append(f"{path}:{index}")
    return hits


def inspect_installed_skill_stale_paths(
    *,
    installed_skills_dir: Path = INSTALLED_SKILLS_DIR,
    protected_catalog_path: Path | None = None,
) -> dict[str, Any]:
    stale_path_hits: dict[str, list[str]] = {}
    protected_kwargs: dict[str, Path] = {"installed_skills_dir": installed_skills_dir}
    if protected_catalog_path is not None:
        protected_kwargs["catalog_path"] = protected_catalog_path
    protected_skills = set(protected_runtime_skill_names(**protected_kwargs))
    protected_skills_skipped: list[str] = []
    if installed_skills_dir.exists():
        for skill_dir in sorted(path for path in installed_skills_dir.iterdir() if path.is_dir()):
            if skill_dir.name in protected_skills:
                protected_skills_skipped.append(skill_dir.name)
                continue
            hits = _stale_path_hits(skill_dir)
            if hits:
                stale_path_hits[skill_dir.name] = hits
    errors = []
    if stale_path_hits:
        errors.append(f"installed-skill-old-path-hits:{sum(len(items) for items in stale_path_hits.values())}")
    return {
        "ok": not errors,
        "errors": errors,
        "installed_skills_dir": str(installed_skills_dir),
        "old_path_hits": stale_path_hits,
        "protected_skills_skipped": sorted(protected_skills_skipped),
    }


def _changed_files(source_dir: Path, runtime_dir: Path) -> list[str]:
    source_digest = _tree_digest(source_dir)
    runtime_digest = _tree_digest(runtime_dir)
    return sorted(
        path
        for path in set(source_digest) | set(runtime_digest)
        if source_digest.get(path) != runtime_digest.get(path)
    )


def inspect_research_autopilot_runtime(
    *,
    source_plugin_root: Path = PROJECT_PLUGIN_DIR,
    source_skill_root: Path = PROJECT_PLUGIN_DIR / "skills",
    installed_skills_dir: Path = INSTALLED_SKILLS_DIR,
    plugin_cache_skills_dir: Path = PLUGIN_CACHE_SKILLS_DIR,
    plugin_cache_root: Path = PLUGIN_CACHE_BUNDLE_ROOT,
) -> dict[str, Any]:
    source_dirs = _source_skill_dirs(source_skill_root)
    source_skills = [path.name for path in source_dirs]

    installed_duplicates: list[str] = []
    cache_missing: list[str] = []
    installed_changed: dict[str, list[str]] = {}
    cache_changed: dict[str, list[str]] = {}
    plugin_bundle_missing: list[str] = []
    plugin_bundle_changed: dict[str, list[str]] = {}

    for source_dir in source_dirs:
        skill = source_dir.name
        installed_dir = installed_skills_dir / skill
        cache_dir = plugin_cache_skills_dir / skill
        if (installed_dir / "SKILL.md").exists():
            installed_duplicates.append(skill)
            changed = _changed_files(source_dir, installed_dir)
            if changed:
                installed_changed[skill] = changed
        if not (cache_dir / "SKILL.md").exists():
            cache_missing.append(skill)
        else:
            changed = _changed_files(source_dir, cache_dir)
            if changed:
                cache_changed[skill] = changed

    for relative_path in PLUGIN_BUNDLE_RUNTIME_DIRS:
        source_dir = source_plugin_root / relative_path
        if not source_dir.exists():
            continue
        cache_dir = plugin_cache_root / relative_path
        if not cache_dir.exists():
            plugin_bundle_missing.append(relative_path)
            continue
        changed = _changed_files(source_dir, cache_dir)
        if changed:
            plugin_bundle_changed[relative_path] = changed

    source_old_path_hits = _stale_path_hits(source_skill_root)
    installed_old_path_hits: dict[str, list[str]] = {}
    cache_old_path_hits: dict[str, list[str]] = {}
    for skill in source_skills:
        installed_hits = _stale_path_hits(installed_skills_dir / skill)
        if installed_hits:
            installed_old_path_hits[skill] = installed_hits
        cache_hits = _stale_path_hits(plugin_cache_skills_dir / skill)
        if cache_hits:
            cache_old_path_hits[skill] = cache_hits

    errors: list[str] = []
    if not source_skill_root.exists():
        errors.append(f"research-autopilot-source-skill-root-missing:{source_skill_root}")
    if cache_missing:
        errors.append(f"research-autopilot-runtime-cache-missing:{cache_missing}")
    if plugin_bundle_missing:
        errors.append(f"research-autopilot-plugin-cache-bundle-missing:{plugin_bundle_missing}")
    if source_old_path_hits:
        errors.append(f"research-autopilot-source-old-path-hits:{len(source_old_path_hits)}")
    if installed_old_path_hits:
        errors.append(f"research-autopilot-installed-duplicate-old-path-hits:{sum(len(items) for items in installed_old_path_hits.values())}")
    if cache_old_path_hits:
        errors.append(f"research-autopilot-cache-old-path-hits:{sum(len(items) for items in cache_old_path_hits.values())}")
    if installed_changed:
        errors.append(f"research-autopilot-installed-duplicates-differ-from-source:{sorted(installed_changed)}")
    if cache_changed:
        errors.append(f"research-autopilot-cache-differs-from-source:{sorted(cache_changed)}")
    if plugin_bundle_changed:
        errors.append(f"research-autopilot-plugin-cache-bundle-differs-from-source:{sorted(plugin_bundle_changed)}")

    return {
        "ok": not errors,
        "errors": errors,
        "source_plugin_root": str(source_plugin_root),
        "source_skill_root": str(source_skill_root),
        "installed_skills_dir": str(installed_skills_dir),
        "plugin_cache_skills_dir": str(plugin_cache_skills_dir),
        "plugin_cache_root": str(plugin_cache_root),
        "source_skills": source_skills,
        "installed_missing": [],
        "installed_duplicates": installed_duplicates,
        "cache_missing": cache_missing,
        "plugin_bundle_missing": plugin_bundle_missing,
        "source_old_path_hits": source_old_path_hits,
        "dual_exposure_policy": "plugin-cache-and-standalone-mirrors",
        "installed_mirrors": installed_duplicates,
        "installed_old_path_hits": installed_old_path_hits,
        "cache_old_path_hits": cache_old_path_hits,
        "installed_changed": installed_changed,
        "cache_changed": cache_changed,
        "plugin_bundle_changed": plugin_bundle_changed,
    }
