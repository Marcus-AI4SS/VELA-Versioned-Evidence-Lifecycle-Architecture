from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "research-stack" / "local-environment"


class LocalEnvironmentSnapshotTests(unittest.TestCase):
    def test_snapshot_manifest_records_local_may_updates(self) -> None:
        manifest = json.loads((SNAPSHOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "vela.local_environment_snapshot.v1")
        self.assertEqual(manifest["source"]["repository"], "skills-environment-local")
        self.assertEqual(manifest["source"]["since"], "2026-05-01")
        self.assertGreaterEqual(manifest["source"]["commit_count_since"], 1)
        self.assertIn("memory governance", manifest["policy"]["include"])
        self.assertIn("desktop app development chain", manifest["policy"]["exclude"])

    def test_excluded_skill_folders_are_not_mirrored(self) -> None:
        skills_root = SNAPSHOT / "skills" / "plugins" / "research-autopilot" / "skills"
        names = {item.name for item in skills_root.iterdir() if item.is_dir()}
        self.assertNotIn("desktop-app-product-blueprint", names)
        self.assertNotIn("desktop-app-architect", names)
        self.assertNotIn("desktop-ui-implementation", names)
        self.assertNotIn("desktop-app-qa-debug", names)
        self.assertNotIn("desktop-app-release-packager", names)
        self.assertNotIn("scholar-panel", names)
        self.assertIn("research-autopilot", names)
        self.assertIn("reference-fulltext-acquisition", names)

    def test_private_paths_are_redacted_from_snapshot_text(self) -> None:
        forbidden = [
            "C:\\Users\\17666",
            "C:/Users/17666",
            "D:\\AI environment",
            "D:/AI environment",
            "Obsidian Vault",
        ]
        text_suffixes = {".css", ".html", ".js", ".json", ".md", ".ps1", ".py", ".svg", ".toml", ".txt", ".yaml", ".yml"}
        offenders: list[str] = []
        for path in SNAPSHOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in text_suffixes:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(token in text for token in forbidden):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_toolchain_inventory_keeps_versions_without_paths(self) -> None:
        inventory = json.loads((SNAPSHOT / "toolchain" / "toolchain_inventory.json").read_text(encoding="utf-8"))
        tools = {tool["command"]: tool for tool in inventory["tools"]}
        for command in ("git", "rg", "python", "node", "powershell"):
            self.assertIn(command, tools)
            self.assertTrue(tools[command]["available"], command)
            self.assertEqual(tools[command]["path_policy"], "absolute local paths are intentionally not exported")

    def test_settings_uses_portable_placeholders(self) -> None:
        settings = (SNAPSHOT / "skills" / "catalog" / "settings.toml").read_text(encoding="utf-8")
        self.assertIn("<LOCAL_ENV_ROOT>", settings)
        self.assertIn("<CODEX_HOME>", settings)
        self.assertIn("<OBSIDIAN_VAULT>", settings)


if __name__ == "__main__":
    unittest.main()
