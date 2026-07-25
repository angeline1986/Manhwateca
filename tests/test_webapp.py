import json
import os
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

from manhwateca.webapp.server import create_server
from manhwateca.webapp.status import build_status


class FakeRepository:
    def list_mangas(self):
        return [object(), object(), object()]


class FakeConfirmedIdRepository:
    def list_mangas(self):
        return [
            type("Work", (), {
                "id": 254,
                "title": "Mad for love",
                "work_code": "56302347523",
                "mangaupdates_url": None,
                "alternative_title": None,
                "notion_sync_status": None,
            })()
        ]


class WebAppTests(unittest.TestCase):
    def test_status_counts_catalog_without_exposing_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data" / "mangas.json").write_text(
                json.dumps([{"nome": "Alpha"}, {"nome": "Beta"}]),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "NOTION_TOKEN": "secret-token",
                    "NOTION_DATABASE_ID": "database-id",
                },
                clear=True,
            ):
                status = build_status(root)

        self.assertEqual(2, status["catalog"]["count"])
        self.assertTrue(status["notion"]["configured"])
        self.assertNotIn("secret-token", json.dumps(status))

    def test_status_prefers_database_catalog_when_available(self):
        with tempfile.TemporaryDirectory() as directory:
            status = build_status(Path(directory), repository_factory=FakeRepository)

        self.assertEqual(3, status["catalog"]["count"])
        self.assertEqual("postgresql", status["catalog"]["source"]["kind"])
        self.assertEqual("PostgreSQL", status["catalog"]["source"]["label"])

    def test_http_server_serves_home_and_status(self):
        project_root = Path(__file__).resolve().parents[1]
        try:
            server = create_server(project_root, port=0)
        except PermissionError:
            self.skipTest("O ambiente de testes não permite abrir sockets locais.")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        try:
            with urllib.request.urlopen(
                f"http://{host}:{port}/api/status"
            ) as response:
                status = json.load(response)
            with urllib.request.urlopen(f"http://{host}:{port}/") as response:
                home = response.read().decode("utf-8")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual("ok", status["status"])
        self.assertIn("Manhwateca Workspace", home)
        for page in (
            "overview",
            "library",
            "organization",
            "mangaupdates",
            "notion",
            "automation",
            "settings",
        ):
            self.assertIn(f'id="page-{page}"', home)
            self.assertIn(f'data-page="{page}"', home)

    def test_confirmed_id_candidates_route_returns_payload_object(self):
        project_root = Path(__file__).resolve().parents[1]
        try:
            server = create_server(project_root, port=0)
        except PermissionError:
            self.skipTest("O ambiente de testes não permite abrir sockets locais.")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        try:
            with patch(
                "manhwateca.webapp.mangaupdates_confirmed_id.MangaRepository",
                return_value=FakeConfirmedIdRepository(),
            ):
                with urllib.request.urlopen(
                    f"http://{host}:{port}/api/mangaupdates/confirmed-id/candidates?search=mad"
                ) as response:
                    payload = json.load(response)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertIsInstance(payload, dict)
        self.assertTrue(payload["success"])
        self.assertEqual([254], [item["id"] for item in payload["items"]])
