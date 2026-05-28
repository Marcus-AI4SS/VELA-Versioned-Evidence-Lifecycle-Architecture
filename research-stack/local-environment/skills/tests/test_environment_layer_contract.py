from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.environment_layers import validate_environment_layer_contract
from scripts.envctl.schema_validation import collect_schema_errors, load_json


class EnvironmentLayerContractTests(unittest.TestCase):
    def test_environment_layer_contract_validates(self) -> None:
        result = validate_environment_layer_contract()
        envelope = load_json(ROOT / "schemas" / "validator_result.schema.json")
        self.assertEqual(collect_schema_errors(result, envelope, "environment_layers_result"), [])
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["validator"], "validate_environment_layer_contract")

    def test_seven_layers_are_explicit_and_complete(self) -> None:
        payload = load_json(ROOT / "catalog" / "environment_layer_contract.json")
        self.assertEqual(
            [item["id"] for item in payload["layers"]],
            [
                "execution",
                "tool",
                "context",
                "lifecycle",
                "observability",
                "verification",
                "governance",
            ],
        )
        expected = {item["id"] for item in payload["layers"]}
        for route in payload["route_layer_map"]:
            self.assertEqual(set(route["required_layers"]), expected)

    def test_agentmemory_and_codegraph_are_runtime_adapters_not_rule_sources(self) -> None:
        payload = load_json(ROOT / "catalog" / "environment_layer_contract.json")
        tools = {item["id"]: item for item in payload["tool_inventory"]}
        self.assertEqual(tools["agentmemory"]["layer"], "context")
        self.assertEqual(tools["codegraph"]["layer"], "context")
        self.assertIn(".agentmemory", " ".join(tools["agentmemory"]["safety_controls"]["allowed_write_scope"]))
        self.assertIn(".codegraph", " ".join(tools["codegraph"]["safety_controls"]["allowed_write_scope"]))
        self.assertIn("source rules", " ".join(tools["agentmemory"]["safety_controls"]["forbidden_actions"]))
        self.assertIn("change source files", " ".join(tools["codegraph"]["safety_controls"]["forbidden_actions"]))
        assertions = "\n".join(payload["governance_assertions"])
        self.assertIn("agentmemory", assertions)
        self.assertIn("codegraph", assertions)

        memory = load_json(ROOT / "catalog" / "local_memory_system.json")
        adapter = memory["runtime_adapter_policy"]
        self.assertEqual(adapter["selected_adapter"], "agentmemory")
        self.assertEqual(adapter["status"], "enabled")
        self.assertNotIn("skills-environment-local", adapter["data_root"])
        forbidden = "\n".join(adapter["forbidden_actions"])
        self.assertIn("auto-promote runtime memory", forbidden)
        self.assertIn("full transcript import", forbidden)
        self.assertIn("secrets", forbidden)

    def test_research_autopilot_is_the_only_total_entry(self) -> None:
        catalog = load_json(ROOT / "catalog" / "skill_catalog.json")
        entries = sorted(
            name
            for name, item in catalog["skills"].items()
            if item["status"] == "active" and (item.get("entry") is True or item.get("role") == "entry")
        )
        self.assertEqual(entries, ["research-autopilot"])

        payload = load_json(ROOT / "catalog" / "environment_layer_contract.json")
        entry_maps = sorted(
            item["skill_id"]
            for item in payload["skill_layer_map"]
            if item["role"] == "entry"
        )
        self.assertEqual(entry_maps, ["research-autopilot"])

    def test_shared_route_terms_have_disambiguation_rules(self) -> None:
        conflicts = load_json(ROOT / "catalog" / "conflict_matrix.json")
        rules = {item["rule"] for item in conflicts["rules"]}
        self.assertIn("revision-package-scope-disambiguation", rules)
        self.assertIn("replication-package-scope-disambiguation", rules)

    def test_lightweight_memory_interfaces_cover_previous_open_items(self) -> None:
        memory = load_json(ROOT / "catalog" / "local_memory_system.json")
        interfaces = set(memory["retrieval_policy"]["enabled_interfaces"])
        for required in {
            "keyword_search",
            "semantic_search_optional_dry_run",
            "confidence_evaluation",
            "decision_archive",
            "task_tracking",
            "task_status",
            "memory_cleanup",
            "memory_list_delete",
            "agentmemory_smart_search",
            "agentmemory_session_history",
            "agentmemory_governance_delete",
            "codegraph_context_index",
        }:
            self.assertIn(required, interfaces)


if __name__ == "__main__":
    unittest.main()
