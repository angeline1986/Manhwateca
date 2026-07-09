from dataclasses import dataclass
from enum import Enum
from typing import Any


class SyncStatus(Enum):
    SYNCED = "synced"
    PAUSED = "paused"
    BLOCKED = "blocked"
    ERROR = "error"


class NextAction(Enum):
    NONE = "none"
    APPLY = "apply"
    REVIEW_DUPLICATES = "review_duplicates"
    REVIEW_MISSING = "review_missing"
    REVIEW_BLOCKERS = "review_blockers"
    RETRY = "retry"


class BlockerSeverity(Enum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class NotionBlocker:
    code: str
    work_id: int | None = None
    work_title: str | None = None
    message: str | None = None
    severity: BlockerSeverity = BlockerSeverity.BLOCKING
    next_action: NextAction = NextAction.REVIEW_BLOCKERS


@dataclass(frozen=True)
class NotionSyncResult:
    status: SyncStatus
    next_action: NextAction
    created_count: int = 0
    updated_count: int = 0
    missing_count: int = 0
    duplicate_count: int = 0
    unchanged_count: int = 0
    blockers: tuple[NotionBlocker, ...] = ()


def build_sync_result(summary: dict[str, Any] | None) -> NotionSyncResult:
    summary = summary or {}
    missing_items = _items(summary.get("missing"))
    duplicate_items = _items(summary.get("duplicates"))
    error_items = _error_items(summary)
    blockers = (
        *_blockers("missing_page", missing_items, NextAction.REVIEW_MISSING),
        *_blockers("duplicate_page", duplicate_items, NextAction.REVIEW_DUPLICATES),
        *_blockers("api_error", error_items, NextAction.RETRY),
    )
    created_count = _count(summary.get("created"))
    updated_count = _count(summary.get("updates"), fallback=summary.get("updated"))
    unchanged_count = _count(summary.get("unchanged"))
    missing_count = _count(summary.get("missing"))
    duplicate_count = _count(summary.get("duplicates"))

    if error_items:
        status = SyncStatus.ERROR
        next_action = NextAction.RETRY
    elif blockers:
        status = SyncStatus.BLOCKED
        next_action = _blocker_next_action(blockers)
    elif created_count or updated_count:
        status = SyncStatus.PAUSED
        next_action = NextAction.APPLY
    else:
        status = SyncStatus.SYNCED
        next_action = NextAction.NONE

    return NotionSyncResult(
        status=status,
        next_action=next_action,
        created_count=created_count,
        updated_count=updated_count,
        missing_count=missing_count,
        duplicate_count=duplicate_count,
        unchanged_count=unchanged_count,
        blockers=blockers,
    )


def _items(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    if isinstance(value, dict):
        return (value,)
    try:
        return tuple(value)
    except TypeError:
        return (value,)


def _count(value: Any, fallback: Any = None) -> int:
    """
    Converte diferentes formatos de summary em uma quantidade.

    Aceita int, list, tuple, dict, string e None. Retorna sempre um
    inteiro >= 0 para manter compatibilidade com formatos de summary
    produzidos pelos fluxos atuais e futuros.
    """
    if value is None:
        return _number(fallback)
    if isinstance(value, (str, bytes)):
        return 1 if value else 0
    if isinstance(value, dict):
        return 1
    try:
        return len(value)
    except TypeError:
        return _number(value)


def _number(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _blockers(
    code: str,
    entries: tuple[Any, ...],
    next_action: NextAction,
) -> tuple[NotionBlocker, ...]:
    return tuple(
        NotionBlocker(
            code=code,
            work_id=_work_id(entry),
            work_title=_work_title(entry),
            message=_message(entry),
            next_action=next_action,
        )
        for entry in entries
    )


def _error_items(summary: dict[str, Any]) -> tuple[Any, ...]:
    return (*_items(summary.get("error")), *_items(summary.get("errors")))


def _work_id(entry: Any) -> int | None:
    value = _field(entry, "work_id", "workId", "manga_id", "mangaId", "id")
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None


def _work_title(entry: Any) -> str | None:
    value = _field(
        entry,
        "work_title",
        "workTitle",
        "title",
        "localTitle",
        "name",
        "Nome",
    )
    if value is None and isinstance(entry, str):
        value = entry
    text = str(value or "").strip()
    return text or None


def _message(entry: Any) -> str | None:
    value = _field(entry, "message", "error", "detail", "reason")
    if value is None and isinstance(entry, str):
        value = entry
    text = str(value or "").strip()
    return text or None


def _field(entry: Any, *names: str) -> Any:
    if isinstance(entry, (str, bytes)):
        return None
    if isinstance(entry, dict):
        for name in names:
            if name in entry:
                return entry[name]
        return None
    for name in names:
        if hasattr(entry, name):
            return getattr(entry, name)
    return None


def _blocker_next_action(blockers: tuple[NotionBlocker, ...]) -> NextAction:
    actions = {blocker.next_action for blocker in blockers}
    if NextAction.REVIEW_DUPLICATES in actions:
        return NextAction.REVIEW_DUPLICATES
    if NextAction.REVIEW_MISSING in actions:
        return NextAction.REVIEW_MISSING
    return NextAction.REVIEW_BLOCKERS
