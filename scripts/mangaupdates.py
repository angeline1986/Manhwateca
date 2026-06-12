import argparse
import csv
import json
import random
import re
import time
import unicodedata
import urllib.error
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path


API_BASE = "https://api.mangaupdates.com/v1"
BL_GENRES = {"yaoi", "shounen ai"}
SUPPORTED_TYPES = {"Manhwa", "Manhua", "Manga", "OEL"}
MAPPINGS_FILE = Path("config/mangaupdates.json")
CACHE_FILE = Path("data/mangaupdates.json")
CATALOG_FILE = Path("data/mangas.json")
CSV_FILE = Path("reports/integrations/manhwateca_import.csv")
PROGRESS_FILE = Path("data/mangaupdates_progress.json")
METADATA_FILE = Path("config/catalog_metadata.json")
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


def title_tokens(value):
    ignored = {
        "a", "an", "as", "at", "by", "for", "from", "in", "into",
        "of", "on", "the", "to", "with",
    }
    return {
        token
        for token in normalize_title(value).split()
        if token not in ignored
    }


def title_similarity(source, candidate):
    normalized_source = normalize_title(source)
    normalized_candidate = normalize_title(candidate)
    sequence_score = SequenceMatcher(
        None,
        normalized_source,
        normalized_candidate,
    ).ratio()
    source_tokens = title_tokens(source)
    candidate_tokens = title_tokens(candidate)
    union = source_tokens | candidate_tokens
    token_score = (
        len(source_tokens & candidate_tokens) / len(union)
        if union
        else 0
    )
    containment = (
        len(source_tokens & candidate_tokens) / len(source_tokens)
        if source_tokens
        else 0
    )
    return round(
        max(sequence_score, token_score, containment * 0.9),
        4,
    )


def truncate_text(value, limit=734):
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[:limit - 1].rstrip() + "…"


def rank_search_results(title, response):
    candidates = []
    seen_ids = set()
    for position, result in enumerate(response.get("results", []), start=1):
        record = result.get("record", {})
        series_id = record.get("series_id")
        if not series_id or series_id in seen_ids:
            continue
        seen_ids.add(series_id)
        candidate_title = record.get("title") or result.get("hit_title") or ""
        score = title_similarity(title, candidate_title)
        if record.get("type") == "Manhwa":
            score = min(1.0, score + 0.05)
        genres = record.get("genres") or []
        normalized_genres = {str(genre).casefold() for genre in genres}
        candidates.append({
            "id": series_id,
            "titulo": candidate_title,
            "tipo": record.get("type"),
            "ano": record.get("year"),
            "url": record.get("url"),
            "descricao": truncate_text(record.get("description")),
            "generos": genres,
            "bl": bool(normalized_genres & BL_GENRES),
            "pontuacao": round(score, 4),
            "posicao": position,
        })
    return sorted(
        candidates,
        key=lambda item: (-item["pontuacao"], item["posicao"]),
    )


def filter_relevant_candidates(candidates):
    supported = [
        candidate
        for candidate in candidates
        if candidate.get("tipo") in SUPPORTED_TYPES
    ]
    bl_candidates = [
        candidate for candidate in supported if candidate.get("bl")
    ]
    return bl_candidates or supported


def select_ranked_candidate(candidates, threshold=0.72, margin=0.08):
    if not candidates:
        return None, "Não encontrada"
    best = candidates[0]
    second_score = candidates[1]["pontuacao"] if len(candidates) > 1 else 0
    if best["pontuacao"] >= 0.99 and second_score < 0.99:
        return best, "Confirmado automaticamente"
    if second_score >= 0.65:
        return None, "Revisar"
    if (
        best["pontuacao"] >= threshold
        and best["pontuacao"] - second_score >= margin
    ):
        return best, "Confirmado automaticamente"
    return None, "Revisar"


def load_id_searches(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"Formato inválido em {path}: era esperada uma lista.")
    for item in data:
        if not isinstance(item, dict) or not item.get("Nome"):
            raise ValueError("Cada item deve possuir o campo Nome.")
    return data


def add_catalog_titles_to_id_searches(items, catalog_path=CATALOG_FILE):
    if not catalog_path.exists():
        return 0

    known = {normalize_title(item["Nome"]) for item in items}
    added = 0
    for manga in load_catalog(catalog_path):
        title = manga["nome"].strip()
        normalized = normalize_title(title)
        if normalized in known:
            continue
        items.append({"Nome": title})
        known.add(normalized)
        added += 1
    return added


def search_terms_for_item(item, metadata):
    name = item["Nome"].strip()
    configured = metadata.get(name, {})
    terms = configured.get("nomes_busca", [])
    if isinstance(terms, str):
        terms = [terms]
    official = configured.get("nome_oficial")
    candidates = [*terms, official, name]
    unique = []
    seen = set()
    for term in candidates:
        term = str(term or "").strip()
        normalized = normalize_title(term)
        if not term or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(term)
    return unique


def search_candidates_for_item(item, metadata, per_page=10):
    best_candidates = []
    best_term = item["Nome"].strip()
    for term in search_terms_for_item(item, metadata):
        response = search_series(term, per_page=per_page)
        candidates = filter_relevant_candidates(
            rank_search_results(term, response)
        )
        if candidates and (
            not best_candidates
            or candidates[0]["pontuacao"] > best_candidates[0]["pontuacao"]
        ):
            best_candidates = candidates
            best_term = term
        if candidates and candidates[0]["pontuacao"] >= 0.95:
            break
    return best_candidates, best_term


def normalize_initial_filter(value):
    value = unicodedata.normalize("NFD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii").upper()
    letters = {character for character in value if character.isalpha()}
    include_numbers = any(character.isdigit() for character in value)
    return letters, include_numbers


def matches_initial_filter(title, initial_filter):
    letters, include_numbers = initial_filter
    if not letters and not include_numbers:
        return True
    normalized = normalize_title(title)
    if not normalized:
        return False
    initial = normalized[0].upper()
    if initial.isdigit():
        return include_numbers
    return initial in letters


def fill_ids_file(
    path,
    delay=3.0,
    limit=None,
    per_page=10,
    retry_review=False,
    catalog_path=CATALOG_FILE,
    initials="",
):
    items = load_id_searches(path)
    metadata = load_json_object(METADATA_FILE)
    added = add_catalog_titles_to_id_searches(items, catalog_path)
    if added:
        save_json(path, items)
        print(f"[CATÁLOGO] {added} nova(s) obra(s) adicionada(s) ao JSON.")

    cleaned = False
    for item in items:
        if item.get("Status") in {
            "Confirmado automaticamente",
            "Confirmado manualmente",
        } and item.pop("IDs", None) is not None:
            cleaned = True
    if cleaned:
        save_json(path, items)

    processed = 0
    initial_filter = normalize_initial_filter(initials)
    for item in items:
        if item.get("ID"):
            continue
        if not matches_initial_filter(item["Nome"], initial_filter):
            continue
        if item.get("Status") == "Revisar" and not retry_review:
            continue
        if limit is not None and processed >= limit:
            break

        name = item["Nome"].strip()
        print(f"[BUSCAR ID] {name}")
        candidates, search_term = search_candidates_for_item(
            item,
            metadata,
            per_page=per_page,
        )
        item["Termo de busca"] = search_term
        selected, status = select_ranked_candidate(candidates)
        item["Status"] = status
        if selected:
            item.pop("IDs", None)
            item["ID"] = selected["id"]
            item["Nome encontrado"] = selected["titulo"]
            print(
                f"[CONFIRMADO] {selected['id']} | "
                f"{selected['titulo']} | {selected['pontuacao']:.2f}"
            )
        else:
            item["IDs"] = candidates
            item.pop("ID", None)
            item.pop("Nome encontrado", None)
            print(f"[REVISAR] {name}: {len(candidates)} candidato(s)")

        save_json(path, items)
        processed += 1
        wait_between_requests(delay)

    return items, processed


def refresh_incomplete_candidates(
    path,
    delay=3.0,
    limit=10,
    per_page=10,
):
    items = load_id_searches(path)
    metadata = load_json_object(METADATA_FILE)
    pending = [
        item
        for item in items
        if item.get("Status") == "Revisar"
        and any(
            "url" not in candidate
            or "descricao" not in candidate
            or "generos" not in candidate
            or "bl" not in candidate
            for candidate in item.get("IDs", [])
        )
    ]
    selected = pending[:limit] if limit is not None else pending
    for item in selected:
        name = item["Nome"].strip()
        print(f"[ATUALIZAR CANDIDATOS] {name}")
        candidates, search_term = search_candidates_for_item(
            item,
            metadata,
            per_page=per_page,
        )
        item["Termo de busca"] = search_term
        selected_candidate, status = select_ranked_candidate(candidates)
        item["Status"] = status
        if selected_candidate:
            item.pop("IDs", None)
            item["ID"] = selected_candidate["id"]
            item["Nome encontrado"] = selected_candidate["titulo"]
        else:
            item["IDs"] = candidates
            item.pop("ID", None)
            item.pop("Nome encontrado", None)
        save_json(path, items)
        wait_between_requests(delay)
    return len(selected), len(pending) - len(selected)


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
    path=CSV_FILE,
    metadata_path=METADATA_FILE,
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


def update_csv_from_confirmed_ids(
    ids_path,
    csv_path=CSV_FILE,
    delay=3.0,
    limit=None,
    cache_path=CACHE_FILE,
):
    items = load_id_searches(ids_path)
    confirmed = [
        item
        for item in items
        if item.get("Status") in {
            "Confirmado automaticamente",
            "Confirmado manualmente",
        }
        and item.get("ID")
    ]
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV não encontrado: {csv_path}. Gere o CSV antes de atualizá-lo."
        )

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = reader.fieldnames or CSV_COLUMNS

    row_index = {}
    for position, row in enumerate(rows):
        for value in (row.get("Nome"), row.get("Alias")):
            if not value:
                continue
            for title in value.split("|"):
                row_index.setdefault(normalize_title(title.strip()), position)

    metadata = load_json_object(METADATA_FILE)
    for local_title, values in metadata.items():
        candidate_names = [
            values.get("nome_oficial"),
            values.get("alias"),
        ]
        position = next(
            (
                row_index.get(normalize_title(candidate))
                for candidate in candidate_names
                if candidate and row_index.get(normalize_title(candidate)) is not None
            ),
            None,
        )
        if position is not None:
            row_index.setdefault(normalize_title(local_title), position)

    cache = load_json_object(cache_path)
    processed = 0
    updated = 0
    uncached = []
    missing_from_csv = []
    handled_ids = set()
    for item in confirmed:
        if limit is not None and processed >= limit:
            break
        series_id = item["ID"]
        if series_id in handled_ids:
            continue
        handled_ids.add(series_id)

        name = item["Nome"].strip()
        position = row_index.get(normalize_title(name))
        if position is None:
            missing_from_csv.append(name)
            continue

        cache_key = str(series_id)
        summary = cache.get(cache_key)
        if not summary:
            uncached.append(name)
            continue

        row = rows[position]
        values = {
            "ID da obra": summary.get("series_id", series_id),
            "Capítulo MangaUpdates": summary.get("latest_chapter") or "",
            "MangaUpdates": summary.get("url") or "",
            "Temática": join_values(summary.get("genres", [])),
            "Formato": summary.get("format") or row.get("Formato", ""),
            "Universo": join_values(summary.get("universe", [])),
            "Correspondência API": (
                "ID confirmado manualmente"
                if item["Status"] == "Confirmado manualmente"
                else "ID confirmado automaticamente"
            ),
        }
        changed = any(
            str(row.get(field, "")) != str(value)
            for field, value in values.items()
        )
        row.update(values)
        processed += 1
        updated += int(changed)

    temporary = csv_path.with_suffix(f"{csv_path.suffix}.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(csv_path)
    return updated, processed, uncached, missing_from_csv


def fetch_confirmed_details(
    ids_path,
    delay=3.0,
    limit=None,
    cache_path=CACHE_FILE,
):
    items = load_id_searches(ids_path)
    confirmed = [
        item
        for item in items
        if item.get("Status") in {
            "Confirmado automaticamente",
            "Confirmado manualmente",
        }
        and item.get("ID")
    ]
    cache = load_json_object(cache_path)
    pending = [
        item for item in confirmed if str(item["ID"]) not in cache
    ]
    selected = pending[:limit] if limit is not None else pending

    for item in selected:
        series_id = item["ID"]
        print(f"[DETALHAR] {item['Nome']} ({series_id})")
        cache[str(series_id)] = summarize_series(get_series(series_id))
        save_json(cache_path, cache)
        wait_between_requests(delay)

    return len(selected), len(pending) - len(selected)


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
        "--update-csv-from-ids",
        type=Path,
        help="Atualiza o CSV usando os IDs confirmados no JSON informado.",
    )
    parser.add_argument(
        "--fetch-details-from-ids",
        type=Path,
        help="Consulta detalhes dos IDs confirmados e atualiza o cache.",
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
    parser.add_argument(
        "--fill-ids",
        type=Path,
        help="Lê um JSON de obras e preenche IDs/candidatos da busca.",
    )
    parser.add_argument(
        "--per-page",
        type=int,
        default=10,
        help="Quantidade de candidatos por busca de ID (padrão: 10).",
    )
    parser.add_argument(
        "--retry-review",
        action="store_true",
        help="Reprocessa itens marcados como Revisar.",
    )
    parser.add_argument(
        "--initials",
        default="",
        help="Filtra obras pelas letras iniciais, por exemplo A, ABC ou 0-9.",
    )
    parser.add_argument(
        "--refresh-incomplete-candidates",
        type=Path,
        help="Atualiza candidatos sem URL, descrição ou classificação BL.",
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
        if args.fill_ids:
            if args.delay < 0:
                raise SystemExit("--delay não pode ser negativo.")
            if args.per_page < 1:
                raise SystemExit("--per-page deve ser maior que zero.")
            items, processed = fill_ids_file(
                args.fill_ids,
                delay=args.delay,
                limit=args.limit,
                per_page=args.per_page,
                retry_review=args.retry_review,
                initials=args.initials,
            )
            confirmed = sum(bool(item.get("ID")) for item in items)
            review = sum(item.get("Status") == "Revisar" for item in items)
            pending = len(items) - confirmed - review
            print()
            print(f"Arquivo atualizado: {args.fill_ids}")
            print(f"Processadas nesta execução: {processed}")
            print(f"IDs confirmados: {confirmed}")
            print(f"Para revisão: {review}")
            print(f"Pendentes: {pending}")
            return
        if args.refresh_incomplete_candidates:
            if args.delay < 0:
                raise SystemExit("--delay não pode ser negativo.")
            if args.per_page < 1:
                raise SystemExit("--per-page deve ser maior que zero.")
            processed, pending = refresh_incomplete_candidates(
                args.refresh_incomplete_candidates,
                delay=args.delay,
                limit=args.limit,
                per_page=args.per_page,
            )
            print()
            print(f"Obras atualizadas nesta execução: {processed}")
            print(f"Obras antigas para próximos lotes: {pending}")
            return
        if args.update_csv_from_ids:
            if args.delay < 0:
                raise SystemExit("--delay não pode ser negativo.")
            updated, checked, uncached, missing_from_csv = (
                update_csv_from_confirmed_ids(
                args.update_csv_from_ids,
                delay=args.delay,
                limit=args.limit,
                )
            )
            print()
            print(f"CSV atualizado: {CSV_FILE}")
            print(f"Obras verificadas: {checked}")
            print(f"Linhas realmente alteradas: {updated}")
            print(f"Aguardando consulta de detalhes na API: {len(uncached)}")
            for name in uncached:
                print(f"- {name}")
            if uncached:
                print()
                print(
                    "Próximo passo: use a opção 5.2 para consultar "
                    "o próximo lote na API."
                )
            print(f"Obras realmente ausentes no CSV: {len(missing_from_csv)}")
            for name in missing_from_csv:
                print(f"- {name}")
            return
        if args.fetch_details_from_ids:
            if args.delay < 0:
                raise SystemExit("--delay não pode ser negativo.")
            processed, pending = fetch_confirmed_details(
                args.fetch_details_from_ids,
                delay=args.delay,
                limit=args.limit,
            )
            print()
            print(f"Detalhes consultados nesta execução: {processed}")
            print(f"IDs confirmados ainda pendentes: {pending}")
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
