import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from manhwateca.webapp.actions import public_actions
from manhwateca.webapp.catalog import catalog_payload
from manhwateca.webapp.editorial import dashboard_payload
from manhwateca.webapp.diagnostics import build_diagnostics
from manhwateca.webapp.mangaupdates import review_payload
from manhwateca.webapp.notion import notion_status
from manhwateca.webapp.notion_metadata import metadata_status
from manhwateca.webapp.post_routes import handle_direct_post
from manhwateca.webapp.status import build_status
from manhwateca.webapp.tasks import TaskManager
from manhwateca.webapp.workflow import WorkflowManager


def create_server(project_root, host="127.0.0.1", port=8000):
    project_root = Path(project_root).resolve()
    handler = create_handler(
        project_root,
        TaskManager(project_root),
        WorkflowManager(project_root),
    )
    return ThreadingHTTPServer((host, port), handler)


def create_handler(project_root, task_manager, workflow_manager=None):
    workflow_manager = workflow_manager or WorkflowManager(project_root)
    web_root = project_root / "web"
    reports_root = project_root / "reports"

    class ManhwatecaHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/api/status":
                self._send_json(build_status(project_root))
                return
            if path == "/api/diagnostics":
                self._send_json(build_diagnostics(project_root))
                return
            if path == "/api/actions":
                self._send_json(public_actions())
                return
            if path == "/api/catalog":
                self._send_json(
                    catalog_payload(
                        project_root,
                        latest_changes=task_manager.latest_catalog_changes(),
                    )
                )
                return
            if path == "/api/editorial":
                self._send_json(dashboard_payload(project_root))
                return
            if path == "/api/mangaupdates/review":
                self._send_json(review_payload(project_root))
                return
            if path == "/api/notion/status":
                self._send_json(notion_status(project_root))
                return
            if path == "/api/notion/metadata":
                self._send_json(metadata_status(project_root))
                return
            if path == "/api/tasks":
                self._send_json({"tasks": task_manager.list()})
                return
            if path == "/api/workflow":
                self._send_json(workflow_manager.status())
                return
            if path.startswith("/api/tasks/"):
                task = task_manager.get(path.rsplit("/", 1)[-1])
                self._send_json(
                    task or {"error": "Tarefa não encontrada."},
                    status=200 if task else 404,
                )
                return
            if path.startswith("/reports/"):
                self._send_static(path.removeprefix("/reports/"), reports_root)
                return
            self._send_static(path, web_root)

        def do_POST(self):
            path = urlparse(self.path).path
            payload = self._read_json()
            if payload is None:
                return
            direct = handle_direct_post(
                path, payload, project_root, workflow_manager
            )
            if direct:
                self._send_json(*direct)
                return
            if not path.startswith("/api/tasks/"):
                self._send_json({"error": "Rota não encontrada."}, status=404)
                return
            action = path.rsplit("/", 1)[-1]
            try:
                task = task_manager.start(
                    action,
                    confirmation=payload.get("confirmation"),
                    parameters=payload.get("parameters"),
                )
            except KeyError:
                self._send_json({"error": "Ação desconhecida."}, status=404)
            except PermissionError as error:
                self._send_json({"error": str(error)}, status=403)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=409)
            else:
                self._send_json(task, status=202)

        def _read_json(self):
            length = int(self.headers.get("Content-Length", "0"))
            if not length:
                return {}
            try:
                return json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json({"error": "JSON inválido."}, status=400)
                return None

        def _send_json(self, payload, status=200):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_static(self, request_path, root):
            relative = "index.html" if request_path == "/" else unquote(
                request_path.lstrip("/")
            )
            target = (root / relative).resolve()
            if root.resolve() not in target.parents and target != root.resolve():
                self._send_json({"error": "Caminho inválido."}, status=403)
                return
            if not target.is_file():
                self._send_json({"error": "Arquivo não encontrado."}, status=404)
                return
            body = target.read_bytes()
            content_type = mimetypes.guess_type(target.name)[0] or (
                "application/octet-stream"
            )
            if content_type.startswith("text/") or content_type in {
                "application/javascript",
                "application/json",
            }:
                content_type += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    return ManhwatecaHandler
