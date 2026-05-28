from __future__ import annotations



import json

import tempfile

import unittest

from pathlib import Path



from scripts import vela_contract

from scripts import vela_initializer





class VelaInitializerTests(unittest.TestCase):

    def test_initializer_manifest_is_valid(self) -> None:

        result = vela_initializer.validate_manifest()

        self.assertTrue(result["ok"], result)

        self.assertEqual(result["schema_version"], "vela.validation.report.v1")

        self.assertEqual(result["errors"], [])



    def test_manifest_materializes_public_project_without_app_agents(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "demo-project"

            result = vela_initializer.materialize_project(project_root, route_hint="literature-review")

            self.assertTrue(result["ok"])

            self.assertTrue((project_root / "research-map.md").exists())

            self.assertFalse((project_root / ".codex" / "agents").exists())



            pipeline = json.loads((project_root / "logs" / "quality-gates" / "pipeline-status.json").read_text(encoding="utf-8"))

            self.assertEqual(pipeline["route_id"], "literature-review")



            context = vela_contract.write_project_context(project_root)

            self.assertEqual(context["schema_version"], "vela.project.context.v1")

            self.assertEqual(context["project"]["route_id"], "literature-review")

            self.assertTrue((project_root / ".vela" / "context.json").exists())



    def test_initializer_rejects_paths_outside_project(self) -> None:

        manifest = vela_initializer.load_manifest()

        manifest["files"] = [{"path": "../escape.txt", "kind": "text", "content": "bad"}]

        result = vela_initializer.validate_manifest(manifest)

        self.assertFalse(result["ok"])

        self.assertTrue(any("inside the project" in error for error in result["errors"]))





if __name__ == "__main__":

    unittest.main()
