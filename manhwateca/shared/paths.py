import os
from pathlib import Path


def get_required_path_env(name: str) -> Path:
    value = os.getenv(name, "").strip()

    if not value:
        raise ValueError(f"{name} não foi definido no .env")

    return Path(value).expanduser()
