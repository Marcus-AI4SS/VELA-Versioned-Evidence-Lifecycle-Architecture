from __future__ import annotations



import sys

import tempfile

import unittest

from datetime import datetime, timezone

from pathlib import Path





ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



from scripts.envctl.evolution_intake import (

    append_report_items_to_backlog,

    build_evolution_intake_report,

    validate_report,

    write_evolution_intake_report,

)

from scripts.envctl.schema_validation import collect_schema_errors, load_json





class EvolutionIntakeTests(unittest.TestCase):

    def test_report_detects_project_retrospective_without_source_writes(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project = Path(tmp) / "demo-project"

            project.mkdir()

            (project / "AGENTS.md").write_text("# Project Rules\n", encoding="utf-8")

            (project / "project_closure_retrospective.md").write_text(

                "# 项目复盘\n\n复盘发现质量门和 validator 需要补充。",

                encoding="utf-8",

            )



            report = build_evolution_intake_report(

                scan_roots=[Path(tmp)],

                lookback_days=7,

                now=datetime(2026, 5, 11, tzinfo=timezone.utc),

            )



            self.assertEqual(validate_report(report), [])

            self.assertEqual(report["mode"], "controlled_auto_landing")

            self.assertFalse(report["source_files_written"])

            self.assertEqual(report["candidate_count"], 1)

            self.assertEqual(report["items"][0]["risk_level"], "medium")

            self.assertEqual(report["items"][0]["proposed_target"], "schema")



    def test_high_risk_runtime_config_signal_is_flagged(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project = Path(tmp) / "runtime-project"

            project.mkdir()

            (project / "research_stack_change_proposal.md").write_text(

                "# 配置提案\n\n需要修改 .codex/config.toml 并自动写入 MCP token。",

                encoding="utf-8",

            )



            report = build_evolution_intake_report(

                scan_roots=[Path(tmp)],

                lookback_days=7,

                now=datetime(2026, 5, 11, tzinfo=timezone.utc),

            )



            self.assertEqual(report["candidate_count"], 1)

            self.assertEqual(report["items"][0]["risk_level"], "high")

            self.assertEqual(report["items"][0]["recommended_action"], "manual_review_required")



    def test_report_writer_creates_markdown_and_json_outputs(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            output = Path(tmp) / "report.md"

            report = build_evolution_intake_report(

                scan_roots=[Path(tmp)],

                lookback_days=7,

                now=datetime(2026, 5, 11, tzinfo=timezone.utc),

            )



            markdown_path, json_path = write_evolution_intake_report(report, output)



            self.assertTrue(markdown_path.exists())

            self.assertTrue(json_path.exists())

            self.assertIn("自适应演化输入报告", markdown_path.read_text(encoding="utf-8"))

            schema = load_json(ROOT / "schemas" / "evolution_intake_report.v1.schema.json")

            self.assertEqual(collect_schema_errors(load_json(json_path), schema, "report"), [])



    def test_append_backlog_is_deduplicated(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project = Path(tmp) / "demo-project"

            project.mkdir()

            proposal = project / "research_stack_change_proposal.md"

            proposal.write_text("# 提案\n\n把重复手工流程放进 skill。", encoding="utf-8")

            report = build_evolution_intake_report(

                scan_roots=[Path(tmp)],

                lookback_days=7,

                now=datetime(2026, 5, 11, tzinfo=timezone.utc),

            )

            backlog = Path(tmp) / "evolution_backlog.json"

            backlog.write_text(

                '{"$schema":"../schemas/evolution_event.v1.schema.json","schema_version":"evolution_event.v1","generated_at":"2026-05-11","events":[]}\n',

                encoding="utf-8",

            )



            first = append_report_items_to_backlog(report, backlog)

            second = append_report_items_to_backlog(report, backlog)



            self.assertEqual(len(first["added"]), 1)

            self.assertTrue(first["source_file_written"])

            self.assertEqual(second["added"], [])

            self.assertEqual(len(second["skipped_existing"]), 1)

            self.assertFalse(second["source_file_written"])



    def test_empty_append_does_not_rewrite_backlog(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            backlog = Path(tmp) / "evolution_backlog.json"

            original = '{"$schema":"../schemas/evolution_event.v1.schema.json","schema_version":"evolution_event.v1","generated_at":"2026-05-11","events":[]}\n'

            backlog.write_text(original, encoding="utf-8")

            report = build_evolution_intake_report(

                scan_roots=[Path(tmp)],

                lookback_days=7,

                now=datetime(2026, 5, 11, tzinfo=timezone.utc),

            )



            result = append_report_items_to_backlog(report, backlog)



            self.assertEqual(result["added"], [])

            self.assertFalse(result["source_file_written"])

            self.assertEqual(backlog.read_text(encoding="utf-8"), original)





if __name__ == "__main__":

    unittest.main()
