from __future__ import annotations



import json

import os

import tempfile

import unittest

from pathlib import Path



from scripts import vela_runtime

from scripts import vela_schema





class LocalRuntimeBootstrapTests(unittest.TestCase):

    def test_runtime_manifest_declares_source_runtime_boundary(self) -> None:

        manifest = json.loads(vela_runtime.RUNTIME_MANIFEST_PATH.read_text(encoding="utf-8"))

        errors = vela_schema.validate_payload(manifest, "vela.local_runtime.manifest.v1", "runtime_manifest")



        self.assertEqual(errors, [])

        self.assertEqual(manifest["schema_version"], "vela.local_runtime.manifest.v1")

        self.assertIn("VELA repository package", manifest["boundary"]["source_authority"]["role"])
        self.assertIn("User runtime", manifest["boundary"]["runtime_authority"]["role"])
        self.assertIn("external memory service data stores", manifest["boundary"]["never_export"])
        self.assertTrue(any(item["id"] == "memory.local-contracts" for item in manifest["components"]))



    def test_runtime_plan_uses_explicit_codex_and_vela_targets(self) -> None:

        with tempfile.TemporaryDirectory() as root:

            base = Path(root)

            plan = vela_runtime.plan_runtime(

                codex_home=base / "codex",

                vela_home=base / "vela",

                include="core,toolchain",

            )

            errors = vela_schema.validate_payload(plan, "vela.local_runtime.plan.v1", "runtime_plan")



            self.assertEqual(errors, [])

            self.assertTrue(plan["ok"], plan["errors"])

            self.assertFalse(plan["ready"])

            self.assertEqual(plan["paths"]["codex_home"], str(base / "codex"))

            self.assertEqual(plan["paths"]["vela_home"], str(base / "vela"))

            self.assertTrue(any(item["id"] == "core.vela-runtime" for item in plan["components"]))


    def test_install_runtime_dry_run_does_not_write_receipt(self) -> None:

        with tempfile.TemporaryDirectory() as root:

            base = Path(root)

            result = vela_runtime.install_runtime(

                codex_home=base / "codex",

                vela_home=base / "vela",

                include="core",

                commit=False,

            )



            self.assertTrue(result["ok"], result["errors"])

            self.assertEqual(result["mode"], "install-dry-run")

            self.assertFalse((base / "vela" / "state" / vela_runtime.RUNTIME_RECEIPT_NAME).exists())



    def test_install_runtime_commit_installs_core_and_writes_receipt(self) -> None:

        with tempfile.TemporaryDirectory() as root:

            base = Path(root)

            result = vela_runtime.install_runtime(

                codex_home=base / "codex",

                vela_home=base / "vela",

                include="core,automation,toolchain",

                python_executable="python",

                commit=True,

            )

            receipt_path = base / "vela" / "state" / vela_runtime.RUNTIME_RECEIPT_NAME



            self.assertTrue(result["ok"], result["errors"])

            self.assertTrue(receipt_path.exists())

            self.assertTrue((base / "codex" / "skills" / "research-autopilot" / "SKILL.md").exists())

            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

            self.assertEqual(receipt["schema_version"], "vela.local_runtime.install.receipt.v1")

            self.assertTrue(any(action["id"] == "core.vela-runtime" for action in receipt["actions"]))
            doctor = vela_runtime.doctor_runtime(codex_home=base / "codex", vela_home=base / "vela", include="core,automation,toolchain", strict=True)

            self.assertTrue(doctor["ready"])

            self.assertIn("ready", doctor["next_action"].lower())



    @unittest.skipUnless(os.name == "nt", "Windows .cmd shim probing is platform-specific")

    def test_runtime_probe_handles_windows_cmd_shims(self) -> None:

        with tempfile.TemporaryDirectory() as root:

            base = Path(root)

            shim = base / "fake-runtime-tool.cmd"

            shim.write_text("@echo off\necho Connected -- v0.0.0\nexit /b 0\n", encoding="ascii")

            previous_path = os.environ.get("PATH", "")

            os.environ["PATH"] = str(base) + os.pathsep + previous_path

            try:

                result = vela_runtime._probe_command("fake-runtime-tool", ["status"])

            finally:

                os.environ["PATH"] = previous_path



            self.assertTrue(result["ok"], result)

            self.assertIn("Connected", result["stdout_head"])



    @unittest.skipUnless(os.name == "nt", "Windows .cmd shim probing is platform-specific")

    def test_codegraph_status_handles_windows_cmd_shims(self) -> None:

        with tempfile.TemporaryDirectory() as root:

            base = Path(root)

            shim = base / "codegraph.cmd"

            shim.write_text(

                '@echo off\n'

                'echo {"initialized":true,"nodeCount":12,"edgeCount":34}\n'

                'exit /b 0\n',

                encoding="ascii",

            )

            previous_path = os.environ.get("PATH", "")

            os.environ["PATH"] = str(base) + os.pathsep + previous_path

            try:

                result = vela_runtime._codegraph_status(base / "project")

            finally:

                os.environ["PATH"] = previous_path



            self.assertTrue(result["ok"], result)

            self.assertTrue(result["initialized"])

            self.assertEqual(result["node_count"], 12)

            self.assertEqual(result["edge_count"], 34)





if __name__ == "__main__":

    unittest.main()
