from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"


class EvidenceBasedLiteratureWorkflowTests(unittest.TestCase):
    def test_skill_source_has_priority_trigger_terms(self) -> None:
        skill_path = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "evidence-based-literature-workflow"
            / "SKILL.md"
        )
        self.assertTrue(skill_path.exists())
        text = skill_path.read_text(encoding="utf-8")
        self.assertIn("Priority evidence-checking coordinator", text)
        for trigger in ["筛选参考文献", "候选文献表", "结构性阅读", "文献核验", "证据核验", "引文核验", "引用核验", "证据句", "证据包"]:
            self.assertIn(trigger, text)
        self.assertIn("select this skill before isolated `citation-verifier`", text)
        self.assertIn("around 50 candidate references", text)
        self.assertIn("20 Chinese sources and 30 English sources", text)
        self.assertIn("upstream and downstream literature", text)
        self.assertIn("SCI, SSCI, or CSSCI source status", text)
        self.assertIn("Never write annotations into source PDFs", text)
        self.assertIn("two independent reviews pass", text)
        self.assertIn("Search-hit or phrase-only highlights are not accepted", text)

        audit_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "evidence-based-literature-workflow"
            / "references"
            / "citation-evidence-audit.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Never annotate the source PDF", audit_text)
        self.assertIn("The accepted registry must cover exactly the current citation table evidence IDs", audit_text)
        self.assertIn("highlighted_phrase_fallback", audit_text)

    def test_catalog_and_route_make_workflow_the_priority_evidence_route(self) -> None:
        catalog = json.loads((SKILLS_ROOT / "catalog" / "skill_catalog.json").read_text(encoding="utf-8"))
        self.assertIn("evidence-based-literature-workflow", catalog["skills"])
        self.assertEqual(catalog["skills"]["evidence-based-literature-workflow"]["role"], "controller")

        routing = json.loads((SKILLS_ROOT / "catalog" / "routing_table.json").read_text(encoding="utf-8"))
        route_ids = [item["id"] for item in routing["routes"]]
        self.assertLess(route_ids.index("evidence-based-literature-workflow"), route_ids.index("literature-review"))
        route = next(item for item in routing["routes"] if item["id"] == "evidence-based-literature-workflow")
        self.assertEqual(route["skills"][0], "evidence-based-literature-workflow")
        self.assertIn("citation-verifier", route["skills"])
        self.assertIn("reference-fulltext-acquisition", route["skills"])
        self.assertIn("writing-reference-capture", route["skills"])
        self.assertIn("筛选参考文献", route["keywords"])
        self.assertIn("候选文献表", route["keywords"])
        self.assertIn("结构性阅读", route["keywords"])
        self.assertIn("证据包", route["keywords"])
        self.assertIn("中文约 20 篇、英文约 30 篇", route["next_step"])
        self.assertIn("上游引用和下游被引文献", route["next_step"])
        self.assertIn("SCI、SSCI 或 CSSCI 来源证据", route["next_step"])

    def test_contracts_cover_route_scope_policy_pipeline_and_playbook(self) -> None:
        policies = json.loads(
            (SKILLS_ROOT / "catalog" / "route_mcp_activation_policy.json").read_text(encoding="utf-8")
        )
        policy = next(item for item in policies["routes"] if item["route_id"] == "evidence-based-literature-workflow")
        policy_mcp = set(policy["required_mcp"]) | set(policy["optional_mcp"]) | set(policy["activation_needed_mcp"])

        routing = json.loads((SKILLS_ROOT / "catalog" / "routing_table.json").read_text(encoding="utf-8"))
        route = next(item for item in routing["routes"] if item["id"] == "evidence-based-literature-workflow")
        self.assertEqual(set(route["mcp"]), policy_mcp)

        scope = json.loads((SKILLS_ROOT / "catalog" / "project_scope_rules.json").read_text(encoding="utf-8"))
        self.assertIn("evidence-based-literature-workflow", scope["route_scope"]["conditional_multi_agent"])
        self.assertEqual(
            scope["conditional_rules"]["evidence-based-literature-workflow"],
            {"copy_of": "literature-review"},
        )

        pipeline = json.loads((SKILLS_ROOT / "catalog" / "research_pipeline_stages.json").read_text(encoding="utf-8"))
        self.assertEqual(
            pipeline["route_stage_sequences"]["evidence-based-literature-workflow"],
            [
                "research_design",
                "literature_discovery",
                "citation_verification",
                "data_material_acquisition",
                "writing_synthesis",
                "review_revision",
            ],
        )
        self.assertIn(
            "doi_and_metadata_verified",
            pipeline["route_stage_gate_overrides"]["evidence-based-literature-workflow"]["citation_verification"],
        )

        playbooks = json.loads((SKILLS_ROOT / "catalog" / "research_team_playbooks.json").read_text(encoding="utf-8"))
        playbook = next(item for item in playbooks["playbooks"] if item["route_id"] == "evidence-based-literature-workflow")
        self.assertEqual(playbook["default_agents"], ["literature-producer", "reviewer"])

    def test_sync_script_and_autopilot_expose_the_workflow(self) -> None:
        sync_script = (SKILLS_ROOT / "scripts" / "sync_research_autopilot_skills.ps1").read_text(encoding="utf-8")
        self.assertIn('"evidence-based-literature-workflow"', sync_script)
        self.assertIn('"pdf"', sync_script)

        autopilot_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "research-autopilot"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("筛选参考文献", autopilot_text)
        self.assertIn("候选文献表", autopilot_text)
        self.assertIn("结构性阅读", autopilot_text)
        self.assertIn("evidence-based-literature-workflow", autopilot_text)


if __name__ == "__main__":
    unittest.main()
