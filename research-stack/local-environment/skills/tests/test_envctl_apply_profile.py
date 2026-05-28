from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.apply_profile import apply_profile, rollback_profile


BASE_CONFIG = """model = "gpt-5.5"

[mcp_servers.chrome-devtools]
command = "cmd"
enabled = true

[mcp_servers.playwright-mcp]
command = "cmd"
enabled = true

[mcp_servers.zotero-mcp]
command = "python"
enabled = true

[mcp_servers.openalex-mcp]
command = "cmd"
enabled = true
"""


class EnvctlApplyProfileTests(unittest.TestCase):
    def write_profile(self, root: Path, name: str, *, managed: list[str], enabled: list[str]) -> None:
        profile = root / f"{name}.toml"
        profile.write_text(
            "\n".join(
                [
                    f'name = "{name}"',
                    'display_name = "Test Profile"',
                    'description = "temporary test profile"',
                    "managed_mcp = [" + ", ".join(f'"{item}"' for item in managed) + "]",
                    "enabled_mcp = [" + ", ".join(f'"{item}"' for item in enabled) + "]",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def test_dry_run_reports_changes_without_writing_config_or_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profiles = root / "profiles"
            backups = root / "backups"
            profiles.mkdir()
            config = root / "config.toml"
            config.write_text(BASE_CONFIG, encoding="utf-8")
            self.write_profile(
                profiles,
                "desktop-app",
                managed=["chrome-devtools", "playwright-mcp", "zotero-mcp"],
                enabled=["chrome-devtools", "playwright-mcp"],
            )

            result = apply_profile("desktop-app", config_path=config, profiles_root=profiles, backup_root=backups, dry_run=True)

            self.assertTrue(result["ok"])
            self.assertEqual(result["mode"], "dry-run")
            self.assertFalse(result["source_files_written"])
            self.assertEqual(config.read_text(encoding="utf-8"), BASE_CONFIG)
            self.assertFalse(backups.exists())
            self.assertIn({"mcp": "zotero-mcp", "from": True, "to": False}, result["changes"])

    def test_matching_profile_dry_run_has_no_format_only_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profiles = root / "profiles"
            backups = root / "backups"
            profiles.mkdir()
            config = root / "config.toml"
            config.write_text(BASE_CONFIG, encoding="utf-8")
            self.write_profile(
                profiles,
                "current",
                managed=["chrome-devtools", "playwright-mcp", "zotero-mcp", "openalex-mcp"],
                enabled=["chrome-devtools", "playwright-mcp", "zotero-mcp", "openalex-mcp"],
            )

            result = apply_profile("current", config_path=config, profiles_root=profiles, backup_root=backups, dry_run=True)

            self.assertTrue(result["ok"])
            self.assertEqual(result["changes"], [])
            self.assertEqual(result["diff"], [])

    def test_commit_backs_up_and_only_changes_managed_mcp_enabled_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profiles = root / "profiles"
            backups = root / "backups"
            profiles.mkdir()
            config = root / "config.toml"
            config.write_text(BASE_CONFIG, encoding="utf-8")
            self.write_profile(
                profiles,
                "minimal",
                managed=["chrome-devtools", "playwright-mcp"],
                enabled=["chrome-devtools"],
            )

            result = apply_profile("minimal", config_path=config, profiles_root=profiles, backup_root=backups, commit=True)
            text = config.read_text(encoding="utf-8")

            self.assertTrue(result["ok"])
            self.assertEqual(result["mode"], "commit")
            self.assertTrue(result["config_written"])
            self.assertFalse(result["source_files_written"])
            self.assertTrue(Path(result["backup_path"]).exists())
            self.assertIn("[mcp_servers.playwright-mcp]\ncommand = \"cmd\"\nenabled = false", text)
            self.assertIn("[mcp_servers.zotero-mcp]\ncommand = \"python\"\nenabled = true", text)

    def test_rollback_latest_restores_most_recent_apply_profile_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profiles = root / "profiles"
            backups = root / "backups"
            profiles.mkdir()
            config = root / "config.toml"
            config.write_text(BASE_CONFIG, encoding="utf-8")
            self.write_profile(
                profiles,
                "minimal",
                managed=["chrome-devtools", "playwright-mcp"],
                enabled=["chrome-devtools"],
            )

            apply_profile("minimal", config_path=config, profiles_root=profiles, backup_root=backups, commit=True)
            self.assertIn("enabled = false", config.read_text(encoding="utf-8"))

            result = rollback_profile(config_path=config, backup_root=backups, backup_id="latest")

            self.assertTrue(result["ok"])
            self.assertEqual(result["mode"], "rollback")
            self.assertEqual(config.read_text(encoding="utf-8"), BASE_CONFIG)

    def test_rollback_rejects_backup_path_outside_backup_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            backups = root / "backups"
            outside = root / "outside.toml"
            config = root / "config.toml"
            backups.mkdir()
            config.write_text(BASE_CONFIG, encoding="utf-8")
            outside.write_text(BASE_CONFIG.replace("enabled = true", "enabled = false", 1), encoding="utf-8")

            result = rollback_profile(config_path=config, backup_root=backups, backup_id=str(outside))

            self.assertFalse(result["ok"])
            self.assertIn("backup-outside-backup-root", result["errors"][0])
            self.assertEqual(config.read_text(encoding="utf-8"), BASE_CONFIG)


if __name__ == "__main__":
    unittest.main()
