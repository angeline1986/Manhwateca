import csv

from manhwateca.mangaupdates_service.repository import load_json_object


CSV_COLUMNS = [
    "ID da obra",
    "Nome",
    "Alias",
    "Interesse",
    "Status",
    "Nota",
    "Último lido",
    "Último capítulo disponível",
    "Tamanho",
    "Capítulos encontrados",
    "Side stories",
    "Status da contagem",
    "Capítulo MangaUpdates",
    "MangaUpdates",
    "Temática",
    "Formato",
    "Universo",
    "Picância",
    "Correspondência API",
]


def join_values(values):
    return " | ".join(
        str(value) for value in values if value not in (None, "")
    )


def build_csv_row(manga, external=None, progress=None, metadata=None):
    external = external or {}
    progress = progress or {}
    metadata = metadata or {}
    if metadata.get("alias"):
        aliases = [metadata["alias"]]
    else:
        aliases = list(manga.get("alias", []))
        aliases.extend(external.get("associated_titles", []))
    aliases = list(dict.fromkeys(aliases))
    themes = manga.get("tematica") or external.get("genres", [])
    universe = manga.get("universo") or external.get("universe", [])
    return {
        "Nome": metadata.get("nome_oficial") or manga["nome"],
        "ID da obra": external.get("series_id", ""),
        "Alias": join_values(aliases),
        "Interesse": metadata.get("interesse") or manga.get("interesse", ""),
        "Status": manga.get("status", ""),
        "Nota": manga.get("nota", ""),
        "Último lido": manga.get("ultimo_lido", ""),
        "Último capítulo disponível": manga.get("main_caps", ""),
        "Tamanho": manga.get("tamanho", ""),
        "Capítulos encontrados": manga.get("chapters_found", ""),
        "Side stories": manga.get("side_stories_found", ""),
        "Status da contagem": manga.get("count_status", ""),
        "Capítulo MangaUpdates": external.get("latest_chapter", ""),
        "MangaUpdates": external.get("url", ""),
        "Temática": join_values(themes),
        "Formato": manga.get("formato") or external.get("format", ""),
        "Universo": join_values(universe),
        "Picância": manga.get("nivel_picancia", ""),
        "Correspondência API": progress.get("match_status", "Pendente"),
    }


def write_csv(
    mangas,
    cache,
    progress,
    path,
    metadata_path,
):
    metadata = load_json_object(metadata_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for manga in mangas:
            title = manga["nome"]
            writer.writerow(
                build_csv_row(
                    manga,
                    external=cache.get(title),
                    progress=progress.get(title),
                    metadata=metadata.get(title),
                )
            )
    temporary.replace(path)
