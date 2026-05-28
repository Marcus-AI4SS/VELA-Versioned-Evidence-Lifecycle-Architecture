from __future__ import annotations



import re

from pathlib import Path

from typing import Any



if __package__ in {None, ""}:

    import sys



    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from scripts import vela_schema

else:

    from scripts import vela_schema





EXCLUDED_DIR_NAMES = {

    ".git",

    ".venv",

    "__pycache__",

    ".pytest_cache",

    "node_modules",

    "artifacts",

    "outputs",

    "public-export",

}

SECRET_FILE_NAMES = {".env", ".env.local", "credentials.json", "secrets.json"}

INTERNAL_FILE_EXCLUDES = {".vela/context.json"}

TEXT_SUFFIXES = {

    ".json",

    ".md",

    ".markdown",

    ".txt",

    ".toml",

    ".yaml",

    ".yml",

    ".csv",

    ".tsv",

}

LOCAL_PATH_RE = re.compile(r"(?i)([A-Z]:\\{1,2}Users\\{1,2}[^\\\s\"]+|/Users/[^/\s\"]+|/home/[^/\s\"]+)")

SECRET_RE = re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[\"']?[A-Za-z0-9_\-./+=]{12,}")





def _relative(root: Path, path: Path) -> str:

    try:

        return path.resolve().relative_to(root.resolve()).as_posix()

    except ValueError:

        return str(path)





def _iter_candidate_files(project_root: Path) -> list[Path]:

    candidates: list[Path] = []

    for path in project_root.rglob("*"):

        relative = path.relative_to(project_root).as_posix()

        if relative in INTERNAL_FILE_EXCLUDES:

            continue

        if any(part in EXCLUDED_DIR_NAMES for part in path.relative_to(project_root).parts):

            continue

        if path.is_file():

            candidates.append(path)

    return candidates





def _read_text_if_supported(path: Path) -> str | None:

    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in SECRET_FILE_NAMES:

        return None

    if path.stat().st_size > 1_000_000:

        return None

    try:

        return path.read_text(encoding="utf-8")

    except UnicodeDecodeError:

        return None





def scan_project(project_root: Path, *, scope_label: str | None = None) -> dict[str, Any]:

    project_root = project_root.expanduser().resolve()

    errors: list[str] = []

    warnings: list[str] = []

    checks: list[dict[str, Any]] = []



    if not project_root.exists():

        return vela_schema.validation_report(

            validator="privacy_scan",

            scope=scope_label or str(project_root),

            decision="fail",

            errors=[f"Project root not found: {project_root}"],

            warnings=[],

            checks=[],

        )



    for path in _iter_candidate_files(project_root):

        relative = _relative(project_root, path)

        issue_count = 0

        lower_parts = {part.lower() for part in Path(relative).parts}

        if path.name.lower() in SECRET_FILE_NAMES:

            errors.append(f"{relative}: secret-like file must not be exported")

            issue_count += 1

        if {"credentials", "private-notes", "secrets"} & lower_parts:

            warnings.append(f"{relative}: private or credential-like path")

            issue_count += 1



        text = _read_text_if_supported(path)

        if text is not None:

            if LOCAL_PATH_RE.search(text):

                warnings.append(f"{relative}: contains local absolute path")

                issue_count += 1

            if SECRET_RE.search(text):

                errors.append(f"{relative}: contains secret-like assignment")

                issue_count += 1



        checks.append({"path": relative, "issues": issue_count})



    return vela_schema.validation_report(

        validator="privacy_scan",

        scope=scope_label or str(project_root),

        errors=errors,

        warnings=warnings,

        checks=checks,

    )
