import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from utils import (
    compact_number_ranges,
    extract_chapter_numbers,
    get_canonical_manga_name,
    scan_chapters,
)


class UtilsTests(unittest.TestCase):
    def test_uses_configured_short_title(self):
        aliases = {
            "segredo_conquistar_amor_não_correspondido":
                "Segredo do Amor Não Correspondido",
        }

        result = get_canonical_manga_name(
            "SEGREDO_CONQUISTAR_AMOR_NÃO_CORRESPONDIDO",
            aliases,
        )

        self.assertEqual("Segredo do Amor Não Correspondido", result)

    def test_uses_configured_spelling_correction(self):
        aliases = {"salt sciety": "Salt Society"}

        self.assertEqual(
            "Salt Society",
            get_canonical_manga_name("Salt Sciety", aliases),
        )

    def test_uses_configured_folder_cleanup(self):
        aliases = {"mousetrap capitulo": "Mousetrap"}

        self.assertEqual(
            "Mousetrap",
            get_canonical_manga_name("Mousetrap capitulo", aliases),
        )

    def test_decomposed_capitulo_is_recognized(self):
        filename = "Obra Capi\u0301tulo 31.pdf"

        self.assertEqual([31], extract_chapter_numbers(filename))

    def test_scan_counts_decomposed_capitulo(self):
        with tempfile.TemporaryDirectory() as directory:
            manga_path = Path(directory)
            (manga_path / "Obra Capi\u0301tulo 30.pdf").touch()
            (manga_path / "Obra Capi\u0301tulo 31.pdf").touch()

            result = scan_chapters(manga_path)

        self.assertEqual(2, result["chapter_files"])
        self.assertEqual(31, result["main_caps"])
        self.assertEqual(2, result["chapters_found"])
        self.assertEqual(["1-29"], result["missing_ranges"])
        self.assertEqual("Revisar", result["count_status"])

    def test_scan_expands_ranges_and_detects_gaps_and_overlaps(self):
        with tempfile.TemporaryDirectory() as directory:
            manga_path = Path(directory)
            (manga_path / "Obra cap 1-5.pdf").touch()
            (manga_path / "Obra cap 5-7.pdf").touch()
            (manga_path / "Obra cap 9.pdf").touch()
            (manga_path / "Obra extra.pdf").touch()

            result = scan_chapters(manga_path)

        self.assertEqual(9, result["main_caps"])
        self.assertEqual(8, result["chapters_found"])
        self.assertEqual(["8"], result["missing_ranges"])
        self.assertIn(5, result["duplicate_chapters"])
        self.assertEqual(["Obra extra.pdf"], result["unparsed_files"])
        self.assertEqual("Revisar", result["count_status"])

    def test_compacts_number_ranges(self):
        self.assertEqual(
            ["1-3", "7", "10-11"],
            compact_number_ranges({1, 2, 3, 7, 10, 11}),
        )


if __name__ == "__main__":
    unittest.main()
