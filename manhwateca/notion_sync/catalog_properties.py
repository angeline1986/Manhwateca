def build_properties(manga):
    properties = {
        "Nome": {"title": [{"text": {"content": manga["nome"]}}]},
        "Status": {"select": {"name": manga["status"]}},
        "Nota": {"select": {"name": manga["nota"]}},
        "Último cap disponível": {"number": manga.get("main_caps", 0)},
        "Tamanho": {"select": {"name": manga["tamanho"]}},
        "Caps encontrados": {"number": manga.get("chapters_found", 0)},
        "Side stories": {"number": manga.get("side_stories_found", 0)},
        "Status da contagem": {
            "select": {"name": manga.get("count_status", "Revisar")}
        },
    }
    if manga.get("alias"):
        properties["Alias"] = {
            "rich_text": [{
                "text": {"content": ", ".join(manga["alias"])}
            }]
        }
    if manga.get("ultimo_lido", 0) > 0:
        properties["Último lido"] = {"number": manga["ultimo_lido"]}
    _add_external_fields(properties, manga)
    _add_classification_fields(properties, manga)
    return properties


def _add_external_fields(properties, manga):
    if manga.get("mangaupdates_latest_chapter") is not None:
        properties["Cap MangaUpdates"] = {
            "number": manga["mangaupdates_latest_chapter"]
        }
    if manga.get("mangaupdates_url"):
        properties["MangaUpdates"] = {"url": manga["mangaupdates_url"]}


def _add_classification_fields(properties, manga):
    if "tematica" in manga:
        properties["Temática"] = {
            "multi_select": [
                {"name": value} for value in manga.get("tematica", [])
            ]
        }
    if "formato" in manga:
        properties["Formato"] = {
            "select": {"name": manga["formato"]} if manga.get("formato") else None
        }
    if "universo" in manga:
        properties["Universo"] = {
            "multi_select": [
                {"name": value} for value in manga.get("universo", [])
            ]
        }
    if "nivel_picancia" in manga:
        properties["Picância"] = {
            "select": (
                {"name": manga["nivel_picancia"]}
                if manga.get("nivel_picancia")
                else None
            )
        }
