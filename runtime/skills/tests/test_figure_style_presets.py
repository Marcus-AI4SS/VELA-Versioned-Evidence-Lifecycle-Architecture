from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1]
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))


class FigureStylePresetsTests(unittest.TestCase):
    def test_figure_style_presets_contract_validates(self) -> None:
        from scripts.envctl.figure_style_presets import validate_figure_style_presets

        result = validate_figure_style_presets()
        self.assertTrue(result["ok"], result)

    def test_default_presets_are_social_science_nature_red_blue_rainbow(self) -> None:
        payload = json.loads((SKILLS_ROOT / "catalog" / "figure_style_presets.json").read_text(encoding="utf-8"))
        defaults = payload["default_presets"]
        self.assertEqual(defaults["formal_research_figure"], "social_science_nature_red_blue_rainbow")
        self.assertEqual(defaults["empirical_figure"], "nature_empirical_red_blue_rainbow")
        self.assertEqual(defaults["review_ready_figure"], "minimal_review_ready_red_blue")
        self.assertEqual(defaults["presentation_figure"], "presentation_premium_red_blue_rainbow")

    def test_image2_prompt_contract_prevents_random_style_and_overlap(self) -> None:
        payload = json.loads((SKILLS_ROOT / "catalog" / "figure_style_presets.json").read_text(encoding="utf-8"))
        presets = {item["id"]: item for item in payload["presets"]}
        formal = presets["social_science_nature_red_blue_rainbow"]
        tokens = set(formal["image2_prompt_requirements"]["prompt_tokens"])
        self.assertTrue(
            {
                "red_blue_rainbow_palette",
                "no_internal_title",
                "no_long_caption",
                "no_overlap",
                "exact_text",
                "no_fake_data",
            }
            <= tokens
        )
        phrases = "\n".join(formal["image2_prompt_requirements"]["required_phrases"])
        self.assertIn("red-blue anchored Nature-style rainbow color palette", phrases)
        self.assertIn("no figure title inside the image", phrases)
        self.assertIn("no long caption inside the image", phrases)
        self.assertIn("no overlapping text", phrases)
        self.assertIn("no invented data", phrases)

    def test_empirical_preset_forbids_image2_data_generation(self) -> None:
        payload = json.loads((SKILLS_ROOT / "catalog" / "figure_style_presets.json").read_text(encoding="utf-8"))
        presets = {item["id"]: item for item in payload["presets"]}
        empirical = presets["nature_empirical_red_blue_rainbow"]
        self.assertIn("image2-generated empirical data", empirical["forbidden_elements"])
        self.assertIn("invented p-values", empirical["forbidden_elements"])
        self.assertIn("invented sample sizes", empirical["forbidden_elements"])
        self.assertIn("legend covering data", empirical["forbidden_elements"])

    def test_quality_gate_contains_new_visual_checks(self) -> None:
        gates = json.loads((SKILLS_ROOT / "catalog" / "quality_gates.json").read_text(encoding="utf-8"))
        gate = next(item for item in gates["gates"] if item["id"] == "figure_table_consistency_checked")
        required = set(gate["required_checks"])
        self.assertTrue(
            {
                "figure_style_preset_selected",
                "red_blue_rainbow_palette_checked",
                "title_caption_outside_image_checked",
                "visual_overlap_checked",
            }
            <= required
        )


if __name__ == "__main__":
    unittest.main()
