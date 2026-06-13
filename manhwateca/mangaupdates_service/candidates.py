import json
import unicodedata
from pathlib import Path

from manhwateca.mangaupdates_service.matching import (
    filter_relevant_candidates,
    normalize_title,
    rank_search_results,
    select_ranked_candidate,
)


CONFIRMED_STATUSES = {
    "Confirmado automaticamente",
    "Confirmado manualmente",
}


def load_id_searches(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"Formato inválido em {path}: era esperada uma lista.")
    for item in data:
        if not isinstance(item, dict) or not item.get("Nome"):
            raise ValueError("Cada item deve possuir o campo Nome.")
    return data


def load_catalog(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"Formato inválido em {path}: era esperada uma lista.")
    return data


def add_catalog_titles_to_id_searches(items, catalog_path):
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
    candidates = [*terms, configured.get("nome_oficial"), name]
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


def search_candidates_for_item(
    item,
    metadata,
    search_function,
    per_page=10,
):
    best_candidates = []
    best_term = item["Nome"].strip()
    for term in search_terms_for_item(item, metadata):
        response = search_function(term, per_page=per_page)
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
    return include_numbers if initial.isdigit() else initial in letters


def clean_confirmed_candidates(items):
    cleaned = False
    for item in items:
        if (
            item.get("Status") in CONFIRMED_STATUSES
            and item.pop("IDs", None) is not None
        ):
            cleaned = True
    return cleaned


def apply_candidate_result(item, candidates, search_term):
    item["Termo de busca"] = search_term
    selected, status = select_ranked_candidate(candidates)
    item["Status"] = status
    if selected:
        item.pop("IDs", None)
        item["ID"] = selected["id"]
        item["Nome encontrado"] = selected["titulo"]
    else:
        item["IDs"] = candidates
        item.pop("ID", None)
        item.pop("Nome encontrado", None)
    return selected


def incomplete_review_items(items):
    return [
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
