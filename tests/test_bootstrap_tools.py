from __future__ import annotations



import unittest

from unittest.mock import patch



from scripts import vela_bootstrap

from scripts import vela

from scripts import vela_schema





class BootstrapToolsTests(unittest.TestCase):

    def test_bootstrap_plan_is_schema_valid_and_lists_core_tools(self) -> None:

        plan = vela_bootstrap.plan_bootstrap_tools(include="system")

        errors = vela_schema.validate_payload(plan, "vela.local_runtime.bootstrap_tools.v1", "bootstrap_tools")



        self.assertEqual(errors, [])

        self.assertEqual(plan["schema_version"], "vela.local_runtime.bootstrap_tools.v1")

        self.assertEqual(plan["mode"], "plan")

        tool_ids = {tool["id"] for tool in plan["tools"]}

        self.assertGreaterEqual({"git", "python", "powershell", "ripgrep", "node", "github-cli"}, tool_ids)



    def test_bootstrap_plan_keeps_runtime_boundaries_explicit(self) -> None:

        plan = vela_bootstrap.plan_bootstrap_tools(include="all")



        protected = {item["id"]: item for item in plan["protected_runtime_boundaries"]}

        self.assertIn("codex-plugin-cache", protected)

        self.assertIn("browser-login-state", protected)

        self.assertIn("zotero-obsidian-private-libraries", protected)

        self.assertTrue(all(item["install_policy"] == "doctor-only" for item in protected.values()))



    def test_bootstrap_install_dry_run_reports_install_strategy_without_mutation(self) -> None:

        plan = vela_bootstrap.bootstrap_tools(include="optional", install=True, yes=False)



        self.assertEqual(plan["mode"], "install-preview")

        self.assertFalse(plan["mutated"])

        optional = {tool["id"]: tool for tool in plan["tools"]}

        self.assertNotIn("agentmemory", optional)

        self.assertIn("codegraph", optional)

        self.assertEqual(optional["codegraph"]["install_strategy"], "manual")



    def test_bootstrap_plan_uses_homebrew_strategy_on_macos(self) -> None:

        with patch("scripts.vela_bootstrap.platform.system", return_value="Darwin"):

            plan = vela_bootstrap.plan_bootstrap_tools(include="system")



        tools = {tool["id"]: tool for tool in plan["tools"]}

        self.assertEqual(tools["git"]["install_strategy"], "homebrew")

        self.assertEqual(tools["git"]["install_policy"], "explicit-bootstrap")

        self.assertEqual(tools["git"]["brew_formula"], "git")

        self.assertEqual(tools["python"]["brew_formula"], "python@3.13")

        self.assertEqual(tools["powershell"]["brew_formula"], "powershell")



    def test_bootstrap_commit_attempts_homebrew_on_macos(self) -> None:

        with patch("scripts.vela_bootstrap.platform.system", return_value="Darwin"):

            with patch("scripts.vela_bootstrap._probe_tool", return_value={"ok": False, "path": None}):

                with patch("scripts.vela_bootstrap._install_tool", return_value={"ok": False, "status": "installer-missing"}) as install_tool:

                    plan = vela_bootstrap.bootstrap_tools(include="system", install=True, yes=True)



        self.assertTrue(install_tool.called)

        self.assertIn("bootstrap-install-failed:git", plan["errors"])



    def test_cli_exposes_bootstrap_tools_command(self) -> None:

        parser = vela.build_parser()

        args = parser.parse_args(["runtime", "bootstrap-tools", "--include", "system", "--install", "--yes"])


        self.assertEqual(args.runtime_command, "bootstrap-tools")
        self.assertEqual(args.include, "system")

        self.assertTrue(args.install)

        self.assertTrue(args.yes)





if __name__ == "__main__":

    unittest.main()
