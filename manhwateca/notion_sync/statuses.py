PENDING = "pending"
SYNCED = "synced"
ERROR = "error"
IGNORED = "ignored"
CONFLICT = "conflict"

VALID_STATUSES = {
    PENDING,
    SYNCED,
    ERROR,
    IGNORED,
    CONFLICT,
}


def validate_status(value: str) -> str:
    if value not in VALID_STATUSES:
        raise ValueError(f"Status de sync inválido: {value}")
    return value
