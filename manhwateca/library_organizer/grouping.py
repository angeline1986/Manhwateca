import re

from manhwateca.shared.titles import normalize_first_letter


GROUPS = {
    "0-9": "0123456789",
    "A": "A",
    "BC": "BC",
    "DE": "DE",
    "FG": "FG",
    "HIJ": "HIJ",
    "KLM": "KLM",
    "NO": "NO",
    "PQR": "PQR",
    "ST": "ST",
    "UVW": "UVW",
    "XYZ": "XYZ",
}


def get_group(folder_name):
    first = normalize_first_letter(folder_name)
    for group_name, letters in GROUPS.items():
        if first in letters:
            return group_name
    return "0-9"


def is_group_folder(folder_name):
    return folder_name in GROUPS


def is_legacy_container(path):
    return bool(re.match(r"^\d{2}(?:[_-].*)?$", path.name))


def get_current_group(path, manga_root):
    current = path.parent
    candidate = None

    while current != current.parent and current != manga_root:
        if current.name in GROUPS:
            return current.name
        if re.match(r"^\d{2}[_-]", current.name) or re.match(
            r"^\d{2}$",
            current.name,
        ):
            return current.name
        if candidate is None:
            candidate = current.name
        current = current.parent

    return candidate or path.parent.name or "Desconhecido"
