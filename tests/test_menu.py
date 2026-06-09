import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import menu


class MenuTests(unittest.TestCase):
    @patch("menu.subprocess.run")
    def test_run_command_uses_project_root(self, run):
        run.return_value.returncode = 0

        result = menu.run_command(["scripts/scan.py"])

        self.assertTrue(result)
        run.assert_called_once_with(
            [sys.executable, "scripts/scan.py"],
            cwd=menu.PROJECT_ROOT,
            check=False,
        )

    @patch("menu.run_command")
    @patch("builtins.input", return_value="cancelar")
    def test_sync_requires_exact_confirmation(self, _input, run_command):
        result = menu.confirm_sync()

        self.assertFalse(result)
        run_command.assert_not_called()

    @patch("menu.run_command")
    @patch("builtins.input", return_value="1")
    def test_confirmed_sync_uses_apply(self, _input, run_command):
        run_command.return_value = True

        result = menu.confirm_sync()

        self.assertTrue(result)
        run_command.assert_called_once_with(["scripts/sync.py", "--apply"])

    @patch("menu.run_command")
    @patch("builtins.input", return_value="1")
    def test_notion_submenu_catalogs_library(self, _input, run_command):
        run_command.return_value = True

        result = menu.notion_menu()

        self.assertTrue(result)
        run_command.assert_called_once_with(["scripts/scan.py"])

    @patch("menu.run_command")
    @patch("builtins.input", return_value="2")
    def test_notion_submenu_runs_simulation(self, _input, run_command):
        run_command.return_value = True

        result = menu.notion_menu()

        self.assertTrue(result)
        run_command.assert_called_once_with(["scripts/sync.py"])

    @patch("menu.confirm_sync")
    @patch("builtins.input", return_value="3")
    def test_notion_submenu_can_apply(self, _input, confirm_sync):
        confirm_sync.return_value = True

        result = menu.notion_menu()

        self.assertTrue(result)
        confirm_sync.assert_called_once_with()

    @patch("menu.generate_reports")
    @patch("builtins.input", return_value="1")
    def test_standardization_submenu_generates_reports(
        self, _input, generate_reports
    ):
        generate_reports.return_value = True

        result = menu.standardization_menu()

        self.assertTrue(result)
        generate_reports.assert_called_once_with()

    @patch("menu.apply_file_names")
    @patch("builtins.input", return_value="2")
    def test_standardization_submenu_can_apply(
        self, _input, apply_file_names
    ):
        apply_file_names.return_value = True

        result = menu.standardization_menu()

        self.assertTrue(result)
        apply_file_names.assert_called_once_with()

    @patch("menu.run_command")
    @patch("builtins.input", return_value="1")
    def test_organization_requires_confirmation(self, _input, run_command):
        run_command.return_value = True

        result = menu.apply_organization()

        self.assertTrue(result)
        run_command.assert_called_once_with(["scripts/organize.py", "--apply"])

    @patch("menu.run_command")
    @patch("builtins.input", return_value="1")
    def test_file_rename_requires_confirmation(self, _input, run_command):
        run_command.return_value = True

        result = menu.apply_file_names()

        self.assertTrue(result)
        run_command.assert_called_once_with(
            ["scripts/rename_files.py", "--apply"]
        )

    def test_review_note_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            notes_path = Path(directory) / "review_notes.md"
            with (
                patch("menu.REVIEW_NOTES", notes_path),
                patch("builtins.input", return_value="Corrigir título da obra"),
            ):
                result = menu.register_review_note()

            self.assertTrue(result)
            self.assertIn(
                "- [ ] Corrigir título da obra",
                notes_path.read_text(encoding="utf-8"),
            )

    @patch("menu.run_command")
    def test_full_flow_stops_after_failure(self, run_command):
        run_command.side_effect = [True, False]

        result = menu.run_full_flow()

        self.assertFalse(result)
        self.assertEqual(2, run_command.call_count)

    @patch("menu.run_command", return_value=True)
    def test_full_flow_runs_reports_before_scan(self, run_command):
        result = menu.run_full_flow()

        self.assertTrue(result)
        self.assertEqual(
            [
                unittest.mock.call(["scripts/organize.py"]),
                unittest.mock.call(["scripts/rename_files.py"]),
                unittest.mock.call(["scripts/scan.py"]),
                unittest.mock.call(["scripts/sync.py"]),
            ],
            run_command.call_args_list,
        )


if __name__ == "__main__":
    unittest.main()
