from __future__ import annotations

import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.team_planner import build_review_pairs, load_route_playbook, pick_producers
from scripts.validate_vela_contracts import collect_contract_errors


def card(
    route_id: str,
    *,
    target_item_count: int = 0,
    work_units: list[str] | None = None,
    deliverable_types: list[str] | None = None,
    sync_targets: list[str] | None = None,
) -> dict:
    return {
        "route_id": route_id,
        "target_item_count": target_item_count,
        "work_units": work_units or [],
        "deliverable_types": deliverable_types or [],
        "sync_targets": sync_targets or [],
        "explicit_project_mode": "auto",
        "needs_clarification": False,
        "route_confirmation_required": False,
        "route_confirmation_question": "",
        "user_confirmed_route": False,
    }


class EnvctlContractTests(unittest.TestCase):
    def test_scholar_nuwa_distillation_uses_user_confirmed_sources_not_doi_gate(self) -> None:
        routing = json.loads((ROOT / "catalog" / "routing_table.json").read_text(encoding="utf-8"))
        pipeline = json.loads((ROOT / "catalog" / "research_pipeline_stages.json").read_text(encoding="utf-8"))

        route = next(item for item in routing["routes"] if item["id"] == "scholar-persona-distillation")
        self.assertIn("用户明确确认", route["next_step"])
        self.assertIn("公开画像/公开情境材料层", route["next_step"])
        self.assertIn("不能替代论文证据", route["next_step"])
        self.assertIn("public-context-candidates.json", route["next_step"])
        self.assertIn("正式论文写作和参考文献链仍必须走引用证据核验", route["next_step"])
        self.assertIn("蒸馏不以 DOI 为硬门槛", route["next_step"])
        self.assertIn("DOI 豁免证据", route["next_step"])
        self.assertNotIn("再把结果作为 source-json 输入", route["next_step"])
        self.assertIn("social-platform-mcp", route["mcp"])

        gates = pipeline["route_stage_gate_overrides"]["scholar-persona-distillation"]["citation_verification"]
        self.assertEqual(gates, ["source_authenticity_confirmed"])

    def test_formal_writing_routes_keep_doi_gate(self) -> None:
        pipeline = json.loads((ROOT / "catalog" / "research_pipeline_stages.json").read_text(encoding="utf-8"))
        overrides = pipeline["route_stage_gate_overrides"]

        for route_id in ["single-paper-review", "literature-review", "social-science-submission-package"]:
            with self.subTest(route_id=route_id):
                self.assertIn("doi_and_metadata_verified", overrides[route_id]["citation_verification"])

    def test_citation_gate_allows_approved_doi_waivers(self) -> None:
        from scripts.envctl.schema_validation import collect_schema_errors, load_json

        rules = json.loads((ROOT / "catalog" / "citation_verification_rules.json").read_text(encoding="utf-8"))
        schema = load_json(ROOT / "schemas" / "citation_verification_report.schema.json")
        report = {
            "schema_version": "citation_verification_report.v1",
            "status": "pass",
            "checked_at": "2026-05-15T00:00:00+08:00",
            "references": [
                {
                    "id": "r1",
                    "author": "Author",
                    "year": "2026",
                    "title": "Verified PDF Paper",
                    "source": "Journal",
                    "doi": None,
                    "verified": True,
                    "verification_source": "uploaded PDF",
                    "verification_basis": "pdf_fulltext",
                    "pdf_fulltext_evidence": {
                        "file_path": "outputs/inbox/reference-fulltext/pdfs/r1.pdf",
                        "source_type": "user_uploaded_pdf",
                        "title_match": True,
                        "author_or_source_match": True,
                        "page_count": 12,
                        "readable": True,
                    },
                },
                {
                    "id": "r2",
                    "author": "Author",
                    "year": "2025",
                    "title": "User Provided Paper",
                    "source": "Journal",
                    "doi": None,
                    "verified": True,
                    "verification_source": "user-provided bibliography export",
                    "verification_basis": "user_provided_source",
                    "doi_waiver_evidence": {
                        "waiver_type": "user_provided_source",
                        "evidence_source": "user-provided RIS export",
                        "locator": "outputs/inbox/reference-fulltext/metadata/user-export.ris",
                        "title_match": True,
                        "author_or_source_match": True,
                        "year_or_source_match": True,
                        "checked_at": "2026-05-15T00:00:00+08:00",
                    },
                },
                {
                    "id": "r3",
                    "author": "Author",
                    "year": "2024",
                    "title": "Indexed Paper",
                    "source": "Journal",
                    "doi": None,
                    "verified": True,
                    "verification_source": "OpenAlex",
                    "verification_basis": "public_academic_index",
                    "doi_waiver_evidence": {
                        "waiver_type": "public_academic_index_record",
                        "evidence_source": "OpenAlex",
                        "locator": "https://openalex.org/W0000000000",
                        "title_match": True,
                        "author_or_source_match": True,
                        "year_or_source_match": True,
                        "checked_at": "2026-05-15T00:00:00+08:00",
                    },
                },
            ],
            "errors": [],
        }

        self.assertNotIn("doi", rules["required_reference_fields"])
        self.assertIn("doi", rules["optional_reference_fields"])
        self.assertIn("doi_waiver_evidence", rules["optional_reference_fields"])
        self.assertIn("all_formal_references_have_doi_or_approved_doi_waiver", rules["pass_requires"])
        self.assertEqual(
            set(rules["doi_waiver_policy"]["applies_to"]),
            {"user_provided_source", "complete_pdf_fulltext", "public_academic_index_record"},
        )
        self.assertEqual(collect_schema_errors(report, schema, "pdf-fulltext-citation-report"), [])

    def test_project_citation_gate_accepts_public_index_waiver_without_doi(self) -> None:
        from scripts.envctl.pipeline_contracts import build_pipeline_contract_result

        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            (project / "logs" / "quality-gates").mkdir(parents=True)
            (project / "research-map.md").write_text("# Test\n", encoding="utf-8")
            (project / "evidence-ledger.yaml").write_text("items: []\n", encoding="utf-8")
            (project / "material-passport.yaml").write_text(
                "route_id: general-research\ncurrent_stage: research_design\ndata_access_level: public_open\n",
                encoding="utf-8",
            )
            (project / "logs" / "quality-gates" / "pipeline-status.json").write_text(
                json.dumps(
                    {
                        "route_id": "general-research",
                        "current_stage": "research_design",
                        "completed_stages": [],
                        "allowed_to_advance": False,
                        "gate_decisions": {"doi_and_metadata_verified": "pass"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (project / "logs" / "quality-gates" / "citation-verification-report.json").write_text(
                json.dumps(
                    {
                        "schema_version": "citation_verification_report.v1",
                        "status": "pass",
                        "checked_at": "2026-05-15T00:00:00+08:00",
                        "references": [
                            {
                                "id": "r1",
                                "author": "Author",
                                "year": "2024",
                                "title": "Indexed Paper",
                                "source": "Journal",
                                "doi": None,
                                "verified": True,
                                "verification_source": "Google Scholar",
                                "verification_basis": "public_academic_index",
                                "doi_waiver_evidence": {
                                    "waiver_type": "public_academic_index_record",
                                    "evidence_source": "Google Scholar",
                                    "locator": "https://scholar.google.com/scholar?q=%22Indexed+Paper%22",
                                    "title_match": True,
                                    "author_or_source_match": True,
                                    "year_or_source_match": True,
                                    "checked_at": "2026-05-15T00:00:00+08:00",
                                },
                            }
                        ],
                        "errors": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = build_pipeline_contract_result(project)

        self.assertEqual(result["errors"], [])

    def test_vela_contracts_are_schema_valid(self) -> None:
        errors, warnings, payload = collect_contract_errors()
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(payload["playbook_count"], 13)
        self.assertEqual(payload["project_initializer_agents"], 11)

    def test_route_confirmation_and_research_progression_are_controlled(self) -> None:
        scope_rules = json.loads((ROOT / "catalog" / "project_scope_rules.json").read_text(encoding="utf-8"))
        pipeline = json.loads((ROOT / "catalog" / "research_pipeline_stages.json").read_text(encoding="utf-8"))

        self.assertEqual(scope_rules["route_confirmation_policy"]["default_for_new_chain"], "ask_before_entering_route")
        self.assertTrue(scope_rules["route_confirmation_policy"]["block_when_required_but_unconfirmed"])
        for field in ["route_confirmation_required", "route_confirmation_question", "user_confirmed_route"]:
            self.assertIn(field, scope_rules["clarification_card_fields"])

        chain = pipeline["research_logic_chain"]
        self.assertTrue(chain["ask_before_advancing"])
        self.assertGreaterEqual(len(chain["milestones"]), 10)
        milestone_ids = [item["id"] for item in chain["milestones"]]
        self.assertIn("empirical_or_field_material_ready", milestone_ids)
        self.assertIn("pdf_citation_annotation_ready", milestone_ids)
        self.assertIn("final_text_ready_for_formatting", milestone_ids)
        for item in chain["milestones"]:
            self.assertIn("是否", item["next_prompt"])

    def test_subagent_registry_schema_is_valid(self) -> None:
        from scripts.envctl.schema_validation import collect_schema_document_errors, collect_schema_errors, load_json

        schema = load_json(ROOT / "schemas" / "subagent_registry.schema.json")
        payload = load_json(ROOT / "catalog" / "subagent_registry.json")
        self.assertEqual(collect_schema_document_errors(schema, "subagent_registry.schema.json"), [])
        self.assertEqual(collect_schema_errors(payload, schema, "subagent_registry.json"), [])

    def test_harness_adapter_reserved_boundary_smoke(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_harness_adapter_contract.py")],
            cwd=str(ROOT.parent),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_social_platform_playbook_selects_analysis_and_manager(self) -> None:
        playbook = load_route_playbook("social-platform-case")
        producers = pick_producers(
            "social-platform-case",
            card(
                "social-platform-case",
                target_item_count=4,
                work_units=["capture", "analysis"],
                deliverable_types=["comment_analysis_report"],
            ),
            playbook,
        )
        self.assertEqual(producers, ["social-platform-producer", "analysis-producer", "project-manager"])

    def test_css_playbook_selects_writing_for_paper_draft(self) -> None:
        playbook = load_route_playbook("computational-social-science")
        producers = pick_producers(
            "computational-social-science",
            card("computational-social-science", work_units=["writing"], deliverable_types=["paper_draft"]),
            playbook,
        )
        self.assertEqual(producers, ["project-manager", "analysis-producer", "writing-producer"])

    def test_desktop_playbook_adds_release_only_for_package_scope(self) -> None:
        playbook = load_route_playbook("desktop-app-development")
        producers = pick_producers(
            "desktop-app-development",
            card("desktop-app-development", work_units=["packaging"], deliverable_types=["release_package"]),
            playbook,
        )
        self.assertEqual(
            producers,
            [
                "project-manager",
                "app-product-producer",
                "app-architect",
                "app-ui-producer",
                "app-release-producer",
            ],
        )

    def test_review_chain_uses_playbook_reviewer(self) -> None:
        playbook = load_route_playbook("desktop-app-development")
        available = {
            "project-manager": {},
            "app-product-producer": {},
            "app-architect": {},
            "app-ui-producer": {},
            "app-release-producer": {},
            "app-qa-reviewer": {},
        }
        producers = ["project-manager", "app-release-producer"]
        reviewers, review_pairs, missing = build_review_pairs("desktop-app-development", producers, available, playbook)
        self.assertEqual(reviewers, ["app-qa-reviewer"])
        self.assertEqual(
            review_pairs,
            {
                "project-manager": "app-qa-reviewer",
                "app-release-producer": "app-qa-reviewer",
            },
        )
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
