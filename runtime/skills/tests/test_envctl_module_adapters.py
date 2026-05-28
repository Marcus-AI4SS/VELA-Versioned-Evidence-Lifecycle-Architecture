from __future__ import annotations



import argparse

import json

import sys

import tempfile

import unittest

from pathlib import Path





ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



from scripts.envctl.agent_contracts import build_agent_contract_result

from scripts.envctl.project_initializer import ensure_project_contract

from scripts.envctl.pipeline_contracts import build_pipeline_contract_result

from scripts.envctl.schema_validation import collect_schema_errors, load_json

from scripts.envctl.team_plan import build_team_plan_result





class EnvctlModuleAdapterTests(unittest.TestCase):

    def test_agent_contract_result_uses_validator_envelope(self) -> None:

        result = build_agent_contract_result()

        schema = load_json(ROOT / "schemas" / "validator_result.schema.json")

        self.assertEqual(collect_schema_errors(result, schema, "agent_contract_result"), [])

        self.assertTrue(result["ok"])

        self.assertEqual(result["validator"], "validate_agents_contract")



    def test_pipeline_contract_result_uses_validator_envelope(self) -> None:

        result = build_pipeline_contract_result()

        schema = load_json(ROOT / "schemas" / "validator_result.schema.json")

        self.assertEqual(collect_schema_errors(result, schema, "pipeline_contract_result"), [])

        self.assertTrue(result["ok"])

        self.assertEqual(result["validator"], "validate_research_pipeline")



    def test_team_plan_module_returns_structured_error_without_exiting(self) -> None:

        result = build_team_plan_result(

            argparse.Namespace(

                project_root=ROOT / "__missing_project__",

                route_id="literature-review",

                project_type=None,

                stage="planning",

                run_id=None,

                target_item_count=0,

                work_unit=[],

                deliverable_type=[],

                sync_target=[],

                explicit_project_mode="auto",

                needs_clarification=False,

                route_confirmation_required=False,

                route_confirmation_question="",

                user_confirmed_route=False,

                quality_gate=None,

                conflict_resolution="project-manager",

                merge_owner=None,

                user_veto_window="confirmed-in-thread",

                bootstrap=False,

                overwrite=False,

                auto_init_project_contract=True,

            )

        )

        self.assertFalse(result["ok"])

        self.assertIn("Project root does not exist", result["error"])



    def test_team_plan_auto_initializes_project_contract(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "研究项目"

            project_root.mkdir()

            result = build_team_plan_result(

                argparse.Namespace(

                    project_root=project_root,

                    route_id="literature-review",

                    project_type=None,

                    stage="planning",

                    run_id=None,

                    target_item_count=20,

                    work_unit=["discovery"],

                    deliverable_type=["literature_synthesis"],

                    sync_target=["zotero"],

                    explicit_project_mode="force_multi_agent",

                    needs_clarification=False,

                    route_confirmation_required=False,

                    route_confirmation_question="",

                    user_confirmed_route=False,

                    quality_gate=None,

                    conflict_resolution="project-manager",

                    merge_owner=None,

                    user_veto_window="confirmed-in-thread",

                    bootstrap=False,

                    overwrite=False,

                    auto_init_project_contract=True,

                )

            )

            self.assertTrue(result["ok"], result)

            self.assertTrue((project_root / "AGENTS.md").exists())

            self.assertTrue((project_root / ".codex" / "agents" / "literature-producer.json").exists())

            self.assertIn("literature-producer", result["selected_producers"])

            self.assertIn("reviewer", result["selected_reviewers"])

            self.assertIsNotNone(result["project_contract_auto_init"])



    def test_team_plan_repairs_disabled_project_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "旧项目"

            ensure_project_contract(project_root)

            agent_path = project_root / ".codex" / "agents" / "literature-producer.json"

            agent_payload = json.loads(agent_path.read_text(encoding="utf-8"))

            agent_payload["enabled"] = False

            agent_path.write_text(json.dumps(agent_payload, ensure_ascii=False, indent=2), encoding="utf-8")



            result = build_team_plan_result(

                argparse.Namespace(

                    project_root=project_root,

                    route_id="literature-review",

                    project_type=None,

                    stage="planning",

                    run_id=None,

                    target_item_count=1,

                    work_unit=["discovery"],

                    deliverable_type=["literature_synthesis"],

                    sync_target=["zotero"],

                    explicit_project_mode="force_multi_agent",

                    needs_clarification=False,

                    route_confirmation_required=False,

                    route_confirmation_question="",

                    user_confirmed_route=False,

                    quality_gate=None,

                    conflict_resolution="project-manager",

                    merge_owner=None,

                    user_veto_window="confirmed-in-thread",

                    bootstrap=False,

                    overwrite=False,

                    auto_init_project_contract=True,

                )

            )

            self.assertTrue(result["ok"], result)

            self.assertIn("literature-producer", result["selected_producers"])

            repaired_payload = json.loads(agent_path.read_text(encoding="utf-8"))

            self.assertIs(repaired_payload["enabled"], True)

            self.assertIn(".codex/agents/literature-producer.json", result["project_contract_auto_init"]["updated_files"])



    def test_team_plan_blocks_unconfirmed_route_when_confirmation_is_required(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "待确认项目"

            project_root.mkdir()

            result = build_team_plan_result(

                argparse.Namespace(

                    project_root=project_root,

                    route_id="literature-review",

                    project_type=None,

                    stage="planning",

                    run_id=None,

                    target_item_count=20,

                    work_unit=["discovery"],

                    deliverable_type=["literature_synthesis"],

                    sync_target=["zotero"],

                    explicit_project_mode="force_multi_agent",

                    needs_clarification=False,

                    route_confirmation_required=True,

                    route_confirmation_question="确认进入 literature-review 路线吗？",

                    user_confirmed_route=False,

                    quality_gate=None,

                    conflict_resolution="project-manager",

                    merge_owner=None,

                    user_veto_window="confirmed-in-thread",

                    bootstrap=False,

                    overwrite=False,

                    auto_init_project_contract=True,

                )

            )



        self.assertFalse(result["ok"])

        self.assertEqual(result["error"], "route-confirmation-required")

        self.assertIn("确认进入 literature-review 路线吗", result["next_step"])





if __name__ == "__main__":

    unittest.main()
