import re
import unicodedata


def normalize_title(value):
    value = unicodedata.normalize("NFD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.casefold().replace("_", " ")
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def catalog_title_candidates(manga, title_aliases):
    name = manga["nome"].strip()
    candidates = {normalize_title(name)}
    candidates.update(
        normalize_title(alias)
        for alias in manga.get("alias", [])
        if alias.strip()
    )
    normalized_name = normalize_title(name)
    for old_name, new_name in title_aliases.items():
        if normalize_title(new_name) == normalized_name:
            candidates.add(normalize_title(old_name))
    return candidates


def csv_equivalent_names(row, metadata, split_values):
    names = {row.get("Nome", "").strip(), *split_values(row.get("Alias"))}
    normalized_names = {normalize_title(name) for name in names if name}
    for local_name, values in metadata.items():
        search_names = values.get("nomes_busca", [])
        if isinstance(search_names, str):
            search_names = [search_names]
        configured = {
            local_name,
            values.get("nome_oficial", ""),
            values.get("alias", ""),
            *search_names,
        }
        if normalized_names & {
            normalize_title(name) for name in configured if name
        }:
            names.update(name for name in configured if name)
    return {normalize_title(name) for name in names if name}
