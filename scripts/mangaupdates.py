import argparse
import csv
import json
import random
import re
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path


API_BASE = "https://api.mangaupdates.com/v1"
MAPPINGS_FILE = Path("config/mangaupdates.json")
CACHE_FILE = Path("data/mangaupdates.json")
CATALOG_FILE = Path("data/mangas.json")
CSV_FILE = Path("reports/manhwateca_import.csv")
PROGRESS_FILE = Path("data/mangaupdates_progress.json")
CSV_COLUMNS = [
    "Nome",
    "ID da obra",
    "Alias",
    "Status",
    "Nota",
    "Último lido",
    "Último capítulo disponível",
    "Capítulos encontrados",
    "Side stories",
    "Lacunas",
    "Status da contagem",
    "Capítulo MangaUpdates",
    "MangaUpdates",
    "Temática",
    "Formato",
    "Universo",
    "Picância",
    "Correspondência API",
]


def request_json(
    url,
    payload=None,
    retries=4,
    base_delay=3.0,
):
    data = None
    headers = {"Content-Type": "application/json", "User-Agent": "Manhwateca/1.0"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == retries:
                raise
            retry_after = error.headers.get("Retry-After")
            wait = (
                float(retry_after)
                if retry_after
                else base_delay * (2 ** attempt) + random.uniform(0, 1)
            )
            print(f"[LIMITE] Aguardando {wait:.1f}s antes de tentar novamente.")
            time.sleep(wait)
        except urllib.error.URLError:
            if attempt == retries:
                raise
            wait = base_delay * (2 ** attempt)
            print(f"[REDE] Aguardando {wait:.1f}s antes de tentar novamente.")
            time.sleep(wait)


def search_series(title, per_page=5):
    return request_json(
        f"{API_BASE}/series/search",
        {"search": title, "page": 1, "perpage": per_page},
    )


def get_series(series_id):
    return request_json(f"{API_BASE}/series/{series_id}")


def normalize_title(value):
    value = unicodedata.normalize("NFD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.casefold().replace("_", " ")
    value = re.sub(r"\([^)]*novel[^)]*\)", " novel ", value)
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def choose_search_result(title, response):
    normalized = normalize_title(title)
    exact = []
    for result in response.get("results", []):
        record = result.get("record", {})
        names = [record.get("title", ""), result.get("hit_title", "")]
        if normalized in {normalize_title(name) for name in names if name}:
            exact.append(record)

    manhwa = [record for record in exact if record.get("type") == "Manhwa"]
    if len(manhwa) == 1:
        return manhwa[0], "Exata (Manhwa)"
    if len(exact) == 1:
        return exact[0], "Exata"
    if not exact:
        return None, "Não encontrada"
    return None, "Ambígua"


def infer_format(details):
    series_type = details.get("type")
    related_types = {
        item.get("relation_type", "").casefold()
        for item in details.get("related_series", [])
    }
    related_names = " ".join(
        item.get("related_series_name", "")
        for item in details.get("related_series", [])
    ).casefold()
    has_novel = "novel" in related_names and "adapted from" in related_types
    if series_type == "Manhwa" and has_novel:
        return "Manhwa e Novel"
    if series_type in {"Manhwa", "Novel"}:
        return series_type
    return series_type


def summarize_series(details):
    categories = [
        item["category"]
        for item in details.get("categories", [])
        if item.get("category")
    ]
    universe = []
    category_names = {category.casefold() for category in categories}
    if "omegaverse" in category_names:
        universe.append("Omegaverse")
    if any("fantasy" in category for category in category_names):
        universe.append("Fantasia")
    if "xianxia" in category_names:
        universe.append("Xianxia")

    return {
        "series_id": details["series_id"],
        "title": details["title"],
        "url": details.get("url"),
        "type": details.get("type"),
        "format": infer_format(details),
        "year": details.get("year"),
        "latest_chapter": details.get("latest_chapter"),
        "status": details.get("status"),
        "completed": details.get("completed"),
        "genres": [
            item["genre"]
            for item in details.get("genres", [])
            if item.get("genre")
        ],
        "categories": categories,
        "associated_titles": [
            item["title"]
            for item in details.get("associated", [])
            if item.get("title")
        ],
        "universe": universe,
    }


def load_json_object(path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"Formato inválido em {path}: era esperado um objeto.")
    return data


def load_catalog(path=CATALOG_FILE):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"Formato inválido em {path}: era esperada uma lista.")
    return data


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def wait_between_requests(delay):
    if delay > 0:
        time.sleep(delay)


def enrich_catalog(
    mangas,
    delay=3.0,
    limit=None,
    progress_path=PROGRESS_FILE,
    cache_path=CACHE_FILE,
):
    progress = load_json_object(progress_path)
    cache = load_json_object(cache_path)
    processed = 0

    for manga in mangas:
        title = manga["nome"]
        if title in progress:
            continue
        if limit is not None and processed >= limit:
            break
        if title in cache:
            progress[title] = {
                "match_status": "Cache confirmado",
                **cache[title],
            }
            save_json(progress_path, progress)
            processed += 1
            continue

        print(f"[BUSCAR] {title}")
        search = search_series(title)
        record, match_status = choose_search_result(title, search)
        entry = {"match_status": match_status}
        wait_between_requests(delay)

        if record:
            series_id = record["series_id"]
            print(f"[DETALHAR] {title} ({series_id})")
            details = get_series(series_id)
            summary = summarize_series(details)
            cache[title] = summary
            entry.update(summary)
            wait_between_requests(delay)

        progress[title] = entry
        save_json(progress_path, progress)
        save_json(cache_path, cache)
        processed += 1

    return progress, cache


def join_values(values):
    return " | ".join(str(value) for value in values if value not in (None, ""))


def build_csv_row(manga, external=None, progress=None):
    external = external or {}
    progress = progress or {}
    aliases = list(manga.get("alias", []))
    aliases.extend(external.get("associated_titles", []))
    aliases = list(dict.fromkeys(aliases))
    themes = manga.get("tematica") or external.get("genres", [])
    universe = manga.get("universo") or external.get("universe", [])
    return {
        "Nome": manga["nome"],
        "ID da obra": external.get("series_id", ""),
        "Alias": join_values(aliases),
        "Status": manga.get("status", ""),
        "Nota": manga.get("nota", ""),
        "Último lido": manga.get("ultimo_lido", ""),
        "Último capítulo disponível": manga.get("main_caps", ""),
        "Capítulos encontrados": manga.get("chapters_found", ""),
        "Side stories": manga.get("side_stories_found", ""),
        "Lacunas": join_values(manga.get("missing_ranges", [])) or "-",
        "Status da contagem": manga.get("count_status", ""),
        "Capítulo MangaUpdates": external.get("latest_chapter", ""),
        "MangaUpdates": external.get("url", ""),
        "Temática": join_values(themes),
        "Formato": manga.get("formato") or external.get("format", ""),
        "Universo": join_values(universe),
        "Picância": manga.get("nivel_picancia", ""),
        "Correspondência API": progress.get("match_status", "Pendente"),
    }


def write_csv(mangas, cache, progress, path=CSV_FILE):
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
                )
            )
    temporary.replace(path)


def refresh_cache(mappings_path=MAPPINGS_FILE, cache_path=CACHE_FILE):
    mappings = load_json_object(mappings_path)
    cache = load_json_object(cache_path)
    for title, series_id in mappings.items():
        print(f"[CONSULTAR] {title} ({series_id})")
        cache[title] = summarize_series(get_series(series_id))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return cache


def main():
    parser = argparse.ArgumentParser(
        description="Consulta e armazena metadados confirmados do MangaUpdates."
    )
    parser.add_argument("--search", help="Busca candidatos sem alterar o cache.")
    parser.add_argument(
        "--generate-csv",
        action="store_true",
        help="Executa busca e detalhe para gerar o CSV de importação.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Intervalo entre requisições, em segundos (padrão: 3).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limita a quantidade de obras processadas nesta execução.",
    )
    args = parser.parse_args()

    try:
        if args.search:
            response = search_series(args.search)
            for result in response.get("results", []):
                record = result.get("record", {})
                print(
                    f"{record.get('series_id')} | {record.get('title')} | "
                    f"{record.get('type')} | {record.get('year')}"
                )
            return
        if args.generate_csv:
            if args.delay < 0:
                raise SystemExit("--delay não pode ser negativo.")
            mangas = load_catalog()
            progress, cache = enrich_catalog(
                mangas,
                delay=args.delay,
                limit=args.limit,
            )
            write_csv(mangas, cache, progress)
            completed = sum(
                1 for manga in mangas if manga["nome"] in progress
            )
            print(f"CSV gerado: {CSV_FILE}")
            print(f"Obras processadas: {completed}/{len(mangas)}")
            print(
                f"Pendentes para outra execução: {len(mangas) - completed}"
            )
            return
        refresh_cache()
        print(f"Cache atualizado: {CACHE_FILE}")
    except urllib.error.URLError as error:
        raise SystemExit(f"Falha ao consultar MangaUpdates: {error}") from error


if __name__ == "__main__":
    main()
