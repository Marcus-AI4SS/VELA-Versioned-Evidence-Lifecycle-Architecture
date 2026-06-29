from __future__ import annotations



import json

import tempfile

import unittest

from pathlib import Path



from scripts import init_research_project

from scripts import vela_privacy

from scripts import vela_public_export





class VelaPrivacyExportTests(unittest.TestCase):

    def test_privacy_scan_reports_local_absolute_path(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "demo-project"

            project_root.mkdir()

            (project_root / "deliverables").mkdir()

            (project_root / "deliverables" / "brief.md").write_text(

                "Local draft path: C:\\Users\\alice\\private\\draft.md",

                encoding="utf-8",

            )

            report = vela_privacy.scan_project(project_root, scope_label=".")

            self.assertFalse(report["ok"], report)

            self.assertTrue(any("local absolute path" in error for error in report["errors"]), report)



    def test_privacy_scan_reports_json_escaped_local_absolute_path(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "demo-project"

            project_root.mkdir()

            (project_root / "evidence").mkdir()

            (project_root / "evidence" / "E001.json").write_text(

                json.dumps({"source": "C:\\Users\\alice\\private\\source.pdf"}),

                encoding="utf-8",

            )

            report = vela_privacy.scan_project(project_root, scope_label=".")

            self.assertFalse(report["ok"], report)

            self.assertTrue(any("local absolute path" in error for error in report["errors"]), report)



    def test_public_export_writes_manifest_without_local_root(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "demo-project"

            output_root = Path(tmp) / "public-export"

            init_research_project.initialize_project(project_root, skip_codex_trust=True, route_hint="literature-review")

            result = vela_public_export.build_public_export(project_root, output_root)

            self.assertTrue(result["ok"], result)

            manifest_path = output_root / "VELA-PUBLIC-EXPORT-MANIFEST.json"

            quality_path = output_root / "EXPORT-QUALITY-REPORT.json"

            self.assertTrue(manifest_path.exists())

            self.assertTrue(quality_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(manifest["schema_version"], "vela.public_export.manifest.v1")

            self.assertEqual(manifest["source_root"], "<local-project-root>")

            self.assertNotIn(str(project_root), manifest_path.read_text(encoding="utf-8"))


    def test_public_export_blocks_output_inside_project_root(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "demo-project"

            init_research_project.initialize_project(project_root, skip_codex_trust=True, route_hint="literature-review")

            result = vela_public_export.build_public_export(project_root, project_root / "deliverables" / "public")

            self.assertFalse(result["ok"], result)

            self.assertEqual(result["reason"], "output_inside_project_root")


    def test_public_export_blocks_local_absolute_paths(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "demo-project"

            output_root = Path(tmp) / "public-export"

            init_research_project.initialize_project(project_root, skip_codex_trust=True, route_hint="literature-review")

            (project_root / "README.md").write_text(

                "Local path: D:\\AI environment-GITHUB\\private\\draft.md",

                encoding="utf-8",

            )

            result = vela_public_export.build_public_export(project_root, output_root)

            self.assertFalse(result["ok"], result)

            self.assertEqual(result["reason"], "privacy_scan_failed")

            self.assertFalse((output_root / "README.md").exists())


    def test_public_export_without_context_uses_safe_project_summary(self) -> None:

        with tempfile.TemporaryDirectory() as tmp:

            project_root = Path(tmp) / "demo-project"

            output_root = Path(tmp) / "public-export"

            project_root.mkdir()

            (project_root / "README.md").write_text("# Demo\n", encoding="utf-8")

            result = vela_public_export.build_public_export(project_root, output_root)

            self.assertTrue(result["ok"], result)

            manifest = json.loads((output_root / "VELA-PUBLIC-EXPORT-MANIFEST.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["project"]["id"], "demo-project")





if __name__ == "__main__":

    unittest.main()
