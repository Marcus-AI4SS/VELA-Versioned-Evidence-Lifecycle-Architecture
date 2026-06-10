from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))


class ScientificFigureWorkflowTests(unittest.TestCase):
    def test_scientific_figure_workflow_contract_validates(self) -> None:
        from scripts.envctl.scientific_figure_workflow import validate_scientific_figure_workflow

        result = validate_scientific_figure_workflow()
        self.assertTrue(result["ok"], result)

    def test_selected_strategy_is_contract_first_integration(self) -> None:
        payload = json.loads((SKILLS_ROOT / "catalog" / "scientific_figure_workflow.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["selected_strategy"], "option_c_contract_first_integration")
        selected = [item for item in payload["adoption_options"] if item["decision"] == "selected"]
        self.assertEqual([item["id"] for item in selected], ["option_c_contract_first_integration"])

    def test_empirical_and_conceptual_modes_have_distinct_owners(self) -> None:
        payload = json.loads((SKILLS_ROOT / "catalog" / "scientific_figure_workflow.json").read_text(encoding="utf-8"))
        modes = {item["id"]: item for item in payload["workflow_modes"]}
        self.assertEqual(modes["empirical_tabular_figure"]["owner_skill"], "figure-table-studio")
        self.assertEqual(modes["conceptual_mechanism_figure"]["owner_skill"], "research-figure-studio")
        self.assertIn("data_health_report", modes["empirical_tabular_figure"]["required_steps"])
        self.assertNotIn("data_health_report", modes["conceptual_mechanism_figure"]["required_steps"])

    def test_publication_rules_and_gate_include_scientific_figure_norms(self) -> None:
        rules = json.loads((SKILLS_ROOT / "catalog" / "publication_style_rules.json").read_text(encoding="utf-8"))
        rule_ids = {item["id"] for item in rules["figure_table"]["rules"]}
        expected = {
            "figure_style_preset_selected",
            "red_blue_rainbow_palette_checked",
            "title_caption_outside_image_checked",
            "visual_overlap_checked",
            "data_health_before_plotting",
            "process_data_traceability",
            "justified_statistics_annotations",
            "caption_what_how_so_what",
            "multi_format_export_and_editable_source",
            "typography_font_size_specification",
            "figure_size_resolution_contract",
            "renderer_selection_by_deliverable",
            "r_plot_adapter_output_bundle",
            "chart_type_selection_by_evidence_need",
            "figure_table_title_caption_plainness",
        }
        self.assertTrue(expected <= rule_ids)

        gates = json.loads((SKILLS_ROOT / "catalog" / "quality_gates.json").read_text(encoding="utf-8"))
        gate = next(item for item in gates["gates"] if item["id"] == "figure_table_consistency_checked")
        self.assertEqual(gate["required_report"], "logs/quality-gates/figure-table-report.json")
        self.assertTrue(expected <= set(gate["required_checks"]))

    def test_external_review_records_adapt_not_install(self) -> None:
        reviews = json.loads((SKILLS_ROOT / "catalog" / "external_adoption_reviews.json").read_text(encoding="utf-8"))
        item = next(review for review in reviews["reviews"] if review["upstream"] == "myzhao0114-del/scientific-figure-skill")
        self.assertEqual(item["decision"], "adapt")
        self.assertIn("data health report before plotting", item["accepted_patterns"])
        self.assertIn("bulk installing upstream skill into runtime", item["rejected_patterns"])

    def test_typography_contract_absorbs_builtin_font_and_size_standards(self) -> None:
        payload = json.loads((SKILLS_ROOT / "catalog" / "scientific_figure_workflow.json").read_text(encoding="utf-8"))
        typography = payload["typography_contract"]
        self.assertEqual(typography["cn_serif_fallback"][:2], ["SimSun", "Songti SC"])
        self.assertEqual(typography["en_serif_fallback"][0], "Times New Roman")
        self.assertEqual(typography["matplotlib_font_sizes_pt"]["base"], 10)
        self.assertEqual(typography["matplotlib_font_sizes_pt"]["axis_label"], 10)
        self.assertEqual(typography["matplotlib_font_sizes_pt"]["tick_label"], 9)
        self.assertEqual(typography["matplotlib_font_sizes_pt"]["legend"], 9)
        self.assertEqual(typography["matplotlib_font_sizes_pt"]["caption"], 9)
        self.assertEqual(typography["matplotlib_font_sizes_pt"]["significance_mark"], 10)
        self.assertEqual(typography["figure_sizes_in"]["single_column"], [3.5, 2.6])
        self.assertEqual(typography["figure_sizes_in"]["double_column"], [7.2, 4.0])
        self.assertEqual(typography["dpi"], 300)

    def test_scientific_workflow_links_style_preset_contract(self) -> None:
        payload = json.loads((SKILLS_ROOT / "catalog" / "scientific_figure_workflow.json").read_text(encoding="utf-8"))
        style_contract = payload["style_preset_contract"]
        self.assertEqual(style_contract["catalog"], "catalog/figure_style_presets.json")
        self.assertEqual(style_contract["schema"], "schemas/figure_style_presets.v1.schema.json")
        self.assertEqual(style_contract["default_formal_research_figure"], "social_science_nature_red_blue_rainbow")
        self.assertEqual(style_contract["default_empirical_figure"], "nature_empirical_red_blue_rainbow")
        self.assertIn("not an independent runtime entrypoint", style_contract["external_visual_source_role"])

    def test_workbench_plotting_adapters_are_absorbed_without_new_route(self) -> None:
        payload = json.loads((SKILLS_ROOT / "catalog" / "scientific_figure_workflow.json").read_text(encoding="utf-8"))
        source_refs = {item["upstream"]: item for item in payload["source_review_refs"]}
        self.assertIn("Jinze-Lee/codex-skills-workbench", source_refs)
        self.assertIn(
            "plotting_tool_selection_by_deliverable",
            source_refs["Jinze-Lee/codex-skills-workbench"]["adopted_as"],
        )

        style_rule_ids = {item["id"] for item in payload["style_rules"]}
        self.assertIn("renderer_selection_by_deliverable", style_rule_ids)
        self.assertIn("r_plot_family_output_bundle", style_rule_ids)
        self.assertIn("ggplot_text_export_diagnostics", style_rule_ids)
        self.assertIn("chart_type_selection_by_evidence_need", style_rule_ids)
        self.assertIn("figure_table_title_caption_plainness", style_rule_ids)

        skill_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "figure-table-studio"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Workbench Plot Adapters", skill_text)
        self.assertIn("Ecology-specific patterns", skill_text)


if __name__ == "__main__":
    unittest.main()
