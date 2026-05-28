from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.protected_paths import protected_runtime_skill_names
from scripts.envctl.runtime_skill_drift import inspect_installed_skill_stale_paths, inspect_research_autopilot_runtime


class RuntimeSkillDriftTests(unittest.TestCase):
    def test_detects_old_paths_and_runtime_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_plugin_root = root / "source-plugin"
            source_root = source_plugin_root / "skills"
            installed_root = root / "installed"
            plugin_cache_root = root / "plugin-cache"
            cache_root = plugin_cache_root / "skills"
            for base in (source_root, installed_root, cache_root):
                (base / "research-autopilot").mkdir(parents=True)
            source_text = "# Skill\n\n`D:\\AI environment-GITHUB\\git-folders\\skills-environment-local\\skills\\catalog\\routing_table.json`\n"
            stale_text = "# Skill\n\n`C:\\Users\\17666\\Desktop\\AI environment-configuration\\git-folders\\skills-environment-local\\skills\\catalog\\routing_table.json`\n"
            (source_root / "research-autopilot" / "SKILL.md").write_text(source_text, encoding="utf-8")
            (installed_root / "research-autopilot" / "SKILL.md").write_text(stale_text, encoding="utf-8")
            (cache_root / "research-autopilot" / "SKILL.md").write_text(stale_text, encoding="utf-8")

            result = inspect_research_autopilot_runtime(
                source_plugin_root=source_plugin_root,
                source_skill_root=source_root,
                installed_skills_dir=installed_root,
                plugin_cache_skills_dir=cache_root,
                plugin_cache_root=plugin_cache_root,
            )

        self.assertFalse(result["ok"])
        self.assertIn("research-autopilot", result["installed_duplicates"])
        self.assertIn("research-autopilot", result["installed_old_path_hits"])
        self.assertIn("research-autopilot", result["cache_old_path_hits"])
        self.assertIn("research-autopilot", result["installed_changed"])
        self.assertIn("research-autopilot", result["cache_changed"])

    def test_detects_plugin_bundle_cache_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_plugin_root = root / "source-plugin"
            source_root = source_plugin_root / "skills"
            installed_root = root / "installed"
            plugin_cache_root = root / "plugin-cache"
            cache_root = plugin_cache_root / "skills"
            for base in (source_root, installed_root, cache_root):
                (base / "research-autopilot").mkdir(parents=True)
                (base / "research-autopilot" / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
            (source_plugin_root / ".codex-plugin").mkdir(parents=True)
            (plugin_cache_root / ".codex-plugin").mkdir(parents=True)
            (source_plugin_root / ".codex-plugin" / "plugin.json").write_text('{"version":"source"}\n', encoding="utf-8")
            (plugin_cache_root / ".codex-plugin" / "plugin.json").write_text('{"version":"cache"}\n', encoding="utf-8")

            result = inspect_research_autopilot_runtime(
                source_plugin_root=source_plugin_root,
                source_skill_root=source_root,
                installed_skills_dir=installed_root,
                plugin_cache_skills_dir=cache_root,
                plugin_cache_root=plugin_cache_root,
            )

        self.assertFalse(result["ok"])
        self.assertIn(".codex-plugin", result["plugin_bundle_changed"])

    def test_allows_synced_standalone_skill_mirrors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_plugin_root = root / "source-plugin"
            source_root = source_plugin_root / "skills"
            installed_root = root / "installed"
            plugin_cache_root = root / "plugin-cache"
            cache_root = plugin_cache_root / "skills"
            for base in (source_root, installed_root, cache_root):
                (base / "research-autopilot").mkdir(parents=True)
                (base / "research-autopilot" / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

            result = inspect_research_autopilot_runtime(
                source_plugin_root=source_plugin_root,
                source_skill_root=source_root,
                installed_skills_dir=installed_root,
                plugin_cache_skills_dir=cache_root,
                plugin_cache_root=plugin_cache_root,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["installed_mirrors"], ["research-autopilot"])

    def test_errors_when_source_skill_root_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = inspect_research_autopilot_runtime(
                source_plugin_root=root / "missing-plugin",
                source_skill_root=root / "missing-plugin" / "skills",
                installed_skills_dir=root / "installed",
                plugin_cache_skills_dir=root / "plugin-cache" / "skills",
                plugin_cache_root=root / "plugin-cache",
            )

        self.assertFalse(result["ok"])
        self.assertTrue(
            any(error.startswith("research-autopilot-source-skill-root-missing:") for error in result["errors"])
        )

    def test_detects_old_paths_across_installed_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            installed_root = Path(tmp)
            skill_dir = installed_root / "research-stack-manager"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "`C:\\Users\\17666\\Desktop\\AI environment-configuration\\git-folders\\skills-environment-local\\skills\\scripts\\validate_research_stack.py`\n",
                encoding="utf-8",
            )

            result = inspect_installed_skill_stale_paths(installed_skills_dir=installed_root)

        self.assertFalse(result["ok"])
        self.assertIn("research-stack-manager", result["old_path_hits"])

    def test_skips_protected_runtime_skill_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            installed_root = Path(tmp) / "skills"
            installed_root.mkdir()
            protected = installed_root / "scholar-nuwa"
            protected.mkdir()
            (protected / "SKILL.md").write_text(
                "`C:\\Users\\17666\\Desktop\\AI environment-configuration\\private\\path`\n",
                encoding="utf-8",
            )
            catalog = Path(tmp) / "protected_runtime_paths.json"
            catalog.write_text(
                '{"schema_version":"protected_runtime_paths.v1","paths":[{"path":"' + str(protected).replace("\\", "/") + '"}]}\n',
                encoding="utf-8",
            )

            names = protected_runtime_skill_names(installed_skills_dir=installed_root, catalog_path=catalog)
            result = inspect_installed_skill_stale_paths(
                installed_skills_dir=installed_root,
                protected_catalog_path=catalog,
            )

        self.assertEqual(names, ["scholar-nuwa"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["protected_skills_skipped"], ["scholar-nuwa"])
        self.assertNotIn("scholar-nuwa", result["old_path_hits"])


if __name__ == "__main__":
    unittest.main()
