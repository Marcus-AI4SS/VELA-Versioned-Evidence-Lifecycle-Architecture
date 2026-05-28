from __future__ import annotations



from pathlib import Path

from typing import Any



try:

    from ..path_utils import CATALOG_ROOT, INSTALLED_SKILLS_DIR

    from .schema_validation import load_json

except ImportError:  # pragma: no cover

    from path_utils import CATALOG_ROOT, INSTALLED_SKILLS_DIR

    from envctl.schema_validation import load_json





PROTECTED_RUNTIME_PATHS = CATALOG_ROOT / "protected_runtime_paths.json"





def _normalize_path(path: Path | str) -> str:

    return str(Path(path).expanduser()).replace("\\", "/").rstrip("/").lower()





def load_protected_runtime_paths(path: Path = PROTECTED_RUNTIME_PATHS) -> dict[str, Any]:

    if not path.exists():

        return {

            "schema_version": "protected_runtime_paths.v1",

            "paths": [],

        }

    return load_json(path)





def protected_runtime_path_strings(path: Path = PROTECTED_RUNTIME_PATHS) -> list[str]:

    payload = load_protected_runtime_paths(path)

    return [

        item["path"]

        for item in payload.get("paths", [])

        if isinstance(item, dict) and isinstance(item.get("path"), str)

    ]





def protected_runtime_skill_names(

    *,

    installed_skills_dir: Path = INSTALLED_SKILLS_DIR,

    catalog_path: Path = PROTECTED_RUNTIME_PATHS,

) -> list[str]:

    installed_root = _normalize_path(installed_skills_dir)

    names: list[str] = []

    for item in protected_runtime_path_strings(catalog_path):

        normalized = _normalize_path(item)

        parent = _normalize_path(Path(item).parent)

        if parent == installed_root:

            names.append(Path(item).name)

    return sorted(set(names))





def is_protected_runtime_path(path: Path, catalog_path: Path = PROTECTED_RUNTIME_PATHS) -> bool:

    normalized = _normalize_path(path)

    protected = [_normalize_path(item) for item in protected_runtime_path_strings(catalog_path)]

    return any(normalized == item or normalized.startswith(f"{item}/") for item in protected)
