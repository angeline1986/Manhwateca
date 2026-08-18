import unittest
from pathlib import Path

class OrganizationRegressionTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.org = (self.root / "web/js/pages/organizationPage.js").read_text(encoding="utf-8")
        self.sidebar = (self.root / "web/js/layout/sidebar.js").read_text(encoding="utf-8")

    def test_legacy_mode_is_reachable(self):
        self.assertIn("manhwateca:organization-legacy", self.org)
        self.assertIn("manhwateca:organization-legacy", self.sidebar)
        self.assertIn("setOrganizationMode(false)", self.org)

    def test_static_stage_badges_are_not_rendered(self):
        self.assertNotIn('class="organization-stage-status">Somente leitura</span>', self.org)
        self.assertNotIn('class="organization-stage-status">Pronto para aplicar</span>', self.org)
        self.assertNotIn('class="organization-stage-status">${escapeHtml(config.status', self.org)

    def test_step_5_and_6_remain_registered(self):
        self.assertIn("validate_chapters:", self.org)
        self.assertIn("review_pending:", self.org)

if __name__ == "__main__":
    unittest.main()
