import json
import os
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from manhwateca.webapp.actions import SAFE_ACTIONS
from manhwateca.webapp.catalog import catalog_payload
from manhwateca.webapp.post_routes import handle_direct_post
from manhwateca.webapp.tasks import TaskManager


class CatalogRecord:
    def __init__(self, title, latest=1):
        self.title = title
        self.alternative_title = None
        self.last_read_chapter = 0
        self.latest_available_chapter = latest
        self.size_label = "Curto"
        self.count_status = "OK"
        self.latest_mangaupdates_chapter = None
        self.cover_url = None
        self.reading_status = "Quero Ler"
        self.personal_rank = "Normal"
        self.themes = []


class WebTaskTests(unittest.TestCase):
    def test_web_actions_do_not_expose_legacy_mangaupdates_scripts(self):
        retired_actions = {
            "mangaupdates_search",
            "mangaupdates_refresh",
            "mangaupdates_details",
            "mangaupdates_force_refresh",
            "mangaupdates_csv",
        }

        self.assertTrue(retired_actions.isdisjoint(SAFE_ACTIONS))
        for action in SAFE_ACTIONS.values():
            self.assertNotIn("scripts/mangaupdates.py", action["command"])

    def test_notion_batch_is_blocked_when_drive_has_uncataloged_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status = root / "reports/integrations/notion_import_status.json"
            status.parent.mkdir(parents=True)
            status.write_text(
                json.dumps({
                    "resumo": {
                        "total_catalogo": 1,
                        "total_importadas": 1,
                        "total_pendentes": 0,
                    },
                }),
                encoding="utf-8",
            )
            catalog = root / "data/mangas.json"
            catalog.parent.mkdir()
            catalog.write_text(
                json.dumps([{"nome": "Alpha"}]),
                encoding="utf-8",
            )
            library = root / "library"
            for name in ("Alpha", "Beta"):
                work = library / "A" / name
                work.mkdir(parents=True)
                (work / f"{name} cap 1.pdf").touch()
            manager = TaskManager(root)

            with (
                patch.dict(os.environ, {"MANGA_ROOT": str(library)}),
                self.assertRaisesRegex(RuntimeError, "Catalogar biblioteca"),
            ):
                manager.start("notion_simulate_batch")

    def test_task_captures_output_and_persists_history(self):
        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Tudo certo\n", stderr=""
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history = root / "reports/logs/tasks.json"
            manager = TaskManager(
                root,
                history_path=history,
                process_runner=lambda *_args, **_kwargs: result,
            )

            task = manager.start("chapter_audit")
            completed = self._wait(manager, task["id"])
            saved = json.loads(history.read_text(encoding="utf-8"))

        self.assertEqual("completed", completed["status"])
        self.assertEqual(["Tudo certo"], completed["messages"])
        self.assertIsInstance(completed["duration_seconds"], float)
        self.assertEqual(task["id"], saved[0]["id"])

    def test_task_records_performance_metrics_from_output(self):
        output = "\n".join([
            "Criações: 2",
            "Atualizações: 3",
            "Sem alteração: 4",
            "Ausentes no Notion: 1",
            "Duplicados bloqueados: 0",
        ])
        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=output, stderr=""
        )
        with tempfile.TemporaryDirectory() as directory:
            manager = TaskManager(
                directory,
                process_runner=lambda *_args, **_kwargs: result,
            )

            task = manager.start("notion_csv_preview")
            completed = self._wait(manager, task["id"])

        self.assertEqual(2, completed["metrics"]["notion"]["created"])
        self.assertEqual(3, completed["metrics"]["notion"]["updated"])
        self.assertEqual(4, completed["metrics"]["notion"]["unchanged"])
        self.assertEqual(1, completed["metrics"]["notion"]["missing"])
        self.assertEqual(
            5,
            completed["metrics"]["external_calls"]["notion_writes"],
        )

    def test_retired_mangaupdates_web_actions_do_not_start_tasks(self):
        calls = []

        def capture(*_args, **_kwargs):
            calls.append(True)
            return subprocess.CompletedProcess([], 0, "", "")

        retired_actions = [
            "mangaupdates_search",
            "mangaupdates_refresh",
            "mangaupdates_details",
            "mangaupdates_force_refresh",
            "mangaupdates_csv",
        ]
        with tempfile.TemporaryDirectory() as directory:
            manager = TaskManager(directory, process_runner=capture)
            for action in retired_actions:
                with self.subTest(action=action):
                    with self.assertRaises(KeyError):
                        manager.start(action)

        self.assertEqual([], calls)

    def test_task_records_affected_items_from_tagged_output(self):
        output = "\n".join([
            "[CRIAR] Alpha",
            "[ATUALIZAR] Beta",
            "[AUSENTE NO NOTION] Gamma",
            "[DUPLICADO NO NOTION] Delta",
        ])
        result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=output, stderr=""
        )
        with tempfile.TemporaryDirectory() as directory:
            manager = TaskManager(
                directory,
                process_runner=lambda *_args, **_kwargs: result,
            )

            task = manager.start("notion_simulate_batch")
            completed = self._wait(manager, task["id"])

        self.assertEqual(["Alpha"], completed["metrics"]["items"]["created"])
        self.assertEqual(["Beta"], completed["metrics"]["items"]["updated"])
        self.assertEqual(["Gamma"], completed["metrics"]["items"]["missing"])
        self.assertEqual(["Delta"], completed["metrics"]["items"]["duplicates"])

    def test_same_group_cannot_run_twice(self):
        release = threading.Event()

        def blocking_runner(*_args, **_kwargs):
            release.wait(timeout=2)
            return subprocess.CompletedProcess([], 0, "", "")

        with tempfile.TemporaryDirectory() as directory:
            manager = TaskManager(
                directory,
                process_runner=blocking_runner,
            )
            first = manager.start("organization_preview")
            with self.assertRaisesRegex(RuntimeError, "incompatível"):
                manager.start("rename_preview")
            release.set()
            completed = self._wait(manager, first["id"])

        self.assertEqual("completed", completed["status"])

    def test_destructive_task_requires_exact_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = TaskManager(
                directory,
                process_runner=lambda *_args, **_kwargs: (
                    subprocess.CompletedProcess([], 0, "", "")
                ),
            )
            with self.assertRaisesRegex(PermissionError, "APLICAR"):
                manager.start("apply_renaming", confirmation="aplicar")

            task = manager.start("apply_renaming", confirmation="APLICAR")
            completed = self._wait(manager, task["id"])

        self.assertTrue(completed["destructive"])
        self.assertEqual("completed", completed["status"])

    def test_catalog_scan_records_changes_without_exposing_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "data/mangas.json"
            catalog.parent.mkdir()
            catalog.write_text(
                json.dumps([{"nome": "Alpha", "main_caps": 10}]),
                encoding="utf-8",
            )

            def update_catalog(*_args, **_kwargs):
                catalog.write_text(
                    json.dumps([
                        {"nome": "Alpha", "main_caps": 12},
                        {"nome": "Beta", "main_caps": 1},
                    ]),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess([], 0, "", "")

            history = root / "reports/logs/tasks.json"
            manager = TaskManager(
                root, history_path=history, process_runner=update_catalog
            )
            started = manager.start("catalog_scan")
            completed = self._wait(manager, started["id"])
            saved = json.loads(history.read_text(encoding="utf-8"))[0]

        self.assertNotIn("_catalog_before", started)
        self.assertNotIn("_catalog_before", saved)
        self.assertEqual(["Beta"], completed["catalog_changes"]["new"])
        self.assertEqual("Alpha", completed["catalog_changes"]["updated"][0]["nome"])

    def test_catalog_scan_compares_active_catalog_source(self):
        state = {"after": False}

        def active_source(_project_root, *_args, **_kwargs):
            titles = ["Alpha", "Beta"] if state["after"] else ["Alpha"]
            records = [CatalogRecord(title) for title in titles]
            return {
                "kind": "postgresql",
                "label": "PostgreSQL",
                "detail": "vw_mangas",
                "count": len(records),
                "mangas": records,
            }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "data/mangas.json"
            catalog.parent.mkdir()
            catalog.write_text(
                json.dumps([
                    {"nome": "Alpha", "main_caps": 1},
                    {"nome": "Beta", "main_caps": 1},
                ]),
                encoding="utf-8",
            )

            def save_to_database(*_args, **_kwargs):
                state["after"] = True
                return subprocess.CompletedProcess([], 0, "", "")

            history = root / "reports/logs/tasks.json"
            with patch("manhwateca.webapp.catalog.active_catalog_source", active_source):
                manager = TaskManager(
                    root,
                    history_path=history,
                    process_runner=save_to_database,
                )
                started = manager.start("catalog_scan")
                completed = self._wait(manager, started["id"])
                restarted = TaskManager(
                    root,
                    history_path=history,
                    process_runner=save_to_database,
                )
                api_payload = catalog_payload(
                    root,
                    latest_changes=restarted.latest_catalog_changes(),
                )

            saved = json.loads(history.read_text(encoding="utf-8"))[0]

        self.assertEqual(["Beta"], completed["catalog_changes"]["new"])
        self.assertEqual(["Beta"], saved["catalog_changes"]["new"])
        self.assertEqual(["Beta"], restarted.latest_catalog_changes()["new"])
        self.assertEqual(["Beta"], api_payload["changes"]["new"])

    def test_catalog_one_route_still_delegates_to_catalog_single_work(self):
        with patch(
            "manhwateca.webapp.post_routes.catalog_single_work",
            return_value={"saved": 1, "work": "Beta", "path": "/library/Beta"},
        ) as catalog_single:
            payload, status = handle_direct_post(
                "/api/catalog/catalog-one",
                {"name": "Beta"},
                Path("."),
            )

        self.assertEqual(200, status)
        self.assertEqual("Beta", payload["work"])
        catalog_single.assert_called_once_with("Beta")

    def test_notion_writes_require_exact_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = TaskManager(
                directory,
                process_runner=lambda *_args, **_kwargs: (
                    subprocess.CompletedProcess([], 0, "", "")
                ),
            )
            simulation = manager.start("notion_simulate_batch")
            self._wait(manager, simulation["id"])

            with self.assertRaises(PermissionError):
                manager.start("notion_apply_batch")
            with self.assertRaises(PermissionError):
                manager.start("notion_update_existing", confirmation="SIM")

            applied = manager.start(
                "notion_apply_batch", confirmation="APLICAR"
            )
            completed = self._wait(manager, applied["id"])

        self.assertEqual("completed", completed["status"])
        self.assertTrue(completed["destructive"])

    def test_notion_csv_preview_is_safe_and_apply_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = TaskManager(
                directory,
                process_runner=lambda *_args, **_kwargs: (
                    subprocess.CompletedProcess([], 0, "", "")
                ),
            )
            preview = manager.start("notion_csv_preview")
            self.assertEqual(
                "completed", self._wait(manager, preview["id"])["status"]
            )
            with self.assertRaises(PermissionError):
                manager.start("notion_csv_apply")
            apply_task = manager.start(
                "notion_csv_apply", confirmation="APLICAR"
            )
            completed = self._wait(manager, apply_task["id"])

        self.assertTrue(completed["destructive"])

    def _wait(self, manager, task_id):
        for _ in range(100):
            task = manager.get(task_id)
            if task["status"] not in {"queued", "running"}:
                return task
            time.sleep(0.01)
        self.fail("A tarefa não terminou no tempo esperado.")
