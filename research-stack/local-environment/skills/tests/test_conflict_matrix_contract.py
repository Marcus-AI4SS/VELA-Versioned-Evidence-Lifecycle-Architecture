from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.conflict_matrix import validate_conflict_matrix
from scripts.envctl.schema_validation import collect_schema_errors, load_json


class ConflictMatrixContractTests(unittest.TestCase):
    def test_conflict_matrix_validates(self) -> None:
        result = validate_conflict_matrix()
        envelope = load_json(ROOT / "schemas" / "validator_result.schema.json")
        self.assertEqual(collect_schema_errors(result, envelope, "conflict_matrix_result"), [])
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["validator"], "validate_conflict_matrix")

    def test_required_route_disambiguation_rules_are_present(self) -> None:
        payload = load_json(ROOT / "catalog" / "conflict_matrix.json")
        rules = {item["rule"]: item for item in payload["rules"]}
        for rule_id in {
            "autopilot-entry",
            "route-confirmation-before-new-chain",
            "revision-package-scope-disambiguation",
            "replication-package-scope-disambiguation",
        }:
            self.assertIn(rule_id, rules)
        self.assertIn("必须先问用户", rules["revision-package-scope-disambiguation"]["reason"])
        self.assertIn("必须先问用户", rules["replication-package-scope-disambiguation"]["reason"])

    def test_retired_skills_are_not_active(self) -> None:
        conflicts = load_json(ROOT / "catalog" / "conflict_matrix.json")
        catalog = load_json(ROOT / "catalog" / "skill_catalog.json")
        active = {name for name, item in catalog["skills"].items() if item["status"] == "active"}
        self.assertFalse(set(conflicts["retired_skills"]) & active)


if __name__ == "__main__":
    unittest.main()
