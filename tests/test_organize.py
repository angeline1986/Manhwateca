import sys
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import organize
from manhwateca.library_organizer.report import generate_report


def plan_item(source, destination):
    return {
        "name": source.name,
        "source": source,
        "destination": destination,
        "group": destination.parent.name,
        "current_group": source.parent.name,
        "exists": destination.exists(),
        "is_correct": source == destination,
        "main_caps": 1,
        "side_caps": 0,
        "total_caps": 1,
    }


class OrganizeTests(unittest.TestCase):
    def test_report_prioritizes_pending_moves_and_collapses_correct_works(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "organize_preview.html"
            correct_xyz = plan_item(
                root / "XYZ" / "Zeta",
                root / "XYZ" / "Zeta",
            )
            correct_a = plan_item(root / "A" / "Alpha", root / "A" / "Alpha")
            pending = plan_item(root / "status" / "Beta", root / "BC" / "Beta")

            generate_report(
                [correct_xyz, correct_a, pending],
                [],
                [],
                [],
                report,
                True,
            )
            rendered = report.read_text(encoding="utf-8")

        self.assertIn("O que será alterado", rendered)
        self.assertIn("Obras já organizadas", rendered)
        self.assertIn('data-filter="move"', rendered)
        self.assertIn("Beta", rendered)
        self.assertIn('BC/<strong class="work-folder">Beta</strong>', rendered)
        self.assertIn(
            '<strong class="work-folder">Beta</strong>',
            rendered,
        )
        self.assertLess(
            rendered.index("<strong>A</strong>"),
            rendered.index("<strong>XYZ</strong>"),
        )
        self.assertNotIn(str(root), rendered.split("<script>")[0])
        self.assertNotIn("Expandir Tudo", rendered)

    def test_detects_pdf_without_chapter_keyword(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Um homem casado"
            path.mkdir()
            (path / "Um homem casado 1 ao 20.pdf").touch()

            self.assertTrue(organize.is_manga_folder(path))

    def test_detects_cover_only_but_ignores_empty_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cover_only = root / "Butler"
            empty_work = root / "Swim in the Scent"
            cover_only.mkdir()
            empty_work.mkdir()
            (cover_only / "Butler.jpeg").touch()

            self.assertTrue(organize.is_manga_folder(cover_only))
            self.assertFalse(organize.is_manga_folder(empty_work))

            legacy_container = root / "02_Legalzin"
            legacy_container.mkdir()
            legacy_empty_work = legacy_container / "Swim in the Scent"
            legacy_empty_work.mkdir()
            (legacy_empty_work / ".DS_Store").touch()

            self.assertFalse(organize.is_manga_folder(legacy_empty_work))
            self.assertEqual(
                [legacy_empty_work],
                organize.find_empty_legacy_folders(root),
            )

    def test_ignores_legacy_status_containers(self):
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory) / "03_Medio"
            container.mkdir()

            self.assertFalse(organize.is_manga_folder(container))

    def test_apply_moves_child_before_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "status" / "Novos"
            child = parent / "Obra"
            child.mkdir(parents=True)
            (parent / "cap 1.pdf").touch()
            (child / "cap 1.pdf").touch()

            child_destination = root / "O" / "Obra"
            parent_destination = root / "N" / "Novos"
            plan = [
                plan_item(parent, parent_destination),
                plan_item(child, child_destination),
            ]

            with patch("organize.DRY_RUN", False):
                result = organize.apply_plan(plan, [], [])

            self.assertTrue(result)
            self.assertTrue(child_destination.exists())
            self.assertTrue(parent_destination.exists())
            self.assertFalse(parent.exists())

    def test_apply_stops_before_moving_when_source_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "status" / "Obra"
            existing.mkdir(parents=True)
            missing = root / "status" / "Ausente"
            plan = [
                plan_item(existing, root / "O" / "Obra"),
                plan_item(missing, root / "A" / "Ausente"),
            ]

            with patch("organize.DRY_RUN", False):
                result = organize.apply_plan(plan, [], [])

            self.assertFalse(result)
            self.assertTrue(existing.exists())
            self.assertFalse((root / "O" / "Obra").exists())

    def test_successful_move_is_written_to_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "status" / "Obra"
            destination = root / "O" / "Obra"
            history = root / "history.jsonl"
            source.mkdir(parents=True)

            with (
                patch("organize.DRY_RUN", False),
                patch("organize.HISTORY_PATH", history),
            ):
                result = organize.apply_plan(
                    [plan_item(source, destination)],
                    [],
                    [],
                )

            entry = json.loads(history.read_text(encoding="utf-8"))
            self.assertTrue(result)
            self.assertEqual("movido", entry["status"])
            self.assertEqual(str(source), entry["source"])
            self.assertEqual(str(destination), entry["destination"])

    def test_apply_regenerates_report_with_final_library_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "status" / "Obra"
            report = root / "organize_preview.html"
            history = root / "history.jsonl"
            source.mkdir(parents=True)
            (source / "Obra cap 1.pdf").touch()

            with (
                patch("organize.MANGA_ROOT", root),
                patch("organize.REPORT_PATH", report),
                patch("organize.HISTORY_PATH", history),
            ):
                result = organize.organize(apply=True)

            rendered = report.read_text(encoding="utf-8")
            applied_entry = json.loads(history.read_text(encoding="utf-8"))
            destination_exists = Path(applied_entry["destination"]).exists()

        self.assertTrue(result)
        self.assertFalse(source.exists())
        self.assertTrue(destination_exists)
        self.assertIn("0</strong><span>Pastas a mover", rendered)
        self.assertIn("Nenhuma pasta precisa ser movida", rendered)
        self.assertNotIn("Será movido", rendered)

    def test_case_only_folder_rename_is_not_a_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "illusion"
            destination = root / "Illusion"
            source.mkdir()
            plan = [plan_item(source, destination)]

            conflicts = organize.detect_conflicts(plan)

            self.assertEqual([], conflicts)

    def test_apply_handles_case_only_folder_rename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "illusion"
            destination = root / "Illusion"
            source.mkdir()
            item = plan_item(source, destination)

            with patch("organize.DRY_RUN", False):
                result = organize.apply_plan([item], [], [])

            self.assertTrue(result)
            self.assertEqual(["Illusion"], [path.name for path in root.iterdir()])


if __name__ == "__main__":
    unittest.main()
