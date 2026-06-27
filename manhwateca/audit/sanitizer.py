from collections.abc import Mapping
from typing import Any


MASK = "***"

SENSITIVE_KEYS = {
    "token",
    "secret",
    "password",
    "authorization",
    "api_key",
    "apikey",
    "database_url",
    "databaseurl",
    "notion_token",
    "notiontoken",
    "mangaupdates_password",
    "mangaupdatespassword",
    "DATABASE_URL",
    "NOTION_TOKEN",
    "MANGAUPDATES_PASSWORD",
}

_NORMALIZED_SENSITIVE_KEYS = {item.lower() for item in SENSITIVE_KEYS}


def _normalize_key(key: Any) -> str:
    return str(key).strip().lower().replace("-", "_")


def _is_sensitive_key(key: Any) -> bool:
    return _normalize_key(key) in _NORMALIZED_SENSITIVE_KEYS


def sanitize_audit_details(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, Mapping):
        sanitized = {}
        for key, item in value.items():
            if _is_sensitive_key(key):
                sanitized[str(key)] = MASK
            else:
                sanitized[str(key)] = sanitize_audit_details(item)
        return sanitized

    if isinstance(value, tuple):
        return [sanitize_audit_details(item) for item in value]

    if isinstance(value, list):
        return [sanitize_audit_details(item) for item in value]

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)
