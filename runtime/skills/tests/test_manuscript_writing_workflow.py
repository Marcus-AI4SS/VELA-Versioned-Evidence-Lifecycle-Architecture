from __future__ import annotations



import json

import sys

import unittest

from pathlib import Path





SKILLS_ROOT = Path(__file__).resolve().parents[1]

if str(SKILLS_ROOT) not in sys.path:

    sys.path.insert(0, str(SKILLS_ROOT))





class ManuscriptWritingWorkflowTests(unittest.TestCase):

    def test_manuscript_writing_workflow_contract_validates(self) -> None:

        from scripts.envctl.manuscript_writing_workflow import validate_manuscript_writing_workflow



        result = validate_manuscript_writing_workflow()

        self.assertTrue(result["ok"], result)



    def test_selected_strategy_is_contract_first_social_science_integration(self) -> None:

        payload = json.loads((SKILLS_ROOT / "catalog" / "manuscript_writing_workflow.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["selected_strategy"], "option_b_contract_first_social_science_integration")

        selected = [item for item in payload["adoption_options"] if item["decision"] == "selected"]

        self.assertEqual([item["id"] for item in selected], ["option_b_contract_first_social_science_integration"])



    def test_language_and_discipline_targets_are_explicit(self) -> None:

        payload = json.loads((SKILLS_ROOT / "catalog" / "manuscript_writing_workflow.json").read_text(encoding="utf-8"))

        language_targets = {item["id"]: item for item in payload["language_targets"]}

        discipline_targets = {item["id"]: item for item in payload["discipline_targets"]}



        self.assertIn("Nature-style", language_targets["en_high_impact_journal"]["default_posture"])

        self.assertIn("英文期刊", "".join(language_targets["cn_humanities_social_science"]["reject_when"]))

        self.assertIn("pipeline", " ".join(discipline_targets["computational_social_science_or_method"]["adapted_from_nature"]))

        self.assertIn("forcing STEM", " ".join(discipline_targets["traditional_quantitative_social_science"]["do_not_import"]))

        self.assertIn(

            "statistical significance",

            " ".join(discipline_targets["qualitative_or_interpretive_social_science"]["do_not_import"]),

        )

        source_refs = {item["upstream"]: item for item in payload["source_review_refs"]}

        self.assertIn("Jinze-Lee/codex-skills-workbench", source_refs)

        self.assertIn(

            "chapter plan before chapter prose",

            source_refs["Jinze-Lee/codex-skills-workbench"]["adopted_as"],

        )

        self.assertIn("Leey21/awesome-ai-research-writing", source_refs)

        self.assertIn(

            "conference or journal venue migration checklist as a submission-package adapter",

            source_refs["Leey21/awesome-ai-research-writing"]["adopted_as"],

        )

        self.assertIn("ganzhi-black/humanities-thesis-skill", source_refs)

        self.assertIn(

            "research object, problem, thesis direction, theory, type, and length confirmation",

            source_refs["ganzhi-black/humanities-thesis-skill"]["adopted_as"],

        )

        self.assertIn("WantongC/journal-adapt-writing-skill", source_refs)

        self.assertIn(

            "target-journal corpus as a dynamic style evidence layer for pre-submission polishing",

            source_refs["WantongC/journal-adapt-writing-skill"]["adopted_as"],

        )



        mode_ids = {item["id"] for item in payload["workflow_modes"]}

        self.assertIn("format_sensitive_translation", mode_ids)

        self.assertIn("micro_revision", mode_ids)

        self.assertIn("humanized_surface_check", mode_ids)

        self.assertIn("venue_migration", mode_ids)

        self.assertIn("humanities_thesis_problem_framing", mode_ids)

        self.assertIn("target_journal_adaptation", mode_ids)

        section_ids = {item["id"] for item in payload["section_contracts"]}

        self.assertIn("humanities_thesis_chapter", section_ids)



    def test_publication_and_writing_rules_reference_manuscript_studio(self) -> None:

        publication = json.loads((SKILLS_ROOT / "catalog" / "publication_style_rules.json").read_text(encoding="utf-8"))

        self.assertEqual(publication["writing"]["owner_skill"], "manuscript-writing-studio")

        writing_rule_ids = {item["id"] for item in publication["writing"]["rules"]}

        self.assertIn("language_target_declared", writing_rule_ids)

        self.assertIn("discipline_target_declared", writing_rule_ids)

        self.assertIn("polishing_diagnosis_before_editing", writing_rule_ids)

        safety_ids = {item["id"] for item in json.loads((SKILLS_ROOT / "catalog" / "manuscript_writing_workflow.json").read_text(encoding="utf-8"))["safety_rules"]}

        self.assertIn("no_auto_thesis_studio_for_ordinary_papers", safety_ids)

        self.assertIn("no_unread_corpus_style_extraction", safety_ids)

        self.assertIn("no_journal_style_over_claim_integrity", safety_ids)

        self.assertIn("no_detector_metric_as_goal", safety_ids)

        self.assertIn("no_fake_human_noise", safety_ids)



        quality = json.loads((SKILLS_ROOT / "catalog" / "writing_quality_rules.json").read_text(encoding="utf-8"))

        check_ids = {item["id"] for item in quality["checks"]}

        self.assertIn("discipline_style_declared", check_ids)

        self.assertIn("results_discussion_boundary", check_ids)

        self.assertIn("polishing_failure_mode_diagnosed", check_ids)

        self.assertIn("format_container_preserved", check_ids)

        self.assertIn("minimal_delta_or_rewrite_scope_declared", check_ids)

        self.assertIn("humanized_surface_without_claim_change", check_ids)

        self.assertIn("humanization_locked_items_checked", check_ids)

        self.assertIn("humanization_second_pass_checked", check_ids)

        self.assertIn("data_bound_results_analysis", check_ids)

        self.assertIn("target_journal_style_profile_checked", check_ids)

        self.assertIn("venue_migration_checklist", check_ids)

        self.assertIn("humanities_problem_framing_declared", check_ids)

        self.assertIn("theory_material_fit_checked", check_ids)

        self.assertIn("quote_analysis_followup_checked", check_ids)

        self.assertIn("chapter_progression_checked", check_ids)

        self.assertIn("terminology_consistency_checked", check_ids)

        self.assertIn("footnote_format_and_function_checked", check_ids)



    def test_route_and_runtime_sync_include_manuscript_studio(self) -> None:

        routes = json.loads((SKILLS_ROOT / "catalog" / "routing_table.json").read_text(encoding="utf-8"))

        route = next(item for item in routes["routes"] if item["id"] == "writing-export")

        self.assertEqual(route["skills"][0], "manuscript-writing-studio")

        self.assertIn("英文润色", route["keywords"])

        self.assertIn("去 AI 味", route["keywords"])

        self.assertIn("降 AIGC 检测率", route["keywords"])

        self.assertIn("academic-humanization-studio", route["helper_skills"])

        self.assertIn("写论文", route["keywords"])

        self.assertIn("理论和文本脱节", route["keywords"])

        self.assertIn("目标期刊适配", route["keywords"])

        self.assertIn("journal adapt", route["aliases"])

        self.assertIn("discussion", route["aliases"])



        submission_route = next(item for item in routes["routes"] if item["id"] == "social-science-submission-package")

        self.assertIn("改投别家", submission_route["keywords"])

        self.assertIn("venue migration", submission_route["aliases"])



        sync_script = (SKILLS_ROOT / "scripts" / "sync_research_autopilot_skills.ps1").read_text(encoding="utf-8")
        self.assertIn('"manuscript-writing-studio"', sync_script)
        self.assertIn('"academic-humanization-studio"', sync_script)


        skill_text = (

            SKILLS_ROOT

            / "plugins"

            / "research-autopilot"

            / "skills"

            / "manuscript-writing-studio"

            / "SKILL.md"

        ).read_text(encoding="utf-8")

        self.assertIn("Long-Form Word And Thesis Adapter", skill_text)

        self.assertIn("Humanities Thesis Adapter", skill_text)

        self.assertIn("理论是工具，材料是落点", skill_text)

        self.assertIn("do not silently switch into a thesis-studio", skill_text)

        self.assertIn("Prompt Pattern Adapters", skill_text)

        self.assertIn("Format-sensitive translation", skill_text)

        self.assertIn("Target Journal Adaptation Adapter", skill_text)

        self.assertIn("目标期刊适配润色模式", skill_text)

        self.assertIn("academic-humanization-studio", skill_text)



        humanization_text = (

            SKILLS_ROOT

            / "plugins"

            / "research-autopilot"

            / "skills"

            / "academic-humanization-studio"

            / "SKILL.md"

        ).read_text(encoding="utf-8")

        self.assertIn("locked-items ledger", humanization_text)

        self.assertIn("five-step loop", humanization_text)

        self.assertIn("Do not promise to bypass", humanization_text)



        packager_text = (

            SKILLS_ROOT

            / "plugins"

            / "research-autopilot"

            / "skills"

            / "social-science-submission-packager"

            / "SKILL.md"

        ).read_text(encoding="utf-8")

        self.assertIn("Venue Migration And Resubmission", packager_text)

        self.assertIn("target-requirement checklist", packager_text)





if __name__ == "__main__":

    unittest.main()
