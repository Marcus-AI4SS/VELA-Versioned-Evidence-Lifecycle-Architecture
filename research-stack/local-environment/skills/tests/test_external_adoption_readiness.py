from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.external_adoption_readiness import validate_external_adoption_readiness
from scripts.envctl.schema_validation import collect_schema_errors, load_json


class ExternalAdoptionReadinessTests(unittest.TestCase):
    def test_external_adoption_readiness_validator_passes(self) -> None:
        result = validate_external_adoption_readiness()
        envelope = load_json(ROOT / "schemas" / "validator_result.schema.json")

        self.assertEqual(collect_schema_errors(result, envelope, "external_adoption_readiness_result"), [])
        self.assertTrue(result["ok"], result)
        probes = result["details"]["runtime_probes"]
        self.assertTrue(probes["rohitg00/agentmemory"]["ok"])
        self.assertTrue(probes["colbymchenry/codegraph"]["ok"])
        self.assertTrue(probes["op7418/guizang-ppt-skill"]["ok"])
        self.assertTrue(probes["opendataloader-project/opendataloader-pdf"]["ok"])

    def test_codegraph_probe_declares_project_local_rule(self) -> None:
        result = validate_external_adoption_readiness()
        codegraph = result["details"]["runtime_probes"]["colbymchenry/codegraph"]

        self.assertTrue(codegraph["initialized"], codegraph)
        self.assertGreater(codegraph["node_count"], 0)
        self.assertIn("project-local", codegraph["project_scope_rule"])

    def test_envctl_validate_adoption_readiness_target(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "skills.scripts.envctl", "validate", "adoption-readiness", "--summary"],
            cwd=str(ROOT.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["scope"], "external_adoption_readiness")


if __name__ == "__main__":
    unittest.main()
