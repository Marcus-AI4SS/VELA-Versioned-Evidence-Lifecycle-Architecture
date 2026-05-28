from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.schema_validation import collect_schema_errors, load_json
from scripts.envctl.validator_envelope import build_validator_result, exit_code_for_result


class ValidatorEnvelopeTests(unittest.TestCase):
    def test_pass_envelope_matches_schema(self) -> None:
        result = build_validator_result(
            validator="unit-test",
            scope="contracts",
            details={"checked": 1},
        )
        schema = load_json(ROOT / "schemas" / "validator_result.schema.json")
        self.assertEqual(collect_schema_errors(result, schema, "validator_result"), [])
        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "pass")
        self.assertEqual(exit_code_for_result(result), 0)

    def test_error_envelope_fails(self) -> None:
        result = build_validator_result(
            validator="unit-test",
            scope="contracts",
            errors=["broken"],
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["decision"], "fail")
        self.assertEqual(exit_code_for_result(result), 1)


if __name__ == "__main__":
    unittest.main()
