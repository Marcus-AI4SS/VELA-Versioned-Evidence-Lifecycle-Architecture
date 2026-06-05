from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.cybernetics import (
    build_evolution_backlog_summary,
    build_reading_status,
    build_skill_audit_report,
    CONTRACTS,
    validate_cybernetics_contracts,
)
from scripts.envctl.schema_validation import collect_schema_errors, load_json


class CyberneticsContractTests(unittest.TestCase):
    def test_cybernetics_contracts_use_validator_envelope(self) -> None:
        result = validate_cybernetics_contracts()
        schema = load_json(ROOT / "schemas" / "validator_result.schema.json")
        self.assertEqual(collect_schema_errors(result, schema, "cybernetics_result"), [])
        self.assertTrue(result["ok"])
        self.assertEqual(result["validator"], "validate_cybernetics")
        self.assertEqual(result["warnings"], [])
        self.assertNotIn("reading_status", result["details"])
        self.assertNotIn("engineering_cybernetics_reading_passes", CONTRACTS)
        self.assertIn("environment_layer_contract", CONTRACTS)
        self.assertIn("conflict_matrix", CONTRACTS)

    def test_memory_policy_has_all_placement_decisions(self) -> None:
        policy = load_json(ROOT / "catalog" / "memory_admission_policy.json")
        labels = {item["decision_label"] for item in policy["placements"]}
        self.assertEqual(labels, {"control_kernel", "skill", "obsidian", "codex_native", "discard"})

    def test_source_rule_crosswalk_covers_recent_review_gaps(self) -> None:
        crosswalk = load_json(ROOT / "catalog" / "cybernetic_source_rule_crosswalk.json")
        schema = load_json(ROOT / "schemas" / "cybernetic_source_rule_crosswalk.v1.schema.json")
        self.assertEqual(collect_schema_errors(crosswalk, schema, "source_rule_crosswalk"), [])
        principle_ids = {item["id"] for item in crosswalk["principles"]}
        self.assertIn("technical-science-layer", principle_ids)
        self.assertIn("feedforward-constraint", principle_ids)
        self.assertIn("disturbance-uncertainty-control", principle_ids)
        self.assertIn("platform-article-19-principles", principle_ids)
        article_sources = {
            source["id"]
            for source in crosswalk["sources"]
            if source["source_type"] == "public_platform_article"
        }
        self.assertEqual(
            article_sources,
            {
                "public-platform-harness-engineering-cybernetics",
                "public-platform-ai-code-review-engineering-cybernetics",
            },
        )

    def test_reading_status_truthfully_tracks_ocr_and_unfinished_passes(self) -> None:
        status = build_reading_status()
        english = next(item for item in status["sources"] if item["id"] == "engineering-cybernetics-en")
        self.assertEqual(status["scope"], "source_evidence_only")
        self.assertEqual(status["required_passes_per_source"], 3)
        self.assertFalse(english["blocked_by_ocr"])
        self.assertEqual(english["text_layer_status"], "ocr_extracted")
        self.assertEqual(english["passes_complete"], 3)
        self.assertEqual(len(status["article_sources"]), 2)
        self.assertTrue(status["all_sources_three_pass_complete"])

    def test_evolution_backlog_records_control_kernel_bootstrap(self) -> None:
        summary = build_evolution_backlog_summary()
        self.assertGreaterEqual(summary["event_count"], 6)
        self.assertGreaterEqual(summary["by_target"].get("control_kernel", 0), 1)
        open_ids = {item["id"] for item in summary["open_events"]}
        self.assertNotIn("2026-05-09-agent-contract-control-coupling", open_ids)
        self.assertNotIn("2026-05-09-citation-verification-report-gate", open_ids)
        self.assertNotIn("2026-05-09-profile-apply-envctl-boundary", open_ids)
        self.assertGreaterEqual(summary["by_status"].get("implemented", 0), 6)

    def test_skill_audit_is_controlled_auto_landing_and_finds_core_controllers(self) -> None:
        report = build_skill_audit_report()
        self.assertEqual(report["mode"], "controlled_auto_landing")
        self.assertFalse(report["source_files_written"])
        self.assertEqual(report["missing_core_controller_skills"], [])
        self.assertIn("research-autopilot", report["core_controllers"])
        self.assertIn("local_memory_system", report)
        self.assertNotIn("reading_status", report)


if __name__ == "__main__":
    unittest.main()
