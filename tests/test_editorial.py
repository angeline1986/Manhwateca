import csv
import json
import tempfile
import unittest
from pathlib import Path

from manhwateca.catalog.editorial import (
    dashboard_payload,
    update_editorial,
)
from manhwateca.catalog.editorial_merge import apply_saved_editorial


FIELDS = [
    "ID da obra", "Nome", "Alias", "Interesse", "Status", "Nota",
    "Último lido", "Último capítulo disponível", "Tamanho",
    "Capítulos encontrados", "Side stories", "Status da contagem",
    "Capítulo MangaUpdates", "MangaUpdates", "Temática", "Formato",
    "Universo", "Picância", "Correspondência API",
]


class EditorialTests(unittest.TestCase):
    def test_update_persists_csv_metadata_and_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory)
            work = update_editorial(root, "Official Alpha", {
                "Status": "Lendo",
                "Nota": "Topzera",
                "Interesse": "Topzera",
                "Picância": "🔥 Alta",
                "Último lido": "12",
                "Alias": "Alfa",
                "Temática": "Drama | Romance",
                "Universo": "Omegaverse",
            })
            metadata = json.loads(
                (root / "config/catalog_metadata.json").read_text()
            )
            catalog = json.loads((root / "data/mangas.json").read_text())

        self.assertEqual("Lendo", work["Status"])
        self.assertEqual("Alfa", metadata["Alpha"]["alias"])
        self.assertEqual("Topzera", metadata["Alpha"]["interesse"])
        self.assertEqual(12, catalog[0]["ultimo_lido"])
        self.assertEqual(["Drama", "Romance"], catalog[0]["tematica"])

    def test_dashboard_summary_and_recatalog_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory)
            payload = dashboard_payload(root)
            mangas = apply_saved_editorial(
                [{"nome": "Alpha", "status": "Quero ler", "nota": "Ok"}],
                root / "reports/integrations/manhwateca_import.csv",
                root / "config/catalog_metadata.json",
            )

        self.assertEqual(1, payload["summary"]["total"])
        self.assertEqual(1, payload["summary"]["new_chapters"])
        self.assertEqual("Fila de Espera", mangas[0]["interesse"])
        self.assertEqual(["Alfa"], mangas[0]["alias"])

    def test_invalid_select_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._project(directory)
            with self.assertRaisesRegex(ValueError, "Status"):
                update_editorial(root, "Official Alpha", {"Status": "Outro"})

    def _project(self, directory):
        root = Path(directory)
        csv_path = root / "reports/integrations/manhwateca_import.csv"
        csv_path.parent.mkdir(parents=True)
        row = {field: "" for field in FIELDS}
        row.update({
            "ID da obra": "10",
            "Nome": "Official Alpha",
            "Alias": "Alfa",
            "Interesse": "Fila de Espera",
            "Status": "Quero ler",
            "Nota": "Ok",
            "Último lido": "3",
            "Último capítulo disponível": "10",
            "Tamanho": "Curto",
            "Status da contagem": "Revisar",
        })
        with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerow(row)
        metadata = root / "config/catalog_metadata.json"
        metadata.parent.mkdir(parents=True)
        metadata.write_text(json.dumps({
            "Alpha": {
                "nome_oficial": "Official Alpha",
                "alias": "Alfa",
                "interesse": "Fila de Espera",
            }
        }), encoding="utf-8")
        catalog = root / "data/mangas.json"
        catalog.parent.mkdir()
        catalog.write_text(json.dumps([{
            "nome": "Alpha", "alias": ["Alfa"], "status": "Quero ler",
            "nota": "Ok", "ultimo_lido": 3, "proximo_a_ler": 4,
        }]), encoding="utf-8")
        return root
