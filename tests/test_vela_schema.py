from __future__ import annotations



import tempfile

import unittest

from pathlib import Path



from scripts import vela_schema





class VelaSchemaTests(unittest.TestCase):

    def test_validation_report_schema_accepts_standard_report(self) -> None:

        report = vela_schema.validation_report(

            validator="unit",

            scope="demo",

            errors=[],

            warnings=[],

            checks=[{"name": "demo", "exists": True}],

        )

        errors = vela_schema.validate_payload(report, "vela.validation.report.v1", "report")

        self.assertEqual(errors, [])



    def test_schema_validation_reports_missing_required_field(self) -> None:

        payload = {

            "schema_version": "vela.codex.handoff.v1",

            "handoff_id": "H001",

            "created_at": "2026-05-05T00:00:00Z",

            "scope": {"task": "Read files."},

            "constraints": ["Do not invent evidence."],

            "expected_output": {"format": "markdown", "path": "logs/result.md"},

            "review_standard": ["Cite evidence IDs."],

            "completion": {"human_review_required": True},

        }

        errors = vela_schema.validate_payload(payload, "vela.codex.handoff.v1", "handoff")

        self.assertTrue(any("relevant_files" in error for error in errors), errors)



    def test_load_json_or_yaml_parses_yaml_handoff(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            path = Path(tmp) / "H001.yaml"

            path.write_text(

                "\n".join(

                    [

                        "schema_version: vela.codex.handoff.v1",

                        "handoff_id: H001",

                        "created_at: 2026-05-05T00:00:00Z",

                        "scope:",

                        "  task: Read files.",

                        "  relevant_files:",

                        "    - research-map.md",

                        "constraints:",

                        "  - Do not invent evidence.",

                        "expected_output:",

                        "  format: markdown",

                        "  path: logs/result.md",

                        "review_standard:",

                        "  - Cite evidence IDs.",

                        "completion:",

                        "  human_review_required: true",

                        "",

                    ]

                ),

                encoding="utf-8",

            )

            payload, errors = vela_schema.load_json_or_yaml(path)

            self.assertEqual(errors, [])

            self.assertEqual(payload["schema_version"], "vela.codex.handoff.v1")





if __name__ == "__main__":

    unittest.main()
