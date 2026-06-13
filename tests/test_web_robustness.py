import json
import os
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from manhwateca.catalog.editorial import update_editorial
from manhwateca.webapp.diagnostics import build_diagnostics
from manhwateca.webapp.tasks import TaskManager
from manhwateca.webapp.workflow import WorkflowManager

class WebRobustnessTests(unittest.TestCase):
    def test_diagnostics_checks_environment_without_exposing_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in (
                "web/index.html",
                "data/mangas.json",
                "reports/integrations/manhwateca_import.csv",
            ):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("[]", encoding="utf-8")
            (root / ".env").write_text("", encoding="utf-8")
            library = root / "library"
            library.mkdir()
            with patch.dict(os.environ, {
                "MANGA_ROOT": str(library),
                "NOTION_TOKEN": "secret",
                "NOTION_DATABASE_ID": "database",
            }, clear=True):
                diagnostics = build_diagnostics(root)

        self.assertTrue(diagnostics["ready"])
        self.assertNotIn("secret", json.dumps(diagnostics))

    def test_interrupted_tasks_are_persisted_as_interrupted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history = root / "tasks.json"
            history.write_text(json.dumps([{
                "id": "task-1",
                "action": "catalog_scan",
                "group": "library",
                "status": "running",
                "created_at": "2026-06-12T10:00:00-03:00",
            }]), encoding="utf-8")

            TaskManager(root, history_path=history)
            saved = json.loads(history.read_text(encoding="utf-8"))

        self.assertEqual("interrupted", saved[0]["status"])

    def test_interrupted_workflow_is_recoverable_and_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "workflow.json"
            path.write_text(json.dumps({
                "status": "running",
                "selected": ["catalog"],
                "results": {},
            }), encoding="utf-8")

            manager = WorkflowManager(root, status_path=path)
            saved = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual("interrupted", manager.status()["run"]["status"])
        self.assertEqual("interrupted", saved["status"])

    def test_editorial_update_creates_backups_and_audit_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = _editorial_project(directory)
            update_editorial(root, "Official Alpha", {"Status": "Lendo"})
            backups = list(
                (root / "reports/backups/editorial").rglob(
                    "manhwateca_import.csv"
                )
            )
            log = root / "reports/logs/editorial_changes.jsonl"
            log_content = log.read_text(encoding="utf-8")

        self.assertTrue(backups)
        self.assertIn("Status", log_content)


def _editorial_project(directory):
    root = Path(directory)
    path = root / "reports/integrations/manhwateca_import.csv"
    path.parent.mkdir(parents=True)
    fields = [
        "ID da obra", "Nome", "Alias", "Interesse", "Status", "Nota",
        "Último lido", "Último capítulo disponível", "Tamanho",
        "Capítulos encontrados", "Side stories", "Status da contagem",
        "Capítulo MangaUpdates", "MangaUpdates", "Temática", "Formato",
        "Universo", "Picância", "Correspondência API",
    ]
    row = {field: "" for field in fields}
    row.update({"Nome": "Official Alpha", "Status": "Quero ler", "Nota": "Ok"})
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)
    metadata = root / "config/catalog_metadata.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text("{}", encoding="utf-8")
    catalog = root / "data/mangas.json"
    catalog.parent.mkdir()
    catalog.write_text("[]", encoding="utf-8")
    return root
