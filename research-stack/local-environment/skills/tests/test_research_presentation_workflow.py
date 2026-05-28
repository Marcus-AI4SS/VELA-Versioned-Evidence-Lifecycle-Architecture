from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))


class ResearchPresentationWorkflowTests(unittest.TestCase):
    def test_contract_validates_and_installed_guizang_skill_exists(self) -> None:
        from scripts.envctl.research_presentation_workflow import validate_research_presentation_workflow

        result = validate_research_presentation_workflow()
        self.assertTrue(result["ok"], result)

        skill_root = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "research-presentation-studio"
        )
        codex_home = Path.home() / ".codex"
        upstream = codex_home / "skills" / "guizang-ppt-skill"
        self.assertTrue((skill_root / "SKILL.md").exists())
        self.assertTrue((upstream / "SKILL.md").exists())
        self.assertTrue((upstream / "assets" / "template.html").exists())
        self.assertTrue((upstream / "assets" / "template-swiss.html").exists())
        self.assertTrue((upstream / "references" / "swiss-layout-lock.md").exists())
        self.assertTrue((upstream / "scripts" / "validate-swiss-deck.mjs").exists())

    def test_route_catalog_and_runtime_sync_are_registered(self) -> None:
        catalog = json.loads((SKILLS_ROOT / "catalog" / "skill_catalog.json").read_text(encoding="utf-8"))
        self.assertIn("research-presentation-studio", catalog["skills"])
        self.assertEqual(catalog["skills"]["research-presentation-studio"]["task_type"], "presentation_design")

        routes = json.loads((SKILLS_ROOT / "catalog" / "routing_table.json").read_text(encoding="utf-8"))
        route = next(item for item in routes["routes"] if item["id"] == "research-presentation")
        self.assertIn("research-presentation-studio", route["skills"])
        self.assertIn("Presentations", route["plugins"])
        self.assertIn("Swiss Style", route["keywords"])
        self.assertIn("论文转PPT", route["keywords"])

        mcp_policy = json.loads((SKILLS_ROOT / "catalog" / "route_mcp_activation_policy.json").read_text(encoding="utf-8"))
        policy = next(item for item in mcp_policy["routes"] if item["route_id"] == "research-presentation")
        self.assertEqual(policy["required_mcp"], [])
        self.assertEqual(policy["optional_mcp"], [])

        sync_script = (SKILLS_ROOT / "scripts" / "sync_research_autopilot_skills.ps1").read_text(encoding="utf-8")
        self.assertIn('"research-presentation-studio"', sync_script)

    def test_workflow_preserves_visual_systems_and_boundaries(self) -> None:
        workflow = json.loads((SKILLS_ROOT / "catalog" / "research_presentation_workflow.json").read_text(encoding="utf-8"))
        systems = {item["id"]: item for item in workflow["visual_systems"]}
        self.assertIn("style_a_magazine_eink", systems)
        self.assertIn("style_b_swiss_international", systems)
        self.assertEqual(len(systems["style_a_magazine_eink"]["theme_options"]), 5)
        self.assertEqual(len(systems["style_b_swiss_international"]["theme_options"]), 4)
        self.assertIn("靛蓝瓷", " ".join(item["label"] for item in systems["style_a_magazine_eink"]["theme_options"]))
        self.assertIn("克莱因蓝", " ".join(item["label"] for item in systems["style_b_swiss_international"]["theme_options"]))
        self.assertIn("validate-swiss-deck.mjs", " ".join(systems["style_b_swiss_international"]["must_follow"]))
        self.assertEqual(workflow["local_tool_mapping"]["official_pptx_tool"], "presentations@openai-primary-runtime")
        self.assertEqual(workflow["local_tool_mapping"]["upstream_runtime_skill"], "guizang-ppt-skill")
        self.assertIn("$CODEX_HOME/skills/guizang-ppt-skill", workflow["local_tool_mapping"]["web_deck_template_root"])
        self.assertIn("image2", workflow["local_tool_mapping"]["image_generation_policy"])

        selection_step = next(item for item in workflow["workflow_steps"] if item["id"] == "visual_system_selection")
        self.assertIn("主题清单", " ".join(selection_step["required_actions"]))
        quality = {item["id"] for item in workflow["quality_rules"]}
        self.assertIn("theme_choice_recorded", quality)

        safety = {item["id"] for item in workflow["safety_rules"]}
        self.assertIn("no_presentation_as_citation_gate", safety)
        self.assertIn("no_paper_figure_contract_bypass", safety)

    def test_pipeline_and_quality_gate_include_presentation_route(self) -> None:
        gates = json.loads((SKILLS_ROOT / "catalog" / "quality_gates.json").read_text(encoding="utf-8"))
        gate = next(item for item in gates["gates"] if item["id"] == "presentation_quality_checked")
        self.assertIn("research-presentation", gate["route_ids"])
        self.assertIn("swiss_locked_layout_validated", gate["required_checks"])

        pipeline = json.loads((SKILLS_ROOT / "catalog" / "research_pipeline_stages.json").read_text(encoding="utf-8"))
        self.assertEqual(
            pipeline["route_stage_sequences"]["research-presentation"],
            ["writing_synthesis", "review_revision", "package_freeze"],
        )
        self.assertIn(
            "presentation_quality_checked",
            pipeline["route_stage_gate_overrides"]["research-presentation"]["writing_synthesis"],
        )


if __name__ == "__main__":
    unittest.main()
