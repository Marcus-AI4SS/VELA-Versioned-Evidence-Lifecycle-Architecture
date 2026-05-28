from __future__ import annotations



import json

import tempfile

import unittest

from pathlib import Path



from scripts import vela_contract

from scripts import vela_initializer





class VelaContractTests(unittest.TestCase):

    def test_validate_project_uses_context_schema(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "demo-project"

            vela_initializer.materialize_project(project_root, route_hint="literature-review")

            vela_contract.write_project_context(project_root)



            report = vela_contract.validate_project(project_root)

            self.assertTrue(report["ok"], report)

            self.assertEqual(report["schema_version"], "vela.validation.report.v1")

            self.assertEqual(report["validator"], "project_validate")

            self.assertEqual(report["context_schema"], "vela.project.context.v1")



    def test_validate_project_rejects_bad_context_shape(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "demo-project"

            vela_initializer.materialize_project(project_root, route_hint=None)

            context_path = project_root / ".vela" / "context.json"

            context_path.parent.mkdir(parents=True, exist_ok=True)

            context_path.write_text(

                json.dumps({"schema_version": "vela.project.context.v1"}, indent=2),

                encoding="utf-8",

            )



            report = vela_contract.validate_project(project_root)

            self.assertFalse(report["ok"], report)

            self.assertTrue(any("project" in error for error in report["errors"]), report)





if __name__ == "__main__":

    unittest.main()
