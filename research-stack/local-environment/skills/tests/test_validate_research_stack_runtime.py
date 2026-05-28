from __future__ import annotations

import unittest
from pathlib import Path

from skills.scripts.validate_research_stack import (
    collect_project_root_file_errors,
    is_isolated_codex_worktree,
    isolated_cross_repo_warning,
    isolated_runtime_skill_warning,
    python_module_command,
)


class ValidateResearchStackRuntimeTests(unittest.TestCase):
    def test_detects_isolated_codex_worktree(self) -> None:
        root = Path("<CODEX_HOME>/worktrees/ee70/skills-environment-local")
        self.assertTrue(is_isolated_codex_worktree(root))
        self.assertFalse(is_isolated_codex_worktree(Path("<LOCAL_ENV_ROOT>")))

    def test_only_worktree_adjacent_repo_absence_is_downgraded(self) -> None:
        self.assertTrue(isolated_cross_repo_warning("cross-repo-drift:missing-vela-repo:C:/tmp/VELA-workflow"))
        self.assertTrue(isolated_cross_repo_warning("cross-repo-drift:missing-helm-repo:C:/tmp/HELM"))
        self.assertFalse(isolated_cross_repo_warning("cross-repo-drift:schema-version-drift:vela.codex.handoff.v1.schema.json"))

    def test_only_runtime_cache_drift_is_downgraded(self) -> None:
        self.assertTrue(
            isolated_runtime_skill_warning(
                "runtime-skill-drift:research-autopilot-cache-differs-from-source:['research-autopilot']"
            )
        )
        self.assertFalse(
            isolated_runtime_skill_warning(
                "runtime-skill-drift:research-autopilot-source-old-path-hits:1"
            )
        )

    def test_python_module_command_uses_module_execution(self) -> None:
        self.assertEqual(
            python_module_command("python", "skills.scripts.envctl", "validate", "contracts"),
            ["python", "-m", "skills.scripts.envctl", "validate", "contracts"],
        )

    def test_missing_project_root_files_are_validator_errors(self) -> None:
        self.assertEqual(
            collect_project_root_file_errors(
                {"project_root_files": {"local_memory_system": True, "memory_candidate_schema": False}}
            ),
            ["project-root-file-missing:memory_candidate_schema"],
        )


if __name__ == "__main__":
    unittest.main()
