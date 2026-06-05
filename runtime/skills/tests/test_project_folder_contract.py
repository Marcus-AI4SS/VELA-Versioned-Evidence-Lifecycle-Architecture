from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.project_folder_contract import validate_project_folder_contract  # noqa: E402
from scripts.envctl.project_initializer import ensure_project_contract  # noqa: E402


class ProjectFolderContractTests(unittest.TestCase):
    def test_source_contract_validates(self) -> None:
        result = validate_project_folder_contract()
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["errors"], [])
        self.assertGreaterEqual(result["details"]["zone_count"], 6)

    def test_ensure_project_contract_creates_required_project_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "研究项目"
            ensure_project_contract(project_root)

            result = validate_project_folder_contract(project_root)

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["errors"], [])

    def test_missing_project_structure_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "空项目"
            project_root.mkdir()

            result = validate_project_folder_contract(project_root)

        self.assertFalse(result["ok"])
        self.assertIn("project_folder_contract:missing-required-file:AGENTS.md", result["errors"])
        self.assertIn("project_folder_contract:missing-required-dir:.codex/agents", result["errors"])

    def test_root_download_pdf_is_warning_not_delete_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp) / "下载测试"
            ensure_project_contract(project_root)
            (project_root / "download.pdf").write_bytes(b"%PDF-1.4\n")

            result = validate_project_folder_contract(project_root)

        self.assertTrue(result["ok"], json.dumps(result, ensure_ascii=False, indent=2))
        self.assertIn(
            "project_folder_contract:forbidden-root-pattern:download.pdf:download*.pdf",
            result["warnings"],
        )


if __name__ == "__main__":
    unittest.main()
