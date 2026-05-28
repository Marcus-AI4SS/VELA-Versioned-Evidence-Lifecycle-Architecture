from __future__ import annotations



import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT.parent
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from skills.scripts.envctl.peer_review_workflow import validate_peer_review_workflow

CATALOG = ROOT / "catalog"




class PeerReviewWorkflowTests(unittest.TestCase):

    def setUp(self) -> None:

        self.payload = json.loads((CATALOG / "peer_review_workflow.json").read_text(encoding="utf-8"))



    def test_contract_validator_passes(self) -> None:

        report = validate_peer_review_workflow()

        self.assertTrue(report["ok"], report.get("errors"))



    def test_selected_strategy_is_contract_first_hybrid(self) -> None:

        selected = self.payload["selected_strategy"]

        options = {item["id"]: item for item in self.payload["adoption_options"]}

        self.assertEqual(selected, "option_b_contract_first_hybrid")

        self.assertEqual(options[selected]["decision"], "selected")



    def test_all_review_sources_are_represented(self) -> None:

        upstreams = {item["upstream"] for item in self.payload["source_review_refs"]}

        self.assertIn("qqfly1to19/awesome_proofreading_auto", upstreams)

        self.assertIn("c-narcissus/research-review-skill-factory", upstreams)

        self.assertIn("Imbad0202/academic-research-skills", upstreams)

        self.assertIn("wanshuiyin/Auto-claude-code-research-in-sleep", upstreams)

        self.assertIn("Yuan1z0825/nature-skills", upstreams)

        self.assertIn("Leey21/awesome-ai-research-writing", upstreams)



    def test_reviewer_perspective_prompt_patterns_are_absorbed(self) -> None:

        source_refs = {item["upstream"]: item for item in self.payload["source_review_refs"]}

        adopted = source_refs["Leey21/awesome-ai-research-writing"]["adopted_as"]

        self.assertIn("fatal-versus-fixable weakness distinction", adopted)

        self.assertIn("strategic advice separates root cause, fixability, and concrete action", adopted)



        skill_text = (

            ROOT

            / "plugins"

            / "research-autopilot"

            / "skills"

            / "academic-paper-review"

            / "SKILL.md"

        ).read_text(encoding="utf-8")

        self.assertIn("Reviewer-Perspective Adapter", skill_text)

        self.assertIn("Distinguish true blocking or fatal issues from fixable weaknesses", skill_text)



    def test_standard_review_does_not_default_to_multi_agent(self) -> None:

        modes = {item["id"]: item for item in self.payload["modes"]}

        self.assertNotEqual(modes["standard_single_review"]["default_subagent_policy"], "always_multi_agent")

        self.assertEqual(modes["submission_package_review"]["default_subagent_policy"], "always_multi_agent")



    def test_issue_contract_has_evidence_and_blocker_fields(self) -> None:

        required = set(self.payload["issue_contract"]["required_fields"])

        self.assertIn("evidence_seen", required)

        self.assertIn("required_action", required)

        self.assertIn("confidence", required)

        self.assertIn("blocker", required)





if __name__ == "__main__":

    unittest.main()
