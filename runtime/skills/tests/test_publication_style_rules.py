from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class PublicationStyleRulesTests(unittest.TestCase):
    def test_publication_style_rules_are_schema_valid(self) -> None:
        from scripts.envctl.schema_validation import collect_schema_errors, load_json

        payload = load_json(ROOT / "catalog" / "publication_style_rules.json")
        schema = load_json(ROOT / "schemas" / "publication_style_rules.v1.schema.json")
        self.assertEqual(collect_schema_errors(payload, schema, "publication_style_rules"), [])

    def test_nature_skills_is_adapted_not_installed(self) -> None:
        reviews = json.loads((ROOT / "catalog" / "external_adoption_reviews.json").read_text(encoding="utf-8"))
        item = next(review for review in reviews["reviews"] if review["upstream"] == "Yuan1z0825/nature-skills")
        self.assertEqual(item["decision"], "adapt")
        self.assertIn("figure contract before plotting", item["accepted_patterns"])
        self.assertIn("bulk installing all nature-* skills", item["rejected_patterns"])
        self.assertIn("Nature/CNS journal scope as the default target for social-science writing", item["rejected_patterns"])

    def test_figure_gate_points_to_publication_style_rules(self) -> None:
        gates = json.loads((ROOT / "catalog" / "quality_gates.json").read_text(encoding="utf-8"))
        gate = next(item for item in gates["gates"] if item["id"] == "figure_table_consistency_checked")
        self.assertEqual(gate["helper_rules"], "catalog/publication_style_rules.json")
        self.assertIn("figure_claim_contract", gate["required_checks"])
        self.assertIn("publication_visual_style", gate["required_checks"])

    def test_writing_quality_gate_absorbs_logic_and_overclaim_checks(self) -> None:
        rules = json.loads((ROOT / "catalog" / "writing_quality_rules.json").read_text(encoding="utf-8"))
        gates = json.loads((ROOT / "catalog" / "quality_gates.json").read_text(encoding="utf-8"))
        check_ids = {item["id"] for item in rules["checks"]}
        gate = next(item for item in gates["gates"] if item["id"] == "writing_quality_checked")
        for expected in {
            "section_logic_reader_flow",
            "direct_argument_progression_checked",
            "four_sentence_storyline_checked",
            "method_transition_continuity_checked",
            "claim_strength_and_boundary",
            "contribution_posture_checked",
            "sentence_paragraph_control",
            "rhythm_variety_checked",
            "reader_facing_terms_checked",
            "format_container_preserved",
            "humanized_surface_without_claim_change",
            "target_journal_style_profile_checked",
            "venue_migration_checklist",
        }:
            self.assertIn(expected, check_ids)
            self.assertIn(expected, gate["required_checks"])

    def test_awesome_ai_research_writing_prompt_patterns_are_absorbed(self) -> None:
        reviews = json.loads((ROOT / "catalog" / "external_adoption_reviews.json").read_text(encoding="utf-8"))
        item = next(review for review in reviews["reviews"] if review["upstream"] == "Leey21/awesome-ai-research-writing")
        self.assertEqual(item["decision"], "adapt")
        self.assertIn("format-sensitive LaTeX versus Word translation", item["accepted_patterns"])
        self.assertIn("conference or journal venue migration checklist", item["accepted_patterns"])
        self.assertIn("generic prompt bundle copied verbatim", item["rejected_patterns"])

        publication = json.loads((ROOT / "catalog" / "publication_style_rules.json").read_text(encoding="utf-8"))
        figure_rule_ids = {item["id"] for item in publication["figure_table"]["rules"]}
        writing_rule_ids = {item["id"] for item in publication["writing"]["rules"]}
        self.assertIn("chart_type_selection_by_evidence_need", figure_rule_ids)
        self.assertIn("figure_table_title_caption_plainness", figure_rule_ids)
        self.assertIn("format_sensitive_translation_container", writing_rule_ids)
        self.assertIn("venue_migration_checklist", writing_rule_ids)

    def test_humanities_thesis_patterns_are_selectively_absorbed(self) -> None:
        reviews = json.loads((ROOT / "catalog" / "external_adoption_reviews.json").read_text(encoding="utf-8"))
        item = next(review for review in reviews["reviews"] if review["upstream"] == "ganzhi-black/humanities-thesis-skill")
        self.assertEqual(item["decision"], "adapt")
        self.assertIn("structured intake before humanities thesis drafting", item["accepted_patterns"])
        self.assertIn("using upstream search.py as a replacement for local CNKI, Google Scholar, OpenAlex, Zotero, or citation-verifier workflows", item["rejected_patterns"])

        publication = json.loads((ROOT / "catalog" / "publication_style_rules.json").read_text(encoding="utf-8"))
        writing_rule_ids = {item["id"] for item in publication["writing"]["rules"]}
        self.assertIn("humanities_problem_framing_declared", writing_rule_ids)
        self.assertIn("theory_material_fit_checked", writing_rule_ids)
        self.assertIn("quote_analysis_followup_checked", writing_rule_ids)
        self.assertIn("chapter_progression_checked", writing_rule_ids)
        self.assertIn("terminology_consistency_checked", writing_rule_ids)
        self.assertIn("footnote_format_and_function_checked", writing_rule_ids)

        gate = next(item for item in json.loads((ROOT / "catalog" / "quality_gates.json").read_text(encoding="utf-8"))["gates"] if item["id"] == "writing_quality_checked")
        self.assertIn("theory_material_fit_checked", gate["required_checks"])
        self.assertIn("footnote_format_and_function_checked", gate["required_checks"])

    def test_journal_adapt_patterns_are_selectively_absorbed(self) -> None:
        reviews = json.loads((ROOT / "catalog" / "external_adoption_reviews.json").read_text(encoding="utf-8"))
        item = next(review for review in reviews["reviews"] if review["upstream"] == "WantongC/journal-adapt-writing-skill")
        self.assertEqual(item["decision"], "adapt")
        self.assertIn("aggregated journal style profile with conflict table and red flags", item["accepted_patterns"])
        self.assertIn("installing upstream journal-adapt as a separate active runtime route", item["rejected_patterns"])

        publication = json.loads((ROOT / "catalog" / "publication_style_rules.json").read_text(encoding="utf-8"))
        writing_rule_ids = {item["id"] for item in publication["writing"]["rules"]}
        self.assertIn("target_journal_style_profile_checked", writing_rule_ids)
        self.assertIn("WantongC/journal-adapt-writing-skill", publication["source_review_ref"])

    def test_stop_slop_is_absorbed_as_pattern_only(self) -> None:
        reviews = json.loads((ROOT / "catalog" / "external_adoption_reviews.json").read_text(encoding="utf-8"))
        item = next(review for review in reviews["reviews"] if review["upstream"] == "hardikpandya/stop-slop")
        self.assertEqual(item["decision"], "adapt")
        self.assertIn("throat-clearing opener removal", item["accepted_patterns"])
        self.assertIn("blanket ban on all adverbs or passive voice in academic prose", item["rejected_patterns"])

        quality = json.loads((ROOT / "catalog" / "writing_quality_rules.json").read_text(encoding="utf-8"))
        self.assertIn("Let me be clear", quality["banned_phrases"])
        self.assertIn("not X but Y", quality["surface_structure_watch_patterns"])
        self.assertIn("不是...而是...", quality["surface_structure_watch_patterns"])
        self.assertIn("uniform four-to-five-line paragraph blocks", quality["surface_structure_watch_patterns"])
        self.assertIn("reader-facing internal engineering terms", quality["surface_structure_watch_patterns"])

        publication = json.loads((ROOT / "catalog" / "publication_style_rules.json").read_text(encoding="utf-8"))
        self.assertIn("hardikpandya/stop-slop", publication["source_review_ref"])

    def test_direct_argument_and_term_rules_are_publication_contracts(self) -> None:
        publication = json.loads((ROOT / "catalog" / "publication_style_rules.json").read_text(encoding="utf-8"))
        writing_rule_ids = {item["id"] for item in publication["writing"]["rules"]}
        for expected in {
            "direct_argument_progression_checked",
            "four_sentence_storyline_checked",
            "method_transition_continuity_checked",
            "contribution_posture_checked",
            "rhythm_variety_checked",
            "reader_facing_terms_checked",
        }:
            self.assertIn(expected, writing_rule_ids)

        reader_rule = next(item for item in publication["writing"]["rules"] if item["id"] == "reader_facing_terms_checked")
        self.assertIn("中文文献", reader_rule["requirement"])
        self.assertIn("不能先查英文再自行翻译", reader_rule["requirement"])

    def test_social_science_adaptation_rejects_biomedical_defaults(self) -> None:
        payload = json.loads((ROOT / "catalog" / "publication_style_rules.json").read_text(encoding="utf-8"))
        rejected = "\n".join(payload["rejected_defaults"])
        self.assertIn("医学", rejected)
        self.assertIn("湿实验", rejected)
        self.assertIn("不整包安装 nature-skills", rejected)

    def test_research_autopilot_references_publication_style_rules(self) -> None:
        skill_text = (
            ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "research-autopilot"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("publication_style_rules.json", skill_text)
        self.assertIn("claim_strength_and_boundary", skill_text)
        self.assertIn("不得把 Nature/CNS、医学、理工或湿实验标准直接当作社科默认标准", skill_text)


if __name__ == "__main__":
    unittest.main()
