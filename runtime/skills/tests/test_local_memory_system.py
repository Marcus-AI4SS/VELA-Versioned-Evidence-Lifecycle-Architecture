from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.memory_system import (
    admission_score,
    build_memory_reconciliation_report,
    build_memory_status_report,
    candidate_from_text,
    decide_candidate,
    validate_memory_reconciliation_report,
    validate_local_memory_system,
    validate_memory_status_report,
    write_memory_reconciliation_report,
    write_memory_status_report,
)
from scripts.envctl.schema_validation import collect_schema_errors, load_json


class LocalMemorySystemTests(unittest.TestCase):
    def test_policy_and_schemas_validate(self) -> None:
        result = validate_local_memory_system()
        envelope = load_json(ROOT / "schemas" / "validator_result.schema.json")
        self.assertEqual(collect_schema_errors(result, envelope, "memory_result"), [])
        self.assertTrue(result["ok"])
        self.assertEqual(result["validator"], "validate_local_memory_system")
        self.assertEqual(result["details"]["automation_mode"], "controlled_auto_landing")

    def test_policy_absorbs_memory_repos_without_default_external_runtime(self) -> None:
        policy = load_json(ROOT / "catalog" / "local_memory_system.json")
        repos = {item["repo"]: item for item in policy["external_inputs"]}
        self.assertIn("384961890-ui/Brain-v1.2.0", repos)
        self.assertIn("yyy-yq1/vector-memory-system", repos)
        self.assertIn("qslowprofile/OpenClaw-memory-knowledge-Management", repos)
        forbidden = set(policy["storage_boundaries"]["forbidden_defaults"])
        self.assertIn("no_vector_database_by_default", forbidden)
        self.assertIn("no_unvetted_background_service_by_default", forbidden)
        self.assertIn("no_transcript_ingestion_by_default", forbidden)
        self.assertIn("no_external_hook_by_default", forbidden)
        self.assertEqual(policy["runtime_adapter_policy"]["selected_adapter"], "local_contract_only")
        self.assertEqual(policy["runtime_adapter_policy"]["status"], "enabled")
        self.assertIn(
            "python -m skills.scripts.envctl validate environment-layers",
            policy["automation_policy"]["required_gates"],
        )

    def test_status_report_is_lightweight_and_schema_valid(self) -> None:
        report = build_memory_status_report()
        self.assertEqual(validate_memory_status_report(report), [])
        self.assertFalse(report["source_files_written"])
        self.assertEqual(report["mode"], "controlled_auto_landing")
        self.assertIn("no_vector_database_by_default", report["lightweight_constraints"])
        self.assertIn("python -m skills.scripts.envctl validate memory", report["automation"]["required_gates"])

    def test_reconciliation_report_is_schema_valid_and_does_not_write_source(self) -> None:
        report = build_memory_reconciliation_report()
        self.assertEqual(validate_memory_reconciliation_report(report), [])
        self.assertFalse(report["source_files_written"])
        self.assertEqual(report["external_memory_service"]["configured"], False)
        self.assertEqual(report["external_memory_service"]["checked"], False)
        self.assertIn("local Git contracts remain the source of truth", report["reconciliation"][0])

    def test_reconciliation_writer_only_writes_requested_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_memory_reconciliation_report()
            output = Path(tmp) / "memory-reconciliation.json"
            written = write_memory_reconciliation_report(report, output)
            self.assertEqual(written, output)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(validate_memory_reconciliation_report(payload), [])

    def test_retrieval_interfaces_have_structured_governance_controls(self) -> None:
        policy = load_json(ROOT / "catalog" / "local_memory_system.json")
        controls = {item["interface"]: item for item in policy["retrieval_policy"]["interface_controls"]}
        for interface in [
            "confidence_evaluation",
            "decision_archive",
            "task_tracking",
            "task_status",
            "memory_cleanup",
            "codegraph_context_index",
        ]:
            self.assertIn(interface, controls)
            self.assertGreaterEqual(len(controls[interface]["required_fields"]), 4)
        cleanup_text = " ".join(controls["memory_cleanup"]["required_fields"] + controls["memory_cleanup"]["safety_rules"])
        self.assertIn("user_confirmation", cleanup_text)
        self.assertIn("protected", cleanup_text)

    def test_status_report_writer_only_writes_requested_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_memory_status_report()
            output = Path(tmp) / "memory-status.json"
            written = write_memory_status_report(report, output)
            self.assertEqual(written, output)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(validate_memory_status_report(payload), [])

    def test_single_unconfirmed_private_preference_needs_review_not_promotion(self) -> None:
        candidate = candidate_from_text(
            text="以后类似任务尽量先给中文结论。",
            source_type="explicit_preference",
            source_ref="chat:demo",
            memory_layer="private_preference",
            privacy_scope="local_private",
            proposed_target="codex_native",
            occurrence_count=1,
            user_confirmed=False,
        )
        result = decide_candidate(candidate)
        self.assertEqual(result["decision"], "needs_review")
        self.assertEqual(result["hard_blocks"], [])

    def test_repeated_confirmed_procedural_memory_can_form_promotion_plan(self) -> None:
        candidate = candidate_from_text(
            text="结构性阅读任务应先建立候选文献表，再获取 PDF，再进入证据核验。",
            source_type="user_correction",
            source_ref="chat:confirmed-rule",
            memory_layer="procedural_memory",
            privacy_scope="public_repo",
            proposed_target="skill",
            occurrence_count=3,
            user_confirmed=True,
        )
        result = decide_candidate(candidate)
        self.assertGreaterEqual(admission_score(candidate), 0.75)
        self.assertEqual(result["decision"], "promotion_plan")
        self.assertEqual(result["hard_blocks"], [])

    def test_secret_signal_is_hard_blocked_even_if_repeated(self) -> None:
        candidate = candidate_from_text(
            text="把 API token 自动写入环境规则，方便以后复用。",
            source_type="explicit_preference",
            source_ref="chat:bad-memory",
            memory_layer="control_memory",
            privacy_scope="public_repo",
            proposed_target="control_kernel",
            occurrence_count=5,
            user_confirmed=True,
        )
        result = decide_candidate(candidate)
        self.assertEqual(result["decision"], "rejected")
        self.assertIn("contains-secret-or-account-signal", result["hard_blocks"])

    def test_private_scope_cannot_target_git_source(self) -> None:
        candidate = candidate_from_text(
            text="把这个只属于当前项目的私有路径写入全局控制核。",
            source_type="route_override",
            source_ref="chat:private-path",
            memory_layer="control_memory",
            privacy_scope="local_private",
            proposed_target="control_kernel",
            occurrence_count=2,
            user_confirmed=True,
        )
        result = decide_candidate(candidate)
        self.assertEqual(result["decision"], "rejected")
        self.assertIn("private-scope-targets-git-source", result["hard_blocks"])


if __name__ == "__main__":
    unittest.main()
