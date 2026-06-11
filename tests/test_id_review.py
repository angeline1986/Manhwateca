import sys
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
        self.assertIn("mangaupdates_id_decisions.json", report)
        self.assertNotIn('<span class="work-title">Confirmada</span>', report)

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
