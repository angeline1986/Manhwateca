import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from manhwateca.flows.domain import StageId
from manhwateca.flows.integrations import IntegrationStatus
from manhwateca.flows.library import LocalLibraryIntegration


class LocalLibraryIntegrationTests(unittest.TestCase):
    def test_validate_requires_configured_library(self):
        integration = LocalLibraryIntegration()

        with patch.dict("os.environ", {"MANGA_ROOT": ""}):
            validation = integration.validate(StageId.ORGANIZE_LIBRARY)

        self.assertFalse(validation.valid)
        self.assertEqual("LIBRARY_NOT_CONFIGURED", validation.errors[0].code)

    def test_validate_rejects_missing_directory(self):
        integration = LocalLibraryIntegration("/tmp/manhwateca-missing-library")

        validation = integration.validate(StageId.ORGANIZE_LIBRARY)

        self.assertFalse(validation.valid)
        self.assertEqual("LIBRARY_NOT_FOUND", validation.errors[0].code)

    def test_scan_empty_library_returns_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            integration = LocalLibraryIntegration(directory)

            result = integration.scan_library()

        self.assertEqual(0, result.works_found)
        self.assertTrue(result.inconsistencies)
        self.assertEqual("LIBRARY_EMPTY", result.inconsistencies[0].code)

    def test_scan_library_reports_works_chapters_and_pending_moves(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / "Zeta"
            work.mkdir()
            (work / "Cap 001.cbz").write_text("content", encoding="utf-8")

            result = LocalLibraryIntegration(root).scan_library()

        self.assertEqual(1, result.works_found)
        self.assertEqual(1, result.chapters_found)
        self.assertEqual(0, result.correct_locations)
        self.assertEqual(1, result.pending_moves)
        self.assertEqual(0, result.conflicts)
        self.assertEqual(0, result.duplicates)

    def test_check_status_reports_operational_library(self):
        with tempfile.TemporaryDirectory() as directory:
            status = LocalLibraryIntegration(directory).check_status()

        self.assertEqual(IntegrationStatus.OPERATIONAL, status.status)

    def test_scan_inaccessible_library_raises_runtime_error(self):
        integration = LocalLibraryIntegration("/tmp/manhwateca-missing-library")

        with self.assertRaisesRegex(RuntimeError, "Biblioteca não encontrada"):
            integration.scan_library()


if __name__ == "__main__":
    unittest.main()
