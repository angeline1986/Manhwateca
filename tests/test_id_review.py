import sys
import csv
import json
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import id_review


class IdReviewTests(unittest.TestCase):
    def test_report_contains_review_candidates_and_export(self):
        report = id_review.render_report([
            {
                "Nome": "Beyond Memories",
                "Status": "Revisar",
                "IDs": [{
                    "id": 46829042951,
                    "titulo": "Beyond the Memories",
                    "tipo": "Manhwa",
                    "ano": "2023",
                    "pontuacao": 1.0,
                    "descricao": "Descrição",
                    "url": "https://example.test",
                    "posicao": 1,
                }],
            },
            {
                "Nome": "Confirmada",
                "Status": "Confirmado automaticamente",
                "ID": 1,
            },
        ])

        self.assertIn("Beyond Memories", report)
        self.assertIn("Beyond the Memories", report)
        self.assertIn("Selecionar este ID", report)
        self.assertIn("Usar este ID", report)
        self.assertIn("mangaupdates_id_decisions.json", report)
        self.assertIn('<span class="work-title">Confirmada</span>', report)
        self.assertIn('data-filter="review"', report)
        self.assertIn('data-filter="confirmed"', report)
        self.assertIn('data-filter="selected"', report)
        self.assertIn('data-category="confirmed"', report)

    def test_report_marks_manual_confirmations_as_applied(self):
        report = id_review.render_report([{
            "Nome": "2020",
            "Status": "Confirmado manualmente",
            "ID": 8230323430,
            "Nome encontrado": "2020",
        }])

        self.assertIn('<span class="status applied">Aplicado</span>', report)
        self.assertIn("Status: Confirmado manualmente", report)
        self.assertIn("if (!reviewNames.has(name)) delete decisions[name]", report)

    def test_import_decisions_validates_candidate_and_creates_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "buscaIds.json"
            decisions_path = directory / "decisions.json"
            ids_path.write_text(
                json.dumps([{
                    "Nome": "Beyond Memories",
                    "Status": "Revisar",
                    "IDs": [{
                        "id": 46829042951,
                        "titulo": "Beyond the Memories",
                    }],
                }]),
                encoding="utf-8",
            )
            decisions_path.write_text(
                json.dumps([{
                    "Nome": "Beyond Memories",
                    "ID": 46829042951,
                    "Nome encontrado": "Beyond the Memories",
                }]),
                encoding="utf-8",
            )

            applied, rejected, backup = id_review.import_decisions(
                decisions_path,
                ids_path=ids_path,
            )

            updated = json.loads(ids_path.read_text(encoding="utf-8"))[0]
            self.assertEqual(["Beyond Memories"], applied)
            self.assertEqual([], rejected)
            self.assertTrue(backup.exists())
            self.assertEqual("Confirmado manualmente", updated["Status"])
            self.assertEqual(46829042951, updated["ID"])
            self.assertNotIn("IDs", updated)

    def test_import_decisions_rejects_id_outside_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "buscaIds.json"
            decisions_path = directory / "decisions.json"
            original = [{
                "Nome": "Beyond Memories",
                "Status": "Revisar",
                "IDs": [{"id": 1, "titulo": "Candidate"}],
            }]
            ids_path.write_text(json.dumps(original), encoding="utf-8")
            decisions_path.write_text(
                json.dumps([{
                    "Nome": "Beyond Memories",
                    "ID": 999,
                    "Nome encontrado": "Unknown",
                }]),
                encoding="utf-8",
            )

            applied, rejected, backup = id_review.import_decisions(
                decisions_path,
                ids_path=ids_path,
            )

            self.assertEqual([], applied)
            self.assertEqual(1, len(rejected))
            self.assertIsNone(backup)
            self.assertEqual(
                original,
                json.loads(ids_path.read_text(encoding="utf-8")),
            )

    def test_report_consolidates_aliases_and_hides_rows_that_have_id(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            csv_path = directory / "catalog.csv"
            metadata_path = directory / "metadata.json"
            with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=["ID da obra", "Nome", "Alias"],
                )
                writer.writeheader()
                writer.writerow({
                    "ID da obra": "",
                    "Nome": "Beyond Memories",
                    "Alias": "Além das Memórias",
                })
                writer.writerow({
                    "ID da obra": "99",
                    "Nome": "Resolved",
                    "Alias": "Resolvida",
                })
            metadata_path.write_text("{}", encoding="utf-8")
            items = [
                {
                    "Nome": "Beyond Memories",
                    "Status": "Revisar",
                    "IDs": [{
                        "id": 1,
                        "titulo": "Beyond the Memories",
                        "pontuacao": 1.0,
                    }],
                },
                {
                    "Nome": "Além das Memórias",
                    "Status": "Revisar",
                    "IDs": [{
                        "id": 1,
                        "titulo": "Beyond the Memories",
                        "pontuacao": 1.0,
                    }],
                },
                {
                    "Nome": "Resolved",
                    "Status": "Revisar",
                    "IDs": [{"id": 99, "titulo": "Resolved"}],
                },
            ]

            report = id_review.render_report(
                items,
                csv_path=csv_path,
                metadata_path=metadata_path,
            )

            self.assertIn("<strong>1</strong> para revisar", report)
            self.assertEqual(1, report.count("Selecionar este ID"))
            self.assertIn("Também catalogada como: Além das Memórias", report)
            self.assertNotIn('<span class="work-title">Resolved</span>', report)

    def test_report_hides_candidates_with_score_at_or_below_threshold(self):
        report = id_review.render_report([{
            "Nome": "Threshold",
            "Status": "Revisar",
            "IDs": [
                {"id": 1, "titulo": "Visible", "pontuacao": 0.71},
                {"id": 2, "titulo": "Hidden", "pontuacao": 0.70},
            ],
        }])

        self.assertIn("Visible", report)
        self.assertNotIn("<strong>Hidden</strong>", report)

    def test_import_decisions_accepts_positive_manual_id(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "buscaIds.json"
            decisions_path = directory / "decisions.json"
            ids_path.write_text(
                json.dumps([{
                    "Nome": "Unknown",
                    "Status": "Revisar",
                    "IDs": [{"id": 1, "titulo": "Wrong"}],
                }]),
                encoding="utf-8",
            )
            decisions_path.write_text(
                json.dumps([{
                    "Nome": "Unknown",
                    "ID": 999,
                    "Nome encontrado": "ID 999",
                    "Origem": "ID informado manualmente",
                }]),
                encoding="utf-8",
            )

            applied, rejected, _ = id_review.import_decisions(
                decisions_path,
                ids_path=ids_path,
            )

            updated = json.loads(ids_path.read_text(encoding="utf-8"))[0]
            self.assertEqual(["Unknown"], applied)
            self.assertEqual([], rejected)
            self.assertEqual(999, updated["ID"])

    def test_manual_id_does_not_require_candidate_title_match(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            ids_path = directory / "buscaIds.json"
            decisions_path = directory / "decisions.json"
            ids_path.write_text(
                json.dumps([{
                    "Nome": "Ian's Cage",
                    "Status": "Revisar",
                    "IDs": [{
                        "id": 29067669459,
                        "titulo": "Ian's Binding",
                    }],
                }]),
                encoding="utf-8",
            )
            decisions_path.write_text(
                json.dumps([{
                    "Nome": "Ian's Cage",
                    "ID": 29067669459,
                    "Nome encontrado": "ID 29067669459",
                    "Origem": "ID informado manualmente",
                }]),
                encoding="utf-8",
            )

            applied, rejected, _ = id_review.import_decisions(
                decisions_path,
                ids_path=ids_path,
            )

            self.assertEqual(["Ian's Cage"], applied)
            self.assertEqual([], rejected)

    def test_count_confirmed_without_details_uses_cache_by_id(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "cache.json"
            cache_path.write_text(
                json.dumps({"1": {"series_id": 1}}),
                encoding="utf-8",
            )
            items = [
                {
                    "Status": "Confirmado manualmente",
                    "ID": 1,
                },
                {
                    "Status": "Confirmado automaticamente",
                    "ID": 2,
                },
                {
                    "Status": "Revisar",
                    "ID": 3,
                },
            ]

            self.assertEqual(
                1,
                id_review.count_confirmed_without_details(
                    items,
                    cache_path=cache_path,
                ),
            )

    def test_report_hides_alias_group_when_one_name_is_confirmed(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            csv_path = directory / "catalog.csv"
            metadata_path = directory / "metadata.json"
            with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=["ID da obra", "Nome", "Alias"],
                )
                writer.writeheader()
                writer.writerow({
                    "ID da obra": "",
                    "Nome": "Official Name",
                    "Alias": "Nome Local",
                })
            metadata_path.write_text("{}", encoding="utf-8")
            items = [
                {
                    "Nome": "Official Name",
                    "Status": "Confirmado manualmente",
                    "ID": 123,
                },
                {
                    "Nome": "Nome Local",
                    "Status": "Revisar",
                    "IDs": [{
                        "id": 123,
                        "titulo": "Official Name",
                        "pontuacao": 1.0,
                    }],
                },
            ]

            report = id_review.render_report(
                items,
                csv_path=csv_path,
                metadata_path=metadata_path,
            )

            self.assertIn("<strong>0</strong> para revisar", report)
            self.assertNotIn("Selecionar este ID", report)
