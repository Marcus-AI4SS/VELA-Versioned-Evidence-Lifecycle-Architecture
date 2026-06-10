from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"


class ResearchFigureStudioTests(unittest.TestCase):
    def test_research_figure_studio_is_registered_and_routed(self) -> None:
        skill_path = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "research-figure-studio"
            / "SKILL.md"
        )
        self.assertTrue(skill_path.exists())

        catalog = json.loads((SKILLS_ROOT / "catalog" / "skill_catalog.json").read_text(encoding="utf-8"))
        self.assertIn("research-figure-studio", catalog["skills"])

        routing = json.loads((SKILLS_ROOT / "catalog" / "routing_table.json").read_text(encoding="utf-8"))
        routes = {item["id"]: item for item in routing["routes"]}
        self.assertIn("research-figure-design", routes)
        self.assertIn("research-figure-studio", routes["research-figure-design"]["skills"])
        self.assertIn("image2", routes["research-figure-design"]["keywords"])

    def test_image2_is_allowed_with_locked_structure(self) -> None:
        skill_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "research-figure-studio"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        contract_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "research-figure-studio"
            / "references"
            / "image2-figure-contract.md"
        ).read_text(encoding="utf-8")
        self.assertIn("image2 is allowed", skill_text)
        self.assertIn("Do not use image2 to invent", contract_text)
        self.assertIn("social_science_nature_red_blue_rainbow", skill_text)
        self.assertIn("red-blue anchored Nature-style rainbow color palette", skill_text)
        self.assertIn("no figure title inside the image", contract_text)
        self.assertIn("no overlapping text", contract_text)
        self.assertIn("all text must be readable", skill_text.lower())
        self.assertIn("Architecture Figure Adapter", skill_text)

    def test_figure_table_studio_is_upgraded_and_distinct(self) -> None:
        skill_path = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "figure-table-studio"
            / "SKILL.md"
        )
        text = skill_path.read_text(encoding="utf-8")
        self.assertIn("top-journal-quality", text)
        self.assertIn("Use `research-figure-studio` for mechanism diagrams", text)
        self.assertIn("Event-Study and Coefficient Plot Rules", text)

    def test_publication_rules_include_top_journal_and_image2_contract(self) -> None:
        rules = json.loads((SKILLS_ROOT / "catalog" / "publication_style_rules.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in rules["figure_table"]["rules"]}
        self.assertIn("top_journal_empirical_graph_conventions", ids)
        self.assertIn("image2_locked_structure_contract", ids)
        self.assertIn("figure_brief_before_rendering", ids)
        self.assertIn("figure_style_preset_selected", ids)
        self.assertIn("red_blue_rainbow_palette_checked", ids)
        self.assertIn("title_caption_outside_image_checked", ids)
        self.assertIn("visual_overlap_checked", ids)
        self.assertIn("chart_type_selection_by_evidence_need", ids)
        self.assertIn("figure_table_title_caption_plainness", ids)

        gates = json.loads((SKILLS_ROOT / "catalog" / "quality_gates.json").read_text(encoding="utf-8"))
        gate = next(item for item in gates["gates"] if item["id"] == "figure_table_consistency_checked")
        self.assertIn("research-figure-design", gate["route_ids"])
        self.assertIn("image2_locked_structure_contract", gate["required_checks"])
        self.assertIn("figure_style_preset_selected", gate["required_checks"])
        self.assertIn("visual_overlap_checked", gate["required_checks"])
        self.assertIn("chart_type_selection_by_evidence_need", gate["required_checks"])

    def test_research_figure_route_creates_then_reviews_figures(self) -> None:
        stages = json.loads((SKILLS_ROOT / "catalog" / "research_pipeline_stages.json").read_text(encoding="utf-8"))
        self.assertEqual(
            stages["route_stage_sequences"]["research-figure-design"],
            ["writing_synthesis", "review_revision"],
        )
        overrides = stages["route_stage_gate_overrides"]["research-figure-design"]
        self.assertIn("figure_table_consistency_checked", overrides["writing_synthesis"])
        self.assertIn("figure_table_consistency_checked", overrides["review_revision"])

    def test_sync_script_includes_both_figure_skills(self) -> None:
        sync_script = (SKILLS_ROOT / "scripts" / "sync_research_autopilot_skills.ps1").read_text(encoding="utf-8")
        self.assertIn('"research-figure-studio"', sync_script)
        self.assertIn('"figure-table-studio"', sync_script)


if __name__ == "__main__":
    unittest.main()
