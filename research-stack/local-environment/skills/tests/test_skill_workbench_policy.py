from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.schema_validation import collect_schema_document_errors, collect_schema_errors, load_json
from scripts.envctl.skill_workbench_policy import validate_skill_workbench_policy


class SkillWorkbenchPolicyTests(unittest.TestCase):
    def test_skill_workbench_policy_schema_validates_catalog(self) -> None:
        schema = load_json(ROOT / "schemas" / "skill_workbench_policy.v1.schema.json")
        payload = load_json(ROOT / "catalog" / "skill_workbench_policy.json")

        self.assertEqual(collect_schema_document_errors(schema, "skill_workbench_policy.schema"), [])
        self.assertEqual(collect_schema_errors(payload, schema, "skill_workbench_policy"), [])

    def test_skill_workbench_policy_keeps_local_source_of_truth(self) -> None:
        payload = load_json(ROOT / "catalog" / "skill_workbench_policy.json")

        self.assertEqual(payload["selected_strategy"], "option_b_contract_first_local_workbench_policy")
        self.assertIn("skills-environment-local", payload["local_boundaries"]["source_of_truth"])
        self.assertIn("scholar-nuwa", payload["local_boundaries"]["protected_runtime_policy"])
        self.assertIn(
            "research_autopilot_plugin_skill",
            {item["id"] for item in payload["package_contracts"]},
        )
        self.assertIn(
            "validate_before_install",
            {item["id"] for item in payload["borrowed_patterns"]},
        )
        self.assertIn(
            "workbench_keyword_harvest_status_model",
            {item["id"] for item in payload["borrowed_patterns"]},
        )
        self.assertIn(
            "workbench_r_plot_micro_patterns",
            {item["id"] for item in payload["borrowed_patterns"]},
        )
        workbench = next(item for item in payload["source_review_refs"] if item["upstream"] == "Jinze-Lee/codex-skills-workbench")
        self.assertIn("keyword literature harvest status model", workbench["adopted_as"])
        self.assertIn("Chinese thesis DOCX manifest and placeholder workflow as explicit opt-in pattern", workbench["adopted_as"])

    def test_skill_workbench_policy_validator_passes(self) -> None:
        result = validate_skill_workbench_policy()
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["ok"])

    def test_envctl_validate_skill_workbench_target(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "skills.scripts.envctl", "validate", "skill-workbench", "--summary"],
            cwd=str(ROOT.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["scope"], "skill_workbench_policy")


if __name__ == "__main__":
    unittest.main()
