from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.schema_validation import collect_schema_errors, load_json  # noqa: E402
from scripts.envctl.scholar_browser_patterns import (  # noqa: E402
    estimate_browser_pattern_efficiency,
    validate_scholar_browser_patterns,
)


class ScholarBrowserPatternTests(unittest.TestCase):
    def test_contract_is_schema_and_semantic_valid(self) -> None:
        schema = load_json(ROOT / "schemas" / "scholar_browser_patterns.v1.schema.json")
        payload = load_json(ROOT / "catalog" / "scholar_browser_patterns.json")
        self.assertEqual(collect_schema_errors(payload, schema, "scholar_browser_patterns"), [])

        result = validate_scholar_browser_patterns()
        self.assertTrue(result["ok"], result)
        self.assertEqual(set(result["details"]["systems"]), {"cnki", "google_scholar"})

    def test_cnki_patterns_keep_authorized_batch_boundaries(self) -> None:
        payload = load_json(ROOT / "catalog" / "scholar_browser_patterns.json")
        cnki = next(item for item in payload["systems"] if item["system_id"] == "cnki")
        selectors = " ".join(
            selector
            for action in cnki["actions"]
            for selector in action.get("selectors_or_params", [])
        )
        rejected = " ".join(cnki["rejected_patterns"]).lower()

        self.assertIn("#au_1_value2", selectors)
        self.assertIn("#CSSCI", selectors)
        self.assertIn("#pdfDown", selectors)
        self.assertIn("input.cbItem", selectors)
        self.assertIn("captcha", rejected)
        self.assertIn("cookies", rejected)
        self.assertEqual(cnki["local_smoke_test"]["result"], "pass")
        self.assertIn("Actual PDF or CAJ download", " ".join(cnki["local_smoke_test"]["blocked_checks"]))

    def test_google_scholar_patterns_are_not_promoted_when_smoke_is_blocked(self) -> None:
        payload = load_json(ROOT / "catalog" / "scholar_browser_patterns.json")
        scholar = next(item for item in payload["systems"] if item["system_id"] == "google_scholar")
        primary_keys = " ".join(scholar["primary_keys"]).lower()
        rejected = " ".join(scholar["rejected_patterns"]).lower()
        blocked_checks = " ".join(scholar["local_smoke_test"]["blocked_checks"]).lower()

        self.assertIn("data-cid", primary_keys)
        self.assertIn("sci-hub", rejected)
        self.assertEqual(scholar["local_smoke_test"]["result"], "blocked")
        self.assertIn("verification page", blocked_checks)
        self.assertIn("chrome devtools mcp", blocked_checks)

    def test_efficiency_estimate_requires_adapted_paths_to_be_cheaper(self) -> None:
        estimate = estimate_browser_pattern_efficiency(item_count=10)
        self.assertEqual(estimate["decision"], "more_efficient_and_more_auditable")
        for item in estimate["estimates"]:
            with self.subTest(item["workflow"]):
                self.assertLess(item["adapted_browser_steps"], item["baseline_browser_steps"])
                self.assertGreater(item["saved_browser_steps"], 0)
        cnki = next(item for item in estimate["estimates"] if item["workflow"] == "cnki_batch_metadata_export")
        self.assertGreaterEqual(cnki["reduction_ratio"], 0.8)


if __name__ == "__main__":
    unittest.main()
