from __future__ import annotations



import tempfile

import unittest

from pathlib import Path



from scripts import vela_handoff





class VelaHandoffTests(unittest.TestCase):

    def test_create_handoff_writes_schema_valid_packet_and_prompt(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "demo-project"

            result = vela_handoff.create_handoff(project_root, "claim-check")

            self.assertTrue(result["ok"], result)

            handoff = Path(str(result["handoff"]))

            prompt = Path(str(result["prompt"]))

            self.assertTrue(handoff.exists())

            self.assertTrue(prompt.exists())

            lint = vela_handoff.lint_handoff(handoff)

            self.assertTrue(lint["ok"], lint)

            self.assertEqual(lint["schema_version"], "vela.validation.report.v1")



    def test_lint_rejects_missing_relevant_files(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            path = Path(tmp) / "bad.yaml"

            path.write_text(

                "\n".join(

                    [

                        "schema_version: vela.codex.handoff.v1",

                        "handoff_id: H001",

                        'created_at: "2026-05-05T00:00:00Z"',

                        "scope:",

                        "  task: Read files.",

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

            report = vela_handoff.lint_handoff(path)

            self.assertFalse(report["ok"])

            self.assertTrue(any("relevant_files" in error for error in report["errors"]), report)



    def test_render_rejects_invalid_handoff(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            path = Path(tmp) / "bad.yaml"

            path.write_text("schema_version: vela.codex.handoff.v1\n", encoding="utf-8")

            with self.assertRaises(ValueError):

                vela_handoff.render_handoff_prompt(path)





if __name__ == "__main__":

    unittest.main()
