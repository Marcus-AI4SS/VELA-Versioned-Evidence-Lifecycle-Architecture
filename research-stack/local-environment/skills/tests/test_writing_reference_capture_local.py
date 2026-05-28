import unittest

from scripts.writing_reference_capture_local import (
    normalize_doi,
    resolve_project_slug,
    select_zotero_target,
)


class WritingReferenceCaptureLocalTests(unittest.TestCase):
    def test_normalize_doi_strips_url_prefix(self) -> None:
        self.assertEqual(
            normalize_doi("https://doi.org/10.1126/science.1167742"),
            "10.1126/science.1167742",
        )

    def test_resolve_project_slug_generates_ascii_slug(self) -> None:
        self.assertEqual(
            resolve_project_slug("CSS Writing Demo 2026"),
            "css-writing-demo-2026",
        )

    def test_select_zotero_target_prefers_exact_collection_match(self) -> None:
        targets = [
            {"id": "L1", "name": "我的文库", "level": 0},
            {"id": "C2", "name": "毕业论文", "level": 1},
            {"id": "C3", "name": "体制", "level": 2},
        ]
        target = select_zotero_target(
            targets=targets,
            project_name="毕业论文",
            requested_target_id=None,
            current_target_id="C3",
            allow_library_root_fallback=False,
            prefer_current_target=False,
        )
        self.assertEqual(target["id"], "C2")

    def test_select_zotero_target_can_fallback_to_library_root(self) -> None:
        targets = [
            {"id": "L1", "name": "我的文库", "level": 0},
            {"id": "C2", "name": "毕业论文", "level": 1},
        ]
        target = select_zotero_target(
            targets=targets,
            project_name="不存在的项目",
            requested_target_id=None,
            current_target_id="C2",
            allow_library_root_fallback=True,
            prefer_current_target=False,
        )
        self.assertEqual(target["id"], "L1")


if __name__ == "__main__":
    unittest.main()
