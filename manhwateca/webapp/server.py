import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from manhwateca.audit.service import AuditService
from manhwateca.flows.api import FlowController
from manhwateca.webapp.actions import public_actions
from manhwateca.webapp.catalog import catalog_payload
from manhwateca.webapp.editorial import dashboard_payload
from manhwateca.webapp.diagnostics import build_diagnostics
from manhwateca.webapp.mangaupdates import (
    MangaUpdatesReviewUnavailable,
    review_payload,
)
from manhwateca.webapp.mangaupdates_works import works_payload
from manhwateca.webapp.mangaupdates_status import (
    MangaUpdatesStatusUnavailable,
    mangaupdates_status,
)
from manhwateca.webapp.mangaupdates_confirmed_id import confirmed_id_candidates_payload
from manhwateca.webapp.notion import notion_status
from manhwateca.webapp.notion_metadata import metadata_status
from manhwateca.webapp.notion_sync_candidates import sync_candidates_payload
from manhwateca.webapp.organization import (
    chapter_review_payload,
    enqueue_organization_decision,
    folder_organization_payload,
    naming_review_payload,
    organization_pending_review_payload,
    resolve_organization_decision,
    structure_review_payload,
)
from manhwateca.webapp.pending_actions import pending_payload
from manhwateca.webapp.post_routes import handle_direct_post
from manhwateca.webapp.releases import (
    dashboard_releases_summary,
    mark_viewed_payload,
    ReleaseMonitorRouteError,
    release_status_payload,
    releases_payload,
    subscriptions_payload,
    update_subscription_payload,
)
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
    flow_controller = FlowController.from_project(
        project_root,
        legacy_manager=workflow_manager,
        audit_service=AuditService(),
    )
    web_root = project_root / "web"
    reports_root = project_root / "reports"

    class ManhwatecaHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlparse(self.path).path
            flow_response = flow_controller.handle_get(path)
            if flow_response:
                self._send_json(*flow_response)
                return
            if path == "/api/status":
                self._send_json(build_status(project_root))
                return
            if path == "/api/diagnostics":
                self._send_json(build_diagnostics(project_root))
                return
            if path == "/api/actions":
                self._send_json(public_actions())
                return
            if path == "/api/pending":
                self._send_json(pending_payload(project_root))
                return
            if path == "/api/catalog":
                self._send_json(
                    catalog_payload(
                        project_root,
                        latest_changes=task_manager.latest_catalog_changes(),
                    )
                )
                return
            if path == "/api/organization/structure-review":
                try:
                    self._send_json(structure_review_payload())
                except (OSError, RuntimeError, ValueError) as error:
                    self._send_json({"error": str(error)}, status=503)
                return
            if path == "/api/organization/folder-review":
                try:
                    self._send_json(folder_organization_payload())
                except (OSError, RuntimeError, ValueError) as error:
                    self._send_json({"error": str(error)}, status=503)
                return
            if path == "/api/organization/chapter-review":
                try:
                    self._send_json(chapter_review_payload(project_root))
                except (OSError, RuntimeError, ValueError) as error:
                    self._send_json({"error": str(error)}, status=503)
                return
            if path == "/api/organization/pending-review":
                self._send_json(organization_pending_review_payload())
                return
            if path == "/api/organization/naming-review":
                try:
                    self._send_json(naming_review_payload())
                except (OSError, RuntimeError, ValueError) as error:
                    self._send_json({"error": str(error)}, status=503)
                return
            if path == "/api/editorial":
                self._send_json(dashboard_payload(project_root))
                return
            if path == "/api/dashboard/releases-summary":
                try:
                    self._send_json(dashboard_releases_summary())
                except ReleaseMonitorRouteError as error:
                    self._send_json({"error": str(error)}, status=error.status)
                return
            if path == "/api/releases":
                try:
                    self._send_json(releases_payload(urlparse(self.path).query))
                except ReleaseMonitorRouteError as error:
                    self._send_json({"error": str(error)}, status=error.status)
                return
            if path == "/api/releases/subscriptions":
                self._send_json(subscriptions_payload())
                return
            if path == "/api/releases/status":
                self._send_json(release_status_payload())
                return
            if path == "/api/mangaupdates/review":
                try:
                    self._send_json(review_payload(project_root))
                except MangaUpdatesReviewUnavailable as error:
                    self._send_json({"error": str(error)}, status=503)
                return
            if path == "/api/mangaupdates/works":
                self._send_json(works_payload(urlparse(self.path).query))
                return
            if path == "/api/mangaupdates/status":
                try:
                    self._send_json(mangaupdates_status(project_root))
                except MangaUpdatesStatusUnavailable as error:
                    self._send_json({"error": str(error)}, status=503)
                return
            if path == "/api/mangaupdates/confirmed-id/candidates":
                self._send_json(*confirmed_id_candidates_payload(urlparse(self.path).query))
                return
            if path == "/api/notion/status":
                self._send_json(notion_status(project_root))
                return
            if path == "/api/notion/metadata":
                self._send_json(metadata_status(project_root))
                return
            if path == "/api/notion/sync-candidates":
                self._send_json(sync_candidates_payload(urlparse(self.path).query))
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
            if path == "/api/organization/decision":
                try:
                    self._send_json(enqueue_organization_decision(payload), status=201)
                except (OSError, RuntimeError, ValueError) as error:
                    self._send_json({"error": str(error)}, status=400)
                return
            if path == "/api/organization/decision/resolve":
                try:
                    self._send_json(resolve_organization_decision(payload))
                except (OSError, RuntimeError, ValueError) as error:
                    self._send_json({"error": str(error)}, status=400)
                return
            flow_response = flow_controller.handle_post(path, payload)
            if flow_response:
                self._send_json(*flow_response)
                return
            direct = handle_direct_post(
                path, payload, project_root, workflow_manager
            )
            if direct:
                self._send_json(*direct)
                return
            if path == "/api/releases/check":
                try:
                    task = task_manager.start("release_check")
                except RuntimeError:
                    self._send_json({"status": "already_running"}, status=409)
                else:
                    self._send_json(task, status=202)
                return
            if path == "/api/releases/subscriptions/update":
                self._send_json(*update_subscription_payload(payload))
                return
            if path == "/api/releases/mark-viewed":
                self._send_json(mark_viewed_payload(payload))
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
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                return

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
            try:
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                return

        def log_message(self, format, *args):
            return

    return ManhwatecaHandler
