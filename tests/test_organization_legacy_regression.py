import unittest
from pathlib import Path


class OrganizationLegacyRegressionTest(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.org = (
            root / "web/js/pages/organizationPage.js"
        ).read_text(encoding="utf-8")
        self.sidebar = (
            root / "web/js/layout/sidebar.js"
        ).read_text(encoding="utf-8")

    def test_legacy_mode_is_wired(self):
        self.assertIn("manhwateca:organization-legacy", self.org)
        self.assertIn("manhwateca:organization-legacy", self.sidebar)
        self.assertIn("setOrganizationMode(false)", self.org)

    def test_update_topbar_does_not_show_static_status(self):
        start = self.org.index("function updateTopbar(config)")
        end = self.org.index("function restoreTopbar", start)
        block = self.org[start:end]
        self.assertNotIn("config.status", block)
        self.assertIn("staticStatus.hidden = true", block)

    def test_step_5_and_6_are_preserved(self):
        self.assertIn("validate_chapters", self.org)
        self.assertIn("review_pending", self.org)


if __name__ == "__main__":
    unittest.main()
