import csv
from pathlib import Path

from manhwateca.catalog.editorial_persistence import (
    update_catalog,
    update_metadata,
)
from manhwateca.catalog.editorial_audit import (
    backup_editorial_files,
    log_editorial_change,
)
from manhwateca.database.connection import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)
from manhwateca.database.manga_repository import MangaRepository


CSV_PATH = Path("reports/integrations/manhwateca_import.csv")
METADATA_PATH = Path("config/catalog_metadata.json")
CATALOG_PATH = Path("data/mangas.json")
EDITABLE_FIELDS = {
    "Status", "Nota", "Interesse", "Picância", "Último lido",
    "Temática", "Universo", "Alias",
}
OPTIONS = {
    "Status": ["Lendo", "Em espera", "Finalizado", "Hiato", "Dropado", "Quero ler"],
    "Nota": ["Topzera", "Legalzin", "Ok", "Meia boca", "Ruim"],
    "Picância": ["", "💕 Baixa", "💫 Média", "🔥 Alta", "🔥🔥🔥 Intenso"],
}


def dashboard_payload(project_root):
    rows, _ = _read_csv(Path(project_root) / CSV_PATH)
    works = [_public_row(row) for row in rows]
    return {"summary": _summary(works), "options": OPTIONS, "works": works}


def update_editorial(project_root, name, changes):
    root = Path(project_root)
    path = root / CSV_PATH
    rows, fields = _read_csv(path)
    row = next((item for item in rows if item.get("Nome") == name), None)
    if row is None:
        raise KeyError(name)
    clean = _validate_changes(changes)
    protected = [
        path, root / METADATA_PATH, root / CATALOG_PATH,
    ]
    backups = backup_editorial_files(root, protected)
    row.update(clean)
    _write_csv(path, rows, fields)
    update_metadata(root / METADATA_PATH, name, clean)
    update_catalog(root / CATALOG_PATH, name, row, clean)
    update_database_editorial(name, clean)
    log_editorial_change(root, name, clean, backups)
    return _public_row(row)


def update_database_editorial(
    name,
    changes,
    repository_factory=MangaRepository,
) -> bool:
    try:
        return repository_factory().update_editorial_fields(name, changes)
    except (DatabaseConfigurationError, DatabaseConnectionError):
        return False


def _public_row(row):
    result = {field: row.get(field, "") for field in EDITABLE_FIELDS}
    result.update({
        "Nome": row.get("Nome", ""),
        "ID da obra": row.get("ID da obra", ""),
        "Tamanho": row.get("Tamanho", ""),
        "Último capítulo disponível": row.get("Último capítulo disponível", ""),
        "Capítulos encontrados": row.get("Capítulos encontrados", ""),
        "Status da contagem": row.get("Status da contagem", ""),
    })
    return result


def _summary(works):
    return {
        "total": len(works),
        "reading": sum(work["Status"] == "Lendo" for work in works),
        "without_id": sum(not work["ID da obra"] for work in works),
        "incomplete": sum(
            not work["Interesse"] or not work["Picância"] for work in works
        ),
        "new_chapters": sum(
            _number(work["Último capítulo disponível"])
            > _number(work["Último lido"]) for work in works
        ),
        "audit": sum(work["Status da contagem"] != "OK" for work in works),
    }


def _validate_changes(changes):
    clean = {}
    for field, value in changes.items():
        if field not in EDITABLE_FIELDS:
            continue
        value = str(value or "").strip()
        if field in OPTIONS and value not in OPTIONS[field]:
            raise ValueError(f"Valor inválido para {field}.")
        if field == "Último lido":
            value = str(max(0, _number(value)))
        clean[field] = value
    if not clean:
        raise ValueError("Nenhum campo editorial informado.")
    return clean


def _read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader), reader.fieldnames


def _write_csv(path, rows, fields):
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _number(value):
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0
