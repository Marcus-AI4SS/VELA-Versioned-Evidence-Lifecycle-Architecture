from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.social_platform_mcp_server import (
    _build_child_env,
    _resolve_agent_browser_exe,
    _resolve_powershell_command,
    build_runtime_probe,
)


class SocialPlatformMcpRuntimeTests(unittest.TestCase):
    def test_child_env_restores_windows_user_tool_paths(self) -> None:
        env = _build_child_env(
            {
                "PATH": r"C:\Windows\system32;C:\Windows",
                "APPDATA": str(Path.home() / "AppData" / "Roaming"),
            }
        )

        self.assertIn(str(Path.home() / "AppData" / "Roaming" / "npm"), env["PATH"])
        self.assertIsNotNone(_resolve_agent_browser_exe(env))
        self.assertTrue(Path(_resolve_powershell_command(env)).exists())

    def test_runtime_probe_launches_required_child_tools(self) -> None:
        probe = build_runtime_probe(
            {
                "PATH": r"C:\Windows\system32;C:\Windows",
                "APPDATA": str(Path.home() / "AppData" / "Roaming"),
            }
        )

        self.assertTrue(probe["ok"], probe)
        self.assertTrue(probe["powershell_launch"]["ok"], probe)
        self.assertTrue(probe["agent_browser_version"]["ok"], probe)


if __name__ == "__main__":
    unittest.main()
