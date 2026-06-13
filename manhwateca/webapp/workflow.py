import json
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from manhwateca.webapp.actions import SAFE_ACTIONS, build_command
from manhwateca.webapp.workflow_config import WORKFLOW_STEPS, public_steps


class WorkflowManager:
    def __init__(self, project_root, runner=None, status_path=None):
        self.root = Path(project_root)
        self.runner = runner or subprocess.run
        self.path = status_path or (
            self.root / "reports/logs/web_workflow.json"
        )
        self.lock = threading.Lock()
        self.state = self._load()
        if self.state.pop("_recovered", False):
            self._save()

    def status(self):
        with self.lock:
            return {
                "steps": public_steps(),
                "run": json.loads(json.dumps(self.state)),
            }

    def start(self, selected=None, resume=False):
        selected = selected or [
            step["id"] for step in WORKFLOW_STEPS
        ]
        valid = {step["id"] for step in WORKFLOW_STEPS}
        if not selected or any(step not in valid for step in selected):
            raise ValueError("Seleção de etapas inválida.")
        with self.lock:
            if self.state.get("status") == "running":
                raise RuntimeError("O fluxo já está em execução.")
            previous = self.state.get("results", {}) if resume else {}
            self.state = {
                "status": "running",
                "selected": selected,
                "current": None,
                "started_at": _now(),
                "finished_at": None,
                "results": previous,
                "notification": None,
            }
            self._save()
        threading.Thread(target=self._run, daemon=True).start()
        return self.status()

    def complete_manual(self, step_id):
        manual = {
            step["id"] for step in WORKFLOW_STEPS if step.get("manual")
        }
        if step_id not in manual:
            raise ValueError("Etapa manual inválida.")
        with self.lock:
            result = self.state.get("results", {}).get(step_id)
            if not result or result.get("status") != "manual":
                raise ValueError("A etapa não está aguardando confirmação.")
            result["status"] = "completed"
            result["note"] = "Etapa manual confirmada pelo usuário."
            self.state["notification"] = None
            self._save()
        return self.start(self.state.get("selected"), resume=True)

    def _run(self):
        for step in WORKFLOW_STEPS:
            if step["id"] not in self.state["selected"]:
                continue
            previous = self.state["results"].get(step["id"], {})
            if previous.get("status") == "completed":
                continue
            if step.get("manual"):
                self._finish_manual(step)
                return
            if not self._run_step(step):
                return
        self._finish("completed")

    def _run_step(self, step):
        self._set_current(step["id"], "running")
        messages = []
        for action in step["actions"]:
            config = SAFE_ACTIONS[action]
            command = [sys.executable, *build_command(config, {})]
            result = self.runner(
                command, cwd=self.root, check=False,
                capture_output=True, text=True,
            )
            messages.extend(_messages(result.stdout, result.stderr))
            if result.returncode:
                self._set_result(
                    step["id"], "failed", messages,
                    f"Falha em {config['label']}.",
                )
                self._finish("failed")
                return False
        self._set_result(step["id"], "completed", messages)
        return True

    def _finish_manual(self, step):
        self._set_result(
            step["id"], "manual", [], step["instructions"]
        )
        self._finish("waiting_manual", step["instructions"])

    def _set_current(self, step_id, status):
        with self.lock:
            self.state["current"] = step_id
            self.state["results"][step_id] = {"status": status, "messages": []}
            self._save()

    def _set_result(self, step_id, status, messages, note=None):
        with self.lock:
            self.state["results"][step_id] = {
                "status": status, "messages": messages[-100:], "note": note,
            }
            self._save()

    def _finish(self, status, notification=None):
        with self.lock:
            self.state.update(
                status=status, current=None, finished_at=_now(),
                notification=notification,
            )
            self._save()

    def _load(self):
        if not self.path.is_file():
            return {"status": "idle", "results": {}}
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"status": "idle", "results": {}}
        if state.get("status") == "running":
            state["status"] = "interrupted"
            state["finished_at"] = _now()
            state["notification"] = (
                "A execução anterior foi interrompida. Use Retomar fluxo."
            )
            state["_recovered"] = True
        return state

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _messages(stdout, stderr):
    return [
        line for content in (stdout, stderr)
        for line in (content or "").splitlines() if line.strip()
    ]
