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
