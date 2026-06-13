import csv
import json


def load_mangas(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Catálogo não encontrado: {path}. Execute scripts/scan.py primeiro."
        )
    with path.open("r", encoding="utf-8") as file:
        mangas = json.load(file)
    if not isinstance(mangas, list):
        raise ValueError(f"Formato inválido em {path}: era esperada uma lista.")
    return mangas


def load_csv_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_metadata(path):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, dict) else {}
