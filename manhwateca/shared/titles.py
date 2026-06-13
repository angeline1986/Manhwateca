import json
import re
import unicodedata
from pathlib import Path


TITLE_ALIASES_FILE = Path("config/titles.json")


def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFC", name)
    return " ".join(name.strip().split())


def clean_manga_name(name: str) -> str:
    name = normalize_name(name)
    name = re.sub(r"^\d+\s*[_\-.]\s*", "", name)
    name = re.sub(r"\s+\d+$", "", name)
    return normalize_name(name)


def load_title_aliases(path=TITLE_ALIASES_FILE) -> dict[str, str]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        aliases = json.load(file)

    if not isinstance(aliases, dict):
        raise ValueError(f"Formato inválido em {path}: era esperado um objeto.")

    return {
        normalize_name(source).casefold(): normalize_name(destination)
        for source, destination in aliases.items()
    }


def get_canonical_manga_name(name: str, aliases=None) -> str:
    clean_name = clean_manga_name(name)
    aliases = load_title_aliases() if aliases is None else aliases
    return aliases.get(clean_name.casefold(), clean_name)


def normalize_first_letter(text: str) -> str:
    text = text.strip()

    if not text:
        return "#"

    first = unicodedata.normalize("NFD", text[0].upper())
    first = first.encode("ascii", "ignore").decode("utf-8")
    return first.upper() if first else "#"
