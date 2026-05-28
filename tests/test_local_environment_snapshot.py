from __future__ import annotations

import json
import subprocess
import sys
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

    def test_excluded_app_agents_are_not_in_project_initializer_manifest(self) -> None:
        manifest = json.loads((SNAPSHOT / "skills" / "catalog" / "project_initializer_manifest.json").read_text(encoding="utf-8"))
        text = json.dumps(manifest, ensure_ascii=False)
        for token in (
            "app-product-producer",
            "app-architect",
            "app-ui-producer",
            "app-release-producer",
            "app-qa-reviewer",
            "desktop-app-development",
        ):
            self.assertNotIn(token, text)

    def test_private_paths_are_redacted_from_snapshot_text(self) -> None:
        forbidden = [
            "C:" + "\\Users" + "\\17666",
            "C:/Users/" + "17666",
            "D:" + "\\AI environment",
            "D:/AI " + "environment",
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

    def test_sanitized_snapshot_preserves_json_null_fields(self) -> None:
        memory = json.loads((SNAPSHOT / "skills" / "catalog" / "local_memory_system.json").read_text(encoding="utf-8"))
        layers = {item["id"]: item for item in memory["memory_layers"]}
        for layer_id in ("project_memory", "procedural_memory", "control_memory"):
            self.assertIn("ttl_days", layers[layer_id])
            self.assertIsNone(layers[layer_id]["ttl_days"])

    def test_protected_runtime_paths_keep_public_boundary_placeholder(self) -> None:
        protected = json.loads((SNAPSHOT / "skills" / "catalog" / "protected_runtime_paths.json").read_text(encoding="utf-8"))
        self.assertEqual(len(protected["paths"]), 1)
        placeholder = protected["paths"][0]
        self.assertEqual(placeholder["path"], "<PROTECTED_RUNTIME_PATH>")
        joined = json.dumps(placeholder, ensure_ascii=False).lower()
        self.assertNotIn("scholar", joined)
        self.assertNotIn("desktop", joined)

    def test_envctl_entrypoint_matches_sanitized_snapshot(self) -> None:
        envctl_main = (SNAPSHOT / "skills" / "scripts" / "envctl" / "__main__.py").read_text(encoding="utf-8")
        self.assertNotIn("scholar_panel", envctl_main)
        previous = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(SNAPSHOT / "skills" / "scripts"))
        try:
            import envctl.__main__ as envctl_main_module

            parser = envctl_main_module.build_parser()
            command_names = set(parser._subparsers._actions[1].choices)
            self.assertIn("validate", command_names)
            self.assertNotIn("scholar-panel", command_names)
        finally:
            sys.path.pop(0)
            sys.dont_write_bytecode = previous

    def test_core_snapshot_validators_survive_sanitization(self) -> None:
        previous = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(SNAPSHOT / "skills" / "scripts"))
        try:
            from envctl.cybernetics import validate_cybernetics_contracts
            from envctl.memory_system import validate_local_memory_system
            from envctl.skill_workbench_policy import validate_skill_workbench_policy

            memory_report = validate_local_memory_system()
            cybernetics_report = validate_cybernetics_contracts()
            skill_workbench_report = validate_skill_workbench_policy()
        finally:
            sys.path.pop(0)
            sys.dont_write_bytecode = previous
        self.assertEqual(memory_report.get("errors"), [])
        self.assertEqual(cybernetics_report.get("errors"), [])
        self.assertEqual(skill_workbench_report.get("errors"), [])

    def test_distribution_stack_validator_passes_after_exclusions(self) -> None:
        script = SNAPSHOT / "skills" / "scripts" / "validate_research_stack.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
