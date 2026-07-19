import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from manhwateca.webapp.workflow import WorkflowManager


class WebWorkflowTests(unittest.TestCase):
    def test_workflow_stops_at_manual_step_and_resumes_without_repeating(self):
        commands = []

        def runner(command, **_kwargs):
            commands.append(command)
            return subprocess.CompletedProcess([], 0, "ok", "")

        with tempfile.TemporaryDirectory() as directory:
            manager = WorkflowManager(directory, runner=runner)
            manager.start(selected=["catalog", "review_ids", "details"])
            waiting = self._wait(manager, "waiting_manual")
            first_count = len(commands)

            manager.complete_manual("review_ids")
            next_manual = self._wait(manager, "waiting_manual")

        self.assertEqual("completed", waiting["results"]["catalog"]["status"])
        self.assertEqual("manual", waiting["results"]["review_ids"]["status"])
        self.assertEqual("manual", next_manual["results"]["details"]["status"])
        self.assertEqual(first_count, len(commands))

    def test_workflow_stops_on_failure(self):
        calls = 0

        def runner(_command, **_kwargs):
            nonlocal calls
            calls += 1
            return subprocess.CompletedProcess([], 1, "", "falhou")

        with tempfile.TemporaryDirectory() as directory:
            manager = WorkflowManager(directory, runner=runner)
            manager.start(selected=["previews", "catalog"])
            failed = self._wait(manager, "failed")

        self.assertEqual(1, calls)
        self.assertEqual("failed", failed["results"]["previews"]["status"])
        self.assertNotIn("catalog", failed["results"])

    def test_resume_skips_completed_steps_and_persists_status(self):
        calls = []

        def runner(command, **_kwargs):
            calls.append(command)
            code = 1 if len(calls) == 2 else 0
            return subprocess.CompletedProcess([], code, "", "")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "workflow.json"
            manager = WorkflowManager(root, runner=runner, status_path=path)
            manager.start(selected=["catalog", "notion_catalog"])
            self._wait(manager, "failed")
            manager.start(selected=["catalog", "notion_catalog"], resume=True)
            completed = self._wait(manager, "completed")
            saved = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(3, len(calls))
        self.assertEqual("completed", completed["results"]["catalog"]["status"])
        self.assertEqual("completed", saved["status"])

    def _wait(self, manager, expected):
        for _ in range(200):
            run = manager.status()["run"]
            if run.get("status") == expected:
                return run
            time.sleep(0.01)
        self.fail(f"O fluxo não chegou ao estado {expected}.")
