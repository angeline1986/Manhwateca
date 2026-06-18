import json, re, subprocess, sys, threading, time, uuid
from datetime import datetime
from pathlib import Path

from manhwateca.webapp.actions import SAFE_ACTIONS, build_command
from manhwateca.webapp.catalog import compare_catalogs, load_catalog
from manhwateca.webapp.notion import notion_status

class TaskManager:
    def __init__(self, project_root, history_path=None, process_runner=None):
        self.project_root = Path(project_root)
        self.history_path = history_path or self.project_root / (
            "reports/logs/web_tasks.json"
        )
        self.process_runner = process_runner or subprocess.run
        self.tasks = {}
        self.lock = threading.Lock()
        if self._load_history():
            self._save_history()

    def start(self, action, confirmation=None, parameters=None):
        if action not in SAFE_ACTIONS:
            raise KeyError(action)
        if action in {"notion_simulate_batch", "notion_apply_batch"}:
            uncataloged = notion_status(self.project_root)["summary"]["uncataloged"]
            if uncataloged:
                raise RuntimeError(
                    f"Existem {uncataloged} obra(s) no Drive ainda não "
                    "catalogada(s). Execute “Catalogar biblioteca” antes "
                    "de sincronizar com o Notion."
                )
        if (
            SAFE_ACTIONS[action].get("requires_confirmation")
            and confirmation != "APLICAR"
        ):
            raise PermissionError(
                "Confirmação inválida. Digite APLICAR para continuar."
            )
        with self.lock:
            if self._has_conflict(SAFE_ACTIONS[action]["group"]):
                raise RuntimeError("Já existe uma tarefa incompatível em execução.")
            task = self._new_task(action)
            task["_parameters"] = parameters or {}
            if action == "catalog_scan":
                task["_catalog_before"] = load_catalog(self.project_root)
            self.tasks[task["id"]] = task
            self._save_history()
        thread = threading.Thread(target=self._execute, args=(task["id"],), daemon=True)
        thread.start()
        return _public_task(task)

    def list(self):
        with self.lock:
            return sorted(
                (_public_task(task) for task in self.tasks.values()),
                key=lambda task: task["created_at"],
                reverse=True,
            )

    def get(self, task_id):
        with self.lock:
            task = self.tasks.get(task_id)
            return _public_task(task) if task else None

    def _execute(self, task_id):
        with self.lock:
            task = self.tasks[task_id]
            task["status"] = "running"
            task["started_at"] = _now()
            task["_started_monotonic"] = time.perf_counter()
            self._save_history()
        config = SAFE_ACTIONS[task["action"]]
        command = [
            sys.executable,
            *build_command(config, task.pop("_parameters", {})),
        ]
        try:
            result = self.process_runner(
                command,
                cwd=self.project_root,
                check=False,
                capture_output=True,
                text=True,
            )
            messages = _messages(result.stdout, result.stderr)
            status = "completed" if result.returncode == 0 else "failed"
            return_code = result.returncode
        except Exception as error:
            messages = [str(error)]
            status = "failed"
            return_code = None
        with self.lock:
            task = self.tasks[task_id]
            duration = _duration_seconds(task.pop("_started_monotonic", None))
            task.update(
                status=status,
                finished_at=_now(),
                duration_seconds=duration,
                return_code=return_code,
                messages=messages,
                metrics=_performance_metrics(task["action"], messages),
            )
            if task["action"] == "catalog_scan" and status == "completed":
                task["catalog_changes"] = compare_catalogs(
                    task.pop("_catalog_before", []),
                    load_catalog(self.project_root),
                )
            else:
                task.pop("_catalog_before", None)
            self._save_history()

    def _new_task(self, action):
        config = SAFE_ACTIONS[action]
        return {
            "id": uuid.uuid4().hex,
            "action": action,
            "label": config["label"],
            "group": config["group"],
            "status": "queued",
            "created_at": _now(),
            "started_at": None,
            "finished_at": None,
            "duration_seconds": None,
            "return_code": None,
            "metrics": {},
            "messages": [],
            "reports": config["reports"],
            "destructive": config.get("requires_confirmation", False),
        }

    def _has_conflict(self, group):
        return any(
            task["status"] in {"queued", "running"} and task["group"] == group
            for task in self.tasks.values()
        )

    def _load_history(self):
        if not self.history_path.is_file():
            return False
        try:
            data = json.loads(self.history_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        recovered = False
        if isinstance(data, list):
            for task in data:
                if task.get("status") in {"queued", "running"}:
                    task["status"] = "interrupted"
                    task["finished_at"] = _now()
                    recovered = True
                if task.get("id"):
                    self.tasks[task["id"]] = task
        return recovered

    def _save_history(self):
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        recent = self.list_unlocked()[:50]
        temporary = self.history_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(recent, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.history_path)

    def list_unlocked(self):
        return sorted(
            (_public_task(task) for task in self.tasks.values()),
            key=lambda task: task["created_at"],
            reverse=True,
        )

    def latest_catalog_changes(self):
        with self.lock:
            for task in self.list_unlocked():
                if task.get("catalog_changes") is not None:
                    return task["catalog_changes"]
        return None

def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def _messages(stdout, stderr):
    lines = []
    for content in (stdout, stderr):
        lines.extend(line for line in (content or "").splitlines() if line.strip())
    return lines[-200:]

def _duration_seconds(started):
    if started is None:
        return None
    return round(max(0, time.perf_counter() - started), 3)

def _performance_metrics(action, messages):
    text = "\n".join(messages)
    metrics = {}
    notion = _extract_counts(text, {
        "created": "Criações",
        "updated": "Atualizações",
        "unchanged": "Sem alteração",
        "missing": "Ausentes no Notion",
        "duplicates": "Duplicados bloqueados",
        "pending": "Obras restantes para próximos lotes",
    })
    if notion:
        metrics["notion"] = notion

    mangaupdates = _extract_counts(text, {
        "processed": "Processadas nesta execução",
        "details": "Detalhes consultados nesta execução",
        "updated": "Obras atualizadas nesta execução",
        "confirmed": "IDs confirmados",
        "review": "Para revisão",
        "pending": "Pendentes",
    })
    if mangaupdates:
        metrics["mangaupdates"] = mangaupdates
    external_calls = _external_calls(action, notion, mangaupdates)
    if external_calls:
        metrics["external_calls"] = external_calls
    items = _tagged_items(text)
    if items:
        metrics["items"] = items
    return metrics

def _extract_counts(text, labels):
    counts = {}
    for key, label in labels.items():
        match = re.search(rf"^{re.escape(label)}:\s*(\d+)", text, re.MULTILINE)
        if match:
            counts[key] = int(match.group(1))
    return counts

def _external_calls(action, notion, mangaupdates):
    calls = {}
    notion_writes = notion.get("created", 0) + notion.get("updated", 0)
    if notion_writes:
        calls["notion_writes"] = notion_writes
    if action.startswith("mangaupdates_") and mangaupdates:
        manga_calls = max(
            mangaupdates.get("processed", 0),
            mangaupdates.get("details", 0),
            mangaupdates.get("updated", 0),
        )
        if manga_calls:
            calls["mangaupdates"] = manga_calls
    return calls

def _tagged_items(text):
    tags = {
        "created": "CRIAR",
        "updated": "ATUALIZAR",
        "missing": "AUSENTE NO NOTION",
        "duplicates": "DUPLICADO NO NOTION",
        "errors": "ERRO",
    }
    items = {}
    for key, tag in tags.items():
        names = [
            match.group(1).strip()
            for match in re.finditer(
                rf"^\[{re.escape(tag)}\]\s+(.+)$",
                text,
                re.MULTILINE,
            )
        ][:50]
        if names:
            items[key] = names
    return items

def _public_task(task):
    return {key: value for key, value in task.items() if not key.startswith("_")}
