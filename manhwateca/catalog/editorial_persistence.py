import json

from manhwateca.notion_sync.matching import normalize_title


def update_metadata(path, name, changes):
    data = _load_object(path)
    key = _metadata_key(data, name)
    metadata = data.setdefault(key, {})
    mapping = {"Alias": "alias", "Interesse": "interesse"}
    for source, target in mapping.items():
        if source in changes:
            metadata[target] = changes[source]
    if key == name:
        metadata.setdefault("nome_oficial", name)
    _write_json(path, data)


def update_catalog(path, name, row, changes):
    if not path.is_file():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    names = {normalize_title(name), normalize_title(row.get("Alias", ""))}
    manga = next((item for item in data if names & {
        normalize_title(item.get("nome")),
        *(normalize_title(alias) for alias in item.get("alias", [])),
    }), None)
    if manga is None:
        return
    mapping = {
        "Status": "status", "Nota": "nota", "Interesse": "interesse",
        "Picância": "nivel_picancia", "Último lido": "ultimo_lido",
        "Temática": "tematica", "Universo": "universo", "Alias": "alias",
    }
    for source, target in mapping.items():
        if source not in changes:
            continue
        value = changes[source]
        if source in {"Temática", "Universo", "Alias"}:
            value = [part.strip() for part in value.split("|") if part.strip()]
        elif source == "Último lido":
            value = int(value)
            manga["proximo_a_ler"] = value + 1
        manga[target] = value
    _write_json(path, data)


def _metadata_key(data, name):
    normalized = normalize_title(name)
    for key, metadata in data.items():
        names = {key, metadata.get("nome_oficial"), metadata.get("alias")}
        if normalized in {normalize_title(item) for item in names if item}:
            return key
    return name


def _load_object(path):
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
