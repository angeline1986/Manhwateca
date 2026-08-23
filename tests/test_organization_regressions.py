import unittest
from pathlib import Path

class OrganizationRegressionTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.org = (self.root / "web/js/pages/organizationPage.js").read_text(encoding="utf-8")
        self.sidebar = (self.root / "web/js/layout/sidebar.js").read_text(encoding="utf-8")
        self.task_runner = (self.root / "web/js/tasks/taskRunner.js").read_text(encoding="utf-8")
        self.task_toast = (self.root / "web/js/tasks/taskToast.js").read_text(encoding="utf-8")

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

    def test_track_library_renders_catalog_change_details_natively(self):
        self.assertIn("renderCatalogChangeDetails(trackCatalogSnapshot)", self.org)
        self.assertIn("Ver detalhes da última catalogação", self.org)
        self.assertIn("NOVAS", self.org)
        self.assertIn("ALTERADAS", self.org)
        self.assertIn("REMOVIDAS", self.org)
        self.assertNotIn("MutationObserver", self.org)

    def test_catalog_scan_does_not_offer_legacy_pending_cta(self):
        self.assertNotIn("Ver pendências de catálogo", self.task_runner)
        self.assertNotIn("organizationCatalogPendingPanel", self.task_runner)

    def test_catalog_scan_toast_has_no_result_navigation(self):
        self.assertIn('task.action === "catalog_scan"', self.task_toast)
        self.assertIn("elements.viewTaskProgress.hidden = true", self.task_toast)
        self.assertIn('"Ver resultado"', self.task_toast)
        self.assertIn('showPage("automation")', self.task_runner)

    def test_catalog_scan_zero_new_works_shows_information_only(self):
        self.assertIn('massCatalog && uncataloged <= 0', self.task_runner)
        self.assertIn("Nenhuma nova obra encontrada", self.task_runner)
        self.assertIn("Não há novas obras para catalogar", self.task_runner)
        self.assertIn("resolve(false)", self.task_runner)

    def test_catalog_scan_with_new_works_still_confirms(self):
        self.assertIn("Confirmar Catalogação em Massa", self.task_runner)
        self.assertIn("Foi encontrada", self.task_runner)
        self.assertIn("Deseja prosseguir?", self.task_runner)

    def test_track_library_last_catalog_summary_is_preserved(self):
        self.assertIn("Última catalogação", self.org)
        self.assertIn("metrics.added", self.org)
        self.assertIn("metrics.updated", self.org)
        self.assertIn("metrics.removed", self.org)

if __name__ == "__main__":
    unittest.main()
