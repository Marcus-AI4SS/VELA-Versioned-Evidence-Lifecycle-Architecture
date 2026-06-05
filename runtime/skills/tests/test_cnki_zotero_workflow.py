from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.envctl.cnki_zotero import (  # noqa: E402
    _build_captcha_checkpoint,
    build_agent_browser_args,
    build_candidate_gate_report,
    build_cnki_download_script,
    build_inbox_audit,
    build_status,
    inspect_controlled_cnki_runtime,
    resolve_inbox,
    validate_cnki_zotero_workflow,
    _cnki_search_url,
    _normalize_cnki_search_type,
    _normalize_cnki_sort,
)
from scripts.envctl.__main__ import build_parser  # noqa: E402
from scripts.envctl.commands import cnki_zotero as cnki_zotero_command  # noqa: E402
from scripts.envctl.commands.cnki_zotero import _extract_candidate_list  # noqa: E402
from scripts.envctl.schema_validation import collect_schema_errors, load_json  # noqa: E402


class CnkiZoteroWorkflowTests(unittest.TestCase):
    def test_contract_is_schema_valid(self) -> None:
        schema = load_json(ROOT / "schemas" / "cnki_zotero_workflow.v1.schema.json")
        payload = load_json(ROOT / "catalog" / "cnki_zotero_workflow.json")
        self.assertEqual(collect_schema_errors(payload, schema, "cnki_zotero_workflow"), [])
        result = validate_cnki_zotero_workflow()
        self.assertTrue(result["ok"], result)

    def test_status_does_not_create_inbox_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            missing = Path(temp_root) / "missing"
            with patch("scripts.envctl.cnki_zotero._websocket_client_available", return_value=True):
                status = build_status(inbox=missing)
            self.assertTrue(status["ok"], status)
            self.assertFalse(status["inbox_exists"])
            self.assertFalse(status["source_files_written"])
            self.assertFalse(missing.exists())
            self.assertTrue(status["runtime"]["direct_cdp_supported"])

    def test_status_reports_missing_direct_cdp_dependency(self) -> None:
        with patch("scripts.envctl.cnki_zotero._websocket_client_available", return_value=False):
            status = build_status()

        self.assertFalse(status["ok"])
        self.assertFalse(status["runtime"]["direct_cdp_supported"])
        self.assertIn("missing-python-dependency:websocket-client", status["errors"])

    def test_runtime_probe_reports_cdp_endpoint_when_requested(self) -> None:
        with (
            patch("scripts.envctl.cnki_zotero._websocket_client_available", return_value=True),
            patch("scripts.envctl.cnki_zotero._resolve_cdp_websocket_url", return_value="ws://127.0.0.1/devtools/browser/test"),
        ):
            report = inspect_controlled_cnki_runtime(cdp="9333", check_cdp=True)

        self.assertTrue(report["ok"], report)
        self.assertTrue(report["direct_cdp"]["reachable"])
        self.assertEqual(report["direct_cdp"]["websocket_url"], "ws://127.0.0.1/devtools/browser/test")

    def test_inbox_audit_classifies_downloads_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            (root / "paper.pdf").write_bytes(b"%PDF-1.7\n")
            (root / "paper.caj").write_bytes(b"CAJ")
            (root / "paper.ris").write_text("TY  - JOUR\n", encoding="utf-8")
            (root / "ignore.tmp").write_text("ignore", encoding="utf-8")
            report = build_inbox_audit(inbox=root)
            self.assertEqual(report["file_count"], 4)
            self.assertEqual(report["by_action"]["local_pdf_add_from_file"], 1)
            self.assertEqual(report["by_action"]["manual_caj_attachment"], 1)
            self.assertEqual(report["by_action"]["metadata_review"], 1)
            self.assertEqual(report["by_action"]["ignored"], 1)
            plan = report["zotero_import_plan"]
            pdf_step = next(item for item in plan if item["tool"] == "official_zotero_plugin_or_local_connector_add_from_file")
            self.assertTrue(pdf_step["requires_review"])

    def test_project_inbox_defaults_to_project_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            project = Path(temp_root) / "project"
            project.mkdir()
            status = build_status(project_root=project, ensure_inbox=True)
            inbox = project / "outputs" / "inbox" / "cnki-downloads"
            self.assertEqual(Path(status["inbox"]), inbox.resolve())
            self.assertEqual(status["scope"], "project")
            self.assertTrue(inbox.exists())

    def test_project_inbox_rejects_external_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            project = Path(temp_root) / "project"
            project.mkdir()
            outside = Path(temp_root) / "outside" / "cnki-downloads"
            with self.assertRaises(ValueError):
                resolve_inbox(outside, project_root=project)

    def test_author_affiliation_gate_blocks_author_only_candidates(self) -> None:
        report = build_candidate_gate_report(
            [
                {
                    "title": "逻辑、想象和诠释",
                    "authors": ["陈云松"],
                    "evidence_sources": ["cnki-mcp-discovery"],
                    "evidence_texts": [],
                }
            ],
            requested_author="陈云松",
            requested_affiliation="南京大学",
        )
        self.assertFalse(report["download_allowed"])
        self.assertEqual(report["blocked_count"], 1)
        self.assertIn("missing-accepted-affiliation-evidence-source", report["items"][0]["errors"])

    def test_author_affiliation_gate_accepts_detail_page_evidence(self) -> None:
        report = build_candidate_gate_report(
            [
                {
                    "title": "社会预测:基于机器学习的研究新范式",
                    "authors": ["陈云松", "吴晓刚"],
                    "institutions": ["南京大学社会学院"],
                    "evidence_sources": ["detail_page_author_affiliation"],
                }
            ],
            requested_author="陈云松",
            requested_affiliation="南京大学",
        )
        self.assertTrue(report["download_allowed"], report)
        self.assertEqual(report["verified_count"], 1)

    def test_agent_browser_args_pin_download_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            inbox = Path(temp_root) / "downloads"
            with patch("scripts.envctl.cnki_zotero.shutil.which", return_value="agent-browser"):
                args = build_agent_browser_args(inbox=inbox, auto_connect=True, session_name="cnki-test")
            self.assertIn("--auto-connect", args)
            self.assertIn("--download-path", args)
            self.assertIn(str(inbox.resolve()), args)
            self.assertIn("--session-name", args)

    def test_captcha_checkpoint_keeps_remaining_queue_for_manual_resume(self) -> None:
        candidates = [
            {"title": "A", "detail_url": "https://example.test/a", "evidence_sources": ["detail_page_author_affiliation"]},
            {"title": "B", "detail_url": "https://example.test/b", "evidence_sources": ["detail_page_author_affiliation"]},
            {"title": "C", "detail_url": "https://example.test/c", "evidence_sources": ["detail_page_author_affiliation"]},
        ]
        items = [
            {"index": 1, "status": "downloaded"},
            {"index": 2, "status": "captcha-required", "errors": ["captcha-required"]},
        ]
        checkpoint = _build_captcha_checkpoint(
            selected=candidates,
            current_index=2,
            items=items,
            inbox_path=Path("C:/project/outputs/inbox/cnki-downloads"),
            project_root="C:/project",
            cdp="9333",
            format_name="pdf",
            mode="direct_cdp_download",
            direct_cdp=True,
        )
        self.assertEqual(checkpoint["status"], "manual_verification_required")
        self.assertEqual(checkpoint["downloaded_count"], 1)
        self.assertEqual(checkpoint["remaining_count"], 2)
        self.assertEqual([item["title"] for item in checkpoint["resume_candidates"]], ["B", "C"])
        self.assertIn("--direct-cdp", checkpoint["resume_command_hint"])
        self.assertIn("9333", checkpoint["resume_command_hint"])

    def test_browser_download_input_accepts_previous_captcha_report(self) -> None:
        report = {
            "schema_version": "cnki_authorized_browser_download.v1",
            "captcha_checkpoint": {
                "resume_candidates": [
                    {"title": "B", "detail_url": "https://example.test/b", "evidence_sources": ["detail_page_author_affiliation"]}
                ]
            },
        }
        candidates = _extract_candidate_list(report, action="browser-download")
        self.assertEqual(candidates[0]["title"], "B")

    def test_fetch_report_input_accepts_nested_download_captcha_checkpoint(self) -> None:
        report = {
            "schema_version": "cnki_search_batch_download.v1",
            "download": {
                "captcha_checkpoint": {
                    "resume_candidates": [
                        {"title": "C", "detail_url": "https://example.test/c", "evidence_sources": ["detail_page_author_affiliation"]}
                    ]
                }
            },
        }
        candidates = _extract_candidate_list(report, action="browser-download")
        self.assertEqual(candidates[0]["title"], "C")

    def test_cnki_download_script_uses_verified_selectors(self) -> None:
        script = build_cnki_download_script("pdf")
        self.assertIn("#pdfDown", script)
        self.assertIn("#cajDown", script)
        self.assertIn("not_logged_in", script)
        self.assertIn("tcaptcha_transform_dy", script)

    def test_cnki_discovery_accepts_flexible_search_and_sort_aliases(self) -> None:
        self.assertEqual(_normalize_cnki_search_type("关键词"), "keyword")
        self.assertEqual(_normalize_cnki_search_type("title"), "title")
        self.assertEqual(_normalize_cnki_sort("最新"), "date")
        self.assertEqual(_normalize_cnki_sort("download"), "download")
        author_url = _cnki_search_url("陈云松", "author")
        subject_url = _cnki_search_url("工程控制论", "subject")
        self.assertIn("korder=AU", author_url)
        self.assertIn("korder=SU", subject_url)
        self.assertIn("%E5%B7%A5%E7%A8%8B%E6%8E%A7%E5%88%B6%E8%AE%BA", subject_url)

    def test_simple_cli_aliases_hide_browser_plumbing(self) -> None:
        parser = build_parser()
        fetch = parser.parse_args(
            [
                "cnki-zotero",
                "fetch",
                "--query",
                "工程控制论",
                "--field",
                "subject",
                "--sort",
                "latest",
                "--project-root",
                "C:\\project",
            ]
        )
        self.assertEqual(fetch.action, "fetch")
        self.assertEqual(fetch.search_type, "subject")
        self.assertEqual(fetch.output, "auto")
        self.assertFalse(parser.parse_args(["cnki-zotero", "browser-download", "--input", "x.json"]).no_stop_on_captcha)

        find = parser.parse_args(["cnki-zotero", "find", "--query", "机器学习", "--field", "keyword"])
        self.assertEqual(find.action, "find")
        self.assertEqual(find.search_type, "keyword")

        ingest = parser.parse_args(["cnki-zotero", "ingest-plan", "--project-root", "C:\\project"])
        self.assertEqual(ingest.action, "ingest-plan")
        self.assertEqual(ingest.output, "auto")

    def test_find_output_auto_uses_managed_report_path(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["cnki-zotero", "find", "--query", "机器学习", "--output", "auto"])
        report = {"ok": True, "candidates": []}
        with (
            patch.object(cnki_zotero_command, "discover_candidates_with_direct_cdp", return_value=report),
            patch.object(cnki_zotero_command, "write_cnki_report", return_value=Path("managed.json")) as writer,
            patch("builtins.print"),
        ):
            self.assertEqual(cnki_zotero_command.run(args), 0)
        writer.assert_called_once()
        self.assertIsNone(writer.call_args.args[1])
        self.assertEqual(writer.call_args.kwargs["prefix"], "cnki-zotero-discovery")

    def test_find_runtime_failure_returns_structured_report(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["cnki-zotero", "find", "--query", "机器学习", "--output", "auto"])
        with (
            patch.object(cnki_zotero_command, "discover_candidates_with_direct_cdp", side_effect=RuntimeError("missing-python-dependency:websocket-client")),
            patch.object(cnki_zotero_command, "write_cnki_report", return_value=Path("managed.json")),
            patch("builtins.print") as printer,
        ):
            self.assertEqual(cnki_zotero_command.run(args), 1)
        payload = printer.call_args.args[0]
        self.assertIn("cnki_runtime_error.v1", payload)
        self.assertIn("missing-python-dependency:websocket-client", payload)


if __name__ == "__main__":
    unittest.main()
