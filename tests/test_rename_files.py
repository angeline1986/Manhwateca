import sys
import tempfile
import unittest
from pathlib import Path
from collections import defaultdict
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import rename_files
from manhwateca.file_normalizer.report import generate_report
from rename_files import normalize_chapter_name


class RenameFilesTests(unittest.TestCase):
    def test_report_lists_only_affected_works_in_group_order(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "rename_preview.html"
            plan = defaultdict(lambda: defaultdict(list))
            plan["ST"]["Speak of the devil"].append({
                "old_name": "speak cap 1.pdf",
                "new_name": "Speak of the devil cap 1.pdf",
                "kind": "chapter",
            })
            plan["A"]["Alpha"].append({
                "old_name": "alpha.jpeg",
                "new_name": "cover.jpeg",
                "kind": "cover",
            })

            generate_report(plan, [], [], report, True)
            rendered = report.read_text(encoding="utf-8")

        self.assertNotIn("Expandir Tudo", rendered)
        self.assertNotIn(">BC<", rendered)
        self.assertLess(rendered.index(">Alpha<"), rendered.index(">Speak of the devil<"))
        self.assertIn("alpha.jpeg", rendered)
        self.assertIn("cover.jpeg", rendered)
        self.assertIn("Esta prévia não altera arquivos", rendered)

    def test_apply_regenerates_report_with_final_file_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manga = root / "A" / "Obra"
            report = root / "rename_preview.html"
            manga.mkdir(parents=True)
            old_file = manga / "obra capitulo 1.pdf"
            old_file.touch()

            with (
                patch("rename_files.MANGA_ROOT", root),
                patch("rename_files.REPORT_PATH", report),
            ):
                result = rename_files.main(apply=True)

            rendered = report.read_text(encoding="utf-8")
            renamed_files = [path.name for path in manga.iterdir()]

        self.assertTrue(result)
        self.assertEqual(["Obra cap 1.pdf"], renamed_files)
        self.assertIn("0 nomes serão ajustados em 0 obras", rendered)
        self.assertIn("Nenhum arquivo precisa ser renomeado", rendered)
        self.assertNotIn("Será renomeado", rendered)

    def test_uses_folder_name_as_canonical_title(self):
        result = normalize_chapter_name(
            "xx cheio de segredos cap 13 FIM.pdf",
            "XX Cheio de Segredos",
        )

        self.assertEqual(
            "XX Cheio de Segredos cap 13 FIM.pdf",
            result,
        )

    def test_preserves_chapter_range_and_note(self):
        result = normalize_chapter_name(
            "titulo alternativo Capítulo 25=28.5 - Fim da Temporada.pdf",
            "Título Oficial",
        )

        self.assertEqual(
            "Título Oficial cap 25-28.5 - Fim da Temporada.pdf",
            result,
        )

    def test_keeps_original_prefix_without_canonical_title(self):
        result = normalize_chapter_name("Obra capitulo 1 ao 5.pdf")

        self.assertEqual("Obra cap 1-5.pdf", result)

    def test_uses_canonical_title_for_side_story(self):
        result = normalize_chapter_name(
            "Maré baixa side story 1=11.pdf",
            "Low tide - Mare Baixa no crepusculo",
        )

        self.assertEqual(
            "Low tide - Mare Baixa no crepusculo side story 1-11.pdf",
            result,
        )

    def test_uses_canonical_title_for_prologue(self):
        result = normalize_chapter_name(
            "Winterfield prólogo.pdf",
            "WinterField",
        )

        self.assertEqual("WinterField prólogo.pdf", result)

    def test_does_not_duplicate_side_in_title(self):
        result = normalize_chapter_name(
            "Dark Fall Side Story 5=8.pdf",
            "Dark Fall Side",
        )

        self.assertEqual("Dark Fall Side story 5-8.pdf", result)

    def test_normalizes_symbol_used_as_chapter_range(self):
        result = normalize_chapter_name(
            "Second Half cap 2 🔰 8.pdf",
            "Second Half",
        )

        self.assertEqual("Second Half cap 2-8.pdf", result)

    def test_normalizes_underscore_around_chapter_marker(self):
        result = normalize_chapter_name(
            "Transmigrating_as_Mr_Alpha's_Golden_Goose_cap_14=17.pdf",
            "A Gansa Dourada do Alfa",
        )

        self.assertEqual(
            "A Gansa Dourada do Alfa cap 14-17.pdf",
            result,
        )

    def test_normalizes_side_story_range(self):
        result = normalize_chapter_name(
            "Drive's high side story 1=10 Fim.pdf",
            "Drive's high",
        )

        self.assertEqual(
            "Drive's high side story 1-10 Fim.pdf",
            result,
        )

    def test_normalizes_range_without_chapter_marker(self):
        result = normalize_chapter_name(
            "Um homem casado 1 ao 20.pdf",
            "Um homem casado",
        )

        self.assertEqual("Um homem casado cap 1-20.pdf", result)

    def test_fixes_side_story_typo(self):
        result = normalize_chapter_name(
            "Noite de Londres cap side stoy 1=5 FIM.pdf",
            "Noite de Londres",
        )

        self.assertEqual(
            "Noite de Londres side story 1-5 FIM.pdf",
            result,
        )

    def test_adds_missing_chapter_marker(self):
        result = normalize_chapter_name(
            "Um homem casado 1 ao 20.pdf",
            "Um homem casado",
        )

        self.assertEqual("Um homem casado cap 1-20.pdf", result)

    def test_removes_trailing_underscore(self):
        result = normalize_chapter_name(
            "Até logo rei cap 122 - Início da 4ª temporada_.pdf",
            "Até logo rei",
        )

        self.assertEqual(
            "Até logo rei cap 122 - Início da 4ª temporada.pdf",
            result,
        )

    def test_normalizes_underscored_range_and_note(self):
        result = normalize_chapter_name(
            "Muhyeok e Naui cap 21_ao_32_FIM_DA.pdf",
            "Muhyeok e Naui",
        )

        self.assertEqual(
            "Muhyeok e Naui cap 21-32 FIM DA.pdf",
            result,
        )

    def test_normalizes_space_separated_chapter_range(self):
        result = normalize_chapter_name(
            "The Dokkaebi’s Soul Qi Bride cap 22 23.pdf",
            "The Dokkaebi’s Soul Qi Bride",
        )

        self.assertEqual(
            "The Dokkaebi’s Soul Qi Bride cap 22-23.pdf",
            result,
        )

    def test_normalizes_side_story_to_lowercase(self):
        result = normalize_chapter_name(
            "Obra Side Story 1-3.pdf",
            "Obra",
        )

        self.assertEqual("Obra side story 1-3.pdf", result)

    def test_replaces_special_separator(self):
        result = normalize_chapter_name(
            "Low tide side story 12 ┇ FIM.pdf",
            "Low tide",
        )

        self.assertEqual("Low tide side story 12 - FIM.pdf", result)

    def test_fixes_second_season_typo(self):
        result = normalize_chapter_name(
            "Areia molhada cap 67-70 Fim da 2segunda temporada.pdf",
            "Areia molhada",
        )

        self.assertEqual(
            "Areia molhada cap 67-70 Fim da 2ª temporada.pdf",
            result,
        )

    def test_removes_trailing_punctuation(self):
        result = normalize_chapter_name(
            "My Jumbo Babe cap 40,.pdf",
            "My Jumbo Babe",
        )

        self.assertEqual("My Jumbo Babe cap 40.pdf", result)

    def test_removes_leading_zeros_from_side_story_range(self):
        result = normalize_chapter_name(
            "A Seducao da Serpente side story 04-07.pdf",
            "A Seducao da Serpente",
        )

        self.assertEqual(
            "A Seducao da Serpente side story 4-7.pdf",
            result,
        )

    def test_removes_redundant_capitulo_cap(self):
        result = normalize_chapter_name(
            "My Perfect Omega capitulo cap 1-7.pdf",
            "My Perfect Omega",
        )

        self.assertEqual("My Perfect Omega cap 1-7.pdf", result)

    def test_apply_handles_case_only_rename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_path = root / "xx cheio cap 1.pdf"
            new_path = root / "XX Cheio cap 1.pdf"
            old_path.touch()
            plan = defaultdict(lambda: defaultdict(list))
            plan["XYZ"]["XX Cheio"].append({
                "old_name": old_path.name,
                "new_name": new_path.name,
                "old_path": str(old_path),
                "new_path": str(new_path),
            })

            with patch("rename_files.DRY_RUN", False):
                result = rename_files.apply_plan(plan, [])

            self.assertTrue(result)
            self.assertEqual(
                ["XX Cheio cap 1.pdf"],
                [path.name for path in root.iterdir()],
            )

    def test_detects_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_path = root / "Título alternativo cap 1.pdf"
            new_path = root / "Título oficial cap 1.pdf"
            old_path.touch()
            new_path.touch()
            plan = defaultdict(lambda: defaultdict(list))
            plan["ST"]["Título oficial"].append({
                "old_name": old_path.name,
                "new_name": new_path.name,
                "old_path": str(old_path),
                "new_path": str(new_path),
            })

            conflicts = rename_files.detect_conflicts(plan)

            self.assertEqual(1, len(conflicts))
            self.assertEqual("destino_existente", conflicts[0]["reason"])

    def test_build_plan_renames_single_image_to_cover(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manga = root / "A" / "Obra"
            manga.mkdir(parents=True)
            image = manga / "Obra.jpeg"
            image.touch()

            with patch("rename_files.MANGA_ROOT", root):
                plan = rename_files.build_plan()

            item = plan["NO"]["Obra"][0]
            self.assertEqual("cover.jpeg", item["new_name"])
            self.assertEqual("cover", item["kind"])
            self.assertFalse(item["multiple_images"])

    def test_multiple_images_are_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manga = root / "A" / "Obra"
            manga.mkdir(parents=True)
            (manga / "frente.jpg").touch()
            (manga / "verso.png").touch()

            with patch("rename_files.MANGA_ROOT", root):
                plan = rename_files.build_plan()

            conflicts = rename_files.detect_conflicts(plan)

            self.assertEqual(2, len(conflicts))
            self.assertTrue(
                all(c["reason"] == "multiplas_imagens" for c in conflicts)
            )


if __name__ == "__main__":
    unittest.main()
