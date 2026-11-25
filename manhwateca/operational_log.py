"""Compact, contextual logs for operational workflows and HTTP requests.

Set ``MANHWATECA_LOG_LEVEL`` to DEBUG, INFO, WARNING, or ERROR (default INFO).
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from datetime import datetime
import logging
import os
from pathlib import Path
import re
import sys


_component = ContextVar(
    "operational_log_component",
    default=os.environ.get("MANHWATECA_LOG_COMPONENT"),
)
_job = ContextVar("operational_log_job", default=os.environ.get("MANHWATECA_LOG_JOB"))
_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_HOME = Path.home()
_logger = logging.getLogger("manhwateca.operational")


def _configured_level() -> int:
    value = os.environ.get("MANHWATECA_LOG_LEVEL", "INFO").strip().upper()
    if value not in _LEVELS:
        value = "INFO"
    return getattr(logging, value)


class _Formatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().astimezone().strftime("%H:%M:%S.%f")[:-3]
        component = getattr(record, "operational_component", None) or _component.get()
        job = getattr(record, "operational_job", None) or _job.get()
        prefix = f"{timestamp} {record.levelname}"
        if component:
            prefix += f" [{_clean_component(component)}]"
        if job:
            prefix += f"[{_single_line(str(job))[:6]}]"
        message = _redact(_single_line(record.getMessage()))
        fields = getattr(record, "operational_fields", {}) or {}
        if fields:
            rendered = " ".join(
                f"{_single_line(str(key))}={_format_value(value)}"
                for key, value in fields.items()
            )
            message += f" · {rendered}"
        return f"{prefix} {message}"


def configure() -> None:
    """Configure the operational stream once and honor the current env level."""
    _logger.setLevel(_configured_level())
    if not _logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_Formatter())
        handler.set_name("manhwateca-operational")
        _logger.addHandler(handler)
        _logger.propagate = False
    else:
        for handler in _logger.handlers:
            handler.setFormatter(_Formatter())


@contextmanager
def log_context(component: str, job: str | None = None):
    """Bind operation identity for the current thread/task context."""
    component_token = _component.set(_clean_component(component))
    job_token = _job.set(str(job) if job is not None else None)
    try:
        yield
    finally:
        _job.reset(job_token)
        _component.reset(component_token)


def log_event(level: str, message: str, *, component=None, job=None, **fields) -> None:
    configure()
    level_name = str(level).upper()
    if level_name not in _LEVELS:
        level_name = "INFO"
    explicit_component = _clean_component(component) if component else None
    explicit_job = str(job) if job is not None else None
    _logger.log(
        getattr(logging, level_name),
        _single_line(message),
        extra={
            "operational_component": explicit_component,
            "operational_job": explicit_job,
            "operational_fields": fields,
        },
        stacklevel=2,
    )


def context_thread_target(target, *args, **kwargs):
    """Return a thread target that runs with a snapshot of the caller context."""
    context = copy_context()
    return lambda: context.run(target, *args, **kwargs)


def context_callable(callback):
    """Capture the current log context for submission to an executor."""
    context = copy_context()
    return lambda *args, **kwargs: context.run(callback, *args, **kwargs)


def subprocess_log_environment(component: str, job: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment["MANHWATECA_LOG_COMPONENT"] = _clean_component(component)
    environment["MANHWATECA_LOG_JOB"] = str(job)[:6]
    return environment


def http_access(method: str, route: str, status: int, size: int | None) -> None:
    route = route or "/"
    if (
        200 <= int(status) < 400
        and method.upper() == "GET"
        and _is_progress_poll(route)
    ):
        return
    log_event(
        "ERROR" if int(status) >= 400 else "INFO",
        "requisição HTTP",
        component="HTTP",
        method=method,
        rota=route,
        status=int(status),
        tamanho=size,
    )


def _is_progress_poll(route: str) -> bool:
    return (
        route in {"/api/flows/status", "/api/workflow"}
        or route.startswith("/api/tasks/") and route.count("/") == 3
    )


def _clean_component(value) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(value)).upper()


def _single_line(value: str) -> str:
    return re.sub(r"[\r\n\t]+", " ", str(value)).strip()


def _redact(value: str) -> str:
    value = value.replace(str(_PROJECT_ROOT), "[PROJETO]")
    if str(_HOME) not in {"", "/"}:
        value = value.replace(str(_HOME), "[HOME]")
    return value


def _format_value(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "sim" if value else "não"
    rendered = _redact(_single_line(str(value)))
    if not rendered:
        return '""'
    if any(character.isspace() for character in rendered) or "=" in rendered:
        rendered = '"' + rendered.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return rendered
