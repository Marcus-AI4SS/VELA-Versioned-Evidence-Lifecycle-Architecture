from __future__ import annotations



import json

import sys

import unittest

from pathlib import Path





SKILLS_ROOT = Path(__file__).resolve().parents[1]

if str(SKILLS_ROOT) not in sys.path:

    sys.path.insert(0, str(SKILLS_ROOT))





class EmpiricalQuantWorkflowTests(unittest.TestCase):

    def test_empirical_quant_workflow_contract_validates(self) -> None:

        from scripts.envctl.empirical_quant_workflow import validate_empirical_quant_workflow



        result = validate_empirical_quant_workflow()

        self.assertTrue(result["ok"], result)



    def test_external_repo_is_adapted_not_bulk_installed(self) -> None:

        payload = json.loads((SKILLS_ROOT / "catalog" / "empirical_quant_workflow.json").read_text(encoding="utf-8"))

        self.assertEqual(payload["selected_strategy"], "option_b_contract_first_empirical_quant_integration")

        source_refs = {item["upstream"]: item for item in payload["source_review_refs"]}

        self.assertIn("brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research", source_refs)

        self.assertIn("bulk installing all external empirical or humanizer skills into runtime", source_refs["brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research"]["not_adopted"])



    def test_modern_causal_design_defaults_are_encoded(self) -> None:

        payload = json.loads((SKILLS_ROOT / "catalog" / "empirical_quant_workflow.json").read_text(encoding="utf-8"))

        design_families = {item["id"]: item for item in payload["design_families"]}

        did = design_families["difference_in_differences"]

        iv = design_families["instrumental_variables"]

        rdd = design_families["regression_discontinuity"]

        shift_share = design_families["shift_share_bartik"]

        ddd = design_families["triple_difference"]



        self.assertIn("Callaway-Sant'Anna group-time ATT for staggered adoption", did["preferred_estimators"])

        self.assertIn("naive TWFE as the only estimator under staggered treatment", did["red_flags"])

        self.assertIn("Anderson-Rubin or weak-IV robust confidence sets when instruments are weak", iv["preferred_estimators"])

        self.assertIn("high-order global polynomial", rdd["red_flags"])

        self.assertIn("Rotemberg weight audit when identification relies on exposure shares", shift_share["preferred_estimators"])

        self.assertIn("DDD with transparent three-way interaction interpretation", ddd["preferred_estimators"])



    def test_stata_ecosystem_is_encoded_as_traceable_tool_chain(self) -> None:

        payload = json.loads((SKILLS_ROOT / "catalog" / "empirical_quant_workflow.json").read_text(encoding="utf-8"))

        ecosystems = {item["id"]: item for item in payload["tool_ecosystems"]}

        stata = ecosystems["stata_aer_replication_pipeline"]

        joined = " ".join(

            stata["required_conventions"] + stata["core_packages_or_commands"] + stata["pipeline_files"] + stata["red_flags"]

        )

        for token in ["run_all.do", "00_install_packages.do", "reghdfe", "csdid", "ivreg2", "rdrobust", "esttab"]:

            self.assertIn(token, joined)



        safety_ids = {item["id"] for item in payload["safety_rules"]}

        self.assertIn("no_stata_output_without_script_trace", safety_ids)

        self.assertIn("no_stata_default_without_project_need", safety_ids)

        self.assertIn("no_economics_standard_as_universal_default", safety_ids)

        self.assertIn("no_naive_twfe_as_staggered_default", safety_ids)

        self.assertIn("no_detector_metric_as_goal", safety_ids)

        self.assertIn("Use only when the project already uses Stata", stata["use_when"])



    def test_quant_route_uses_empirical_contract_and_gate(self) -> None:

        routing = json.loads((SKILLS_ROOT / "catalog" / "routing_table.json").read_text(encoding="utf-8"))

        route = next(item for item in routing["routes"] if item["id"] == "empirical-quant")

        self.assertIn("causal_identification_checked", route["quality_gate_required"])

        self.assertIn("DID", route["keywords"])

        self.assertIn("AER", route["aliases"])

        self.assertIn("reghdfe", route["keywords"])

        self.assertIn("Stata replication pipeline", route["aliases"])

        self.assertIn("academic-humanization-studio", route["helper_skills"])



        stages = json.loads((SKILLS_ROOT / "catalog" / "research_pipeline_stages.json").read_text(encoding="utf-8"))

        self.assertIn("causal_identification_checked", stages["route_stage_gate_overrides"]["empirical-quant"]["analysis_execution"])



        gates = json.loads((SKILLS_ROOT / "catalog" / "quality_gates.json").read_text(encoding="utf-8"))

        gate = next(item for item in gates["gates"] if item["id"] == "causal_identification_checked")

        self.assertEqual(gate["helper_rules"], "catalog/empirical_quant_workflow.json")

        self.assertIn("causal_identification_red_flags", gate["required_checks"])



    def test_quant_skill_source_is_present_for_runtime_sync(self) -> None:

        skill_path = SKILLS_ROOT / "plugins" / "research-autopilot" / "skills" / "quant-analysis" / "SKILL.md"

        self.assertTrue(skill_path.exists())

        text = skill_path.read_text(encoding="utf-8")

        self.assertIn("empirical_quant_workflow.json", text)

        self.assertIn("Academic De-AI Surface Audit", text)

        self.assertIn("Stata Ecosystem", text)

        self.assertIn("reghdfe", text)





if __name__ == "__main__":

    unittest.main()
