from __future__ import annotations



import sys

import unittest

from pathlib import Path





ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



from scripts.envctl.helm_snapshot import build_helm_snapshot_manifest, validate_helm_snapshot_contract





class HelmSnapshotContractTests(unittest.TestCase):

    def test_snapshot_manifest_is_schema_valid_and_private_safe(self) -> None:

        result = validate_helm_snapshot_contract()

        self.assertEqual(result["errors"], [])

        self.assertTrue(result["ok"])

        self.assertEqual(result["details"]["privacy_scan"]["findings"], [])



    def test_snapshot_excludes_outputs_and_runtime(self) -> None:

        manifest = build_helm_snapshot_manifest(generated_at="2026-05-05T00:00:00Z")

        self.assertIn("skills/outputs", manifest["excluded_roots"])

        self.assertIn("python/runtime", manifest["excluded_roots"])

        self.assertIn("skills/catalog/settings.toml", manifest["excluded_roots"])

        self.assertIn("skills/schemas/helm_snapshot_manifest.schema.json", manifest["schema_files"])





if __name__ == "__main__":

    unittest.main()
