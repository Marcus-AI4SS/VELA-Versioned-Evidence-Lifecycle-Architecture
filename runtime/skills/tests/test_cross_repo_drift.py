from __future__ import annotations



import sys

import unittest

from pathlib import Path





ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



from scripts.envctl.cross_repo_drift import validate_cross_repo_drift





class CrossRepoDriftTests(unittest.TestCase):

    def test_current_repos_have_no_contract_drift(self) -> None:

        result = validate_cross_repo_drift()

        self.assertEqual(result["warnings"], [])

        self.assertEqual(result["errors"], [])

        self.assertTrue(result["ok"])





if __name__ == "__main__":

    unittest.main()
