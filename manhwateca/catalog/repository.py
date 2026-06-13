import json
from pathlib import Path


OUTPUT_FILE = Path("data/mangas.json")


def save_mangas(mangas: list[dict], path=OUTPUT_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(mangas, file, ensure_ascii=False, indent=2)
