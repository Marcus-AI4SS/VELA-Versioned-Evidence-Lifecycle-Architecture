from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "skills"


class ReferenceFulltextAcquisitionTests(unittest.TestCase):
    def test_skill_is_registered_in_catalog_and_route(self) -> None:
        skill_path = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "reference-fulltext-acquisition"
            / "SKILL.md"
        )
        self.assertTrue(skill_path.exists())

        catalog = json.loads((SKILLS_ROOT / "catalog" / "skill_catalog.json").read_text(encoding="utf-8"))
        self.assertIn("reference-fulltext-acquisition", catalog["skills"])

        routing = json.loads((SKILLS_ROOT / "catalog" / "routing_table.json").read_text(encoding="utf-8"))
        routes = {item["id"]: item for item in routing["routes"]}
        self.assertIn("reference-fulltext-acquisition", routes)
        self.assertIn("reference-fulltext-acquisition", routes["literature-review"]["skills"])
        self.assertIn("reference-fulltext-acquisition", routes["reference-fulltext-acquisition"]["skills"])

    def test_route_policy_covers_fulltext_route_mcp(self) -> None:
        routing = json.loads((SKILLS_ROOT / "catalog" / "routing_table.json").read_text(encoding="utf-8"))
        policies = json.loads(
            (SKILLS_ROOT / "catalog" / "route_mcp_activation_policy.json").read_text(encoding="utf-8")
        )
        route = next(item for item in routing["routes"] if item["id"] == "reference-fulltext-acquisition")
        policy = next(item for item in policies["routes"] if item["route_id"] == "reference-fulltext-acquisition")
        policy_mcp = set(policy["required_mcp"]) | set(policy["optional_mcp"]) | set(policy["activation_needed_mcp"])
        self.assertEqual(set(route["mcp"]), policy_mcp)

    def test_sync_script_installs_runtime_skill(self) -> None:
        sync_script = (SKILLS_ROOT / "scripts" / "sync_research_autopilot_skills.ps1").read_text(encoding="utf-8")
        self.assertIn('"reference-fulltext-acquisition"', sync_script)
        self.assertIn("standalone_skills_synced", sync_script)
        self.assertIn("PluginCacheOnly", sync_script)

    def test_english_fulltext_fallback_prefers_scholar_right_side_pdf(self) -> None:
        skill_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "reference-fulltext-acquisition"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        workflow_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "reference-fulltext-acquisition"
            / "references"
            / "fulltext-acquisition-workflow.md"
        ).read_text(encoding="utf-8")
        self.assertIn("批量阶段没有取得可校验 PDF", skill_text)
        self.assertIn("必要时进入“所有版本”和定向查询", skill_text)
        self.assertIn("优先在用户已登录 Chrome 中点击右侧 `[PDF] domain`", skill_text)
        self.assertIn("自动进入 Google Scholar 单篇检索", workflow_text)
        self.assertIn("右侧的 `[PDF] domain`", workflow_text)
        self.assertIn("Google Scholar 逐篇点击补抓", workflow_text)
        self.assertIn("google_scholar_all_versions_status.csv", workflow_text)

    def test_browser_visible_pdf_recovery_and_identity_audit_are_required(self) -> None:
        skill_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "reference-fulltext-acquisition"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        workflow_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "reference-fulltext-acquisition"
            / "references"
            / "fulltext-acquisition-workflow.md"
        ).read_text(encoding="utf-8")
        self.assertIn("优先调用用户已登录 Chrome", skill_text)
        self.assertIn("不能只用脚本 HTTP 请求直拉后判定成败", skill_text)
        self.assertIn("Google Scholar 右侧 `[PDF]` 只是候选，不是身份确认", skill_text)
        self.assertIn("双独立审核", skill_text)
        self.assertIn("用户 Chrome 优先规则", workflow_text)
        self.assertIn("browser_download_recovery_status.csv", workflow_text)
        self.assertIn("dual_agent_manual_acceptance.csv", workflow_text)
        self.assertIn("acquired_dual_agent_identity_accepted_open_version", workflow_text)
        self.assertIn("response/comment/review", workflow_text)

    def test_writing_capture_and_fulltext_descriptions_are_distinct(self) -> None:
        writing_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "writing-reference-capture"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        fulltext_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "reference-fulltext-acquisition"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("only the papers actually cited or used", writing_text)
        self.assertIn("Not for downloading PDFs", writing_text)
        self.assertIn("obtain and verify full-text PDFs", fulltext_text)
        self.assertIn("Not for final writing citation capture", fulltext_text)

    def test_keyword_harvest_adapter_keeps_social_science_boundaries(self) -> None:
        fulltext_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "reference-fulltext-acquisition"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        evidence_text = (
            SKILLS_ROOT
            / "plugins"
            / "research-autopilot"
            / "skills"
            / "evidence-based-literature-workflow"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Keyword Harvest Adapter", fulltext_text)
        self.assertIn("no-dedup candidate table", fulltext_text)
        self.assertIn("PDF folder PDF-only", fulltext_text)
        self.assertIn("PubMed, PMC, or Europe PMC only", fulltext_text)
        self.assertIn("raw no-dedup candidate table", evidence_text)
        self.assertIn("PubMed/PMC/Europe PMC are not default search layers", evidence_text)


if __name__ == "__main__":
    unittest.main()
