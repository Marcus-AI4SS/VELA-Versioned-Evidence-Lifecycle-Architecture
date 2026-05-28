from __future__ import annotations



import sys

import unittest

from pathlib import Path





ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



from scripts.envctl.initializer_policy import validate_initializer_policy





class InitializerPolicyTests(unittest.TestCase):

    def test_current_vela_initializer_is_public_safe(self) -> None:

        result = validate_initializer_policy()

        self.assertEqual(result["errors"], [])

        self.assertEqual(result["warnings"], [])

        self.assertTrue(result["ok"])

        self.assertEqual(result["details"]["local_initializer_agents"], 6)
        self.assertIsInstance(result["details"]["vela_initializer_agents"], int)




if __name__ == "__main__":

    unittest.main()
