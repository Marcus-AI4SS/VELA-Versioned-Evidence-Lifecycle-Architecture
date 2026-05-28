from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

try:
    from .path_utils import CATALOG_ROOT, SKILLS_ROOT
except ImportError:
    from path_utils import CATALOG_ROOT, SKILLS_ROOT

ROOT = SKILLS_ROOT
SETTINGS_PATH = CATALOG_ROOT / "settings.toml"


def load_settings_text() -> str:
    return SETTINGS_PATH.read_text(encoding="utf-8")


def parse_setting(text: str, key: str) -> str:
    for line in text.splitlines():
        if line.startswith(f"{key} = "):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


def resolve_target_dir() -> Path:
    text = load_settings_text()
    vault_path = parse_setting(text, "vault_path")
    vault_subdir = parse_setting(text, "vault_subdir")
    if vault_path:
        target = Path(vault_path)
        if vault_subdir:
            target = target / vault_subdir
        target.mkdir(parents=True, exist_ok=True)
        return target
    fallback = Path(parse_setting(text, "sync_export_dir"))
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def build_note(title: str, body: str, tags: list[str]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    frontmatter = [
        "---",
        f'title: "{title}"',
        f'created: "{now}"',
        "tags:",
    ]
    for tag in tags:
        frontmatter.append(f"  - {tag}")
    frontmatter.extend(["---", "", body.strip(), ""])
    return "\n".join(frontmatter)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--tags", default="codex,research")
    args = parser.parse_args()

    target_dir = resolve_target_dir()
    target = target_dir / f"{args.title}.md"
    body = args.source.read_text(encoding="utf-8")
    content = build_note(args.title, body, [tag.strip() for tag in args.tags.split(",") if tag.strip()])
    target.write_text(content, encoding="utf-8")
    print(str(target))


if __name__ == "__main__":
    main()
