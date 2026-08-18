import unittest
from pathlib import Path


class OrganizationSubtabContractTest(unittest.TestCase):
    def test_new_organization_subtabs_have_config_and_render_paths(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "web/js/pages/organizationPage.js").read_text(
            encoding="utf-8"
        )

        required_config = [
            'validate_chapters: {',
            'review_pending: {',
        ]
        required_paths = [
            'if (subtab === "validate_chapters")',
            'if (subtab === "review_pending")',
            'async function loadChapterReview()',
            'async function loadPendingReview()',
        ]

        for marker in required_config + required_paths:
            with self.subTest(marker=marker):
                self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
