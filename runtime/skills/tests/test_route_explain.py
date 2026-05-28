from __future__ import annotations



import sys

import unittest

from pathlib import Path





ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



from scripts.envctl.route_explain import (

    build_route_explanation,

    build_startup_context_summary,

    validate_route_explanation_report,

    validate_startup_context_summary,

)





class RouteExplainTests(unittest.TestCase):

    def test_revision_package_requires_scope_clarification(self) -> None:

        report = build_route_explanation("我要做 revision package")

        self.assertEqual(validate_route_explanation_report(report), [])

        self.assertTrue(report["clarification_required"])

        self.assertIsNone(report["selected_route"])

        self.assertIn(

            "revision-package-scope-disambiguation",

            {item["rule"] for item in report["triggered_conflict_rules"]},

        )

        candidates = {item["route_id"] for item in report["top_candidates"]}

        self.assertIn("writing-export", candidates)

        self.assertIn("social-science-submission-package", candidates)



    def test_specific_empirical_query_can_select_quant_route(self) -> None:

        report = build_route_explanation("DID Stata 稳健性 表格")

        self.assertEqual(validate_route_explanation_report(report), [])

        self.assertFalse(report["clarification_required"])

        self.assertEqual(report["selected_route"], "empirical-quant")



    def test_startup_summary_is_compact_and_route_scoped(self) -> None:

        report = build_startup_context_summary("writing-export")

        self.assertEqual(validate_startup_context_summary(report), [])

        self.assertEqual(report["total_entry"], "research-autopilot")

        self.assertEqual(report["selected_route_context"]["route_id"], "writing-export")

        self.assertIn("完整 routing_table", report["do_not_inject_by_default"])





if __name__ == "__main__":

    unittest.main()
