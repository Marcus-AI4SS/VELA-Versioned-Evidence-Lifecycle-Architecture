from __future__ import annotations



import json

import tempfile

import unittest

from pathlib import Path



from scripts import vela_runtime_install


class RuntimeInstallTests(unittest.TestCase):
    def test_install_runtime_into_clean_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as root:

            base = Path(root)

            codex_home = base / "codex"

            vela_home = base / "vela"

            result = vela_runtime_install.install_runtime_core(
                codex_home=codex_home,

                vela_home=vela_home,

                python_executable="python",

            )

            self.assertTrue(result["ok"])

            self.assertGreaterEqual(result["installed_skill_count"], 10)

            self.assertTrue((codex_home / "skills" / "research-autopilot" / "SKILL.md").exists())

            marker = json.loads((codex_home / "skills" / "research-autopilot" / ".vela-managed.json").read_text(encoding="utf-8"))

            self.assertEqual(marker["manager"], "VELA")

            self.assertTrue((vela_home / "runtime" / "manifest.json").exists())
            self.assertTrue((vela_home / "bin" / "envctl.cmd").exists())



            doctor = vela_runtime_install.doctor_runtime_core(codex_home=codex_home, vela_home=vela_home)
            self.assertTrue(doctor["ok"], doctor["errors"])



    def test_install_refuses_unmanaged_skill_conflict_without_force(self) -> None:

        with tempfile.TemporaryDirectory() as root:

            base = Path(root)

            codex_home = base / "codex"

            vela_home = base / "vela"

            conflict = codex_home / "skills" / "research-autopilot"

            conflict.mkdir(parents=True)

            (conflict / "SKILL.md").write_text("# User skill\n", encoding="utf-8")



            result = vela_runtime_install.install_runtime_core(codex_home=codex_home, vela_home=vela_home)
            self.assertFalse(result["ok"])

            self.assertIn("research-autopilot", result["conflicts"])

            self.assertEqual((conflict / "SKILL.md").read_text(encoding="utf-8"), "# User skill\n")



    def test_install_force_backs_up_unmanaged_skill_conflict(self) -> None:

        with tempfile.TemporaryDirectory() as root:

            base = Path(root)

            codex_home = base / "codex"

            vela_home = base / "vela"

            conflict = codex_home / "skills" / "research-autopilot"

            conflict.mkdir(parents=True)

            (conflict / "SKILL.md").write_text("# User skill\n", encoding="utf-8")



            result = vela_runtime_install.install_runtime_core(codex_home=codex_home, vela_home=vela_home, force=True)
            self.assertTrue(result["ok"], result["errors"])

            self.assertEqual(len(result["backups"]), 1)

            backup = Path(result["backups"][0]["backup"])

            self.assertTrue((backup / "SKILL.md").exists())

            marker = codex_home / "skills" / "research-autopilot" / ".vela-managed.json"

            self.assertTrue(marker.exists())





if __name__ == "__main__":

    unittest.main()
